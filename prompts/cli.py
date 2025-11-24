#!/usr/bin/env python3
"""
Command-line interface for NEUIToolkit prompt management.

Commands:
- list: List all available prompts
- test: Test a prompt with sample text
- compare: Compare two prompt versions (A/B testing)
- validate: Validate prompt syntax and structure
- create: Create a new prompt template
- evaluate: Run evaluation benchmarks
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional
import logging

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from prompts.prompt_manager import (
    get_prompt_manager,
    Domain,
    PromptType,
    PromptRegistry
)
from prompts.evaluator import create_evaluator, EvaluationResult

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def cmd_list(args):
    """List all available prompts."""
    pm = get_prompt_manager()
    prompts = pm.registry.list_prompts()

    if not prompts:
        print("No prompts found.")
        return

    print(f"\n{'Type':<15} {'Domain':<12} {'Version':<10} {'Variables'}")
    print("-" * 70)

    for p in prompts:
        vars_str = ", ".join(p['variables'][:3])  # Show first 3 variables
        if len(p['variables']) > 3:
            vars_str += f" ... (+{len(p['variables']) - 3} more)"

        print(f"{p['type']:<15} {p['domain']:<12} {p['version']:<10} {vars_str}")

    print(f"\nTotal: {len(prompts)} prompts")


def cmd_test(args):
    """Test a prompt with sample text."""
    pm = get_prompt_manager(
        domain=Domain(args.domain) if args.domain else None,
        version=args.version
    )

    # Read input text
    if args.file:
        text = Path(args.file).read_text()
    else:
        print("Enter text (Ctrl+D when done):")
        text = sys.stdin.read()

    # Render prompt based on type
    try:
        if args.type == "entity":
            prompt = pm.render_entity_prompt(corpus=text, top_n=args.top_n)
        elif args.type == "relationship":
            # For testing, use empty entity list
            prompt = pm.render_relationship_prompt(corpus=text, entities=[])
        elif args.type == "rule":
            prompt = pm.render_rule_prompt(corpus=text)
        elif args.type == "ontology":
            prompt = pm.render_ontology_prompt(corpus=text)
        elif args.type == "justification":
            prompt = pm.render_justification_prompt(corpus=text, rules=[])
        else:
            logger.error(f"Unknown prompt type: {args.type}")
            return

        if args.output:
            Path(args.output).write_text(prompt)
            print(f"Prompt saved to: {args.output}")
        else:
            print("\n" + "="*80)
            print("RENDERED PROMPT:")
            print("="*80)
            print(prompt)
            print("="*80)

    except Exception as e:
        logger.error(f"Error rendering prompt: {e}")


def cmd_compare(args):
    """Compare two prompt versions (A/B testing)."""
    # This is a placeholder - full implementation would require running actual extractions
    print(f"\nComparing prompts:")
    print(f"  Prompt A: {args.domain_a}/{args.version_a}")
    print(f"  Prompt B: {args.domain_b}/{args.version_b}")
    print(f"\nTo perform a full comparison:")
    print(f"  1. Run extraction with prompt A")
    print(f"  2. Run extraction with prompt B")
    print(f"  3. Use the evaluator.py module to compare results")
    print(f"\nExample:")
    print(f"  python backend/orchestrator.py --domain {args.domain_a} --version {args.version_a}")
    print(f"  python backend/orchestrator.py --domain {args.domain_b} --version {args.version_b}")


def cmd_validate(args):
    """Validate prompt syntax and structure."""
    pm = get_prompt_manager(
        domain=Domain(args.domain) if args.domain else None,
        version=args.version
    )

    prompt_type = PromptType(args.type)

    try:
        template = pm.registry.get(prompt_type, Domain(args.domain) if args.domain else None, args.version)

        print(f"\nValidating prompt: {args.type} ({args.domain or 'general'} v{args.version})")
        print("-" * 70)

        warnings = template.validate()

        if not warnings:
            print("✓ Prompt is valid")
            print(f"  - Variables: {', '.join(template.variables)}")
            print(f"  - Length: {len(template.template)} characters")
        else:
            print("⚠ Validation warnings:")
            for warning in warnings:
                print(f"  - {warning}")

        # Check required variables
        print(f"\nRequired variables: {', '.join(template.metadata.required_vars)}")
        print(f"Optional variables: {', '.join(template.metadata.optional_vars)}")

        if args.verbose:
            print(f"\nFull template:")
            print("="*80)
            print(template.template[:500])
            if len(template.template) > 500:
                print(f"\n... ({len(template.template) - 500} more characters)")
            print("="*80)

    except KeyError as e:
        logger.error(f"Prompt not found: {e}")
    except Exception as e:
        logger.error(f"Error validating prompt: {e}")


def cmd_create(args):
    """Create a new prompt template."""
    print(f"\nCreating new prompt: {args.type} ({args.domain} v{args.version})")

    # Determine filename
    filename = f"{args.type}_extraction_{args.domain}_v{args.version}.prompt.txt"
    filepath = Path("prompts/domains") / args.domain / filename

    if filepath.exists() and not args.force:
        logger.error(f"Prompt already exists: {filepath}")
        logger.error("Use --force to overwrite")
        return

    # Create directory if needed
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Template content
    template = f"""**Objective:** Extract {args.type} from {args.domain} text.

