"""
Unit tests for Quality Assurance Layer
"""

import pytest
from backend.quality_assurance import QualityAssurance, QualityMetrics


class TestQualityMetrics:
    """Tests for QualityMetrics dataclass"""

    def test_quality_metrics_creation(self):
        """Test creating quality metrics"""
        metrics = QualityMetrics(
            confidence_score=0.85,
            duplicate_count=0,
            consistency_score=0.90,
            issues=[],
            warnings=[]
        )

        assert metrics.confidence_score == 0.85
        assert metrics.duplicate_count == 0
        assert metrics.consistency_score == 0.90
        assert len(metrics.issues) == 0
        assert len(metrics.warnings) == 0


class TestQualityAssuranceEntityAssessment:
    """Tests for entity assessment"""

    def test_assess_valid_entity(self, sample_entities):
        """Test assessing a valid entity"""
        qa = QualityAssurance(min_confidence=0.5)
        entity = sample_entities[0]

        metrics = qa.assess_entity(entity)

        assert metrics.confidence_score >= 0.8
        assert len(metrics.issues) == 0

    def test_assess_entity_missing_name(self):
        """Test assessing entity with missing name"""
        qa = QualityAssurance()
        entity = {"aliases": [], "category": "Test"}

        metrics = qa.assess_entity(entity)

        assert metrics.confidence_score == 0.0
        assert any("missing" in issue.lower() for issue in metrics.issues)

    def test_assess_entity_short_name(self):
        """Test assessing entity with too short name"""
        qa = QualityAssurance()
        entity = {"name": "A", "aliases": [], "category": "Test"}

        metrics = qa.assess_entity(entity)

        assert metrics.confidence_score < 1.0
        assert any("too short" in issue.lower() for issue in metrics.issues)

    def test_assess_entity_all_caps(self):
        """Test assessing entity with all caps name"""
        qa = QualityAssurance()
        entity = {"name": "MITOCHONDRIA", "aliases": [], "category": "Test"}

        metrics = qa.assess_entity(entity)

        assert metrics.confidence_score < 1.0
        assert any("all caps" in warning.lower() for warning in metrics.warnings)

    def test_assess_entity_invalid_characters(self):
        """Test assessing entity with invalid characters"""
        qa = QualityAssurance()
        entity = {"name": "Test<Entity>", "aliases": [], "category": "Test"}

        metrics = qa.assess_entity(entity)

        assert metrics.confidence_score < 1.0
        assert any("invalid characters" in issue.lower() for issue in metrics.issues)

    def test_assess_entity_duplicate_detection(self, sample_entities):
        """Test duplicate entity detection"""
        qa = QualityAssurance()

        # Assess first entity
        metrics1 = qa.assess_entity(sample_entities[0])
        assert metrics1.duplicate_count == 0

        # Assess same entity again
        metrics2 = qa.assess_entity(sample_entities[0])
        assert any("duplicate" in warning.lower() for warning in metrics2.warnings)

    def test_assess_entity_category_consistency(self):
        """Test category consistency checking"""
        qa = QualityAssurance()

        entity1 = {"name": "Test", "aliases": [], "category": "Type1"}
        entity2 = {"name": "Test", "aliases": [], "category": "Type2"}

        qa.assess_entity(entity1)
        metrics2 = qa.assess_entity(entity2)

        assert any("multiple categories" in warning.lower() for warning in metrics2.warnings)

    def test_assess_entity_no_category(self):
        """Test entity without category"""
        qa = QualityAssurance()
        entity = {"name": "Test", "aliases": []}

        metrics = qa.assess_entity(entity)

        assert any("missing category" in warning.lower() for warning in metrics.warnings)


