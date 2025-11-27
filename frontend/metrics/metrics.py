# eval_metrics.py
from math import log2
from typing import List, Set, Dict
import numpy as np

def precision_at_k(ranked: List[int], relevant: Set[int], k: int) -> float:
    if k <= 0:
        return 0.0
    topk = ranked[:k]
    return sum(1 for d in topk if d in relevant) / k

def recall_at_k(ranked: List[int], relevant: Set[int], k: int) -> float:
    if not relevant:
        return 0.0
    topk = ranked[:k]
    return sum(1 for d in topk if d in relevant) / len(relevant)

def f1_at_k(ranked: List[int], relevant: Set[int], k: int) -> float:
    p = precision_at_k(ranked, relevant, k)
    r = recall_at_k(ranked, relevant, k)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)

def average_precision(ranked: List[int], relevant: Set[int]) -> float:
    """AP: average precision for a single query."""
    if not relevant:
        return 0.0
    hits = 0
    sum_prec = 0.0
    for i, d in enumerate(ranked, start=1):
        if d in relevant:
            hits += 1
            sum_prec += hits / i
    if hits == 0:
        return 0.0
    return sum_prec / len(relevant)

def map_score(results: Dict[int, List[int]], qrels: Dict[int, Set[int]]) -> float:
    """Mean Average Precision over queries present in results."""
    ap_list = []
    for qid, ranked in results.items():
        rel = qrels.get(qid, set())
        ap_list.append(average_precision(ranked, rel))
    if not ap_list:
        return 0.0
    return sum(ap_list) / len(ap_list)

def dcg_at_k(ranked: List[int], relevant: Set[int], k: int) -> float:
    dcg = 0.0
    for i, d in enumerate(ranked[:k], start=1):
        rel = 1.0 if d in relevant else 0.0
        if i == 1:
            dcg += rel
        else:
            dcg += rel / log2(i + 0)
    return dcg

def idcg_at_k(num_relevant: int, k: int) -> float:
    """Ideal DCG: when all top positions are relevant."""
    idcg = 0.0
    for i in range(1, min(num_relevant, k) + 1):
        if i == 1:
            idcg += 1.0
        else:
            idcg += 1.0 / log2(i + 0)
    return idcg

def ndcg_at_k(ranked: List[int], relevant: Set[int], k: int) -> float:
    idcg = idcg_at_k(len(relevant), k)
    if idcg == 0:
        return 0.0
    return dcg_at_k(ranked, relevant, k) / idcg

def precision_recall_curve_points(ranked: List[int], relevant: Set[int]) -> List[tuple]:
    """Return list of (recall, precision) pairs at each rank where relevant found."""
    points = []
    hits = 0
    for i, d in enumerate(ranked, start=1):
        if d in relevant:
            hits += 1
            prec = hits / i
            rec = hits / len(relevant) if relevant else 0.0
            points.append((rec, prec))
    # Add (0,1) and (1,0) optionally
    return points
