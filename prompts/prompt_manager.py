"""
Centralized prompt management system for NEUIToolkit.

This module provides a flexible, version-controlled prompt management system
that supports template variables, domain-specific prompts, and dependency injection.
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class PromptType(str, Enum):
    """Types of extraction prompts."""
    ENTITY = "entity"
    RELATIONSHIP = "relationship"
    RULE = "rule"
    ONTOLOGY = "ontology"
    JUSTIFICATION = "justification"


class Domain(str, Enum):
    """Domain-specific prompt sets."""
    GENERAL = "general"
    EDUCATION = "education"
    MEDICAL = "medical"
    LEGAL = "legal"
    SCIENTIFIC = "scientific"
    BUSINESS = "business"


@dataclass
class PromptMetadata:
    """Metadata for a prompt template.

    Attributes:
        version: Semantic version (e.g., "1.0.0")
        author: Creator of the prompt
        created_at: Creation timestamp
        updated_at: Last update timestamp
        description: Purpose and usage notes
        required_vars: Required template variables
        optional_vars: Optional template variables
        domain: Target domain for this prompt
    """
    version: str
    author: str = "NEUIToolkit"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    description: str = ""
    required_vars: Set[str] = field(default_factory=set)
    optional_vars: Set[str] = field(default_factory=set)
    domain: Domain = Domain.GENERAL

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "version": self.version,
            "author": self.author,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "description": self.description,
            "required_vars": list(self.required_vars),
            "optional_vars": list(self.optional_vars),
            "domain": self.domain.value
        }


class PromptTemplate:
    """A prompt template with variable substitution.

    Supports both {variable} and {{variable}} style placeholders.
    Validates required variables and provides helpful error messages.
    """

    def __init__(
        self,
        template: str,
        metadata: Optional[PromptMetadata] = None,
        prompt_type: Optional[PromptType] = None
    ):
        """Initialize prompt template.

        Args:
            template: The prompt template string with placeholders
            metadata: Optional metadata about the prompt
            prompt_type: Type of prompt (entity, relationship, etc.)
        """
        self.template = template
        self.metadata = metadata or PromptMetadata(version="1.0.0")
        self.prompt_type = prompt_type

        # Extract variables from template
        self._extract_variables()

    def _extract_variables(self) -> None:
        """Extract variable names from template."""
        # Find all {variable} and {{variable}} patterns
        # Only match valid variable names (alphanumeric + underscores)
        single_brace = set(re.findall(r'\{([a-zA-Z_][a-zA-Z0-9_]*)\}', self.template))
        double_brace = set(re.findall(r'\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}', self.template))

        self.variables = single_brace | double_brace

        # Update metadata if variables found
        if not self.metadata.required_vars and self.variables:
            self.metadata.required_vars = self.variables

    def render(self, **kwargs) -> str:
        """Render template with provided variables.

        Args:
            **kwargs: Variable values to substitute

        Returns:
            Rendered prompt string

        Raises:
            ValueError: If required variables are missing
        """
        # Check for missing required variables
        missing = self.metadata.required_vars - set(kwargs.keys())
        if missing:
            raise ValueError(
                f"Missing required variables: {missing}. "
                f"Required: {self.metadata.required_vars}, "
                f"Provided: {set(kwargs.keys())}"
            )

        # Add default values for optional variables
        render_vars = kwargs.copy()
        for var in self.metadata.optional_vars:
            if var not in render_vars:
                render_vars[var] = ""

        # Render template
        try:
            # Handle both {var} and {{var}} styles
            result = self.template
            for key, value in render_vars.items():
                # Replace {key} and {{key}}
                result = result.replace(f"{{{key}}}", str(value))
                result = result.replace(f"{{{{{key}}}}}", str(value))

            return result
        except Exception as e:
            raise ValueError(f"Error rendering template: {e}")

    def validate(self) -> List[str]:
        """Validate template for common issues.

        Returns:
            List of validation warnings (empty if valid)
        """
        warnings = []

        # Check for empty template
        if not self.template.strip():
            warnings.append("Template is empty")

        # Check for unclosed braces
        if self.template.count("{") != self.template.count("}"):
            warnings.append("Mismatched braces in template")

        # Check for very short templates
        if len(self.template) < 50:
            warnings.append("Template seems very short (< 50 chars)")

        # Check for suspicious patterns
        if "{{" in self.template and "{" in self.template.replace("{{", ""):
            warnings.append("Mixed brace styles ({} and {{}}) - use consistently")

        return warnings


class PromptRegistry:
    """Registry for managing multiple prompt versions and domains.

    Supports:
    - Multiple versions of each prompt type
    - Domain-specific prompts (education, medical, etc.)
    - A/B testing with multiple prompt variants
    - Fallback to default prompts
    """

    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize prompt registry.

        Args:
            base_dir: Base directory for prompt files
        """
        self.base_dir = base_dir or Path("prompts")
        self.prompts: Dict[str, PromptTemplate] = {}
        self._default_domain = Domain.GENERAL
        self._default_version = "1.0.0"

    def register(
        self,
        prompt_type: PromptType,
        template: PromptTemplate,
        domain: Domain = Domain.GENERAL,
        version: str = "1.0.0"
    ) -> None:
        """Register a prompt template.

        Args:
            prompt_type: Type of prompt
            template: The prompt template
            domain: Domain for this prompt
            version: Version identifier
        """
        key = self._make_key(prompt_type, domain, version)
        template.prompt_type = prompt_type
        template.metadata.domain = domain
        template.metadata.version = version
        self.prompts[key] = template

        logger.info(f"Registered prompt: {key}")

    def get(
        self,
        prompt_type: PromptType,
        domain: Optional[Domain] = None,
        version: Optional[str] = None
    ) -> PromptTemplate:
        """Get a prompt template.

        Args:
            prompt_type: Type of prompt to retrieve
            domain: Optional domain (defaults to GENERAL)
            version: Optional version (defaults to latest)

        Returns:
            PromptTemplate instance

        Raises:
            KeyError: If prompt not found and no fallback available
        """
        domain = domain or self._default_domain
        version = version or self._default_version

        # Try exact match
        key = self._make_key(prompt_type, domain, version)
        if key in self.prompts:
            return self.prompts[key]

        # Try domain fallback to GENERAL
        if domain != Domain.GENERAL:
            key = self._make_key(prompt_type, Domain.GENERAL, version)
            if key in self.prompts:
                logger.debug(f"Using GENERAL domain fallback for {prompt_type}")
                return self.prompts[key]

        # Try any version of this type
        for k, template in self.prompts.items():
            if k.startswith(f"{prompt_type.value}:"):
                logger.warning(f"Using alternate version for {prompt_type}: {k}")
                return template

        raise KeyError(
            f"No prompt found for type={prompt_type}, domain={domain}, version={version}"
        )

    def load_from_directory(self, directory: Optional[Path] = None) -> int:
        """Load all prompt files from directory.

        Args:
            directory: Directory to load from (defaults to base_dir)

        Returns:
            Number of prompts loaded
        """
        directory = directory or self.base_dir
        if not directory.exists():
            logger.warning(f"Prompt directory not found: {directory}")
            return 0

        loaded = 0
        for prompt_file in directory.glob("*.prompt.txt"):
            try:
                # Parse filename: {type}[_{domain}][_v{version}].prompt.txt
                name = prompt_file.stem.replace(".prompt", "")
                parts = name.split("_")

                # Extract type
                prompt_type_str = parts[0]
                prompt_type = PromptType(prompt_type_str)

                # Extract domain (if present)
                domain = Domain.GENERAL
                version = "1.0.0"

                for part in parts[1:]:
                    if part in [d.value for d in Domain]:
                        domain = Domain(part)
                    elif part.startswith("v"):
                        version = part[1:]  # Remove 'v' prefix

                # Load content
                content = prompt_file.read_text()

                # Create metadata
                metadata = PromptMetadata(
                    version=version,
                    description=f"Loaded from {prompt_file.name}",
                    domain=domain
                )

                # Create and register template
                template = PromptTemplate(content, metadata, prompt_type)
                self.register(prompt_type, template, domain, version)
                loaded += 1

            except Exception as e:
                logger.error(f"Error loading {prompt_file}: {e}")

        logger.info(f"Loaded {loaded} prompts from {directory}")
        return loaded

    def list_prompts(self) -> List[Dict[str, Any]]:
        """List all registered prompts with metadata.

        Returns:
            List of prompt information dictionaries
        """
        return [
            {
                "key": key,
                "type": template.prompt_type.value if template.prompt_type else "unknown",
                "domain": template.metadata.domain.value,
                "version": template.metadata.version,
                "variables": list(template.variables),
                "description": template.metadata.description
            }
            for key, template in self.prompts.items()
        ]

    def _make_key(self, prompt_type: PromptType, domain: Domain, version: str) -> str:
        """Create registry key for prompt."""
        return f"{prompt_type.value}:{domain.value}:{version}"