class TestQualityAssuranceRelationshipAssessment:
    """Tests for relationship assessment"""

    def test_assess_valid_relationship(self, sample_relationships):
        """Test assessing a valid relationship"""
        qa = QualityAssurance()
        # First add entities to seen set
        qa.seen_entities.add("mitochondria")
        qa.seen_entities.add("atp")

        relationship = sample_relationships[0]
        metrics = qa.assess_relationship(relationship)

        assert metrics.confidence_score >= 0.7
        assert len(metrics.issues) == 0

    def test_assess_relationship_missing_fields(self):
        """Test assessing relationship with missing fields"""
        qa = QualityAssurance()
        relationship = {"subject": "A", "predicate": ""}

        metrics = qa.assess_relationship(relationship)

        assert metrics.confidence_score == 0.0
        assert len(metrics.issues) > 0

    def test_assess_relationship_self_referential(self):
        """Test assessing self-referential relationship"""
        qa = QualityAssurance()
        qa.seen_entities.add("test")

        relationship = {
            "subject": "Test",
            "predicate": "is",
            "object": "Test",
            "justification": "Self referential"
        }

        metrics = qa.assess_relationship(relationship)

        assert metrics.confidence_score < 1.0
        assert any("self-referential" in warning.lower() for warning in metrics.warnings)

    def test_assess_relationship_vague_predicate(self):
        """Test assessing relationship with vague predicate"""
        qa = QualityAssurance()
        qa.seen_entities.add("entity1")
        qa.seen_entities.add("entity2")

        relationship = {
            "subject": "Entity1",
            "predicate": "relates to",
            "object": "Entity2",
            "justification": "They are related somehow"
        }

        metrics = qa.assess_relationship(relationship)

        assert metrics.confidence_score < 1.0
        assert any("vague" in warning.lower() for warning in metrics.warnings)

    def test_assess_relationship_unknown_entities(self):
        """Test assessing relationship with unknown entities"""
        qa = QualityAssurance()

        relationship = {
            "subject": "Unknown1",
            "predicate": "connects",
            "object": "Unknown2",
            "justification": "Connection exists"
        }

        metrics = qa.assess_relationship(relationship)

        assert metrics.confidence_score < 1.0
        assert len(metrics.warnings) >= 2  # Both subject and object unknown

    def test_assess_relationship_duplicate_detection(self, sample_relationships):
        """Test duplicate relationship detection"""
        qa = QualityAssurance()
        qa.seen_entities.add("mitochondria")
        qa.seen_entities.add("atp")

        # Assess first relationship
        metrics1 = qa.assess_relationship(sample_relationships[0])
        assert metrics1.duplicate_count == 0

        # Assess same relationship again
        metrics2 = qa.assess_relationship(sample_relationships[0])
        assert metrics2.duplicate_count == 1

    def test_assess_relationship_no_justification(self):
        """Test relationship without justification"""
        qa = QualityAssurance()
        qa.seen_entities.add("a")
        qa.seen_entities.add("b")

        relationship = {
            "subject": "A",
            "predicate": "connects",
            "object": "B"
        }

        metrics = qa.assess_relationship(relationship)

        assert metrics.confidence_score < 1.0
        assert any("missing justification" in warning.lower() for warning in metrics.warnings)


class TestQualityAssuranceRuleAssessment:
    """Tests for rule assessment"""

    def test_assess_valid_rule(self, sample_rules):
        """Test assessing a valid rule"""
        qa = QualityAssurance()
        rule = sample_rules[0]

        metrics = qa.assess_rule(rule)

        assert metrics.confidence_score >= 0.9
        assert len(metrics.issues) == 0

    def test_assess_rule_missing_clauses(self):
        """Test assessing rule with missing clauses"""
        qa = QualityAssurance()
        rule = {"if": "", "then": "result"}

        metrics = qa.assess_rule(rule)

        assert metrics.confidence_score == 0.0
        assert any("missing" in issue.lower() for issue in metrics.issues)

    def test_assess_rule_short_clauses(self):
        """Test assessing rule with too short clauses"""
        qa = QualityAssurance()
        rule = {"if": "a", "then": "b"}

        metrics = qa.assess_rule(rule)

        assert metrics.confidence_score < 1.0
        assert len(metrics.issues) >= 2

    def test_assess_rule_circular_logic(self):
        """Test assessing rule with circular logic"""
        qa = QualityAssurance()
        rule = {"if": "condition", "then": "condition"}

        metrics = qa.assess_rule(rule)

        assert metrics.confidence_score < 0.5
        assert any("circular" in issue.lower() for issue in metrics.issues)

    def test_assess_rule_with_confidence(self):
        """Test assessing rule with confidence value"""
        qa = QualityAssurance()
        rule = {
            "if": "condition exists",
            "then": "result occurs",
            "confidence": 0.8
        }

        metrics = qa.assess_rule(rule)

        # Confidence should be factored in
        assert metrics.confidence_score <= 0.8

    def test_assess_rule_invalid_confidence(self):
        """Test assessing rule with invalid confidence"""
        qa = QualityAssurance()
        rule = {
            "if": "condition exists",
            "then": "result occurs",
            "confidence": 1.5  # Out of range
        }

        metrics = qa.assess_rule(rule)

        assert metrics.confidence_score < 1.0
        assert any("out of range" in issue.lower() for issue in metrics.issues)


