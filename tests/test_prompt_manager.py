"""
Tests for the centralized prompt management system.
"""

import pytest
from pathlib import Path
from prompts.prompt_manager import (
    PromptTemplate,
    PromptMetadata,
    PromptRegistry,
    PromptManager,
    PromptType,
    Domain,
    get_prompt_manager,
    reset_prompt_manager
)


class TestPromptMetadata:
    """Tests for PromptMetadata dataclass."""

    def test_create_metadata(self):
        """Test creating prompt metadata."""
        metadata = PromptMetadata(
            version="1.0.0",
            description="Test prompt",
            required_vars={"corpus", "top_n"}
        )

        assert metadata.version == "1.0.0"
        assert metadata.description == "Test prompt"
        assert metadata.required_vars == {"corpus", "top_n"}
        assert metadata.domain == Domain.GENERAL

    def test_metadata_to_dict(self):
        """Test converting metadata to dictionary."""
        metadata = PromptMetadata(
            version="1.0.0",
            description="Test",
            required_vars={"corpus"}
        )

        data = metadata.to_dict()

        assert data["version"] == "1.0.0"
        assert data["description"] == "Test"
        assert "corpus" in data["required_vars"]
        assert data["domain"] == "general"


class TestPromptTemplate:
    """Tests for PromptTemplate class."""

    def test_create_template(self):
        """Test creating a prompt template."""
        template = PromptTemplate(
            "Extract entities from: {corpus}",
            PromptMetadata(version="1.0.0")
        )

        assert "{corpus}" in template.template
        assert "corpus" in template.variables

    def test_extract_variables(self):
        """Test automatic variable extraction."""
        template = PromptTemplate(
            "Process {corpus} and extract {top_n} items",
            PromptMetadata(version="1.0.0")
        )

        assert "corpus" in template.variables
        assert "top_n" in template.variables
        assert len(template.variables) == 2

    def test_render_template(self):
        """Test rendering template with variables."""
        template = PromptTemplate(
            "Extract {count} entities from: {text}",
            PromptMetadata(
                version="1.0.0",
                required_vars={"text", "count"}
            )
        )

        result = template.render(text="sample", count=10)

        assert "sample" in result
        assert "10" in result
        assert "{text}" not in result
        assert "{count}" not in result

    def test_render_missing_variables(self):
        """Test error on missing required variables."""
        template = PromptTemplate(
            "Extract from: {corpus}",
            PromptMetadata(
                version="1.0.0",
                required_vars={"corpus"}
            )
        )

        with pytest.raises(ValueError, match="Missing required variables"):
            template.render()

    def test_render_optional_variables(self):
        """Test rendering with optional variables."""
        metadata = PromptMetadata(
            version="1.0.0",
            required_vars={"corpus"},
            optional_vars={"context"}
        )
        template = PromptTemplate(
            "Extract from {corpus}. Context: {context}",
            metadata
        )

        # Should work without optional var (defaults to empty string)
        result = template.render(corpus="test")
        assert "test" in result

        # Should work with optional var
        result = template.render(corpus="test", context="education")
        assert "education" in result

    def test_validate_template(self):
        """Test template validation."""
        # Valid template
        valid = PromptTemplate(
            "Extract entities from {corpus} with limit {top_n}",
            PromptMetadata(version="1.0.0")
        )
        warnings = valid.validate()
        assert len(warnings) == 0

        # Empty template
        empty = PromptTemplate("", PromptMetadata(version="1.0.0"))
        warnings = empty.validate()
        assert any("empty" in w.lower() for w in warnings)

        # Mismatched braces
        bad_braces = PromptTemplate(
            "Extract {corpus",
            PromptMetadata(version="1.0.0")
        )
        warnings = bad_braces.validate()
        assert any("brace" in w.lower() for w in warnings)

    def test_double_brace_variables(self):
        """Test templates with {{variable}} style."""
        template = PromptTemplate(
            "Extract from {{corpus}} limit {{top_n}}",
            PromptMetadata(version="1.0.0")
        )

        result = template.render(corpus="test", top_n=5)

        assert "test" in result
        assert "5" in result
        assert "{{corpus}}" not in result


