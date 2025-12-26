"""
rag_benchmark.py - Standalone RAG Engine for Benchmarking

Mirrors the production RAG pipeline:
- FAISS index loading
- BM25 sparse retrieval
- Hybrid search (75% cosine + 25% BM25)
- CrossEncoder re-ranking
- LLM generation (Cerebras)
"""

import os
import sys
import time
import re
import math
import pickle
import numpy as np
import faiss
from typing import List, Tuple, Dict, Optional
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

# Model configuration (same as production)
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
RERANKER_MODEL = "cross-encoder/ms-marco-MiniLM-L6-v2"
CEREBRAS_MODEL = "llama-3.1-8b"

# Search configuration
TOP_K = 5
HYBRID_COSINE_WEIGHT = 0.75
HYBRID_BM25_WEIGHT = 0.25
RERANK_WEIGHT = 0.6
HYBRID_WEIGHT = 0.4


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
# BM25 IMPLEMENTATION (same as production)
# ==============================================================================

class BM25:
    """Simple BM25 implementation for hybrid search."""
    
    def __init__(self, documents: List[str], k1: float = 1.5, b: float = 0.75):
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
        return re.findall(r'\w+', text.lower())
    
    def _idf(self, term: str) -> float:
        doc_freq = self.doc_freqs.get(term, 0)
        return math.log((self.doc_count - doc_freq + 0.5) / (doc_freq + 0.5) + 1)
    
    def score(self, query: str, doc_idx: int) -> float:
        query_terms = self._tokenize(query)
        doc_terms = self.tokenized_docs[doc_idx]
        doc_len = len(doc_terms)
        
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
        scores = [(i, self.score(query, i)) for i in range(self.doc_count)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


# ==============================================================================
# BENCHMARK RAG ENGINE
# ==============================================================================

class BenchmarkRAGEngine:
    """Standalone RAG engine for benchmarking (mirrors production)."""
    
    def __init__(self):
        print("🧪 Initializing Benchmark RAG Engine...")
        
        # Check API key
        api_key = os.environ.get("CEREBRAS_API_KEY")
        if not api_key:
            raise ValueError("CEREBRAS_API_KEY not set in environment")
        
        # Load embedding model
        print(f"  Loading embedding model: {EMBEDDING_MODEL}")
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Load re-ranker
        print(f"  Loading re-ranker: {RERANKER_MODEL}")
        self.reranker = CrossEncoder(RERANKER_MODEL)
        
        # Initialize Cerebras client
        print("  Initializing Cerebras client...")
        self.cerebras_client = Cerebras(api_key=api_key)
        
        # Load FAISS index and metadata
        self._load_index()
        
        print("✅ Benchmark RAG Engine ready!")
    
    def _load_index(self):
        """Load FAISS index and metadata, initialize BM25."""
        if not os.path.exists(FAISS_INDEX_PATH):
            raise FileNotFoundError(f"FAISS index not found: {FAISS_INDEX_PATH}")
        
        print(f"  Loading FAISS index: {FAISS_INDEX_PATH}")
        self.index = faiss.read_index(FAISS_INDEX_PATH)
        
        print(f"  Loading metadata: {METADATA_PATH}")
        with open(METADATA_PATH, "rb") as f:
            self.metadata = pickle.load(f)
        
        num_vectors = self.index.ntotal
        print(f"  Loaded {num_vectors:,} vectors")
        
        # Initialize BM25
        if num_vectors > 0:
            documents = [
                self.metadata["id_to_text"].get(i, "") 
                for i in range(num_vectors)
            ]
            self.bm25 = BM25(documents)
            print(f"  Initialized BM25 index")
        else:
            self.bm25 = None
    
    def hybrid_search(self, query: str, top_k: int = TOP_K) -> RetrievalResult:
        """
        Hybrid search: 75% cosine + 25% BM25, with CrossEncoder re-ranking.
        
        Returns RetrievalResult with chunk IDs, texts, scores, and timing.
        """
        start_time = time.time()
        
        # Step 1: Dense retrieval (FAISS)
        query_embedding = self.embedding_model.encode([query])
        num_candidates = min(top_k * 3, self.index.ntotal)
        distances, indices = self.index.search(query_embedding, num_candidates)
        
        # Convert L2 distances to similarity scores
        dense_scores = {}
        for idx, dist in zip(indices[0], distances[0]):
            if idx != -1:
                score = 1.0 / (1.0 + dist)
                dense_scores[idx] = score
        
        # Step 2: BM25 retrieval
        bm25_scores = {}
        if self.bm25 is not None:
            bm25_results = self.bm25.search(query, top_k=num_candidates)
            max_bm25 = max(score for _, score in bm25_results) if bm25_results else 1.0
            for idx, score in bm25_results:
                if max_bm25 > 0:
                    bm25_scores[idx] = score / max_bm25
        
        # Step 3: Hybrid scoring
        hybrid_scores = {}
        all_indices = set(dense_scores.keys()) | set(bm25_scores.keys())
        
        for idx in all_indices:
            cosine_score = dense_scores.get(idx, 0.0)
            bm25_score = bm25_scores.get(idx, 0.0)
            hybrid_scores[idx] = HYBRID_COSINE_WEIGHT * cosine_score + HYBRID_BM25_WEIGHT * bm25_score
        
        # Get top candidates for re-ranking
        sorted_candidates = sorted(
            hybrid_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k * 2]
        
        # Step 4: Re-rank with CrossEncoder
        if sorted_candidates:
            candidate_texts = [
                self.metadata["id_to_text"].get(idx, "")
                for idx, _ in sorted_candidates
            ]
            
            pairs = [[query, text] for text in candidate_texts]
            rerank_scores = self.reranker.predict(pairs)
            
            reranked_results = []
            for i, (idx, hybrid_score) in enumerate(sorted_candidates):
                rerank_score = float(rerank_scores[i])
                final_score = RERANK_WEIGHT * rerank_score + HYBRID_WEIGHT * hybrid_score
                reranked_results.append((idx, final_score))
            
            reranked_results.sort(key=lambda x: x[1], reverse=True)
            top_results = reranked_results[:top_k]
        else:
            top_results = []
        
        # Prepare output
        chunk_ids = [idx for idx, _ in top_results]
        chunks = [self.metadata["id_to_text"].get(idx, "") for idx in chunk_ids]
        scores = [score for _, score in top_results]
        
        retrieval_time_ms = (time.time() - start_time) * 1000
        
        return RetrievalResult(
            chunk_ids=chunk_ids,
            chunks=chunks,
            scores=scores,
            retrieval_time_ms=retrieval_time_ms
        )
    
    def generate_answer(self, query: str, context_chunks: List[str]) -> GenerationResult:
        """
        Generate answer using Cerebras LLM with retrieved context.
        """
        start_time = time.time()
        
        # Build context
        context = "\n\n---\n\n".join(context_chunks)
        
        prompt = f"""Based on the following context, answer the question.
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
            answer = response.choices[0].message.content.strip()
        except Exception as e:
            answer = f"Error generating answer: {e}"
        
        generation_time_ms = (time.time() - start_time) * 1000
        
        return GenerationResult(
            answer=answer,
            generation_time_ms=generation_time_ms
        )


# Singleton
_engine: Optional[BenchmarkRAGEngine] = None


def get_benchmark_engine() -> BenchmarkRAGEngine:
    """Get or create the benchmark RAG engine singleton."""
    global _engine
    if _engine is None:
        _engine = BenchmarkRAGEngine()
    return _engine
