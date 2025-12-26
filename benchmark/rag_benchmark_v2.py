"""
rag_benchmark_v2.py - Optimized Enhanced RAG Engine for Benchmarking

V2 Improvements (OPTIMIZED for speed):
- Query expansion: Single LLM call to expand query with synonyms/related terms
- BM25 on FAISS candidates only: Score only top FAISS results, not all 47K docs
- Simplified MMR: Fast diversity scoring using pre-computed embeddings
- No query decomposition (too slow, minimal benefit)
- No Self-RAG in retrieval (can enable in generation if needed)
"""

import os
import sys
import time
import re
import math
import json
import pickle
import numpy as np
import faiss
from typing import List, Tuple, Dict, Optional, Set
from collections import Counter
from dataclasses import dataclass
from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer, CrossEncoder
from cerebras.cloud.sdk import Cerebras

# Load environment from backend/.env
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_ENV = os.path.join(SCRIPT_DIR, "..", "backend", ".env")
load_dotenv(BACKEND_ENV)

# ==============================================================================
# CONFIGURATION
# ==============================================================================

FAISS_INDEX_PATH = os.path.join(SCRIPT_DIR, "benchmark_faiss_index.bin")
METADATA_PATH = os.path.join(SCRIPT_DIR, "benchmark_metadata.pkl")

# Model configuration
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
CEREBRAS_MODEL = "llama-3.1-8b"

# Search configuration
TOP_K = 5
HYBRID_COSINE_WEIGHT = 0.75
HYBRID_BM25_WEIGHT = 0.25
RERANK_WEIGHT = 0.6
HYBRID_WEIGHT = 0.4

# V2: MMR lambda (higher = more relevance, lower = more diversity)
MMR_LAMBDA = 0.7

# V2: Number of FAISS candidates to get before BM25 scoring
FAISS_CANDIDATES = 50  # Much smaller than scoring all 47K docs


# ==============================================================================
# DATA CLASSES
# ==============================================================================

@dataclass
class RetrievalResult:
    """Result from a retrieval operation."""
    chunk_ids: List[int]
    chunks: List[str]
    scores: List[float]
    retrieval_time_ms: float


@dataclass
class GenerationResult:
    """Result from LLM generation."""
    answer: str
    generation_time_ms: float


# ==============================================================================
# FAST BM25 (ONLY SCORES GIVEN CANDIDATES)
# ==============================================================================

class FastBM25:
    """
    Optimized BM25 that only scores a subset of documents.
    Instead of scoring all 47K docs, we score only FAISS candidates.
    """
    
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        
        # Pre-tokenize all documents
        self.tokenized_docs = [self._tokenize(doc) for doc in documents]
        self.avg_doc_len = sum(len(doc) for doc in self.tokenized_docs) / max(self.doc_count, 1)
        
        # Pre-compute document frequencies
        self.doc_freqs: Dict[str, int] = {}
        for doc in self.tokenized_docs:
            for term in set(doc):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        
        # Pre-compute term frequencies for each document
        self.term_freqs = [Counter(doc) for doc in self.tokenized_docs]
    
    def _tokenize(self, text: str) -> List[str]:
        if not isinstance(text, str):
            return []
        return re.findall(r'\w+', text.lower())
    
    def _idf(self, term: str) -> float:
        doc_freq = self.doc_freqs.get(term, 0)
        return math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def score_candidate(self, query_terms: List[str], doc_idx: int) -> float:
        """Score a single document against pre-tokenized query."""
        if doc_idx >= len(self.tokenized_docs):
            return 0.0
        
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
    
    def score_candidates(self, query: str, candidate_ids: List[int]) -> Dict[int, float]:
        """Score only the given candidate IDs (not all docs)."""
        query_terms = self._tokenize(query)
        scores = {}
        for doc_idx in candidate_ids:
            scores[doc_idx] = self.score_candidate(query_terms, doc_idx)
        return scores


# ==============================================================================
# ENHANCED RAG ENGINE V2 (OPTIMIZED)
# ==============================================================================

