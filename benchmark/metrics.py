"""
metrics.py - RAG Evaluation Metrics

Implements all benchmark metrics:
- Retrieval: Hit Rate, MRR, Precision, Recall, nDCG
- QA: BLEU, ROUGE-L, Exact Match, F1
"""

import re
import math
from typing import List, Set
from collections import Counter

# ==============================================================================
# RETRIEVAL METRICS
# ==============================================================================

def hit_rate_at_k(retrieved_ids: List[int], relevant_ids: Set[int], k: int = 5) -> float:
    """
    Hit Rate @K: 1 if any relevant document appears in top-K, else 0.
    
    Args:
        retrieved_ids: List of retrieved document IDs (in order)
        relevant_ids: Set of ground truth relevant document IDs
        k: Number of top results to consider
    
    Returns:
        1.0 if hit, 0.0 otherwise
    """
    top_k = set(retrieved_ids[:k])
    return 1.0 if len(top_k & relevant_ids) > 0 else 0.0


def mean_reciprocal_rank(retrieved_ids: List[int], relevant_ids: Set[int]) -> float:
    """
    MRR: 1/rank of the first relevant document.
    
    Args:
        retrieved_ids: List of retrieved document IDs (in order)
        relevant_ids: Set of ground truth relevant document IDs
    
    Returns:
        1/rank if found, 0.0 otherwise
    """
    for i, doc_id in enumerate(retrieved_ids):
        if doc_id in relevant_ids:
            return 1.0 / (i + 1)
    return 0.0


def precision_at_k(retrieved_ids: List[int], relevant_ids: Set[int], k: int = 5) -> float:
    """
    Precision @K: Proportion of relevant documents in top-K.
    
    Args:
        retrieved_ids: List of retrieved document IDs (in order)
        relevant_ids: Set of ground truth relevant document IDs
        k: Number of top results to consider
    
    Returns:
        Precision score (0-1)
    """
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    relevant_in_top_k = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return relevant_in_top_k / len(top_k)


def recall_at_k(retrieved_ids: List[int], relevant_ids: Set[int], k: int = 5) -> float:
    """
    Recall @K: Proportion of relevant documents retrieved in top-K.
    
    Args:
        retrieved_ids: List of retrieved document IDs (in order)
        relevant_ids: Set of ground truth relevant document IDs
        k: Number of top results to consider
    
    Returns:
        Recall score (0-1)
    """
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    relevant_retrieved = len(top_k & relevant_ids)
    return relevant_retrieved / len(relevant_ids)


def dcg_at_k(retrieved_ids: List[int], relevant_ids: Set[int], k: int = 5) -> float:
    """
    Discounted Cumulative Gain @K.
    """
    dcg = 0.0
    for i, doc_id in enumerate(retrieved_ids[:k]):
        rel = 1.0 if doc_id in relevant_ids else 0.0
        dcg += rel / math.log2(i + 2)  # +2 because log2(1) = 0
    return dcg


def ndcg_at_k(retrieved_ids: List[int], relevant_ids: Set[int], k: int = 5) -> float:
    """
    Normalized Discounted Cumulative Gain @K.
    
    Args:
        retrieved_ids: List of retrieved document IDs (in order)
        relevant_ids: Set of ground truth relevant document IDs
        k: Number of top results to consider
    
    Returns:
        nDCG score (0-1)
    """
    dcg = dcg_at_k(retrieved_ids, relevant_ids, k)
    
    # Ideal DCG: all relevant docs at the top
    ideal_retrieved = list(relevant_ids)[:k] + [None] * max(0, k - len(relevant_ids))
    idcg = dcg_at_k(ideal_retrieved, relevant_ids, k) if relevant_ids else 0.0
    
    if idcg == 0:
        return 0.0
    return dcg / idcg


# ==============================================================================
# QA METRICS
# ==============================================================================

def tokenize(text: str) -> List[str]:
    """Simple tokenization: lowercase and split on non-alphanumeric."""
    return re.findall(r'\w+', text.lower())


def exact_match(prediction: str, reference: str) -> float:
    """
    Exact Match: 1 if normalized strings are identical, else 0.
    """
    pred_normalized = " ".join(tokenize(prediction))
    ref_normalized = " ".join(tokenize(reference))
    return 1.0 if pred_normalized == ref_normalized else 0.0


