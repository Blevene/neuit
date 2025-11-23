# Prompt Management System

This directory contains the centralized prompt management system for NEUIToolkit, which provides flexible, version-controlled prompts with domain-specific customization.

## Overview

The prompt management system supports:
- **Template Variables**: Dynamic content injection
- **Version Control**: Multiple prompt versions for A/B testing
- **Domain-Specific Prompts**: Customized prompts for different domains
- **Validation**: Ensures prompts have required variables
- **Dependency Injection**: Easy testing and swapping

## Architecture

```
prompts/
├── prompt_manager.py           # Core prompt management code
├── entity_extraction.prompt.txt        # General entity extraction
├── relationship_extraction.prompt.txt  # General relationship extraction
├── rule_induction.prompt.txt           # General rule induction
├── ontology_generation.prompt.txt      # General ontology generation
├── explanation_generation.prompt.txt   # General explanation generation
└── domains/                            # Domain-specific prompts (future)
    ├── education/
    │   ├── entity_extraction_education_v1.0.0.prompt.txt
    │   └── relationship_extraction_education_v1.0.0.prompt.txt
    ├── medical/
    └── legal/
```

## Usage

### Basic Usage

```python
from prompts.prompt_manager import get_prompt_manager

# Get the default prompt manager
pm = get_prompt_manager()

# Render prompts with variables
entity_prompt = pm.render_entity_prompt(
    corpus="Sample text...",
    top_n=10
)

relationship_prompt = pm.render_relationship_prompt(
    corpus="Sample text...",
    entities=[{"name": "Cell", "category": "Biology"}]
)
```

### Domain-Specific Prompts

```python
from prompts.prompt_manager import get_prompt_manager, Domain

# Use education-specific prompts
pm = get_prompt_manager(domain=Domain.EDUCATION)

# Use medical-specific prompts
pm = get_prompt_manager(domain=Domain.MEDICAL)
```

### Environment Configuration

Set in `.env` file:

```bash
# Domain: general, education, medical, legal, scientific, business
PROMPT_DOMAIN=education

# Version for A/B testing
PROMPT_VERSION=1.0.0
```

### Direct API

```python
from prompts.prompt_manager import PromptManager, PromptRegistry, Domain

# Create custom registry
registry = PromptRegistry()
registry.load_from_directory(Path("custom_prompts/"))

# Create manager with custom registry
pm = PromptManager(registry=registry, domain=Domain.MEDICAL)
```

## Prompt File Naming Convention

Prompt files follow this naming pattern:

```
{type}[_{domain}][_v{version}].prompt.txt
```

Examples:
- `entity_extraction.prompt.txt` - General entity extraction, v1.0.0 (default)
- `entity_extraction_education_v1.1.0.prompt.txt` - Education domain, v1.1.0
- `relationship_extraction_medical_v2.0.0.prompt.txt` - Medical domain, v2.0.0

## Template Variables

### Entity Extraction
- `{corpus}` - Input text corpus (required)
- `{top_n}` - Maximum entities to extract (required)

### Relationship Extraction
- `{corpus}` - Input text corpus (required)
- `{concepts}` - Comma-separated entity names (required)

### Rule Induction
- `{corpus}` - Input text corpus (required)

### Ontology Generation
- `{corpus}` - Input text corpus (required)

### Justification Generation
- `{corpus}` - Input text corpus (required)
- `{rules}` - JSON string of extracted rules (required)

## Creating Custom Prompts

### 1. Create Prompt File

Create a file following the naming convention:

```bash
touch prompts/entity_extraction_medical_v1.0.0.prompt.txt
```

### 2. Write Prompt Template

Use `{variable}` syntax for placeholders:

```
You are an expert in medical knowledge extraction.
Analyze the following medical text and extract key medical entities:

Text:
{corpus}

Extract up to {top_n} medical entities including:
- Diseases
- Medications
- Procedures
- Anatomical structures

Return as JSON array...
```

### 3. Use in Code

```python
from prompts.prompt_manager import get_prompt_manager, Domain

pm = get_prompt_manager(domain=Domain.MEDICAL, version="1.0.0")
prompt = pm.render_entity_prompt(corpus=text, top_n=20)
```

## Programmatic Registration

For dynamic prompts or testing:

```python
from prompts.prompt_manager import (
    PromptManager,
    PromptTemplate,
    PromptMetadata,
    PromptType,
    Domain
)

# Create template
template_str = "Extract entities from: {corpus}. Limit: {top_n}"
metadata = PromptMetadata(
    version="2.0.0",
    description="Custom entity extraction",
    required_vars={"corpus", "top_n"}
)

template = PromptTemplate(template_str, metadata)

# Register with manager
pm = PromptManager()
pm.registry.register(
    prompt_type=PromptType.ENTITY,
    template=template,
    domain=Domain.GENERAL,
    version="2.0.0"
)
```

