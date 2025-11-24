"""
Prompt Evaluation and Benchmarking System for NEUIToolkit.

This module provides tools for:
- Evaluating prompt quality and performance
- A/B testing between prompt versions
- Benchmarking against gold standard datasets
- Comparing domain-specific vs general prompts
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of evaluation metrics."""
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    ACCURACY = "accuracy"


@dataclass
class EvaluationResult:
    """Results from a prompt evaluation.

    Attributes:
        prompt_id: Identifier for the prompt being evaluated
        domain: Domain of the prompt
        version: Version of the prompt
        metrics: Dictionary of metric scores
        extraction_count: Number of extractions produced
        evaluation_time: Timestamp of evaluation
        sample_size: Number of test cases evaluated
        notes: Additional observations
    """
    prompt_id: str
    domain: str
    version: str
    metrics: Dict[str, float]
    extraction_count: int
    evaluation_time: datetime = field(default_factory=datetime.now)
    sample_size: int = 0
    notes: str = ""

    def get_overall_score(self) -> float:
        """Calculate weighted overall score."""
        if not self.metrics:
            return 0.0

        # Weighted average (F1 and accuracy more important)
        weights = {
            MetricType.F1_SCORE: 0.3,
            MetricType.ACCURACY: 0.3,
            MetricType.PRECISION: 0.15,
            MetricType.RECALL: 0.15,
            MetricType.CONSISTENCY: 0.1
        }

        total_weight = 0
        weighted_sum = 0

        for metric, weight in weights.items():
            if metric.value in self.metrics:
                weighted_sum += self.metrics[metric.value] * weight
                total_weight += weight

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "prompt_id": self.prompt_id,
            "domain": self.domain,
            "version": self.version,
            "metrics": self.metrics,
            "extraction_count": self.extraction_count,
            "evaluation_time": self.evaluation_time.isoformat(),
            "sample_size": self.sample_size,
            "overall_score": self.get_overall_score(),
            "notes": self.notes
        }


@dataclass
class GoldStandardItem:
    """A gold standard test case for evaluation.

    Attributes:
        id: Unique identifier
        text: Input text corpus
        expected_entities: Expected entity extractions
        expected_relationships: Expected relationship extractions
        expected_rules: Expected rule extractions
        domain: Domain category
        difficulty: Difficulty level (easy, medium, hard)
    """
    id: str
    text: str
    expected_entities: List[Dict[str, Any]]
    expected_relationships: List[Dict[str, Any]] = field(default_factory=list)
    expected_rules: List[Dict[str, Any]] = field(default_factory=list)
    domain: str = "general"
    difficulty: str = "medium"


