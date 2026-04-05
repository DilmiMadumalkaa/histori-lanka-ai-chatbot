"""
Phase 3: RAG Testing - Evaluation Metrics
==========================================
Precision, Recall, MRR, NDCG, MAP for measuring retrieval quality
"""

from typing import List, Dict, Tuple
import numpy as np
from dataclasses import dataclass


@dataclass
class EvaluationMetrics:
    """Container for retrieval evaluation metrics"""
    
    # Basic metrics
    precision_at_3: float  # P@3: How many of top 3 are relevant?
    precision_at_5: float  # P@5: How many of top 5 are relevant?
    precision_at_10: float # P@10: How many of top 10 are relevant?
    
    recall_at_5: float     # R@5: What fraction of relevant docs in top 5?
    recall_at_10: float    # R@10: What fraction of relevant docs in top 10?
    
    mrr: float             # MRR: Average position of first relevant result
    ndcg_at_10: float      # NDCG@10: Discounted cumulative gain with ideal ranking
    map_at_10: float       # MAP@10: Mean average precision at 10
    
    # Statistical
    mean_rank: float       # Average rank of first relevant result
    median_rank: float     # Median rank of first relevant result
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for reporting"""
        return {
            "precision@3": round(self.precision_at_3, 4),
            "precision@5": round(self.precision_at_5, 4),
            "precision@10": round(self.precision_at_10, 4),
            "recall@5": round(self.recall_at_5, 4),
            "recall@10": round(self.recall_at_10, 4),
            "mrr": round(self.mrr, 4),
            "ndcg@10": round(self.ndcg_at_10, 4),
            "map@10": round(self.map_at_10, 4),
            "mean_rank": round(self.mean_rank, 2),
            "median_rank": round(self.median_rank, 2)
        }


class RankingEvaluator:
    """Evaluate retrieval system performance"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []
    
    def evaluate(self, retrieved: List[str], relevant: List[str]) -> EvaluationMetrics:
        """
        Evaluate a single retrieval result
        
        Args:
            retrieved: List of retrieved site names (in order)
            relevant: List of ground truth relevant site names
        
        Returns:
            EvaluationMetrics object with all metrics
        """
        
        # Normalize (lowercase, handle variations)
        retrieved = self._normalize(retrieved)
        relevant = self._normalize(relevant)
        
        # Calculate basic metrics
        p_at_3 = self.precision_at_k(retrieved, relevant, 3)
        p_at_5 = self.precision_at_k(retrieved, relevant, 5)
        p_at_10 = self.precision_at_k(retrieved, relevant, 10)
        
        r_at_5 = self.recall_at_k(retrieved, relevant, 5)
        r_at_10 = self.recall_at_k(retrieved, relevant, 10)
        
        mrr = self.mrr_score(retrieved, relevant)
        ndcg = self.ndcg_score(retrieved, relevant, 10)
        map_score = self.map_score(retrieved, relevant, 10)
        
        # Ranking statistics
        first_rank = self.first_rank_position(retrieved, relevant)
        ranks = []
        for site in relevant:
            try:
                rank = retrieved.index(site) + 1
                ranks.append(rank)
            except ValueError:
                ranks.append(len(retrieved) + 1)
        
        mean_rank = float(np.mean(ranks)) if ranks else len(retrieved) + 1
        median_rank = float(np.median(ranks)) if ranks else len(retrieved) + 1
        
        metrics = EvaluationMetrics(
            precision_at_3=p_at_3,
            precision_at_5=p_at_5,
            precision_at_10=p_at_10,
            recall_at_5=r_at_5,
            recall_at_10=r_at_10,
            mrr=mrr,
            ndcg_at_10=ndcg,
            map_at_10=map_score,
            mean_rank=mean_rank,
            median_rank=median_rank
        )
        
        self.results.append(metrics)
        return metrics
    
    @staticmethod
    def _normalize(sites: List[str]) -> List[str]:
        """Normalize site names for comparison"""
        normalized = []
        for site in sites:
            # Lowercase and remove extra whitespace
            norm = site.lower().strip()
            # Handle common variations
            if "temple of the tooth" in norm:
                norm = "temple of the tooth"
            elif "peradeniya" in norm:
                norm = "peradeniya botanical garden"
            normalized.append(norm)
        return normalized
    
    @staticmethod
    def precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """Precision@k: Fraction of top-k that are relevant"""
        if k == 0:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        hits = sum(1 for item in retrieved_at_k if item in relevant)
        return hits / k
    
    @staticmethod
    def recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
        """Recall@k: Fraction of relevant items in top-k"""
        if not relevant:
            return 0.0
        
        retrieved_at_k = retrieved[:k]
        hits = sum(1 for item in retrieved_at_k if item in relevant)
        return hits / len(relevant)
    
    @staticmethod
    def mrr_score(retrieved: List[str], relevant: List[str]) -> float:
        """MRR: Mean Reciprocal Rank - 1/rank of first relevant result"""
        for i, item in enumerate(retrieved):
            if item in relevant:
                return 1.0 / (i + 1)
        return 0.0  # No relevant result found
    
    @staticmethod
    def first_rank_position(retrieved: List[str], relevant: List[str]) -> int:
        """Position of first relevant result"""
        for i, item in enumerate(retrieved):
            if item in relevant:
                return i + 1
        return len(retrieved) + 1
    
    @staticmethod
    def ndcg_score(retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        NDCG@k: Normalized Discounted Cumulative Gain
        Measures ranking quality by penalizing relevant results appearing later
        """
        # Ideal ranking (all relevant first)
        ideal = relevant[:k]
        ideal += [x for x in retrieved if x not in ideal][:k - len(ideal)]
        
        def dcg(ranking):
            score = 0.0
            for i, item in enumerate(ranking[:k]):
                rel = 1.0 if item in relevant else 0.0
                score += rel / np.log2(i + 2)  # +2 because indexing starts at 0
            return score
        
        dcg_actual = dcg(retrieved)
        dcg_ideal = dcg(ideal)
        
        if dcg_ideal == 0:
            return 1.0
        
        return dcg_actual / dcg_ideal
    
    @staticmethod
    def map_score(retrieved: List[str], relevant: List[str], k: int) -> float:
        """
        MAP@k: Mean Average Precision
        Average of precisions at positions where relevant items appear
        """
        precisions = []
        
        for i, item in enumerate(retrieved[:k]):
            if item in relevant:
                # Calculate precision@(i+1)
                hits = sum(1 for x in retrieved[:i+1] if x in relevant)
                precisions.append(hits / (i + 1))
        
        if not precisions:
            return 0.0
        
        return sum(precisions) / len(relevant)
    
    def get_aggregated_metrics(self) -> Dict:
        """Calculate average metrics across all evaluations"""
        if not self.results:
            return {}
        
        metrics = {
            "precision@3": np.mean([m.precision_at_3 for m in self.results]),
            "precision@5": np.mean([m.precision_at_5 for m in self.results]),
            "precision@10": np.mean([m.precision_at_10 for m in self.results]),
            "recall@5": np.mean([m.recall_at_5 for m in self.results]),
            "recall@10": np.mean([m.recall_at_10 for m in self.results]),
            "mrr": np.mean([m.mrr for m in self.results]),
            "ndcg@10": np.mean([m.ndcg_at_10 for m in self.results]),
            "map@10": np.mean([m.map_at_10 for m in self.results]),
            "mean_rank": np.mean([m.mean_rank for m in self.results]),
        }
        
        # Add standard deviations
        metrics["precision@3_std"] = np.std([m.precision_at_3 for m in self.results])
        metrics["recall@10_std"] = np.std([m.recall_at_10 for m in self.results])
        metrics["mrr_std"] = np.std([m.mrr for m in self.results])
        
        # Add percentiles
        mrr_scores = [m.mrr for m in self.results]
        metrics["mrr_percentile_50"] = float(np.percentile(mrr_scores, 50))
        metrics["mrr_percentile_75"] = float(np.percentile(mrr_scores, 75))
        metrics["mrr_percentile_90"] = float(np.percentile(mrr_scores, 90))
        
        return metrics


class RetrievalComparator:
    """Compare two retrieval systems (e.g., with/without reranking)"""
    
    def __init__(self):
        self.baseline_results = []
        self.test_results = []
    
    def add_baseline(self, retrieved: List[str], relevant: List[str]):
        """Add baseline retrieval result"""
        evaluator = RankingEvaluator()
        metrics = evaluator.evaluate(retrieved, relevant)
        self.baseline_results.append(metrics)
    
    def add_test(self, retrieved: List[str], relevant: List[str]):
        """Add test system retrieval result"""
        evaluator = RankingEvaluator()
        metrics = evaluator.evaluate(retrieved, relevant)
        self.test_results.append(metrics)
    
    def compare(self) -> Dict:
        """Compare baseline vs test system"""
        
        if not self.baseline_results or not self.test_results:
            return {"error": "Need both baseline and test results"}
        
        baseline_avg = self._average_metrics(self.baseline_results)
        test_avg = self._average_metrics(self.test_results)
        
        improvements = {}
        for metric in baseline_avg.keys():
            baseline = baseline_avg[metric]
            test = test_avg[metric]
            
            if baseline == 0:
                improvement = 0 if test == 0 else float('inf')
            else:
                improvement = (test - baseline) / baseline * 100
            
            improvements[metric] = {
                "baseline": round(baseline, 4),
                "test": round(test, 4),
                "improvement_pct": round(improvement, 2),
                "absolute_change": round(test - baseline, 4)
            }
        
        return improvements
    
    @staticmethod
    def _average_metrics(results: List[EvaluationMetrics]) -> Dict:
        """Calculate average metrics"""
        return {
            "precision@3": np.mean([m.precision_at_3 for m in results]),
            "precision@5": np.mean([m.precision_at_5 for m in results]),
            "precision@10": np.mean([m.precision_at_10 for m in results]),
            "recall@5": np.mean([m.recall_at_5 for m in results]),
            "recall@10": np.mean([m.recall_at_10 for m in results]),
            "mrr": np.mean([m.mrr for m in results]),
            "ndcg@10": np.mean([m.ndcg_at_10 for m in results]),
            "map@10": np.mean([m.map_at_10 for m in results]),
        }


# Utility functions for interpreting metrics

def interpret_mrr(mrr: float) -> str:
    """Interpret MRR score"""
    if mrr >= 0.8:
        return "Excellent - First relevant result usually in top 2"
    elif mrr >= 0.5:
        return "Good - First relevant result usually in top 3"
    elif mrr >= 0.33:
        return "Fair - First relevant result usually in top 4"
    else:
        return "Poor - First relevant result often beyond top 5"


def interpret_precision(p: float) -> str:
    """Interpret precision score"""
    if p >= 0.8:
        return "Excellent - Most results are relevant"
    elif p >= 0.6:
        return "Good - Majority of results are relevant"
    elif p >= 0.4:
        return "Fair - Some irrelevant results mixed in"
    else:
        return "Poor - Many irrelevant results"


def interpret_recall(r: float) -> str:
    """Interpret recall score"""
    if r >= 0.8:
        return "Excellent - Most relevant results found"
    elif r >= 0.6:
        return "Good - Majority of relevant results found"
    elif r >= 0.4:
        return "Fair - Some relevant results found"
    else:
        return "Poor - Missing many relevant results"


if __name__ == "__main__":
    # Example usage
    print("=" * 70)
    print("EVALUATION METRICS - EXAMPLES")
    print("=" * 70)
    
    # Test case 1: Perfect retrieval
    print("\nTest 1: Perfect retrieval")
    evaluator = RankingEvaluator()
    retrieved = ["Sigiriya", "Polonnaruwa", "Yapahuwa", "Kandy", "Galle"]
    relevant = ["Sigiriya", "Polonnaruwa", "Yapahuwa"]
    metrics = evaluator.evaluate(retrieved, relevant)
    print(f"  P@3: {metrics.precision_at_3:.2f} (all 3 are relevant)")
    print(f"  MRR: {metrics.mrr:.2f} (first relevant at position 1)")
    print(f"  Recall@5: {metrics.recall_at_5:.2f} (found all 3 relevant)")
    
    # Test case 2: Partially relevant retrieval
    print("\nTest 2: Partially relevant retrieval")
    retrieved = ["Kandy", "Sigiriya", "Museum", "Polonnaruwa", "Random"]
    relevant = ["Sigiriya", "Polonnaruwa", "Yapahuwa"]
    metrics = evaluator.evaluate(retrieved, relevant)
    print(f"  P@3: {metrics.precision_at_3:.2f} (only 1 of 3 relevant)")
    print(f"  MRR: {metrics.mrr:.2f} (first relevant at position 2)")
    print(f"  Recall@5: {metrics.recall_at_5:.2f} (found 2 of 3 relevant)")
    
    print("\n[+] Metrics module ready for RAG testing!")
