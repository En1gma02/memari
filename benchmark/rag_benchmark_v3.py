"""
rag_benchmark_v3.py - V3 RAG Engine for Long-Term Memory Chatbot

V3 Improvements:
1. Contextual Chunk Expansion: Include surrounding chunks for more context
2. Reciprocal Rank Fusion (RRF): Better fusion than weighted average
3. Adaptive Top-K: Adjust K based on confidence scores

Designed for: Long-term memory AI chatbot (not legal agent)
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
DEFAULT_TOP_K = 5
FAISS_CANDIDATES = 50

# V3: Adaptive Top-K thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.7  # Use fewer chunks
LOW_CONFIDENCE_THRESHOLD = 0.4   # Use more chunks + fusion
ADAPTIVE_TOP_K_HIGH = 3          # When confident
ADAPTIVE_TOP_K_LOW = 7           # When uncertain

# V3: RRF constant (typically 60)
RRF_K = 60

# V3: Contextual expansion window
CONTEXT_WINDOW = 1  # Include 1 chunk before and after


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
    adaptive_k_used: int = 5
    confidence_level: str = "medium"


@dataclass
class GenerationResult:
    """Result from LLM generation."""
    answer: str
    generation_time_ms: float


# ==============================================================================
# FAST BM25 (SCORES ONLY CANDIDATES)
# ==============================================================================

class FastBM25:
    """BM25 that only scores given candidates, not all documents."""
    
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents = documents
        self.doc_count = len(documents)
        self.tokenized_docs = [self._tokenize(doc) for doc in documents]
        self.avg_doc_len = sum(len(doc) for doc in self.tokenized_docs) / max(self.doc_count, 1)
        
        self.doc_freqs: Dict[str, int] = {}
        for doc in self.tokenized_docs:
            for term in set(doc):
                self.doc_freqs[term] = self.doc_freqs.get(term, 0) + 1
        
        self.term_freqs = [Counter(doc) for doc in self.tokenized_docs]
    
    def _tokenize(self, text: str) -> List[str]:
        if not isinstance(text, str):
            return []
        return re.findall(r'\w+', text.lower())
    
    def _idf(self, term: str) -> float:
        doc_freq = self.doc_freqs.get(term, 0)
        return math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def score_candidate(self, query_terms: List[str], doc_idx: int) -> float:
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
        query_terms = self._tokenize(query)
        return {doc_idx: self.score_candidate(query_terms, doc_idx) for doc_idx in candidate_ids}


# ==============================================================================
# V3 RAG ENGINE
# ==============================================================================

class BenchmarkRAGEngineV3:
    """
    V3 RAG Engine with:
    - Contextual Chunk Expansion
    - Reciprocal Rank Fusion (RRF)
    - Adaptive Top-K based on confidence
    """
    
    def __init__(self):
        print("🧪 Initializing Benchmark RAG Engine V3...")
        print("   Features: RRF, Contextual Expansion, Adaptive Top-K")
        
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
        print("✅ Benchmark RAG Engine V3 ready!")
    
    def _load_index(self):
        """Load FAISS index and metadata."""
        if not os.path.exists(FAISS_INDEX_PATH):
            raise FileNotFoundError(f"FAISS index not found: {FAISS_INDEX_PATH}")
        
        print(f"  Loading FAISS index: {FAISS_INDEX_PATH}")
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        
        print(f"  Loading metadata: {METADATA_PATH}")
        with open(METADATA_PATH, "rb") as f:
            self.metadata = pickle.load(f)
        
        self.num_vectors = self.index.ntotal
        print(f"  Loaded {self.num_vectors:,} vectors")
        
        if self.num_vectors > 0:
            documents = [self.metadata["id_to_text"].get(i, "") for i in range(self.num_vectors)]
            self.bm25 = FastBM25(documents)
            print(f"  Initialized FastBM25")
        else:
            self.bm25 = None
    
    # ==========================================================================
    # V3: RECIPROCAL RANK FUSION
    # ==========================================================================
    
    def _reciprocal_rank_fusion(
        self, 
        rankings: List[List[Tuple[int, float]]], 
        k: int = RRF_K
    ) -> List[Tuple[int, float]]:
        """
        Combine multiple rankings using Reciprocal Rank Fusion.
        
        RRF_score(d) = Σ 1 / (k + rank_i(d))
        
        This is more robust than weighted averaging because it focuses
        on ranks rather than raw scores which may have different scales.
        """
        rrf_scores: Dict[int, float] = {}
        
        for ranking in rankings:
            for rank, (doc_id, _) in enumerate(ranking, start=1):
                if doc_id not in rrf_scores:
                    rrf_scores[doc_id] = 0.0
                rrf_scores[doc_id] += 1.0 / (k + rank)
        
        # Sort by RRF score descending
        sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results
    
    # ==========================================================================
    # V3: CONTEXTUAL CHUNK EXPANSION
    # ==========================================================================
    
    def _expand_context(self, chunk_ids: List[int], window: int = CONTEXT_WINDOW) -> List[int]:
        """
        Expand chunk IDs to include surrounding chunks for more context.
        
        If we retrieved chunk 42, also include 41 and 43.
        This helps when answers span chunk boundaries.
        """
        expanded = set()
        
        for chunk_id in chunk_ids:
            # Add the original chunk
            expanded.add(chunk_id)
            
            # Add surrounding chunks within bounds
            for offset in range(-window, window + 1):
                neighbor_id = chunk_id + offset
                if 0 <= neighbor_id < self.num_vectors:
                    expanded.add(neighbor_id)
        
        # Return in original order, with neighbors inserted
        result = []
        seen = set()
        for chunk_id in chunk_ids:
            for offset in range(-window, window + 1):
                neighbor_id = chunk_id + offset
                if 0 <= neighbor_id < self.num_vectors and neighbor_id not in seen:
                    result.append(neighbor_id)
                    seen.add(neighbor_id)
        
        return result
    
    # ==========================================================================
    # V3: ADAPTIVE TOP-K
    # ==========================================================================
    
    def _get_adaptive_k(self, top_score: float) -> Tuple[int, str]:
        """
        Determine how many chunks to retrieve based on confidence.
        
        High confidence (score > 0.7) → Use fewer chunks (3)
        Low confidence (score < 0.4) → Use more chunks (7)
        Medium → Use default (5)
        """
        if top_score >= HIGH_CONFIDENCE_THRESHOLD:
            return ADAPTIVE_TOP_K_HIGH, "high"
        elif top_score <= LOW_CONFIDENCE_THRESHOLD:
            return ADAPTIVE_TOP_K_LOW, "low"
        else:
            return DEFAULT_TOP_K, "medium"
    
    # ==========================================================================
    # MAIN SEARCH METHOD
    # ==========================================================================
    
    def hybrid_search(self, query: str, top_k: int = DEFAULT_TOP_K) -> RetrievalResult:
        """
        V3 Hybrid search with:
        1. Multi-path retrieval (FAISS dense, BM25 sparse)
        2. Reciprocal Rank Fusion (RRF) to combine
        3. CrossEncoder re-ranking
        4. Adaptive Top-K based on confidence
        5. Contextual chunk expansion
        """
        start_time = time.time()
        
        # Query expansion via LLM (single call, from V2)
        expanded_query = self._expand_query(query)
        
        # =======================================================================
        # STEP 1: Multi-path retrieval
        # =======================================================================
        
        rankings = []
        
        # Path 1: FAISS dense retrieval on original query
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(query_embedding, FAISS_CANDIDATES)
        dense_ranking = []
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:
                score = 1.0 / (1.0 + dist)
                dense_ranking.append((int(idx), score))
        dense_ranking.sort(key=lambda x: x[1], reverse=True)
        rankings.append(dense_ranking)
        
        # Path 2: FAISS dense retrieval on expanded query
        if expanded_query != query and isinstance(expanded_query, str):
            exp_embedding = self.embedding_model.encode([expanded_query])
            distances2, indices2 = self.index.search(exp_embedding, FAISS_CANDIDATES)
            exp_ranking = []
            for idx, dist in zip(indices2[0], distances2[0]):
                if idx != -1:
                    score = 1.0 / (1.0 + dist)
                    exp_ranking.append((int(idx), score))
            exp_ranking.sort(key=lambda x: x[1], reverse=True)
            rankings.append(exp_ranking)
        
        # Path 3: BM25 sparse retrieval
        if self.bm25:
            all_candidate_ids = list(set([idx for idx, _ in dense_ranking]))
            bm25_scores = self.bm25.score_candidates(query, all_candidate_ids)
            bm25_ranking = sorted(bm25_scores.items(), key=lambda x: x[1], reverse=True)
            rankings.append(bm25_ranking)
        
        # =======================================================================
        # STEP 2: Reciprocal Rank Fusion
        # =======================================================================
        
        rrf_results = self._reciprocal_rank_fusion(rankings)
        
        # Get top candidates for re-ranking
        top_candidates = rrf_results[:top_k * 3]
        
        # =======================================================================
        # STEP 3: CrossEncoder re-ranking
        # =======================================================================
        
        if top_candidates:
            candidate_texts = [self.metadata["id_to_text"].get(idx, "") for idx, _ in top_candidates]
            pairs = [[query, text] for text in candidate_texts]
            rerank_scores = self.reranker.predict(pairs)
            
            reranked = []
            for i, (idx, rrf_score) in enumerate(top_candidates):
                # Combine RRF with reranker (60% reranker, 40% RRF)
                final_score = 0.6 * float(rerank_scores[i]) + 0.4 * rrf_score
                reranked.append((idx, final_score))
            reranked.sort(key=lambda x: x[1], reverse=True)
        else:
            reranked = []
        
        # =======================================================================
        # STEP 4: Adaptive Top-K
        # =======================================================================
        
        top_score = reranked[0][1] if reranked else 0.0
        adaptive_k, confidence_level = self._get_adaptive_k(top_score)
        
        # Use the smaller of requested top_k and adaptive_k
        final_k = min(top_k, adaptive_k) if confidence_level == "high" else max(top_k, adaptive_k)
        
        top_results = reranked[:final_k]
        
        # =======================================================================
        # STEP 5: Contextual Chunk Expansion
        # =======================================================================
        
        chunk_ids = [idx for idx, _ in top_results]
        expanded_chunk_ids = self._expand_context(chunk_ids)
        
        # Limit to reasonable size (max 2x the requested chunks)
        expanded_chunk_ids = expanded_chunk_ids[:final_k * 2]
        
        # Get chunk texts
        chunks = [self.metadata["id_to_text"].get(idx, "") for idx in expanded_chunk_ids]
        
        # Scores for original chunks only
        score_map = {idx: score for idx, score in top_results}
        scores = [score_map.get(idx, 0.0) for idx in expanded_chunk_ids]
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        return RetrievalResult(
            chunk_ids=expanded_chunk_ids,
            chunks=chunks,
            scores=scores,
            retrieval_time_ms=retrieval_time_ms,
            adaptive_k_used=final_k,
            confidence_level=confidence_level
        )
    
    def _expand_query(self, query: str) -> str:
        """Expand query with synonyms (from V2)."""
        prompt = f"""Expand this question with synonyms and related terms.
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
    
    def generate_answer(self, query: str, context_chunks: List[str], use_self_rag: bool = False) -> GenerationResult:
        """Generate answer using Cerebras LLM."""
        start_time = time.time()
        context = "\n\n---\n\n".join(context_chunks)
        
        prompt = f"""Based on the following context, answer the question accurately and helpfully.
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
_engine_v3: Optional[BenchmarkRAGEngineV3] = None


def get_benchmark_engine_v3() -> BenchmarkRAGEngineV3:
    """Get or create the V3 benchmark RAG engine singleton."""
    global _engine_v3
    if _engine_v3 is None:
        _engine_v3 = BenchmarkRAGEngineV3()
    return _engine_v3