You are a {args.domain} domain expert. Extract relevant {args.type} from the provided text.

**Few-Shot Example:**
Text: [Add example text here]

Output:
[Add example output here]

**Instructions:**
1. Extract relevant {args.type}
2. Use domain-specific terminology
3. Provide clear justifications
4. Return ONLY valid JSON

**Corpus:**
{{corpus}}

**Output Format (JSON only):**
"""

    filepath.write_text(template)
    print(f"✓ Created: {filepath}")
    print(f"\nNext steps:")
    print(f"  1. Edit the prompt file to add examples and instructions")
    print(f"  2. Validate: python prompts/cli.py validate --type {args.type} --domain {args.domain}")
    print(f"  3. Test: python prompts/cli.py test --type {args.type} --domain {args.domain} --file sample.txt")


def cmd_evaluate(args):
    """Run evaluation benchmarks."""
    evaluator = create_evaluator()

    if not evaluator.gold_standard_data:
        logger.error("No gold standard data found. Create prompts/examples/gold_standard.json")
        return

    print(f"\nEvaluation mode: {args.mode}")
    print(f"Gold standard cases: {len(evaluator.gold_standard_data)}")
    print("\nThis command provides the evaluation framework.")
    print("To run full evaluation, integrate with the orchestrator to:")
    print("  1. Run extraction on gold standard texts")
    print("  2. Compare results with expected outputs")
    print("  3. Calculate metrics and generate reports")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="NEUIToolkit Prompt Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    list_parser = subparsers.add_parser('list', help='List all available prompts')

    # Test command
    test_parser = subparsers.add_parser('test', help='Test a prompt with sample text')
    test_parser.add_argument('--type', required=True, choices=['entity', 'relationship', 'rule', 'ontology', 'justification'])
    test_parser.add_argument('--domain', help='Domain (general, education, medical, etc.)')
    test_parser.add_argument('--version', default='1.0.0', help='Prompt version')
    test_parser.add_argument('--file', help='Input file (otherwise read from stdin)')
    test_parser.add_argument('--top-n', type=int, default=10, help='Top N entities to extract')
    test_parser.add_argument('--output', help='Output file for rendered prompt')

    # Compare command
    compare_parser = subparsers.add_parser('compare', help='Compare two prompt versions')
    compare_parser.add_argument('--domain-a', required=True, help='Domain for prompt A')
    compare_parser.add_argument('--version-a', default='1.0.0', help='Version for prompt A')
    compare_parser.add_argument('--domain-b', required=True, help='Domain for prompt B')
    compare_parser.add_argument('--version-b', default='1.0.0', help='Version for prompt B')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate prompt syntax')
    validate_parser.add_argument('--type', required=True, choices=['entity', 'relationship', 'rule', 'ontology', 'justification'])
    validate_parser.add_argument('--domain', help='Domain (general, education, medical, etc.)')
    validate_parser.add_argument('--version', default='1.0.0', help='Prompt version')
    validate_parser.add_argument('--verbose', action='store_true', help='Show full prompt')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create new prompt template')
    create_parser.add_argument('--type', required=True, help='Prompt type')
    create_parser.add_argument('--domain', required=True, help='Domain')
    create_parser.add_argument('--version', default='1.0.0', help='Version')
    create_parser.add_argument('--force', action='store_true', help='Overwrite if exists')

    # Evaluate command
    evaluate_parser = subparsers.add_parser('evaluate', help='Run evaluation benchmarks')
    evaluate_parser.add_argument('--mode', default='full', choices=['full', 'quick'], help='Evaluation mode')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    commands = {
        'list': cmd_list,
        'test': cmd_test,
        'compare': cmd_compare,
        'validate': cmd_validate,
        'create': cmd_create,
        'evaluate': cmd_evaluate
    }

    commands[args.command](args)


if __name__ == '__main__':
    main()
