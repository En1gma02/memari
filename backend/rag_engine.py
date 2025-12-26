"""
rag_engine.py - RAG (Retrieval-Augmented Generation) Engine

Handles:
- FAISS index loading and searching
- Hybrid retrieval (75% cosine + 25% BM25)
- CrossEncoder re-ranking
- Session rewriting and indexing
- User persona updates
"""

import faiss
import pickle
import numpy as np
import time
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict
from collections import Counter
import math

from sentence_transformers import SentenceTransformer, CrossEncoder
from cerebras.cloud.sdk import Cerebras

from config import (
    FAISS_INDEX_PATH,
    METADATA_PATH,
    USER_PERSONA_PATH,
    CEREBRAS_API_KEY,
    CEREBRAS_MODEL,
    EMBEDDING_MODEL,
    EMBEDDING_DIMENSION,
    CONFIDENCE_THRESHOLD,
    TOP_K_RESULTS,
    FUSION_QUERY_COUNT,
    CEREBRAS_DELAY_SECONDS,
    ARI_FAISS_INDEX_PATH,
    ARI_METADATA_PATH,
    # V2 RAG Optimizations
    FAISS_CANDIDATES,
    CONTEXT_EXPANSION_WINDOW,
    CONTEXT_EXPANSION_MIN_SCORE,
    ADAPTIVE_K_HIGH_THRESHOLD,
    ADAPTIVE_K_LOW_THRESHOLD,
    ADAPTIVE_K_HIGH,
    ADAPTIVE_K_LOW,
    # Speed optimizations
    DISABLE_FUSION_RETRIEVAL,
    DISABLE_QUERY_EXPANSION
)
from prompts import SESSION_REWRITING_PROMPT, PERSONA_UPDATE_PROMPT
from models import MemoryResult, MemoryChunk, PersonaUpdate


# ==============================================================================
# BM25 IMPLEMENTATION
# ==============================================================================

class BM25:
    """Simple BM25 implementation for hybrid search."""
    
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        """
        Initialize BM25 with documents.
        
        Args:
            documents: List of document strings
            k1: Term frequency saturation parameter
            b: Document length normalization parameter
        """
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        
        # Tokenize documents
        self.tokenized_docs = [self._tokenize(doc) for doc in documents]
        
        # Calculate average document length
        self.avg_doc_len = sum(len(doc) for doc in self.tokenized_docs) / max(self.doc_count, 1)
        
        # Calculate document frequencies
        self.doc_freqs: Dict[str, int] = {}
        for doc in self.tokenized_docs:
            for term in set(doc):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        
        # Pre-compute term frequencies for each document (V2 optimization)
        self.term_freqs = [Counter(doc) for doc in self.tokenized_docs]
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
        if not isinstance(text, str):
            return []
        return re.findall(r'\w+', text.lower())
    
    def _idf(self, term: str) -> float:
        """Calculate IDF for a term."""
        doc_freq = self.doc_freqs.get(term, 0)
        return math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def score(self, query: str, doc_idx: int) -> float:
        """Calculate BM25 score for a query against a document."""
        query_terms = self._tokenize(query)
        doc_terms = self.tokenized_docs[doc_idx]
        doc_len = len(doc_terms)
        
        # Use pre-computed term frequencies (V2 optimization)
        term_freqs = self.term_freqs[doc_idx]
        
        score = 0.0
        for term in query_terms:
            if term in term_freqs:
                tf = term_freqs[term]
                idf = self._idf(term)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                score += idf * numerator / denominator
        
        return score
    
    def search(self, query: str, top_k: int = 5) -> List[Tuple[int, float]]:
        """
        Search documents using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of (doc_idx, score) tuples sorted by score descending
        """
        scores = [(i, self.score(query, i)) for i in range(self.doc_count)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]
    
    def score_candidates(self, query: str, candidate_ids: List[int]) -> Dict[int, float]:
        """
        V2: Score only the given candidate IDs (not all documents).
        Much faster for large document collections.
        """
        query_terms = self._tokenize(query)
        scores = {}
        for doc_idx in candidate_ids:
            if 0 <= doc_idx < self.doc_count:
                scores[doc_idx] = self._score_with_terms(query_terms, doc_idx)
        return scores
    
    def _score_with_terms(self, query_terms: List[str], doc_idx: int) -> float:
        """Score a document with pre-tokenized query terms."""
        doc_len = len(self.tokenized_docs[doc_idx])
        term_freqs = self.term_freqs[doc_idx]
        
        score = 0.0
        for term in query_terms:
            if term in term_freqs:
                tf = term_freqs[term]
                idf = self._idf(term)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_len)
                score += idf * numerator / denominator
        return score


