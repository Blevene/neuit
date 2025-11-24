"""
Tests for prompt evaluation and benchmarking system.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
from prompts.evaluator import (
    PromptEvaluator,
    EvaluationResult,
    GoldStandardItem,
    MetricType,
    create_evaluator
)


class TestEvaluationResult:
    """Tests for EvaluationResult dataclass."""

    def test_evaluation_result_creation(self):
        """Test creating an evaluation result."""
        result = EvaluationResult(
            prompt_id="entity:education:1.0.0",
            domain="education",
            version="1.0.0",
            metrics={"precision": 0.85, "recall": 0.80, "f1_score": 0.82},
            extraction_count=10,
            sample_size=5
        )

        assert result.prompt_id == "entity:education:1.0.0"
        assert result.domain == "education"
        assert result.version == "1.0.0"
        assert result.metrics["precision"] == 0.85
        assert result.extraction_count == 10

    def test_overall_score_calculation(self):
        """Test calculating overall weighted score."""
        result = EvaluationResult(
            prompt_id="test",
            domain="general",
            version="1.0.0",
            metrics={
                "precision": 0.9,
                "recall": 0.8,
                "f1_score": 0.85,
                "accuracy": 0.87
            },
            extraction_count=10
        )

        score = result.get_overall_score()
        assert 0.8 <= score <= 0.9  # Should be weighted average

    def test_to_dict_conversion(self):
        """Test converting result to dictionary."""
        result = EvaluationResult(
            prompt_id="test",
            domain="medical",
            version="1.0.0",
            metrics={"precision": 0.85},
            extraction_count=5
        )

        result_dict = result.to_dict()

        assert result_dict["prompt_id"] == "test"
        assert result_dict["domain"] == "medical"
        assert "overall_score" in result_dict
        assert "evaluation_time" in result_dict


class TestGoldStandardItem:
    """Tests for GoldStandardItem dataclass."""

    def test_gold_standard_creation(self):
        """Test creating a gold standard item."""
        item = GoldStandardItem(
            id="test-1",
            text="Sample text for testing",
            expected_entities=[
                {"name": "Entity1", "category": "Concept"}
            ],
            domain="education"
        )

        assert item.id == "test-1"
        assert len(item.expected_entities) == 1
        assert item.domain == "education"
        assert item.difficulty == "medium"  # Default value


class TestPromptEvaluator:
    """Tests for PromptEvaluator class."""

    @pytest.fixture
    def evaluator(self, tmp_path):
        """Create evaluator with temporary gold standard."""
        gold_standard_file = tmp_path / "gold_standard.json"
        gold_standard_data = [
            {
                "id": "edu-1",
                "text": "Students must master algebra before calculus.",
                "expected_entities": [
                    {"name": "Algebra", "category": "Topic"},
                    {"name": "Calculus", "category": "Topic"}
                ],
                "domain": "education"
            }
        ]

        gold_standard_file.write_text(json.dumps(gold_standard_data))
        return PromptEvaluator(gold_standard_file)

    def test_evaluator_initialization(self, evaluator):
        """Test evaluator initialization."""
        assert isinstance(evaluator, PromptEvaluator)
        assert len(evaluator.gold_standard_data) == 1

    def test_load_gold_standard(self, evaluator):
        """Test loading gold standard data."""
        assert len(evaluator.gold_standard_data) == 1
        item = evaluator.gold_standard_data[0]
        assert item.id == "edu-1"
        assert item.domain == "education"

    def test_evaluate_entities_perfect_match(self, evaluator):
        """Test entity evaluation with perfect match."""
        extracted = [
            {"name": "Algebra", "category": "Topic"},
            {"name": "Calculus", "category": "Topic"}
        ]
        expected = [
            {"name": "Algebra", "category": "Topic"},
            {"name": "Calculus", "category": "Topic"}
        ]

        metrics = evaluator.evaluate_entities(extracted, expected)

        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1_score"] == 1.0

    def test_evaluate_entities_partial_match(self, evaluator):
        """Test entity evaluation with partial match."""
        extracted = [
            {"name": "Algebra", "category": "Topic"},
            {"name": "Geometry", "category": "Topic"}  # Not in expected
        ]
        expected = [
            {"name": "Algebra", "category": "Topic"},
            {"name": "Calculus", "category": "Topic"}  # Not in extracted
        ]

        metrics = evaluator.evaluate_entities(extracted, expected)

        assert metrics["precision"] == 0.5  # 1 correct out of 2 extracted
        assert metrics["recall"] == 0.5  # 1 correct out of 2 expected
        assert 0.4 < metrics["f1_score"] < 0.6

    def test_evaluate_relationships(self, evaluator):
        """Test relationship evaluation."""
        extracted = [
            {"subject": "Algebra", "predicate": "prerequisite_for", "object": "Calculus"}
        ]
        expected = [
            {"subject": "Algebra", "predicate": "prerequisite_for", "object": "Calculus"}
        ]

        metrics = evaluator.evaluate_relationships(extracted, expected)

        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["f1_score"] == 1.0

    def test_calculate_consistency(self, evaluator):
        """Test consistency calculation."""
        # Good extractions
        good_extractions = [
            {"name": "Entity1", "category": "Concept"},
            {"name": "Entity2", "category": "Concept"}
        ]

        consistency = evaluator.calculate_consistency(good_extractions)
        assert consistency == 1.0

        # Duplicate names
        bad_extractions = [
            {"name": "Entity1", "category": "Concept"},
            {"name": "Entity1", "category": "Concept"}  # Duplicate
        ]

        consistency = evaluator.calculate_consistency(bad_extractions)
        assert consistency < 1.0

    def test_compare_prompts(self, evaluator):
        """Test A/B comparison of prompts."""
        result_a = EvaluationResult(
            prompt_id="prompt_a",
            domain="education",
            version="1.0.0",
            metrics={"precision": 0.80, "recall": 0.75, "f1_score": 0.77},
            extraction_count=10
        )

        result_b = EvaluationResult(
            prompt_id="prompt_b",
            domain="education",
            version="2.0.0",
            metrics={"precision": 0.90, "recall": 0.85, "f1_score": 0.87},
            extraction_count=10
        )

        comparison = evaluator.compare_prompts(result_a, result_b)

        assert comparison["winner"] == "prompt_b"
        assert comparison["improvement"] > 0
        assert "metric_comparison" in comparison

    def test_generate_report(self, evaluator):
        """Test report generation."""
        results = [
            EvaluationResult(
                prompt_id="test1",
                domain="education",
                version="1.0.0",
                metrics={"precision": 0.85, "recall": 0.80, "f1_score": 0.82},
                extraction_count=10
            ),
            EvaluationResult(
                prompt_id="test2",
                domain="medical",
                version="1.0.0",
                metrics={"precision": 0.90, "recall": 0.85, "f1_score": 0.87},
                extraction_count=12
            )
        ]

        report = evaluator.generate_report(results)

        assert "summary" in report
        assert "aggregate_metrics" in report
        assert "best_prompts" in report
        assert report["summary"]["total_evaluations"] == 2
        assert "education" in report["aggregate_metrics"]
        assert "medical" in report["aggregate_metrics"]

    def test_recommendations_generation(self, evaluator):
        """Test recommendation generation."""
        # Low-performing results
        results = [
            EvaluationResult(
                prompt_id="test",
                domain="education",
                version="1.0.0",
                metrics={"precision": 0.50, "recall": 0.45, "f1_score": 0.47},
                extraction_count=5
            )
        ]

        recommendations = evaluator._generate_recommendations(results)
        assert len(recommendations) > 0
        assert any("low" in r.lower() for r in recommendations)


class TestFactoryFunctions:
    """Test factory functions."""

    def test_create_evaluator(self):
        """Test creating evaluator via factory function."""
        evaluator = create_evaluator()
        assert isinstance(evaluator, PromptEvaluator)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
