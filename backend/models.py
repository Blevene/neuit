"""
Pydantic models for NEUIToolkit data structures.

This module provides validated data models for all extraction types,
configuration, and metadata. Using Pydantic ensures runtime validation,
better IDE support, and clear API contracts.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator, field_validator
from enum import Enum
from datetime import datetime


# ============================================================================
# Extraction Data Models
# ============================================================================


class Entity(BaseModel):
    """Represents an extracted entity/concept.

    Attributes:
        name: The primary name of the entity
        category: Semantic category (e.g., 'Concept', 'Structure', 'Process')
        aliases: Alternative names or references
        confidence: Quality score from QA layer (0.0-1.0)
    """

    name: str = Field(..., min_length=1, description="Entity name")
    category: str = Field(..., min_length=1, description="Entity category")
    aliases: List[str] = Field(default_factory=list, description="Alternative names")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score")

    @field_validator('name', 'category')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace."""
        return v.strip()

    @field_validator('aliases')
    @classmethod
    def clean_aliases(cls, v: List[str]) -> List[str]:
        """Remove empty aliases and strip whitespace."""
        return [alias.strip() for alias in v if alias.strip()]

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Mitochondria",
                "category": "Organelle",
                "aliases": ["Powerhouse of the cell"],
                "confidence": 0.95
            }
        }


class Relationship(BaseModel):
    """Represents a semantic relationship between entities.

    Attributes:
        subject: The source entity
        predicate: The relationship type
        object: The target entity
        justification: Explanation from source text
        confidence: Quality score from QA layer (0.0-1.0)
    """

    subject: str = Field(..., min_length=1, description="Subject entity")
    predicate: str = Field(..., min_length=1, description="Relationship predicate")
    object: str = Field(..., min_length=1, description="Object entity", alias="object")
    justification: Optional[str] = Field(None, description="Text justification")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score")

    @field_validator('subject', 'predicate', 'object')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace."""
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "subject": "Neuron",
                "predicate": "uses",
                "object": "Neurotransmitter",
                "justification": "Neurons use neurotransmitters to communicate.",
                "confidence": 0.88
            }
        }
        populate_by_name = True


class Rule(BaseModel):
    """Represents a logical if-then rule.

    Attributes:
        id: Unique rule identifier
        if_clause: The conditional clause
        then_clause: The consequent clause
        confidence: Rule confidence (0.0-1.0)
        source_document: Document this rule was extracted from
    """

    id: int = Field(..., ge=0, description="Rule ID")
    if_clause: str = Field(..., min_length=1, description="If clause", alias="if")
    then_clause: str = Field(..., min_length=1, description="Then clause", alias="then")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Rule confidence")
    source_document: Optional[str] = Field(None, description="Source document name")

    @field_validator('if_clause', 'then_clause')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """Remove leading/trailing whitespace."""
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "if": "Student masters prerequisites",
                "then": "Student can advance to next topic",
                "confidence": 0.92,
                "source_document": "curriculum_guide.pdf"
            }
        }
        populate_by_name = True


class Ontology(BaseModel):
    """Represents an ontology in Turtle/RDF format.

    Attributes:
        content: The Turtle/RDF content
        format: Format type (default: 'turtle')
        namespaces: Dictionary of namespace prefixes
        triple_count: Estimated number of triples
    """

    content: str = Field(..., min_length=1, description="Ontology content")
    format: str = Field(default="turtle", description="Ontology format")
    namespaces: Dict[str, str] = Field(default_factory=dict, description="Namespace mappings")
    triple_count: Optional[int] = Field(None, ge=0, description="Number of triples")

    class Config:
        json_schema_extra = {
            "example": {
                "content": "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
                "format": "turtle",
                "namespaces": {
                    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
                    "rdfs": "http://www.w3.org/2000/01/rdf-schema#"
                }
            }
        }


# ============================================================================
# Quality Assurance Models
# ============================================================================


class QualityMetrics(BaseModel):
    """Quality assessment metrics for extractions.

    Attributes:
        total_count: Total number of items assessed
        passed_count: Number of items that passed QA
        failed_count: Number of items that failed QA
        quality_score: Aggregate quality score (0.0-1.0)
        details: Item-level details and scores
    """

    total_count: int = Field(..., ge=0, description="Total items")
    passed_count: int = Field(..., ge=0, description="Items passed")
    failed_count: int = Field(..., ge=0, description="Items failed")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed metrics")

    @field_validator('passed_count', 'failed_count')
    @classmethod
    def validate_counts(cls, v: int, info) -> int:
        """Ensure counts are valid."""
        if v < 0:
            raise ValueError("Count cannot be negative")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "total_count": 10,
                "passed_count": 8,
                "failed_count": 2,
                "quality_score": 0.85,
                "details": {"avg_confidence": 0.87}
            }
        }


class QualityReport(BaseModel):
    """Comprehensive quality report for all extraction types.

    Attributes:
        overall_quality_score: Aggregate quality across all types
        entity_quality: Entity quality metrics
        relationship_quality: Relationship quality metrics
        rule_quality: Rule quality metrics
        summary: Human-readable summary
        recommendations: List of recommendations
        timestamp: When report was generated
    """

    overall_quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall quality")
    entity_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Entity quality")
    relationship_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Relationship quality")
    rule_quality: Optional[float] = Field(None, ge=0.0, le=1.0, description="Rule quality")
    summary: str = Field(..., description="Summary text")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")
    timestamp: datetime = Field(default_factory=datetime.now, description="Report timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "overall_quality_score": 0.85,
                "entity_quality": 0.90,
                "relationship_quality": 0.82,
                "rule_quality": 0.83,
                "summary": "Good quality extractions with minor issues",
                "recommendations": ["Review low-confidence relationships"]
            }
        }


# ============================================================================
# Document Processing Models
# ============================================================================


class DocumentFormat(str, Enum):
    """Supported document formats."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    JSON = "json"
    UNKNOWN = "unknown"