class BenchmarkRAGEngineV2:
    """
    Optimized RAG engine with:
    - Query expansion (single LLM call)
    - BM25 on FAISS candidates only (not all 47K docs)
    - Simplified MMR diversity
    """
    
    def __init__(self):
        print("🧪 Initializing Benchmark RAG Engine V2 (Optimized)...")
        print("   Speed improvements: FAISS-first BM25, simplified MMR")
        
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not set in environment")
        
        print(f"  Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        print(f"  Loading re-ranker: {RERANKER_MODEL}")
        self.reranker = CrossEncoder(RERANKER_MODEL)
        
        print("  Initializing Cerebras client...")
        self.cerebras_client = Cerebras(api_key=api_key)
        
        self._load_index()
        print("✅ Benchmark RAG Engine V2 ready!")
    
    def _load_index(self):
        """Load FAISS index and metadata, initialize FastBM25."""
        if not os.path.exists(FAISS_INDEX_PATH):
            raise FileNotFoundError(f"FAISS index not found: {FAISS_INDEX_PATH}")
        
        print(f"  Loading FAISS index: {FAISS_INDEX_PATH}")
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        
        print(f"  Loading metadata: {METADATA_PATH}")
        with open(METADATA_PATH, "rb") as f:
            self.metadata = pickle.load(f)
        
        num_vectors = self.index.ntotal
        print(f"  Loaded {num_vectors:,} vectors")
        
        if num_vectors > 0:
            documents = [self.metadata["id_to_text"].get(i, "") for i in range(num_vectors)]
            self.bm25 = FastBM25(documents)
            print(f"  Initialized FastBM25 (scores candidates only)")
        else:
            self.bm25 = None
    
    # ==========================================================================
    # V2: QUERY EXPANSION (SINGLE LLM CALL)
    # ==========================================================================
    
    def _expand_query(self, query: str) -> str:
        """
        V2: Add synonyms and related legal terms via single LLM call.
        """
        prompt = f"""Expand this legal question with synonyms and related Indian law terms.
Keep it as ONE expanded query. Be concise.

Original: {query}

Expanded:"""
        
        try:
            response = self.cerebras_client.chat.completions.create(
                model=CEREBRAS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=0.2
            )
            if response and response.choices and response.choices[0].message.content:
                expanded = response.choices[0].message.content.strip()
                return expanded if expanded and isinstance(expanded, str) else query
        except Exception:
            pass
        return query
    
    # ==========================================================================
    # V2: SIMPLIFIED MMR (NO EXTRA EMBEDDING CALLS)
    # ==========================================================================
    
    def _apply_mmr_penalty(
        self, 
        candidates: List[Tuple[int, float]],
        top_k: int
    ) -> List[Tuple[int, float]]:
        """
        Simplified MMR: Apply diversity penalty based on text similarity.
        Uses Jaccard similarity of tokens instead of embeddings (faster).
        """
        if len(candidates) <= top_k:
            return candidates
        
        # Get tokenized versions
        def tokenize(text):
            return set(re.findall(r'\w+', text.lower()))
        
        candidate_tokens = [
            tokenize(self.metadata["id_to_text"].get(idx, ""))
            for idx, _ in candidates
        ]
        
        selected = []
        remaining = list(range(len(candidates)))
        
        for _ in range(min(top_k, len(candidates))):
            best_score = float('-inf')
            best_idx = -1
            
            for i in remaining:
                # Original score
                relevance = candidates[i][1]
                
                # Diversity penalty: max Jaccard similarity to selected
                max_sim = 0.0
                for j in [candidates[s][0] for s in selected]:
                    j_idx = next((k for k, (idx, _) in enumerate(candidates) if idx == j), None)
                    if j_idx is not None and candidate_tokens[i] and candidate_tokens[j_idx]:
                        intersection = len(candidate_tokens[i] & candidate_tokens[j_idx])
                        union = len(candidate_tokens[i] | candidate_tokens[j_idx])
                        sim = intersection / union if union > 0 else 0
                        max_sim = max(max_sim, sim)
                
                # MMR-like score
                mmr_score = MMR_LAMBDA * relevance - (1 - MMR_LAMBDA) * max_sim
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_idx = i
            
            if best_idx != -1:
                selected.append(best_idx)
                remaining.remove(best_idx)
        
        return [(candidates[i][0], candidates[i][1]) for i in selected]
    
    # ==========================================================================
    # MAIN SEARCH METHOD (OPTIMIZED)
    # ==========================================================================
    
    def hybrid_search(self, query: str, top_k: int = TOP_K) -> RetrievalResult:
        """
        V2 Optimized hybrid search:
        1. Expand query with LLM (single call)
        2. Get FAISS candidates (fast)
        3. Score ONLY those candidates with BM25 (not all 47K)
        4. Hybrid combine & CrossEncoder rerank
        5. Apply MMR diversity
        """
        start_time = time.time()
        
        # Step 1: Query expansion (single LLM call)
        expanded_query = self._expand_query(query)
        
        # Step 2: Get FAISS candidates (both original and expanded)
        all_candidates: Dict[int, float] = {}
        
        for q in [query, expanded_query]:
            if not isinstance(q, str) or not q.strip():
                continue
            query_embedding = self.embedding_model.encode([q])
            distances, indices = self.index.search(query_embedding, FAISS_CANDIDATES)
            
            for idx, dist in zip(indices[0], distances[0]):
                if idx != -1:
                    score = 1.0 / (1.0 + dist)
                    if idx not in all_candidates or score > all_candidates[idx]:
                        all_candidates[idx] = score
        
        # Step 3: BM25 on FAISS candidates only (key optimization!)
        if self.bm25 and all_candidates:
            candidate_ids = list(all_candidates.keys())
            bm25_scores = self.bm25.score_candidates(query, candidate_ids)
            
            # Normalize BM25 scores
            max_bm25 = max(bm25_scores.values()) if bm25_scores else 1.0
            
            # Hybrid combine
            for idx in all_candidates:
                cosine_score = all_candidates[idx]
                bm25_score = bm25_scores.get(idx, 0) / max_bm25 if max_bm25 > 0 else 0
                all_candidates[idx] = HYBRID_COSINE_WEIGHT * cosine_score + HYBRID_BM25_WEIGHT * bm25_score
        
        # Step 4: Sort and get top candidates for reranking
        sorted_candidates = sorted(all_candidates.items(), key=lambda x: x[1], reverse=True)[:top_k * 2]
        
        # Step 5: CrossEncoder reranking
        if sorted_candidates:
            candidate_texts = [self.metadata["id_to_text"].get(idx, "") for idx, _ in sorted_candidates]
            pairs = [[query, text] for text in candidate_texts]
            rerank_scores = self.reranker.predict(pairs)
            
            reranked = []
            for i, (idx, hybrid_score) in enumerate(sorted_candidates):
                final_score = RERANK_WEIGHT * float(rerank_scores[i]) + HYBRID_WEIGHT * hybrid_score
                reranked.append((idx, final_score))
            reranked.sort(key=lambda x: x[1], reverse=True)
        else:
            reranked = []
        
        # Step 6: Apply MMR diversity penalty
        mmr_results = self._apply_mmr_penalty(reranked, top_k)
        
        # Prepare output
        chunk_ids = [idx for idx, _ in mmr_results]
        chunks = [self.metadata["id_to_text"].get(idx, "") for idx in chunk_ids]
        scores = [score for _, score in mmr_results]
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        return RetrievalResult(
            chunk_ids=chunk_ids,
            chunks=chunks,
            scores=scores,
            retrieval_time_ms=retrieval_time_ms
        )
    
    def generate_answer(self, query: str, context_chunks: List[str], use_self_rag: bool = False) -> GenerationResult:
        """Generate answer using Cerebras LLM."""
        start_time = time.time()
        context = "\n\n---\n\n".join(context_chunks)
        
        prompt = f"""Based on the following context from Indian law, answer the question accurately.
If the answer is not in the context, say "I don't have enough information."

Context:
{context}

Question: {query}

Answer:"""
        
        try:
            response = self.cerebras_client.chat.completions.create(
                model=CEREBRAS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=512,
                temperature=0.3
            )
            answer = response.choices[0].message.content.strip() if response.choices else ""
        except Exception as e:
            answer = f"Error generating answer: {e}"
        
        generation_time_ms = (time.time() - start_time) * 1000
        return GenerationResult(answer=answer, generation_time_ms=generation_time_ms)


# Singleton
_engine_v2: Optional[BenchmarkRAGEngineV2] = None


def get_benchmark_engine_v2() -> BenchmarkRAGEngineV2:
    """Get or create the V2 benchmark RAG engine singleton."""
    global _engine_v2
    if _engine_v2 is None:
        _engine_v2 = BenchmarkRAGEngineV2()
    return _engine_v2