# ==============================================================================
# RAG ENGINE
# ==============================================================================

class RAGEngine:
    """Main RAG engine with hybrid retrieval and re-ranking."""
    
    def __init__(self):
        """Initialize the RAG engine with models and FAISS index."""
        print("🧠 Initializing RAG Engine...")
        
        # Initialize embedding model
        print(f"Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Initialize re-ranker (CrossEncoder)
        print("Loading re-ranker: cross-encoder/ms-marco-MiniLM-L6-v2")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")
        
        # Initialize Cerebras client
        self.cerebras_client = Cerebras(api_key=CEREBRAS_API_KEY)
        
        # Load FAISS index and metadata
        self.index = None
        self.metadata = None
        self.bm25 = None
        self._load_index()
        
        # Load Ari Life index
        self.ari_index = None
        self.ari_metadata = None
        self.ari_bm25 = None
        self._load_ari_index()
        
        print("✅ RAG Engine initialized successfully!")
    
    def _load_index(self):
        """Load FAISS index, metadata, and initialize BM25."""
        if not FAISS_INDEX_PATH.exists():
            print("⚠️  FAISS index not found. Creating empty index.")
            self.index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
            self.metadata = {"id_to_text": {}, "id_to_original": {}}
            self.bm25 = None
            return
        
        print(f"Loading FAISS index from {FAISS_INDEX_PATH}")
        self.index = faiss.read_index(str(FAISS_INDEX_PATH))
        
        print(f"Loading metadata from {METADATA_PATH}")
        with open(METADATA_PATH, "rb") as f:
            self.metadata = pickle.load(f)
        
        num_vectors = self.index.ntotal
        print(f"Loaded {num_vectors} memory vectors")
        
        # Initialize BM25 with all documents
        if num_vectors > 0:
            documents = [
                self.metadata["id_to_text"].get(i, "") 
                for i in range(num_vectors)
            ]
            self.bm25 = BM25(documents)
            print(f"Initialized BM25 index with {num_vectors} documents")
    
    def _load_ari_index(self):
        """Load Ari Life FAISS index, metadata, and initialize BM25."""
        if not ARI_FAISS_INDEX_PATH.exists():
            print("⚠️  Ari Life FAISS index not found. Run index_ari_life.py first.")
            self.ari_index = faiss.IndexFlatL2(EMBEDDING_DIMENSION)
            self.ari_metadata = {"id_to_text": {}, "id_to_original": {}}
            self.ari_bm25 = None
            return
        
        print(f"Loading Ari Life FAISS index from {ARI_FAISS_INDEX_PATH}")
        self.ari_index = faiss.read_index(str(ARI_FAISS_INDEX_PATH))
        
        print(f"Loading Ari Life metadata from {ARI_METADATA_PATH}")
        with open(ARI_METADATA_PATH, "rb") as f:
            self.ari_metadata = pickle.load(f)
        
        num_vectors = self.ari_index.ntotal
        print(f"Loaded {num_vectors} Ari Life vectors")
        
        # Initialize BM25 for Ari Life
        if num_vectors > 0:
            documents = [
                self.ari_metadata["id_to_text"].get(i, "") 
                for i in range(num_vectors)
            ]
            self.ari_bm25 = BM25(documents)
            print(f"Initialized Ari Life BM25 index with {num_vectors} documents")
    
    def get_user_persona(self) -> str:
        """Read and return the user persona file."""
        if not USER_PERSONA_PATH.exists():
            return "No user persona available yet."
        
        with open(USER_PERSONA_PATH, "r", encoding="utf-8") as f:
            return f.read()
    
    def get_long_term_memory(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        force_fusion: bool = False
    ) -> MemoryResult:
        """
        Search long-term memory with hybrid retrieval (75% cosine + 25% BM25)
        and CrossEncoder re-ranking.
        
        Args:
            query: Search query text
            top_k: Number of results to retrieve
            force_fusion: Force fusion retrieval regardless of confidence
        
        Returns:
            MemoryResult with chunks, scores, and fusion usage info
        """
        # Use the generic search method
        return self._search_index(
            query=query,
            index=self.index,
            metadata=self.metadata,
            bm25=self.bm25,
            top_k=top_k,
            force_fusion=force_fusion,
            index_name="Long Term Memory"
        )

    def get_ari_life_memory(
        self,
        query: str,
        top_k: int = TOP_K_RESULTS,
        force_fusion: bool = False
    ) -> MemoryResult:
        """
        Search Ari's life story with hybrid retrieval.
        """
        return self._search_index(
            query=query,
            index=self.ari_index,
            metadata=self.ari_metadata,
            bm25=self.ari_bm25,
            top_k=top_k,
            force_fusion=force_fusion,
            index_name="Ari Life"
        )
    
    def _search_index(
        self,
        query: str,
        index,
        metadata,
        bm25,
        top_k: int,
        force_fusion: bool,
        index_name: str
    ) -> MemoryResult:
        """
        V2 Optimized hybrid search with:
        - Query expansion (LLM adds synonyms)
        - FAISS-first BM25 (score only candidates, not all docs)
        - Adaptive Top-K based on confidence
        - Contextual chunk expansion for LLM
        """
        if index.ntotal == 0:
            print(f"⚠️  {index_name} FAISS index is empty")
            return MemoryResult(chunks=[], scores=[], fusion_used=False)
        
        print(f"🔍 V2 Hybrid search in {index_name} for: '{query}'")
        
        # =====================================================================
        # Step 1: Query expansion (V2) - SKIP IF DISABLED FOR SPEED
        # =====================================================================
        if DISABLE_QUERY_EXPANSION:
            expanded_query = query  # Skip slow LLM call
        else:
            expanded_query = self._expand_query(query)
        
        # =====================================================================
        # Step 2: Dense retrieval (FAISS) on both original and expanded query
        # =====================================================================
        all_candidates: Dict[int, float] = {}
        
        for q in [query, expanded_query]:
            if not isinstance(q, str) or not q.strip():
                continue
            query_embedding = self.embedding_model.encode([q])
            num_candidates = min(FAISS_CANDIDATES, index.ntotal)
            distances, indices = index.search(query_embedding, num_candidates)
            
            for idx, dist in zip(indices[0], distances[0]):
                if idx != -1:
                    score = 1.0 / (1.0 + dist)
                    if idx not in all_candidates or score > all_candidates[idx]:
                        all_candidates[idx] = score
        
        # =====================================================================
        # Step 3: BM25 on FAISS candidates only (V2 - MAJOR SPEED IMPROVEMENT)
        # =====================================================================
        if bm25 is not None and all_candidates:
            candidate_ids = list(all_candidates.keys())
            bm25_scores = bm25.score_candidates(query, candidate_ids)
            
            # Normalize BM25 scores
            max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
            
            # Hybrid combine (75% cosine + 25% BM25)
            for idx in all_candidates:
                cosine_score = all_candidates[idx]
                bm25_score = bm25_scores.get(idx, 0) / max_bm25 if max_bm25 > 0 else 0
                all_candidates[idx] = 0.75 * cosine_score + 0.25 * bm25_score
        
        # Sort and get top candidates for re-ranking
        sorted_candidates = sorted(
            all_candidates.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k * 2]
        
        print(f"  Found {len(sorted_candidates)} candidates for re-ranking")
        
        # =====================================================================
        # Step 4: CrossEncoder re-ranking
        # =====================================================================
        if sorted_candidates:
            candidate_texts = [
                metadata["id_to_text"].get(idx, "") 
                for idx, _ in sorted_candidates
            ]
            
            pairs = [[query, text] for text in candidate_texts]
            rerank_scores = self.reranker.predict(pairs)
            
            # Normalize CrossEncoder scores to 0-1 using sigmoid
            # CrossEncoder returns logits which can be negative
            def sigmoid(x):
                return 1 / (1 + np.exp(-x))
            
            reranked_results = []
            for i, (idx, hybrid_score) in enumerate(sorted_candidates):
                rerank_score = sigmoid(float(rerank_scores[i]))  # Normalize to 0-1
                final_score = 0.6 * rerank_score + 0.4 * hybrid_score
                reranked_results.append((idx, final_score))
            
            reranked_results.sort(key=lambda x: x[1], reverse=True)
        else:
            reranked_results = []
        
        # =====================================================================
        # Step 5: Adaptive Top-K (V2)
        # =====================================================================
        top_score = reranked_results[0][1] if reranked_results else 0.0
        
        if top_score >= ADAPTIVE_K_HIGH_THRESHOLD:
            adaptive_k = ADAPTIVE_K_HIGH
            confidence_level = "high"
        elif top_score <= ADAPTIVE_K_LOW_THRESHOLD:
            adaptive_k = ADAPTIVE_K_LOW
            confidence_level = "low"
        else:
            adaptive_k = top_k
            confidence_level = "medium"
        
        # Use the adaptive K
        final_k = min(top_k, adaptive_k) if confidence_level == "high" else max(top_k, adaptive_k)
        top_results = reranked_results[:final_k]
        
        print(f"  Adaptive K: {final_k} (confidence: {confidence_level}, top_score: {top_score:.3f})")
        
        # Check if we should use fusion retrieval (low confidence fallback)
        # SKIP IF DISABLED FOR SPEED
        use_fusion = not DISABLE_FUSION_RETRIEVAL and (
            force_fusion or (top_score < CONFIDENCE_THRESHOLD and confidence_level == "low")
        )
        
        if use_fusion:
            print(f"⚡ Low confidence ({top_score:.3f}) - triggering fusion retrieval")
            return self._fusion_retrieval(query, top_k, index, metadata, index_name)
        
        # =====================================================================
        # Step 6: Contextual Chunk Expansion (V2)
        # =====================================================================
        chunk_ids = [idx for idx, _ in top_results]
        score_map = {idx: score for idx, score in top_results}
        expanded_chunk_ids = self._expand_context(chunk_ids, index.ntotal, score_map)
        
        # Prepare results with expanded context
        chunks = []
        scores = []
        
        for idx in expanded_chunk_ids:
            chunk_text = metadata["id_to_text"].get(idx, "")
            if chunk_text:
                chunks.append(chunk_text)
                scores.append(score_map.get(idx, 0.0))
        
        print(f"  Returning {len(chunks)} results (with context expansion)")
        
        return MemoryResult(chunks=chunks, scores=scores, fusion_used=False)
    
    def _expand_query(self, query: str) -> str:
        """
        V2: Expand query with synonyms and related terms.
        Uses LLM to add relevant keywords for better retrieval.
        """
        prompt = f"""Expand this question with synonyms and related terms.
Keep it as ONE expanded query. Be concise.

Original: {query}

Expanded:"""
        
        try:
            response = self.cerebras_client.chat.completions.create(
                model=CEREBRAS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.2
            )
            if response and response.choices and response.choices[0].message.content:
                expanded = response.choices[0].message.content.strip()
                if expanded and isinstance(expanded, str):
                    print(f"  Query expanded: '{query[:50]}...' → '{expanded[:50]}...'")
                    return expanded
        except Exception as e:
            print(f"  ⚠️ Query expansion failed: {e}")
        return query
    
    def _expand_context(self, chunk_ids: List[int], total_chunks: int, score_map: Dict[int, float] = None, metadata = None) -> List[int]:
        """
        V2: Include neighboring chunks for more context.
        Only includes neighbors that score above CONTEXT_EXPANSION_MIN_SCORE.
        """
        expanded = []
        seen = set()
        
        for chunk_id in chunk_ids:
            # Always add the original chunk
            if chunk_id not in seen:
                expanded.append(chunk_id)
                seen.add(chunk_id)
            
            # Add surrounding chunks within window (only if they have good scores)
            for offset in range(-CONTEXT_EXPANSION_WINDOW, CONTEXT_EXPANSION_WINDOW + 1):
                if offset == 0:  # Skip the original (already added)
                    continue
                neighbor_id = chunk_id + offset
                if 0 <= neighbor_id < total_chunks and neighbor_id not in seen:
                    # Check if neighbor has a score above threshold
                    neighbor_score = score_map.get(neighbor_id, 0.0) if score_map else 0.0
                    if neighbor_score >= CONTEXT_EXPANSION_MIN_SCORE:
                        expanded.append(neighbor_id)
                        seen.add(neighbor_id)
        
        return expanded
    
    def _fusion_retrieval(self, query: str, top_k: int, index, metadata, index_name) -> MemoryResult:
        """
        Fusion retrieval: Generate query variations and search IN PARALLEL.
        Uses ThreadPoolExecutor for concurrent FAISS searches.
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        # Generate query variations using Cerebras
        query_variations = self._generate_query_variations(query)
        print(f"  Generated {len(query_variations)} query variations (parallel search)")
        
        # Define search function for a single query
        def search_single_query(variation: str) -> Dict[int, Tuple[str, float]]:
            results = {}
            query_embedding = self.embedding_model.encode([variation])
            num_candidates = min(top_k * 2, index.ntotal)
            distances, indices = index.search(query_embedding, num_candidates)
            
            for idx, dist in zip(indices[0], distances[0]):
                if idx != -1:
                    score = 1.0 / (1.0 + dist)
                    chunk_text = metadata["id_to_text"].get(idx, "")
                    results[idx] = (chunk_text, score)
            return results
        
        # Execute all searches in parallel
        all_results = {}
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=len(query_variations)) as executor:
            future_to_query = {
                executor.submit(search_single_query, variation): variation 
                for variation in query_variations
            }
            
            for future in as_completed(future_to_query):
                try:
                    results = future.result()
                    # Merge results, keeping highest score
                    for idx, (text, score) in results.items():
                        if idx not in all_results or score > all_results[idx][1]:
                            all_results[idx] = (text, score)
                except Exception as e:
                    print(f"  ⚠️ Parallel search failed: {e}")
        
        parallel_time = (time.time() - start_time) * 1000
        print(f"  ✓ Parallel fusion completed in {parallel_time:.0f}ms")
        
        # Sort and return
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        chunks = [chunk for chunk, _ in sorted_results]
        scores = [score for _, score in sorted_results]
        
        return MemoryResult(chunks=chunks, scores=scores, fusion_used=True)
    
    def _generate_query_variations(self, original_query: str) -> List[str]:
        """Generate query variations using Cerebras LLM."""
        prompt = f"""Generate {FUSION_QUERY_COUNT - 1} alternative ways to phrase this search query. Each variation should capture the same intent but use different words. Optimized for RAG retrieval.

Original query: {original_query}

Return ONLY a JSON array of alternative queries, nothing else.
Example: ["query 1", "query 2"]

Alternative queries:"""
        
        try:
            response = self.cerebras_client.chat.completions.create(
                model=CEREBRAS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
                temperature=0.7
            )
            
            import json
            result = response.choices[0].message.content.strip()
            variations = json.loads(result)
            return [original_query] + variations
            
        except Exception as e:
            print(f"⚠️  Error generating query variations: {e}")
            return [original_query]
    
    def rewrite_session(self, session_text: str) -> str:
        """Rewrite a conversation session for optimal retrieval."""
        prompt = SESSION_REWRITING_PROMPT.format(session_text=session_text)
        
        try:
            response = self.cerebras_client.chat.completions.create(
                model=CEREBRAS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.3
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️  Error rewriting session: {e}")
            return session_text
    
    def index_memory(self, memory_chunk: MemoryChunk):
        """Add a new memory chunk to the FAISS index."""
        embedding = self.embedding_model.encode([memory_chunk.rewritten_text])
        next_id = self.index.ntotal
        
        self.index.add(embedding)
        self.metadata["id_to_text"][next_id] = memory_chunk.rewritten_text
        self.metadata["id_to_original"][next_id] = memory_chunk.original_text
        
        # Rebuild BM25 index
        documents = [
            self.metadata["id_to_text"].get(i, "") 
            for i in range(self.index.ntotal)
        ]
        self.bm25 = BM25(documents)
        
        self._save_index()
        print(f"✅ Indexed new memory chunk (ID: {next_id})")
    
    def update_user_persona(self, new_session: str) -> PersonaUpdate:
        """Update user persona based on new conversation."""
        current_persona = self.get_user_persona()
        prompt = PERSONA_UPDATE_PROMPT.format(
            current_persona=current_persona,
            new_session=new_session
        )
        
        try:
            response = self.cerebras_client.chat.completions.create(
                model=CEREBRAS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.3
            )
            
            updated_content = response.choices[0].message.content.strip()
            
            with open(USER_PERSONA_PATH, "w", encoding="utf-8") as f:
                f.write(updated_content)
            
            return PersonaUpdate(
                updated_content=updated_content,
                changes_summary="Persona updated with new conversation insights"
            )
        except Exception as e:
            print(f"⚠️  Error updating persona: {e}")
            return PersonaUpdate(
                updated_content=current_persona,
                changes_summary="No changes - update failed"
            )
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        faiss.write_index(self.index, str(FAISS_INDEX_PATH))
        with open(METADATA_PATH, "wb") as f:
            pickle.dump(self.metadata, f)
        print(f"💾 Saved index and metadata")


# Singleton instance
_rag_engine: Optional[RAGEngine] = None


def get_rag_engine() -> RAGEngine:
    """Get or create the RAG engine singleton."""
    global _rag_engine
    if _rag_engine is None:
        _rag_engine = RAGEngine()
    return _rag_engine