class DocumentMetadata(BaseModel):
    """Metadata for a processed document.

    Attributes:
        filename: Document filename
        source_path: Full path to source document
        format: Document format
        num_entities: Number of extracted entities
        num_relationships: Number of extracted relationships
        num_rules: Number of extracted rules
        ontology_lines: Number of lines in ontology
        num_justifications: Number of justifications
        processing_time_seconds: Processing duration
        quality_score: Overall quality score
        timestamp: Processing timestamp
    """

    filename: str = Field(..., min_length=1, description="Document filename")
    source_path: str = Field(..., description="Source file path")
    format: DocumentFormat = Field(default=DocumentFormat.UNKNOWN, description="Document format")
    num_entities: int = Field(default=0, ge=0, description="Entity count")
    num_relationships: int = Field(default=0, ge=0, description="Relationship count")
    num_rules: int = Field(default=0, ge=0, description="Rule count")
    ontology_lines: int = Field(default=0, ge=0, description="Ontology line count")
    num_justifications: int = Field(default=0, ge=0, description="Justification count")
    processing_time_seconds: Optional[float] = Field(None, ge=0.0, description="Processing time")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score")
    timestamp: datetime = Field(default_factory=datetime.now, description="Processing timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "filename": "biology_chapter.pdf",
                "source_path": "/data/biology_chapter.pdf",
                "format": "pdf",
                "num_entities": 25,
                "num_relationships": 18,
                "num_rules": 5,
                "ontology_lines": 42,
                "processing_time_seconds": 27.3,
                "quality_score": 0.87
            }
        }


# ============================================================================
# Extraction Results Models
# ============================================================================


class ExtractionResults(BaseModel):
    """Complete extraction results for a document.

    Attributes:
        entities: List of extracted entities
        relationships: List of extracted relationships
        rules: List of extracted rules
        ontology: Extracted ontology (if any)
        metadata: Document metadata
        quality_metrics: Quality assessment metrics
    """

    entities: List[Entity] = Field(default_factory=list, description="Extracted entities")
    relationships: List[Relationship] = Field(default_factory=list, description="Extracted relationships")
    rules: List[Rule] = Field(default_factory=list, description="Extracted rules")
    ontology: Optional[Ontology] = Field(None, description="Extracted ontology")
    metadata: DocumentMetadata = Field(..., description="Document metadata")
    quality_metrics: Optional[QualityMetrics] = Field(None, description="Quality metrics")

    def entity_count(self) -> int:
        """Get entity count."""
        return len(self.entities)

    def relationship_count(self) -> int:
        """Get relationship count."""
        return len(self.relationships)

    def rule_count(self) -> int:
        """Get rule count."""
        return len(self.rules)

    class Config:
        json_schema_extra = {
            "example": {
                "entities": [],
                "relationships": [],
                "rules": [],
                "metadata": {
                    "filename": "test.pdf",
                    "source_path": "/data/test.pdf"
                }
            }
        }


