"""
Quality Assurance Layer for Knowledge Extraction
Provides confidence scoring, duplicate detection, and consistency checking
"""

import logging
from typing import List, Dict, Any, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict
import re

logger = logging.getLogger(__name__)


@dataclass
class QualityMetrics:
    """Quality metrics for extracted knowledge"""
    confidence_score: float  # 0.0 to 1.0
    duplicate_count: int
    consistency_score: float  # 0.0 to 1.0
    issues: List[str]
    warnings: List[str]


class QualityAssurance:
    """Quality assurance for knowledge extraction results"""

    def __init__(self, min_confidence: float = 0.5, enable_strict_mode: bool = False):
        """
        Initialize QA layer

        Args:
            min_confidence: Minimum confidence threshold for acceptance
            enable_strict_mode: If True, reject low-quality extractions
        """
        self.min_confidence = min_confidence
        self.enable_strict_mode = enable_strict_mode
        self.seen_entities: Set[str] = set()
        self.seen_relationships: Set[Tuple[str, str, str]] = set()
        self.entity_categories: Dict[str, Set[str]] = defaultdict(set)

    def assess_entity(self, entity: Dict[str, Any]) -> QualityMetrics:
        """
        Assess quality of an extracted entity

        Args:
            entity: Entity dictionary with 'name', 'aliases', 'category'

        Returns:
            QualityMetrics object
        """
        issues = []
        warnings = []
        confidence = 1.0

        # Required field validation
        # Track duplicate status before adding to seen set
        duplicate_count = 0

        if not entity.get("name"):
            issues.append("Entity missing required 'name' field")
            confidence *= 0.0
        else:
            name = entity["name"].strip()

            # Check for duplicates
            if name.lower() in self.seen_entities:
                duplicate_count = 1
                warnings.append(f"Duplicate entity: {name}")
            else:
                self.seen_entities.add(name.lower())

            # Validate name quality
            if len(name) < 2:
                issues.append(f"Entity name too short: {name}")
                confidence *= 0.5

            if name.isupper() and len(name) > 5:
                warnings.append(f"Entity name is all caps: {name}")
                confidence *= 0.9

            # Check for suspicious patterns
            if any(char in name for char in ['[', ']', '{', '}', '<', '>']):
                issues.append(f"Entity name contains invalid characters: {name}")
                confidence *= 0.6

        # Category validation
        category = entity.get("category", "").strip()
        if category:
            # Track category consistency
            entity_name_lower = entity.get("name", "").lower()
            if entity_name_lower in self.entity_categories:
                existing_categories = self.entity_categories[entity_name_lower]
                if category not in existing_categories:
                    warnings.append(f"Entity '{entity.get('name')}' has multiple categories: {existing_categories} vs {category}")
                    confidence *= 0.8
            self.entity_categories[entity_name_lower].add(category)
        else:
            warnings.append("Entity missing category")
            confidence *= 0.9

        # Aliases validation
        aliases = entity.get("aliases", [])
        if isinstance(aliases, list):
            if len(aliases) == 0:
                warnings.append("Entity has no aliases (may be okay)")
            elif len(aliases) > 10:
                warnings.append(f"Entity has unusually many aliases: {len(aliases)}")
                confidence *= 0.9
        else:
            issues.append("Aliases field must be a list")
            confidence *= 0.7

        # Calculate consistency score
        consistency_score = 1.0 - (len(warnings) * 0.1)
        consistency_score = max(0.0, min(1.0, consistency_score))

        return QualityMetrics(
            confidence_score=max(0.0, min(1.0, confidence)),
            duplicate_count=duplicate_count,
            consistency_score=consistency_score,
            issues=issues,
            warnings=warnings
        )

    def assess_relationship(self, relationship: Dict[str, Any]) -> QualityMetrics:
        """
        Assess quality of an extracted relationship

        Args:
            relationship: Relationship dictionary with 'subject', 'predicate', 'object'

        Returns:
            QualityMetrics object
        """
        issues = []
        warnings = []
        confidence = 1.0
        duplicate_count = 0  # Initialize duplicate_count early

        # Required field validation
        subject = relationship.get("subject", "").strip()
        predicate = relationship.get("predicate", "").strip()
        obj = relationship.get("object", "").strip()

        if not subject:
            issues.append("Relationship missing 'subject'")
            confidence *= 0.0
        if not predicate:
            issues.append("Relationship missing 'predicate'")
            confidence *= 0.0
        if not obj:
            issues.append("Relationship missing 'object'")
            confidence *= 0.0

        if subject and predicate and obj:
            # Create relationship tuple for duplicate detection
            rel_tuple = (subject.lower(), predicate.lower(), obj.lower())

            # Check for duplicates
            if rel_tuple in self.seen_relationships:
                duplicate_count = 1
                warnings.append(f"Duplicate relationship: {subject} -> {predicate} -> {obj}")
            else:
                self.seen_relationships.add(rel_tuple)

            # Check for self-relationships
            if subject.lower() == obj.lower():
                warnings.append(f"Self-referential relationship: {subject} -> {predicate} -> {obj}")
                confidence *= 0.8

            # Validate predicate quality
            if len(predicate) < 2:
                issues.append(f"Predicate too short: {predicate}")
                confidence *= 0.5

            # Check for vague predicates
            vague_predicates = {'relates to', 'associated with', 'connected to', 'linked to'}
            if predicate.lower() in vague_predicates:
                warnings.append(f"Vague predicate: {predicate}")
                confidence *= 0.85

            # Check for unknown entities (not in seen_entities)
            if subject.lower() not in self.seen_entities:
                warnings.append(f"Subject not in entity list: {subject}")
                confidence *= 0.9

            if obj.lower() not in self.seen_entities:
                warnings.append(f"Object not in entity list: {obj}")
                confidence *= 0.9

        # Justification validation
        justification = relationship.get("justification", "").strip()
        if not justification:
            warnings.append("Relationship missing justification")
            confidence *= 0.85
        elif len(justification) < 10:
            warnings.append("Justification too short")
            confidence *= 0.9

        # Calculate consistency score
        consistency_score = 1.0 - (len(warnings) * 0.1)
        consistency_score = max(0.0, min(1.0, consistency_score))

        return QualityMetrics(
            confidence_score=max(0.0, min(1.0, confidence)),
            duplicate_count=duplicate_count,
            consistency_score=consistency_score,
            issues=issues,
            warnings=warnings
        )

    def assess_rule(self, rule: Dict[str, Any]) -> QualityMetrics:
        """
        Assess quality of an extracted rule

        Args:
            rule: Rule dictionary with 'if', 'then', 'confidence'

        Returns:
            QualityMetrics object
        """
        issues = []
        warnings = []
        confidence = 1.0

        # Required field validation
        if_clause = rule.get("if", "").strip()
        then_clause = rule.get("then", "").strip()

        if not if_clause:
            issues.append("Rule missing 'if' clause")
            confidence *= 0.0
        elif len(if_clause) < 5:
            issues.append("'if' clause too short")
            confidence *= 0.6

        if not then_clause:
            issues.append("Rule missing 'then' clause")
            confidence *= 0.0
        elif len(then_clause) < 5:
            issues.append("'then' clause too short")
            confidence *= 0.6

        # Check for rule confidence if provided
        rule_confidence = rule.get("confidence")
        if rule_confidence is not None:
            try:
                conf_val = float(rule_confidence)
                if conf_val < 0.0 or conf_val > 1.0:
                    issues.append(f"Rule confidence out of range: {conf_val}")
                    confidence *= 0.7
                else:
                    # Use the rule's own confidence as a factor
                    confidence *= conf_val
            except (ValueError, TypeError):
                warnings.append(f"Invalid confidence value: {rule_confidence}")
                confidence *= 0.9

        # Check for circular logic
        if if_clause.lower() == then_clause.lower():
            issues.append("Circular rule: if and then clauses are identical")
            confidence *= 0.3

        # Calculate consistency score
        consistency_score = 1.0 - (len(warnings) * 0.1)
        consistency_score = max(0.0, min(1.0, consistency_score))

        return QualityMetrics(
            confidence_score=max(0.0, min(1.0, confidence)),
            duplicate_count=0,
            consistency_score=consistency_score,
            issues=issues,
            warnings=warnings
        )

    def filter_low_quality(
        self,
        items: List[Dict[str, Any]],
        item_type: str
    ) -> Tuple[List[Dict[str, Any]], List[QualityMetrics]]:
        """
        Filter out low-quality items based on confidence threshold

        Args:
            items: List of extracted items (entities, relationships, or rules)
            item_type: Type of item ('entity', 'relationship', 'rule')

        Returns:
            Tuple of (filtered_items, quality_metrics)
        """
        assess_func = {
            'entity': self.assess_entity,
            'relationship': self.assess_relationship,
            'rule': self.assess_rule
        }.get(item_type)

        if not assess_func:
            logger.warning(f"Unknown item type: {item_type}")
            return items, []

        filtered_items = []
        all_metrics = []

        for item in items:
            metrics = assess_func(item)
            all_metrics.append(metrics)

            # Log issues and warnings
            if metrics.issues:
                logger.warning(f"Quality issues in {item_type}: {metrics.issues}")

            # Filter based on confidence
            if metrics.confidence_score >= self.min_confidence:
                filtered_items.append(item)
            elif self.enable_strict_mode:
                logger.info(f"Filtered out low-quality {item_type} (confidence: {metrics.confidence_score:.2f})")

        logger.info(
            f"Quality filtering: {len(filtered_items)}/{len(items)} {item_type}s passed "
            f"(threshold: {self.min_confidence:.2f})"
        )

        return filtered_items, all_metrics

    def generate_quality_report(
        self,
        entities_metrics: List[QualityMetrics],
        relationships_metrics: List[QualityMetrics],
        rules_metrics: List[QualityMetrics]
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report

        Args:
            entities_metrics: Metrics for all entities
            relationships_metrics: Metrics for all relationships
            rules_metrics: Metrics for all rules

        Returns:
            Quality report dictionary
        """
        def aggregate_metrics(metrics_list: List[QualityMetrics]) -> Dict[str, Any]:
            if not metrics_list:
                return {}

            avg_confidence = sum(m.confidence_score for m in metrics_list) / len(metrics_list)
            avg_consistency = sum(m.consistency_score for m in metrics_list) / len(metrics_list)
            total_issues = sum(len(m.issues) for m in metrics_list)
            total_warnings = sum(len(m.warnings) for m in metrics_list)
            total_duplicates = sum(m.duplicate_count for m in metrics_list)

            return {
                "count": len(metrics_list),
                "avg_confidence": round(avg_confidence, 3),
                "avg_consistency": round(avg_consistency, 3),
                "total_issues": total_issues,
                "total_warnings": total_warnings,
                "total_duplicates": total_duplicates
            }

        report = {
            "entities": aggregate_metrics(entities_metrics),
            "relationships": aggregate_metrics(relationships_metrics),
            "rules": aggregate_metrics(rules_metrics),
            "threshold": self.min_confidence,
            "strict_mode": self.enable_strict_mode
        }

        # Calculate overall quality score
        all_confidences = [m.confidence_score for m in entities_metrics + relationships_metrics + rules_metrics]
        if all_confidences:
            report["overall_quality_score"] = round(sum(all_confidences) / len(all_confidences), 3)
        else:
            report["overall_quality_score"] = 0.0

        return report

    def reset(self):
        """Reset internal state for processing a new document"""
        self.seen_entities.clear()
        self.seen_relationships.clear()
        self.entity_categories.clear()