def f1_score(prediction: str, reference: str) -> float:
    """
    Token-level F1 score.
    """
    pred_tokens = tokenize(prediction)
    ref_tokens = tokenize(reference)
    
    if not pred_tokens or not ref_tokens:
        return 0.0
    
    pred_counter = Counter(pred_tokens)
    ref_counter = Counter(ref_tokens)
    
    # Count common tokens
    common = sum((pred_counter & ref_counter).values())
    
    if common == 0:
        return 0.0
    
    precision = common / len(pred_tokens)
    recall = common / len(ref_tokens)
    
    return 2 * precision * recall / (precision + recall)


def bleu_score(prediction: str, reference: str, max_n: int = 4) -> float:
    """
    BLEU score (simplified implementation).
    Uses corpus-level BLEU with smoothing.
    """
    pred_tokens = tokenize(prediction)
    ref_tokens = tokenize(reference)
    
    if not pred_tokens or not ref_tokens:
        return 0.0
    
    # Calculate n-gram precisions
    precisions = []
    for n in range(1, max_n + 1):
        pred_ngrams = Counter(zip(*[pred_tokens[i:] for i in range(n)]))
        ref_ngrams = Counter(zip(*[ref_tokens[i:] for i in range(n)]))
        
        if not pred_ngrams:
            precisions.append(0.0)
            continue
        
        # Clipped counts
        clipped_count = sum(min(pred_ngrams[ng], ref_ngrams.get(ng, 0)) for ng in pred_ngrams)
        total_count = sum(pred_ngrams.values())
        
        # Add smoothing to avoid zero
        precision = (clipped_count + 1) / (total_count + 1)
        precisions.append(precision)
    
    if not precisions or all(p == 0 for p in precisions):
        return 0.0
    
    # Geometric mean of precisions
    log_sum = sum(math.log(p) if p > 0 else -float('inf') for p in precisions)
    geo_mean = math.exp(log_sum / len(precisions))
    
    # Brevity penalty
    bp = 1.0 if len(pred_tokens) >= len(ref_tokens) else math.exp(1 - len(ref_tokens) / len(pred_tokens))
    
    return bp * geo_mean


def rouge_l_score(prediction: str, reference: str) -> float:
    """
    ROUGE-L score (Longest Common Subsequence based F1).
    """
    pred_tokens = tokenize(prediction)
    ref_tokens = tokenize(reference)
    
    if not pred_tokens or not ref_tokens:
        return 0.0
    
    # LCS length using DP
    m, n = len(pred_tokens), len(ref_tokens)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if pred_tokens[i - 1] == ref_tokens[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    
    lcs_length = dp[m][n]
    
    if lcs_length == 0:
        return 0.0
    
    precision = lcs_length / len(pred_tokens)
    recall = lcs_length / len(ref_tokens)
    
    return 2 * precision * recall / (precision + recall)


# ==============================================================================
# AGGREGATION
# ==============================================================================

def compute_retrieval_metrics(
    retrieved_ids: List[int], 
    relevant_ids: Set[int], 
    k: int = 5
) -> dict:
    """
    Compute all retrieval metrics at once.
    
    Returns dict with: hit_rate, mrr, precision, recall, ndcg
    """
    return {
        "hit_rate": hit_rate_at_k(retrieved_ids, relevant_ids, k),
        "mrr": mean_reciprocal_rank(retrieved_ids, relevant_ids),
        "precision": precision_at_k(retrieved_ids, relevant_ids, k),
        "recall": recall_at_k(retrieved_ids, relevant_ids, k),
        "ndcg": ndcg_at_k(retrieved_ids, relevant_ids, k)
    }


def compute_qa_metrics(prediction: str, reference: str) -> dict:
    """
    Compute all QA metrics at once.
    
    Returns dict with: bleu, rouge_l, exact_match, f1
    """
    return {
        "bleu": bleu_score(prediction, reference),
        "rouge_l": rouge_l_score(prediction, reference),
        "exact_match": exact_match(prediction, reference),
        "f1": f1_score(prediction, reference)
    }