## Validation

Prompts are automatically validated for:
- Missing required variables
- Mismatched braces
- Empty templates
- Suspicious patterns

```python
template = PromptTemplate("Extract from {corpus}")
warnings = template.validate()
if warnings:
    for warning in warnings:
        print(f"Warning: {warning}")
```

## Best Practices

### 1. Use Descriptive Variable Names
```python
# Good
{corpus}, {top_n}, {concepts}

# Avoid
{text}, {n}, {c}
```

### 2. Include Instructions
```python
"""
You are an expert knowledge extractor.
Task: Extract entities from the provided text.
Format: Return JSON array with objects containing 'name', 'category', 'aliases'.
"""
```

### 3. Provide Examples
```python
"""
Example output:
[
  {"name": "Cell", "category": "Biology", "aliases": ["Basic unit of life"]},
  {"name": "DNA", "category": "Molecule", "aliases": ["Genetic material"]}
]
"""
```

### 4. Version Your Prompts
- Use semantic versioning: `1.0.0`, `1.1.0`, `2.0.0`
- Major version: Breaking changes
- Minor version: Improvements
- Patch version: Bug fixes

### 5. Domain-Specific Vocabulary
```python
# Education domain - use pedagogical terms
"Extract learning objectives, prerequisites, and concepts..."

# Medical domain - use clinical terms
"Extract diagnoses, treatments, and clinical findings..."
```

## Testing

Test your prompts:

```python
from prompts.prompt_manager import PromptTemplate, PromptMetadata

# Create test template
template = PromptTemplate(
    "Extract {top_n} entities from: {corpus}",
    PromptMetadata(
        version="1.0.0",
        required_vars={"corpus", "top_n"}
    )
)

# Validate
assert template.validate() == []

# Test rendering
result = template.render(corpus="test text", top_n=10)
assert "{corpus}" not in result
assert "{top_n}" not in result
```

## Migration from Old System

Old system (deprecated):
```python
# OLD - Don't use
PROMPTS = {
    "entity": Path("prompts/entity.txt").read_text()
}
prompt = PROMPTS["entity"].replace("{corpus}", text)
```

New system:
```python
# NEW - Use this
from prompts.prompt_manager import get_prompt_manager

pm = get_prompt_manager()
prompt = pm.render_entity_prompt(corpus=text, top_n=10)
```

## Advanced Features

### Fallback Strategy

The system automatically falls back:
1. Try exact match (domain + version)
2. Fall back to GENERAL domain
3. Fall back to any version
4. Raise error if none found

### A/B Testing

Test multiple prompt versions:

```python
# Version A
pm_a = PromptManager(version="1.0.0")
results_a = extract_with_prompts(pm_a)

# Version B
pm_b = PromptManager(version="2.0.0")
results_b = extract_with_prompts(pm_b)

# Compare results
compare_quality(results_a, results_b)
```

### Listing Available Prompts

```python
pm = get_prompt_manager()
prompts = pm.registry.list_prompts()

for p in prompts:
    print(f"{p['type']} - {p['domain']} v{p['version']}")
    print(f"  Variables: {p['variables']}")
    print(f"  Description: {p['description']}")
```

## Troubleshooting

### Missing Variable Error

```
ValueError: Missing required variables: {'corpus'}
```

**Solution**: Ensure all required variables are provided:
```python
prompt = pm.render_entity_prompt(corpus=text, top_n=10)  # ✓
```

### Prompt Not Found

```
KeyError: No prompt found for type=entity, domain=medical, version=1.0.0
```

**Solution**: Check prompt exists or use fallback:
```python
# Use general domain as fallback
pm = get_prompt_manager(domain=Domain.GENERAL)
```

### Template Rendering Issues

```
Error rendering template: ...
```

**Solution**: Check for syntax errors in prompt file:
- Ensure braces are balanced: `{` and `}`
- Use consistent style: either `{var}` or `{{var}}`

## Future Enhancements

- [ ] Prompt analytics and performance tracking
- [ ] Auto-generated prompts from examples
- [ ] Multi-language support
- [ ] Prompt optimization suggestions
- [ ] Integration with prompt engineering tools
- [ ] Crowd-sourced prompt library

## Contributing

To contribute new prompts:

1. Create prompt file following naming convention
2. Include clear instructions and examples
3. Define required variables in metadata
4. Test with representative data
5. Submit PR with description and benchmarks

## Resources

- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [OpenAI Best Practices](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Guide](https://docs.anthropic.com/claude/docs/prompt-engineering)

---

**Questions?** See [CONTRIBUTING.md](../CONTRIBUTING.md) or open an issue.