class TestPromptRegistry:
    """Tests for PromptRegistry class."""

    def test_create_registry(self):
        """Test creating a prompt registry."""
        registry = PromptRegistry()
        assert len(registry.prompts) == 0

    def test_register_prompt(self):
        """Test registering a prompt."""
        registry = PromptRegistry()
        template = PromptTemplate(
            "Test {corpus}",
            PromptMetadata(version="1.0.0")
        )

        registry.register(
            PromptType.ENTITY,
            template,
            Domain.GENERAL,
            "1.0.0"
        )

        assert len(registry.prompts) == 1

    def test_get_prompt(self):
        """Test retrieving a registered prompt."""
        registry = PromptRegistry()
        template = PromptTemplate(
            "Test {corpus}",
            PromptMetadata(version="1.0.0")
        )

        registry.register(PromptType.ENTITY, template, Domain.GENERAL, "1.0.0")
        retrieved = registry.get(PromptType.ENTITY, Domain.GENERAL, "1.0.0")

        assert retrieved == template

    def test_get_prompt_fallback_domain(self):
        """Test fallback to GENERAL domain."""
        registry = PromptRegistry()
        template = PromptTemplate(
            "Test {corpus}",
            PromptMetadata(version="1.0.0")
        )

        # Register only GENERAL domain
        registry.register(PromptType.ENTITY, template, Domain.GENERAL, "1.0.0")

        # Request EDUCATION domain - should fallback to GENERAL
        retrieved = registry.get(PromptType.ENTITY, Domain.EDUCATION, "1.0.0")
        assert retrieved == template

    def test_get_prompt_not_found(self):
        """Test error when prompt not found."""
        registry = PromptRegistry()

        with pytest.raises(KeyError):
            registry.get(PromptType.ENTITY, Domain.GENERAL, "1.0.0")

    def test_list_prompts(self):
        """Test listing all registered prompts."""
        registry = PromptRegistry()

        template1 = PromptTemplate("Test1 {corpus}", PromptMetadata(version="1.0.0"))
        template2 = PromptTemplate("Test2 {corpus}", PromptMetadata(version="1.0.0"))

        registry.register(PromptType.ENTITY, template1, Domain.GENERAL, "1.0.0")
        registry.register(PromptType.RELATIONSHIP, template2, Domain.GENERAL, "1.0.0")

        prompts = registry.list_prompts()

        assert len(prompts) == 2
        assert any(p["type"] == "entity" for p in prompts)
        assert any(p["type"] == "relationship" for p in prompts)


class TestPromptManager:
    """Tests for PromptManager high-level interface."""

    @pytest.fixture
    def setup_manager(self):
        """Set up a prompt manager with test prompts."""
        registry = PromptRegistry()

        # Register test prompts
        entity_template = PromptTemplate(
            "Extract {top_n} entities from: {corpus}",
            PromptMetadata(
                version="1.0.0",
                required_vars={"corpus", "top_n"}
            )
        )
        registry.register(PromptType.ENTITY, entity_template, Domain.GENERAL, "1.0.0")

        relationship_template = PromptTemplate(
            "Extract relationships from {corpus}. Concepts: {concepts}",
            PromptMetadata(
                version="1.0.0",
                required_vars={"corpus", "concepts"}
            )
        )
        registry.register(PromptType.RELATIONSHIP, relationship_template, Domain.GENERAL, "1.0.0")

        rule_template = PromptTemplate(
            "Extract rules from: {corpus}",
            PromptMetadata(version="1.0.0", required_vars={"corpus"})
        )
        registry.register(PromptType.RULE, rule_template, Domain.GENERAL, "1.0.0")

        ontology_template = PromptTemplate(
            "Generate ontology from: {corpus}",
            PromptMetadata(version="1.0.0", required_vars={"corpus"})
        )
        registry.register(PromptType.ONTOLOGY, ontology_template, Domain.GENERAL, "1.0.0")

        justification_template = PromptTemplate(
            "Explain rules: {rules} using context: {corpus}",
            PromptMetadata(version="1.0.0", required_vars={"corpus", "rules"})
        )
        registry.register(PromptType.JUSTIFICATION, justification_template, Domain.GENERAL, "1.0.0")

        return PromptManager(registry=registry)

    def test_render_entity_prompt(self, setup_manager):
        """Test rendering entity extraction prompt."""
        pm = setup_manager

        result = pm.render_entity_prompt(corpus="sample text", top_n=10)

        assert "sample text" in result
        assert "10" in result
        assert "{corpus}" not in result
        assert "{top_n}" not in result

    def test_render_relationship_prompt(self, setup_manager):
        """Test rendering relationship extraction prompt."""
        pm = setup_manager

        entities = [
            {"name": "Cell"},
            {"name": "Nucleus"}
        ]

        result = pm.render_relationship_prompt(corpus="sample", entities=entities)

        assert "sample" in result
        assert "Cell, Nucleus" in result

    def test_render_rule_prompt(self, setup_manager):
        """Test rendering rule induction prompt."""
        pm = setup_manager

        result = pm.render_rule_prompt(corpus="test corpus")

        assert "test corpus" in result
        assert "{corpus}" not in result

    def test_render_ontology_prompt(self, setup_manager):
        """Test rendering ontology generation prompt."""
        pm = setup_manager

        result = pm.render_ontology_prompt(corpus="test")

        assert "test" in result

    def test_render_justification_prompt(self, setup_manager):
        """Test rendering justification generation prompt."""
        pm = setup_manager

        rules = [{"id": 1, "if": "A", "then": "B"}]

        result = pm.render_justification_prompt(corpus="text", rules=rules)

        assert "text" in result
        assert "[{" in result  # JSON representation of rules

    def test_set_domain(self, setup_manager):
        """Test changing active domain."""
        pm = setup_manager

        pm.set_domain(Domain.EDUCATION)
        assert pm.domain == Domain.EDUCATION

        pm.set_domain(Domain.MEDICAL)
        assert pm.domain == Domain.MEDICAL

    def test_set_version(self, setup_manager):
        """Test changing active version."""
        pm = setup_manager

        pm.set_version("2.0.0")
        assert pm.version == "2.0.0"

    def test_get_info(self, setup_manager):
        """Test getting manager configuration info."""
        pm = setup_manager

        info = pm.get_info()

        assert "domain" in info
        assert "version" in info
        assert "registered_prompts" in info
        assert info["domain"] == "general"