# ============================================================================
# LLM Provider Models
# ============================================================================


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    AZURE = "azure"


class ProviderStats(BaseModel):
    """Statistics for LLM provider usage.

    Attributes:
        primary_provider: Primary provider name
        total_calls: Total number of API calls
        successful_calls: Number of successful calls
        failures: Number of failed calls
        total_cost: Total cost in USD
        providers_used: List of providers used
        fallback_count: Number of times fallback was triggered
    """

    primary_provider: str = Field(..., description="Primary provider")
    total_calls: int = Field(default=0, ge=0, description="Total calls")
    successful_calls: int = Field(default=0, ge=0, description="Successful calls")
    failures: int = Field(default=0, ge=0, description="Failed calls")
    total_cost: float = Field(default=0.0, ge=0.0, description="Total cost USD")
    providers_used: List[str] = Field(default_factory=list, description="Providers used")
    fallback_count: int = Field(default=0, ge=0, description="Fallback activations")

    class Config:
        json_schema_extra = {
            "example": {
                "primary_provider": "openai",
                "total_calls": 100,
                "successful_calls": 98,
                "failures": 2,
                "total_cost": 1.45,
                "providers_used": ["openai", "anthropic"],
                "fallback_count": 2
            }
        }


# ============================================================================
# Neo4j Models
# ============================================================================


class Neo4jImportStats(BaseModel):
    """Statistics from Neo4j import operation.

    Attributes:
        entities_created: Number of entities created
        relationships_created: Number of relationships created
        rules_created: Number of rules created
        documents_created: Number of document nodes created
        import_time_seconds: Import duration
        errors: List of errors encountered
    """

    entities_created: int = Field(default=0, ge=0, description="Entities created")
    relationships_created: int = Field(default=0, ge=0, description="Relationships created")
    rules_created: int = Field(default=0, ge=0, description="Rules created")
    documents_created: int = Field(default=0, ge=0, description="Documents created")
    import_time_seconds: Optional[float] = Field(None, ge=0.0, description="Import time")
    errors: List[str] = Field(default_factory=list, description="Errors encountered")

    class Config:
        json_schema_extra = {
            "example": {
                "entities_created": 25,
                "relationships_created": 18,
                "rules_created": 5,
                "documents_created": 1,
                "import_time_seconds": 2.3,
                "errors": []
            }
        }


# ============================================================================
# Utility Functions
# ============================================================================


def validate_entity_dict(data: Dict[str, Any]) -> Entity:
    """Validate and convert dictionary to Entity model.

    Args:
        data: Dictionary with entity data

    Returns:
        Validated Entity instance

    Raises:
        ValidationError: If data is invalid
    """
    return Entity(**data)


def validate_relationship_dict(data: Dict[str, Any]) -> Relationship:
    """Validate and convert dictionary to Relationship model.

    Args:
        data: Dictionary with relationship data

    Returns:
        Validated Relationship instance

    Raises:
        ValidationError: If data is invalid
    """
    return Relationship(**data)


def validate_rule_dict(data: Dict[str, Any]) -> Rule:
    """Validate and convert dictionary to Rule model.

    Args:
        data: Dictionary with rule data

    Returns:
        Validated Rule instance

    Raises:
        ValidationError: If data is invalid
    """
    return Rule(**data)


def entities_to_dicts(entities: List[Entity]) -> List[Dict[str, Any]]:
    """Convert Entity models to dictionaries.

    Args:
        entities: List of Entity instances

    Returns:
        List of dictionaries
    """
    return [entity.model_dump(exclude_none=True) for entity in entities]


def relationships_to_dicts(relationships: List[Relationship]) -> List[Dict[str, Any]]:
    """Convert Relationship models to dictionaries.

    Args:
        relationships: List of Relationship instances

    Returns:
        List of dictionaries
    """
    return [rel.model_dump(exclude_none=True, by_alias=True) for rel in relationships]


def rules_to_dicts(rules: List[Rule]) -> List[Dict[str, Any]]:
    """Convert Rule models to dictionaries.

    Args:
        rules: List of Rule instances

    Returns:
        List of dictionaries
    """
    return [rule.model_dump(exclude_none=True, by_alias=True) for rule in rules]