class PromptManager:
    """High-level interface for prompt management.

    This is the main interface that the orchestrator should use.
    Provides simple methods for rendering prompts with variables.
    """

    def __init__(
        self,
        registry: Optional[PromptRegistry] = None,
        domain: Domain = Domain.GENERAL,
        version: str = "1.0.0"
    ):
        """Initialize prompt manager.

        Args:
            registry: Prompt registry (creates new if None)
            domain: Default domain to use
            version: Default version to use
        """
        self.registry = registry or PromptRegistry()
        self.domain = domain
        self.version = version

        # Load prompts from directory if registry is empty
        if not self.registry.prompts:
            self.registry.load_from_directory()

    def render_entity_prompt(self, corpus: str, top_n: int = 10) -> str:
        """Render entity extraction prompt.

        Args:
            corpus: Input text corpus
            top_n: Maximum number of entities to extract

        Returns:
            Rendered prompt string
        """
        template = self.registry.get(PromptType.ENTITY, self.domain, self.version)
        return template.render(corpus=corpus, top_n=str(top_n))

    def render_relationship_prompt(
        self,
        corpus: str,
        entities: List[Dict[str, Any]]
    ) -> str:
        """Render relationship extraction prompt.

        Args:
            corpus: Input text corpus
            entities: Previously extracted entities

        Returns:
            Rendered prompt string
        """
        template = self.registry.get(PromptType.RELATIONSHIP, self.domain, self.version)
        concepts = ", ".join([e.get("name", "") for e in entities])
        return template.render(corpus=corpus, concepts=concepts)

    def render_rule_prompt(self, corpus: str) -> str:
        """Render rule induction prompt.

        Args:
            corpus: Input text corpus

        Returns:
            Rendered prompt string
        """
        template = self.registry.get(PromptType.RULE, self.domain, self.version)
        return template.render(corpus=corpus)

    def render_ontology_prompt(self, corpus: str) -> str:
        """Render ontology generation prompt.

        Args:
            corpus: Input text corpus

        Returns:
            Rendered prompt string
        """
        template = self.registry.get(PromptType.ONTOLOGY, self.domain, self.version)
        return template.render(corpus=corpus)

    def render_justification_prompt(
        self,
        corpus: str,
        rules: List[Dict[str, Any]]
    ) -> str:
        """Render justification generation prompt.

        Args:
            corpus: Input text corpus
            rules: Previously extracted rules

        Returns:
            Rendered prompt string
        """
        template = self.registry.get(PromptType.JUSTIFICATION, self.domain, self.version)
        import json
        return template.render(corpus=corpus, rules=json.dumps(rules))

    def set_domain(self, domain: Domain) -> None:
        """Change the active domain.

        Args:
            domain: New domain to use
        """
        self.domain = domain
        logger.info(f"Switched to domain: {domain.value}")

    def set_version(self, version: str) -> None:
        """Change the active version.

        Args:
            version: New version to use
        """
        self.version = version
        logger.info(f"Switched to version: {version}")

    def get_info(self) -> Dict[str, Any]:
        """Get current manager configuration.

        Returns:
            Dictionary with current settings
        """
        return {
            "domain": self.domain.value,
            "version": self.version,
            "registered_prompts": len(self.registry.prompts),
            "available_prompts": self.registry.list_prompts()
        }


# Singleton instance for global access
_default_manager: Optional[PromptManager] = None


def get_prompt_manager(
    domain: Optional[Domain] = None,
    version: Optional[str] = None
) -> PromptManager:
    """Get the default prompt manager instance.

    Creates a singleton on first call, returns existing instance thereafter.

    Args:
        domain: Optional domain to set
        version: Optional version to set

    Returns:
        PromptManager instance
    """
    global _default_manager

    if _default_manager is None:
        _default_manager = PromptManager(
            domain=domain or Domain.GENERAL,
            version=version or "1.0.0"
        )
    else:
        if domain:
            _default_manager.set_domain(domain)
        if version:
            _default_manager.set_version(version)

    return _default_manager


def reset_prompt_manager() -> None:
    """Reset the default prompt manager (mainly for testing)."""
    global _default_manager
    _default_manager = None