class PromptEvaluator:
    """Evaluate and benchmark prompt performance."""

    def __init__(self, gold_standard_path: Optional[Path] = None):
        """Initialize evaluator.

        Args:
            gold_standard_path: Path to gold standard test data
        """
        self.gold_standard_path = gold_standard_path or Path("prompts/examples/gold_standard.json")
        self.gold_standard_data: List[GoldStandardItem] = []
        self.evaluation_history: List[EvaluationResult] = []

        if self.gold_standard_path.exists():
            self.load_gold_standard()

    def load_gold_standard(self) -> int:
        """Load gold standard test data.

        Returns:
            Number of test cases loaded
        """
        try:
            with open(self.gold_standard_path) as f:
                data = json.load(f)

            for item in data:
                gold_item = GoldStandardItem(
                    id=item["id"],
                    text=item["text"],
                    expected_entities=item.get("expected_entities", []),
                    expected_relationships=item.get("expected_relationships", []),
                    expected_rules=item.get("expected_rules", []),
                    domain=item.get("domain", "general"),
                    difficulty=item.get("difficulty", "medium")
                )
                self.gold_standard_data.append(gold_item)

            logger.info(f"Loaded {len(self.gold_standard_data)} gold standard test cases")
            return len(self.gold_standard_data)

        except Exception as e:
            logger.error(f"Error loading gold standard: {e}")
            return 0

    def evaluate_entities(
        self,
        extracted: List[Dict[str, Any]],
        expected: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate entity extraction quality.

        Args:
            extracted: Entities extracted by the prompt
            expected: Expected/gold standard entities

        Returns:
            Dictionary of metric scores
        """
        if not expected:
            return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0}

        # Normalize names for comparison
        extracted_names = {e.get("name", "").lower() for e in extracted}
        expected_names = {e.get("name", "").lower() for e in expected}

        # Calculate metrics
        true_positives = len(extracted_names & expected_names)
        false_positives = len(extracted_names - expected_names)
        false_negatives = len(expected_names - extracted_names)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        }

    def evaluate_relationships(
        self,
        extracted: List[Dict[str, Any]],
        expected: List[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Evaluate relationship extraction quality.

        Args:
            extracted: Relationships extracted by the prompt
            expected: Expected/gold standard relationships

        Returns:
            Dictionary of metric scores
        """
        if not expected:
            return {"precision": 0.0, "recall": 0.0, "f1_score": 0.0}

        # Create normalized triples for comparison
        def normalize_triple(rel: Dict) -> str:
            return f"{rel.get('subject', '').lower()}|{rel.get('predicate', '').lower()}|{rel.get('object', '').lower()}"

        extracted_triples = {normalize_triple(r) for r in extracted}
        expected_triples = {normalize_triple(r) for r in expected}

        # Calculate metrics
        true_positives = len(extracted_triples & expected_triples)
        false_positives = len(extracted_triples - expected_triples)
        false_negatives = len(expected_triples - extracted_triples)

        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1_score": f1,
            "true_positives": true_positives,
            "false_positives": false_positives,
            "false_negatives": false_negatives
        }

    def calculate_consistency(self, extractions: List[Dict[str, Any]]) -> float:
        """Calculate consistency score for extractions.

        Checks for duplicate entities, consistent categorization, etc.

        Args:
            extractions: List of extracted items

        Returns:
            Consistency score (0.0-1.0)
        """
        if not extractions:
            return 1.0

        issues = 0

        # Check for duplicate names
        names = [e.get("name", "") for e in extractions]
        if len(names) != len(set(names)):
            issues += 1

        # Check for consistent categorization
        categories = [e.get("category", "") for e in extractions]
        if "" in categories:
            issues += len([c for c in categories if c == ""])

        # Consistency score
        max_issues = len(extractions)
        consistency = 1.0 - (issues / max_issues) if max_issues > 0 else 1.0

        return max(0.0, consistency)

    def compare_prompts(
        self,
        prompt_a_results: EvaluationResult,
        prompt_b_results: EvaluationResult
    ) -> Dict[str, Any]:
        """Compare two prompt evaluation results (A/B testing).

        Args:
            prompt_a_results: Results from prompt A
            prompt_b_results: Results from prompt B

        Returns:
            Comparison summary with winner and metrics
        """
        comparison = {
            "prompt_a": {
                "id": prompt_a_results.prompt_id,
                "domain": prompt_a_results.domain,
                "version": prompt_a_results.version,
                "overall_score": prompt_a_results.get_overall_score()
            },
            "prompt_b": {
                "id": prompt_b_results.prompt_id,
                "domain": prompt_b_results.domain,
                "version": prompt_b_results.version,
                "overall_score": prompt_b_results.get_overall_score()
            },
            "metric_comparison": {},
            "winner": None,
            "improvement": 0.0
        }

        # Compare individual metrics
        all_metrics = set(prompt_a_results.metrics.keys()) | set(prompt_b_results.metrics.keys())
        for metric in all_metrics:
            a_score = prompt_a_results.metrics.get(metric, 0.0)
            b_score = prompt_b_results.metrics.get(metric, 0.0)
            comparison["metric_comparison"][metric] = {
                "prompt_a": a_score,
                "prompt_b": b_score,
                "difference": b_score - a_score
            }

        # Determine winner
        a_overall = prompt_a_results.get_overall_score()
        b_overall = prompt_b_results.get_overall_score()

        if b_overall > a_overall:
            comparison["winner"] = "prompt_b"
            comparison["improvement"] = ((b_overall - a_overall) / a_overall * 100) if a_overall > 0 else 0
        elif a_overall > b_overall:
            comparison["winner"] = "prompt_a"
            comparison["improvement"] = ((a_overall - b_overall) / b_overall * 100) if b_overall > 0 else 0
        else:
            comparison["winner"] = "tie"
            comparison["improvement"] = 0.0

        return comparison

    def generate_report(
        self,
        results: List[EvaluationResult],
        output_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Generate comprehensive evaluation report.

        Args:
            results: List of evaluation results
            output_path: Optional path to save report

        Returns:
            Report dictionary
        """
        if not results:
            return {"error": "No results to report"}

        report = {
            "summary": {
                "total_evaluations": len(results),
                "evaluated_at": datetime.now().isoformat(),
                "domains": list(set(r.domain for r in results)),
                "versions": list(set(r.version for r in results))
            },
            "aggregate_metrics": {},
            "best_prompts": {},
            "recommendations": []
        }

        # Aggregate metrics by domain
        by_domain: Dict[str, List[EvaluationResult]] = {}
        for result in results:
            by_domain.setdefault(result.domain, []).append(result)

        for domain, domain_results in by_domain.items():
            overall_scores = [r.get_overall_score() for r in domain_results]

            report["aggregate_metrics"][domain] = {
                "count": len(domain_results),
                "mean_score": statistics.mean(overall_scores),
                "median_score": statistics.median(overall_scores),
                "stdev": statistics.stdev(overall_scores) if len(overall_scores) > 1 else 0,
                "min_score": min(overall_scores),
                "max_score": max(overall_scores)
            }

            # Identify best prompt for domain
            best = max(domain_results, key=lambda r: r.get_overall_score())
            report["best_prompts"][domain] = {
                "prompt_id": best.prompt_id,
                "version": best.version,
                "score": best.get_overall_score(),
                "metrics": best.metrics
            }

        # Generate recommendations
        report["recommendations"] = self._generate_recommendations(results)

        # Save report if path provided
        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Report saved to {output_path}")

        return report

    def _generate_recommendations(self, results: List[EvaluationResult]) -> List[str]:
        """Generate actionable recommendations from results.

        Args:
            results: Evaluation results

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Calculate average scores
        overall_scores = [r.get_overall_score() for r in results]
        avg_score = statistics.mean(overall_scores) if overall_scores else 0

        if avg_score < 0.6:
            recommendations.append("Overall prompt quality is low (<60%). Consider revising prompts with more examples and clearer instructions.")

        if avg_score >= 0.8:
            recommendations.append("Prompt quality is excellent (>80%). Consider using these as templates for other domains.")

        # Check for domain variations
        by_domain = {}
        for result in results:
            by_domain.setdefault(result.domain, []).append(result.get_overall_score())

        for domain, scores in by_domain.items():
            avg = statistics.mean(scores)
            if avg < 0.6:
                recommendations.append(f"Domain '{domain}' shows low performance ({avg:.2%}). Add more domain-specific examples and terminology.")

        # Check for consistency issues
        consistency_scores = [r.metrics.get("consistency", 1.0) for r in results if "consistency" in r.metrics]
        if consistency_scores and statistics.mean(consistency_scores) < 0.8:
            recommendations.append("Consistency scores are low. Review prompt instructions for clarity and add validation examples.")

        return recommendations


def create_evaluator(gold_standard_path: Optional[Path] = None) -> PromptEvaluator:
    """Factory function to create a prompt evaluator.

    Args:
        gold_standard_path: Path to gold standard data

    Returns:
        PromptEvaluator instance
    """
    return PromptEvaluator(gold_standard_path)
