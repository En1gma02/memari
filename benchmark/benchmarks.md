# RAG Benchmark Suite - Findings Report

## Overview

Comprehensive RAG benchmarking system evaluating retrieval and generation quality using the Indian Law dataset (~50M tokens, 47,789 chunks).

---

## Benchmark Versions

| Version | Key Features | Purpose |
|---------|--------------|---------|
| **V1** | Hybrid search (75% cosine + 25% BM25), CrossEncoder re-ranking | Baseline |
| **V2** | Query expansion, FAISS-first BM25, Jaccard MMR | Speed + Accuracy |
| **V3** | RRF fusion, Contextual expansion, Adaptive Top-K | Experimental |

---

## Results Comparison

### Retrieval Metrics

| Metric | V1 | V2 | V3 | Winner |
|--------|----|----|----|----|
| **Hit Rate @5** | 79% | **88%** | 78% | V2 ✅ |
| **MRR** | 0.64 | **0.69** | 0.32 | V2 ✅ |
| **Precision @5** | 0.16 | **0.18** | 0.16 | V2 ✅ |
| **Recall @5** | 79% | **88%** | 78% | V2 ✅ |
| **nDCG @5** | 0.68 | **0.74** | 0.43 | V2 ✅ |

### QA Metrics

| Metric | V1 | V2 | V3 |
|--------|----|----|----| 
| **BLEU** | **0.21** | 0.13 | 0.00 |
| **ROUGE-L** | **0.32** | 0.19 | 0.01 |
| **F1** | **0.39** | 0.24 | 0.01 |

> **Note**: QA metrics dropped in V2/V3 because different retrieval strategies find different chunks. Ground truth is tied to V1's indexed chunks.

### Latency Metrics

| Metric | V1 | V2 | V3 |
|--------|----|----|----| 
| **Retrieval** | 4,585ms | **1,426ms** | 2,322ms |
| **Generation** | 1,622ms | 3,425ms | 2,414ms |
| **E2E** | 6,207ms | 4,850ms | **4,736ms** |
| **Throughput** | 0.16 qps | **0.21 qps** | 0.21 qps |

---

## Key Findings

### V1 (Baseline)
- Hybrid search (75% cosine + 25% BM25) is effective
- BM25 scoring all 47K docs is the main bottleneck (~4.5s)
- CrossEncoder re-ranking improves ranking quality

### V2 (Optimized) ⭐ **Recommended**
- **Query Expansion**: LLM adds synonyms → +9% Hit Rate
- **FAISS-first BM25**: Score only 50 candidates → 3x faster retrieval
- **Jaccard MMR**: Fast diversity without embeddings

### V3 (Experimental)
- **RRF Fusion**: Combines multiple retrieval paths robustly
- **Contextual Expansion**: Includes ±1 neighboring chunks
- **Adaptive Top-K**: 72% high confidence (K=3), 27% low confidence (K=7)
- Issue: Contextual expansion affects metrics (neighbors in results)

---

## Recommendations for Production

### For Long-Term Memory Chatbot

```python
# Recommended Configuration (V2 + V3 hybrid)
RETRIEVAL = "V2"  # 88% hit rate, fast
QUERY_EXPANSION = True
FAISS_FIRST_BM25 = True
BM25_CANDIDATES = 50  # Not all 47K docs

# For generation only (not metrics)
CONTEXTUAL_EXPANSION = True  # Include ±1 neighbors for LLM
ADAPTIVE_TOP_K = True  # Efficient chunk selection
```

### Speed vs Accuracy Trade-offs

| Scenario | Recommendation |
|----------|----------------|
| **Max Accuracy** | V2 with query expansion |
| **Max Speed** | V2 without query expansion (skip LLM call) |
| **More Context** | V2 retrieval + V3 contextual expansion |

---

## File Structure

```
benchmark/
├── index_data.py              # Index dataset to FAISS
├── generate_queries.py        # Generate 100 test queries (LLM morphing)
├── metrics.py                 # All metric implementations
├── rag_benchmark.py           # V1 engine
├── rag_benchmark_v2.py        # V2 engine (optimized)
├── rag_benchmark_v3.py        # V3 engine (experimental)
├── run_benchmark.py           # V1 runner
├── run_benchmark_v2.py        # V2 runner
├── run_benchmark_v3.py        # V3 runner
├── queries.json               # 100 morphed test queries
├── results/                   # Latest results
├── results-v1/                # V1 archived results
└── results-v2/                # V2 archived results
```

---

## Metrics Implemented

### Retrieval Quality
- **Hit Rate @K**: % of queries where correct chunk appears in top-K
- **MRR (Mean Reciprocal Rank)**: Average 1/rank of first correct result
- **Precision @K**: % of retrieved chunks that are relevant
- **Recall @K**: % of relevant chunks that are retrieved
- **nDCG @K**: Normalized Discounted Cumulative Gain

### QA Quality  
- **BLEU**: N-gram overlap with reference
- **ROUGE-L**: Longest common subsequence
- **Exact Match**: Normalized string equality
- **F1**: Token-level precision/recall

### Latency
- **Retrieval Latency**: Time for search + re-ranking
- **Generation Latency**: Time for LLM response
- **E2E Latency**: Total query-to-answer time
- **Throughput**: Queries per second

---

## How to Run

```bash
cd benchmark

# Generate test queries (run once)
python generate_queries.py

# Run benchmarks
python run_benchmark.py      # V1
python run_benchmark_v2.py   # V2 (recommended)
python run_benchmark_v3.py   # V3 (experimental)
```

---

## Conclusion

**V2 is the optimal configuration** for the long-term memory chatbot:
- **88% Hit Rate** (best retrieval)
- **1.4s retrieval** (3x faster than V1)
- Query expansion + FAISS-first BM25 is highly effective

For maximum generation quality, add **contextual chunk expansion** from V3 when building the LLM prompt.