class TestQualityAssuranceFiltering:
    """Tests for quality filtering"""

    def test_filter_entities(self, sample_entities):
        """Test filtering entities by quality"""
        qa = QualityAssurance(min_confidence=0.7)

        filtered, metrics = qa.filter_low_quality(sample_entities, 'entity')

        assert len(filtered) <= len(sample_entities)
        assert len(metrics) == len(sample_entities)

    def test_filter_low_quality_entities(self, low_quality_entities):
        """Test filtering out low-quality entities"""
        qa = QualityAssurance(min_confidence=0.7, enable_strict_mode=True)

        filtered, metrics = qa.filter_low_quality(low_quality_entities, 'entity')

        # Should filter out most low quality entities
        assert len(filtered) < len(low_quality_entities)

    def test_filter_relationships(self, sample_relationships):
        """Test filtering relationships by quality"""
        qa = QualityAssurance(min_confidence=0.5)
        # Add entities first
        qa.seen_entities.update(['mitochondria', 'atp', 'cell membrane', 'cell'])

        filtered, metrics = qa.filter_low_quality(sample_relationships, 'relationship')

        assert len(filtered) <= len(sample_relationships)
        assert len(metrics) == len(sample_relationships)

    def test_filter_rules(self, sample_rules):
        """Test filtering rules by quality"""
        qa = QualityAssurance(min_confidence=0.7)

        filtered, metrics = qa.filter_low_quality(sample_rules, 'rule')

        assert len(filtered) <= len(sample_rules)
        assert len(metrics) == len(sample_rules)

    def test_strict_mode_filtering(self, low_quality_entities):
        """Test strict mode filtering"""
        qa_strict = QualityAssurance(min_confidence=0.7, enable_strict_mode=True)
        qa_lenient = QualityAssurance(min_confidence=0.7, enable_strict_mode=False)

        strict_filtered, _ = qa_strict.filter_low_quality(low_quality_entities, 'entity')
        lenient_filtered, _ = qa_lenient.filter_low_quality(low_quality_entities, 'entity')

        # Lenient mode keeps low quality items, strict mode removes them
        assert len(strict_filtered) <= len(lenient_filtered)


class TestQualityAssuranceReporting:
    """Tests for quality reporting"""

    def test_generate_quality_report(self, sample_entities, sample_relationships, sample_rules):
        """Test generating comprehensive quality report"""
        qa = QualityAssurance()
        qa.seen_entities.update(['mitochondria', 'atp', 'cell membrane', 'cell'])

        # Get metrics
        _, entity_metrics = qa.filter_low_quality(sample_entities, 'entity')
        _, rel_metrics = qa.filter_low_quality(sample_relationships, 'relationship')
        _, rule_metrics = qa.filter_low_quality(sample_rules, 'rule')

        # Generate report
        report = qa.generate_quality_report(entity_metrics, rel_metrics, rule_metrics)

        assert 'entities' in report
        assert 'relationships' in report
        assert 'rules' in report
        assert 'overall_quality_score' in report
        assert 'threshold' in report

        assert report['entities']['count'] == len(sample_entities)
        assert report['relationships']['count'] == len(sample_relationships)
        assert report['rules']['count'] == len(sample_rules)

    def test_empty_quality_report(self):
        """Test generating report with no data"""
        qa = QualityAssurance()

        report = qa.generate_quality_report([], [], [])

        assert report['overall_quality_score'] == 0.0
        assert report['entities'] == {}

    def test_quality_report_metrics(self, sample_entities):
        """Test quality report contains correct metrics"""
        qa = QualityAssurance()

        _, entity_metrics = qa.filter_low_quality(sample_entities, 'entity')
        report = qa.generate_quality_report(entity_metrics, [], [])

        assert 'avg_confidence' in report['entities']
        assert 'avg_consistency' in report['entities']
        assert 'total_issues' in report['entities']
        assert 'total_warnings' in report['entities']


class TestQualityAssuranceReset:
    """Tests for QA reset functionality"""

    def test_reset_clears_state(self, sample_entities):
        """Test that reset clears internal state"""
        qa = QualityAssurance()

        # Process some entities
        qa.filter_low_quality(sample_entities, 'entity')

        assert len(qa.seen_entities) > 0
        assert len(qa.entity_categories) > 0

        # Reset
        qa.reset()

        assert len(qa.seen_entities) == 0
        assert len(qa.entity_categories) == 0
        assert len(qa.seen_relationships) == 0


class TestQualityAssuranceConfiguration:
    """Tests for QA configuration"""

    def test_custom_confidence_threshold(self):
        """Test setting custom confidence threshold"""
        qa = QualityAssurance(min_confidence=0.8)
        assert qa.min_confidence == 0.8

    def test_strict_mode_enabled(self):
        """Test strict mode configuration"""
        qa = QualityAssurance(enable_strict_mode=True)
        assert qa.enable_strict_mode is True

    def test_default_configuration(self):
        """Test default QA configuration"""
        qa = QualityAssurance()
        assert qa.min_confidence == 0.5
        assert qa.enable_strict_mode is False
