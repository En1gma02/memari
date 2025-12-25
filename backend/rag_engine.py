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
    CEREBRAS_DELAY_SECONDS
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
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization: lowercase and split on non-alphanumeric."""
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
        
        # Count term frequencies in document
        term_freqs = Counter(doc_terms)
        
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
        print("Loading re-ranker: cross-encoder/reranker-bert-tiny-gooaq-bce")
        self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-2-v2")
        
        # Initialize Cerebras client
        self.cerebras_client = Cerebras(api_key=CEREBRAS_API_KEY)
        
        # Load FAISS index and metadata
        self.index = None
        self.metadata = None
        self.bm25 = None
        self._load_index()
        
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
        if self.index.ntotal == 0:
            print("⚠️  FAISS index is empty")
            return MemoryResult(chunks=[], scores=[], fusion_used=False)
        
        print(f"🔍 Hybrid search for: '{query}'")
        
        # Step 1: Dense retrieval (FAISS - cosine similarity)
        query_embedding = self.embedding_model.encode([query])
        # Get more candidates for re-ranking
        num_candidates = min(top_k * 3, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, num_candidates)
        
        # Convert L2 distances to similarity scores (0-1 range)
        dense_scores = {}
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:
                # L2 to cosine-like similarity
                score = 1.0 / (1.0 + dist)
                dense_scores[idx] = score
        
        # Step 2: BM25 retrieval (sparse)
        bm25_scores = {}
        if self.bm25 is not None:
            bm25_results = self.bm25.search(query, top_k=num_candidates)
            # Normalize BM25 scores to 0-1 range
            max_bm25 = max(score for _, score in bm25_results) if bm25_results else 1.0
            for idx, score in bm25_results:
                if max_bm25 > 0:
                    bm25_scores[idx] = score / max_bm25
                else:
                    bm25_scores[idx] = 0.0
        
        # Step 3: Hybrid scoring (75% cosine + 25% BM25)
        hybrid_scores = {}
        all_indices = set(dense_scores.keys()) | set(bm25_scores.keys())
        
        for idx in all_indices:
            cosine_score = dense_scores.get(idx, 0.0)
            bm25_score = bm25_scores.get(idx, 0.0)
            hybrid_scores[idx] = 0.75 * cosine_score + 0.25 * bm25_score
        
        # Get top candidates for re-ranking
        sorted_candidates = sorted(
            hybrid_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:top_k * 2]
        
        print(f"  Found {len(sorted_candidates)} candidates for re-ranking")
        
        # Step 4: Re-rank with CrossEncoder
        if sorted_candidates:
            candidate_texts = [
                self.metadata["id_to_text"].get(idx, "") 
                for idx, _ in sorted_candidates
            ]
            
            # Create pairs for re-ranking
            pairs = [[query, text] for text in candidate_texts]
            
            # Get re-ranker scores
            rerank_scores = self.reranker.predict(pairs)
            
            # Combine with original ranking
            reranked_results = []
            for i, (idx, hybrid_score) in enumerate(sorted_candidates):
                rerank_score = float(rerank_scores[i])
                # Final score: 60% reranker + 40% hybrid
                final_score = 0.6 * rerank_score + 0.4 * hybrid_score
                reranked_results.append((idx, final_score))
            
            # Sort by final score
            reranked_results.sort(key=lambda x: x[1], reverse=True)
            top_results = reranked_results[:top_k]
        else:
            top_results = []
        
        # Check if we should use fusion retrieval
        top_score = top_results[0][1] if top_results else 0.0
        use_fusion = force_fusion or (top_score < CONFIDENCE_THRESHOLD and len(top_results) > 0)
        
        if use_fusion:
            print(f"⚡ Low confidence ({top_score:.3f}) - triggering fusion retrieval")
            return self._fusion_retrieval(query, top_k)
        
        # Prepare results
        chunks = []
        scores = []
        
        for idx, score in top_results:
            chunk_text = self.metadata["id_to_text"].get(idx, "")
            chunks.append(chunk_text)
            scores.append(score)
        
        print(f"  Returning {len(chunks)} results (top score: {scores[0]:.3f})" if scores else "  No results")
        
        return MemoryResult(chunks=chunks, scores=scores, fusion_used=False)
    
    def _fusion_retrieval(self, query: str, top_k: int) -> MemoryResult:
        """
        Fusion retrieval: Generate query variations and merge results.
        """
        # Generate query variations using Cerebras
        query_variations = self._generate_query_variations(query)
        print(f"  Generated {len(query_variations)} query variations")
        
        # Search with all queries
        all_results = {}
        
        for variation in query_variations:
            # Get hybrid scores for this variation
            query_embedding = self.embedding_model.encode([variation])
            num_candidates = min(top_k * 2, self.index.ntotal)
            distances, indices = self.index.search(query_embedding, num_candidates)
            
            for idx, dist in zip(indices[0], distances[0]):
                if idx != -1:
                    score = 1.0 / (1.0 + dist)
                    chunk_text = self.metadata["id_to_text"].get(idx, "")
                    
                    if idx not in all_results or score > all_results[idx][1]:
                        all_results[idx] = (chunk_text, score)
            
            time.sleep(0.5)  # Small delay between variations
        
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
        prompt = f"""Generate {FUSION_QUERY_COUNT - 1} alternative ways to phrase this search query. Each variation should capture the same intent but use different words.

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
