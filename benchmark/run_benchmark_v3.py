"""
run_benchmark_v3.py - RAG Benchmark Orchestrator V3

V3 Features:
- Contextual Chunk Expansion
- Reciprocal Rank Fusion (RRF)
- Adaptive Top-K based on confidence

Usage: python run_benchmark_v3.py
"""

import os
import sys
import json
import csv
import time
from datetime import datetime
from tqdm import tqdm
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_benchmark_v3 import get_benchmark_engine_v3
from metrics import compute_retrieval_metrics, compute_qa_metrics

# ==============================================================================
# CONFIGURATION
# ==============================================================================

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
QUERIES_PATH = os.path.join(SCRIPT_DIR, "queries.json")
RESULTS_DIR = os.path.join(SCRIPT_DIR, "results")
OUTPUT_CSV = os.path.join(RESULTS_DIR, "benchmark_results.csv")

TOP_K = 5

CSV_COLUMNS = [
    "id", "query", "original_query", "expected_response", "llm_output",
    "expected_chunk_id", "retrieved_chunk_ids",
    "hit_rate_5", "mrr", "precision_5", "recall_5", "ndcg_5",
    "bleu", "rouge_l", "exact_match", "f1",
    "retrieval_latency_ms", "generation_latency_ms", "e2e_latency_ms",
    "adaptive_k", "confidence_level"
]