class TestGlobalPromptManager:
    """Tests for global prompt manager singleton."""

    def teardown_method(self):
        """Reset global manager after each test."""
        reset_prompt_manager()

    def test_get_default_manager(self):
        """Test getting the default global manager."""
        pm = get_prompt_manager()
        assert pm is not None
        assert isinstance(pm, PromptManager)

    def test_singleton_pattern(self):
        """Test that get_prompt_manager returns same instance."""
        pm1 = get_prompt_manager()
        pm2 = get_prompt_manager()
        assert pm1 is pm2

    def test_reset_manager(self):
        """Test resetting the global manager."""
        pm1 = get_prompt_manager()
        reset_prompt_manager()
        pm2 = get_prompt_manager()

        # Should be different instances
        assert pm1 is not pm2


class TestIntegration:
    """Integration tests for prompt management system."""

    def test_end_to_end_workflow(self):
        """Test complete workflow from registration to rendering."""
        # Create registry
        registry = PromptRegistry()

        # Create and register template
        template = PromptTemplate(
            "Extract {count} items from: {text}",
            PromptMetadata(
                version="1.0.0",
                description="Test extraction",
                required_vars={"text", "count"}
            )
        )

        registry.register(
            PromptType.ENTITY,
            template,
            Domain.GENERAL,
            "1.0.0"
        )

        # Create manager
        manager = PromptManager(registry=registry)

        # Render prompt (using entity prompt helper)
        # Note: This will use the registered template
        retrieved = registry.get(PromptType.ENTITY, Domain.GENERAL, "1.0.0")
        result = retrieved.render(text="Sample corpus", count=15)

        # Verify
        assert "Sample corpus" in result
        assert "15" in result
        assert "{text}" not in result

    def test_domain_specific_prompts(self):
        """Test using domain-specific prompts."""
        registry = PromptRegistry()

        # Register general prompt
        general_template = PromptTemplate(
            "General: Extract from {corpus}",
            PromptMetadata(version="1.0.0")
        )
        registry.register(PromptType.ENTITY, general_template, Domain.GENERAL, "1.0.0")

        # Register education-specific prompt
        edu_template = PromptTemplate(
            "Education: Extract learning objectives from {corpus}",
            PromptMetadata(version="1.0.0")
        )
        registry.register(PromptType.ENTITY, edu_template, Domain.EDUCATION, "1.0.0")

        # Test retrieval
        general_prompt = registry.get(PromptType.ENTITY, Domain.GENERAL, "1.0.0")
        assert "General:" in general_prompt.template

        edu_prompt = registry.get(PromptType.ENTITY, Domain.EDUCATION, "1.0.0")
        assert "Education:" in edu_prompt.template
        assert "learning objectives" in edu_prompt.template

    def test_version_management(self):
        """Test managing multiple versions of prompts."""
        registry = PromptRegistry()

        # Register v1.0.0
        v1 = PromptTemplate(
            "V1: Extract from {corpus}",
            PromptMetadata(version="1.0.0")
        )
        registry.register(PromptType.ENTITY, v1, Domain.GENERAL, "1.0.0")

        # Register v2.0.0
        v2 = PromptTemplate(
            "V2: Enhanced extraction from {corpus}",
            PromptMetadata(version="2.0.0")
        )
        registry.register(PromptType.ENTITY, v2, Domain.GENERAL, "2.0.0")

        # Test retrieval
        prompt_v1 = registry.get(PromptType.ENTITY, Domain.GENERAL, "1.0.0")
        assert "V1:" in prompt_v1.template

        prompt_v2 = registry.get(PromptType.ENTITY, Domain.GENERAL, "2.0.0")
        assert "V2:" in prompt_v2.template
        assert "Enhanced" in prompt_v2.template


@pytest.mark.integration
class TestPromptManagerIntegration:
    """Integration tests that work with actual prompt files."""

    def test_load_prompts_from_directory(self, tmp_path):
        """Test loading prompts from directory."""
        # Create test prompt file
        prompt_dir = tmp_path / "prompts"
        prompt_dir.mkdir()

        prompt_file = prompt_dir / "entity_extraction.prompt.txt"
        prompt_file.write_text("Extract entities from {corpus}. Limit: {top_n}")

        # Load prompts
        registry = PromptRegistry(base_dir=prompt_dir)
        loaded_count = registry.load_from_directory()

        assert loaded_count == 1
        assert len(registry.prompts) == 1

        # Verify loaded prompt works
        template = registry.get(PromptType.ENTITY, Domain.GENERAL, "1.0.0")
        result = template.render(corpus="test", top_n=5)
        assert "test" in result
        assert "5" in result
