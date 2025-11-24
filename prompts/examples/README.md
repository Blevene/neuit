# Prompt Examples and Test Data

This directory contains example data for testing and evaluating prompt performance.

## Contents

### gold_standard.json

Gold standard test cases for evaluating extraction quality. Each test case includes:
- `id`: Unique identifier
- `text`: Input text corpus
- `expected_entities`: Ground truth entity extractions
- `expected_relationships`: Ground truth relationship extractions
- `expected_rules`: Ground truth rule extractions
- `domain`: Domain category (education, medical, scientific, legal, business)
- `difficulty`: Difficulty level (easy, medium, hard)

### Usage

The gold standard is used by the `prompts/evaluator.py` module to:
1. Benchmark prompt performance
2. Compare different prompt versions (A/B testing)
3. Calculate precision, recall, and F1 scores
4. Generate evaluation reports

### Adding New Test Cases

To add new test cases:

1. Follow the JSON schema in `gold_standard.json`
2. Include representative examples from each domain
3. Ensure expected outputs are accurate and complete
4. Specify appropriate difficulty levels
5. Run validation: `python prompts/cli.py evaluate`

### Example Structure

```json
{
  "id": "unique-id",
  "text": "Input text to extract from...",
  "expected_entities": [
    {
      "name": "Entity Name",
      "aliases": ["Synonym 1", "Synonym 2"],
      "category": "Category"
    }
  ],
  "expected_relationships": [
    {
      "subject": "Entity A",
      "predicate": "relationship_type",
      "object": "Entity B"
    }
  ],
  "expected_rules": [
    {
      "id": 1,
      "if": "Condition",
      "then": "Consequence",
      "confidence": 0.95
    }
  ],
  "domain": "education",
  "difficulty": "medium"
}
```

### Domain-Specific Examples

- **Education**: Curriculum content, learning objectives, prerequisites
- **Medical**: Clinical guidelines, diagnoses, treatments
- **Scientific**: Research methods, theories, experimental results
- **Legal**: Statutes, case law, legal obligations
- **Business**: Strategies, metrics, market analysis

## Best Practices

1. **Accuracy**: Ensure expected outputs are correct and complete
2. **Diversity**: Include varied examples covering different subtopics
3. **Realism**: Use authentic text samples from real documents
4. **Balance**: Maintain similar distribution across domains and difficulty levels
5. **Validation**: Regularly review and update test cases

## Contributing

To contribute new test cases:
1. Add cases to `gold_standard.json`
2. Test with: `pytest tests/test_prompt_evaluator.py -v`
3. Submit PR with description of test coverage

---

For more information, see the [Prompt README](../README.md).