def run_benchmark():
    print("=" * 70)
    print("  RAG Benchmark Suite V3")
    print("  Features: RRF, Contextual Expansion, Adaptive Top-K")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    print(f"\n[1/4] Loading queries from {QUERIES_PATH}...")
    if not os.path.exists(QUERIES_PATH):
        print(f"ERROR: Queries file not found. Run generate_queries.py first.")
        sys.exit(1)
    
    with open(QUERIES_PATH, "r", encoding="utf-8") as f:
        queries = json.load(f)
    print(f"      Loaded {len(queries)} queries")
    
    print(f"\n[2/4] Initializing RAG engine V3...")
    engine = get_benchmark_engine_v3()
    
    print(f"\n[3/4] Running benchmark...")
    results = []
    
    # Aggregates
    total_hit_rate = total_mrr = total_precision = total_recall = total_ndcg = 0
    total_bleu = total_rouge = total_em = total_f1 = 0
    total_retrieval_latency = total_generation_latency = total_e2e_latency = 0
    confidence_counts = {"high": 0, "medium": 0, "low": 0}
    
    for query_data in tqdm(queries, desc="Benchmarking V3"):
        query_id = query_data["id"]
        query = query_data["query"]
        original_query = query_data.get("original_query", query)
        expected_chunk_id = query_data["expected_chunk_id"]
        expected_response = query_data.get("expected_response", "")
        
        relevant_ids = {expected_chunk_id}
        e2e_start = time.time()
        
        # V3 hybrid search with RRF, adaptive K, contextual expansion
        retrieval_result = engine.hybrid_search(query, top_k=TOP_K)
        
        # Generate answer
        generation_result = engine.generate_answer(query, retrieval_result.chunks)
        
        e2e_latency_ms = (time.time() - e2e_start) * 1000
        
        # Metrics (note: we use original chunk_ids for metrics, not expanded)
        retrieval_metrics = compute_retrieval_metrics(
            retrieved_ids=retrieval_result.chunk_ids,
            relevant_ids=relevant_ids,
            k=TOP_K
        )
        qa_metrics = compute_qa_metrics(
            prediction=generation_result.answer,
            reference=expected_response
        )
        
        # Aggregate
        total_hit_rate += retrieval_metrics["hit_rate"]
        total_mrr += retrieval_metrics["mrr"]
        total_precision += retrieval_metrics["precision"]
        total_recall += retrieval_metrics["recall"]
        total_ndcg += retrieval_metrics["ndcg"]
        total_bleu += qa_metrics["bleu"]
        total_rouge += qa_metrics["rouge_l"]
        total_em += qa_metrics["exact_match"]
        total_f1 += qa_metrics["f1"]
        total_retrieval_latency += retrieval_result.retrieval_time_ms
        total_generation_latency += generation_result.generation_time_ms
        total_e2e_latency += e2e_latency_ms
        confidence_counts[retrieval_result.confidence_level] += 1
        
        result = {
            "id": query_id,
            "query": query,
            "original_query": original_query,
            "expected_response": expected_response[:500] + "..." if len(expected_response) > 500 else expected_response,
            "llm_output": generation_result.answer[:500] + "..." if len(generation_result.answer) > 500 else generation_result.answer,
            "expected_chunk_id": expected_chunk_id,
            "retrieved_chunk_ids": str(retrieval_result.chunk_ids[:5]),  # First 5 for readability
            "hit_rate_5": round(retrieval_metrics["hit_rate"], 4),
            "mrr": round(retrieval_metrics["mrr"], 4),
            "precision_5": round(retrieval_metrics["precision"], 4),
            "recall_5": round(retrieval_metrics["recall"], 4),
            "ndcg_5": round(retrieval_metrics["ndcg"], 4),
            "bleu": round(qa_metrics["bleu"], 4),
            "rouge_l": round(qa_metrics["rouge_l"], 4),
            "exact_match": round(qa_metrics["exact_match"], 4),
            "f1": round(qa_metrics["f1"], 4),
            "retrieval_latency_ms": round(retrieval_result.retrieval_time_ms, 2),
            "generation_latency_ms": round(generation_result.generation_time_ms, 2),
            "e2e_latency_ms": round(e2e_latency_ms, 2),
            "adaptive_k": retrieval_result.adaptive_k_used,
            "confidence_level": retrieval_result.confidence_level
        }
        results.append(result)
    
    # Write CSV
    print(f"\n[4/4] Writing results to {OUTPUT_CSV}...")
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(results)
    print(f"      Saved {len(results)} results")
    
    n = len(queries)
    
    print("\n" + "=" * 70)
    print("  BENCHMARK V3 SUMMARY")
    print("=" * 70)
    print("\n  📊 Retrieval Metrics (averaged):")
    print(f"      Hit Rate @{TOP_K}:    {total_hit_rate / n:.4f}")
    print(f"      MRR:             {total_mrr / n:.4f}")
    print(f"      Precision @{TOP_K}:  {total_precision / n:.4f}")
    print(f"      Recall @{TOP_K}:     {total_recall / n:.4f}")
    print(f"      nDCG @{TOP_K}:       {total_ndcg / n:.4f}")
    
    print("\n  📝 QA Metrics (averaged):")
    print(f"      BLEU:            {total_bleu / n:.4f}")
    print(f"      ROUGE-L:         {total_rouge / n:.4f}")
    print(f"      Exact Match:     {total_em / n:.4f}")
    print(f"      F1:              {total_f1 / n:.4f}")
    
    print("\n  ⏱️  Latency Metrics (averaged):")
    print(f"      Retrieval:       {total_retrieval_latency / n:.2f} ms")
    print(f"      Generation:      {total_generation_latency / n:.2f} ms")
    print(f"      E2E:             {total_e2e_latency / n:.2f} ms")
    
    total_time_s = total_e2e_latency / 1000
    throughput = n / total_time_s if total_time_s > 0 else 0
    print(f"      Throughput:      {throughput:.2f} queries/sec")
    
    print("\n  🎯 Adaptive Top-K Distribution:")
    print(f"      High confidence: {confidence_counts['high']} queries")
    print(f"      Medium:          {confidence_counts['medium']} queries")
    print(f"      Low confidence:  {confidence_counts['low']} queries")
    
    # Save summary
    summary_path = os.path.join(RESULTS_DIR, "benchmark_summary.json")
    summary = {
        "timestamp": datetime.now().isoformat(),
        "version": "v3",
        "improvements": ["reciprocal_rank_fusion", "contextual_chunk_expansion", "adaptive_top_k"],
        "num_queries": n,
        "top_k": TOP_K,
        "retrieval_metrics": {
            "hit_rate": round(total_hit_rate / n, 4),
            "mrr": round(total_mrr / n, 4),
            "precision": round(total_precision / n, 4),
            "recall": round(total_recall / n, 4),
            "ndcg": round(total_ndcg / n, 4)
        },
        "qa_metrics": {
            "bleu": round(total_bleu / n, 4),
            "rouge_l": round(total_rouge / n, 4),
            "exact_match": round(total_em / n, 4),
            "f1": round(total_f1 / n, 4)
        },
        "latency_metrics": {
            "avg_retrieval_ms": round(total_retrieval_latency / n, 2),
            "avg_generation_ms": round(total_generation_latency / n, 2),
            "avg_e2e_ms": round(total_e2e_latency / n, 2),
            "throughput_qps": round(throughput, 2)
        },
        "confidence_distribution": confidence_counts
    }
    
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n      Summary saved to: {summary_path}")
    
    print("\n" + "=" * 70)
    print("  BENCHMARK V3 COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    run_benchmark()
