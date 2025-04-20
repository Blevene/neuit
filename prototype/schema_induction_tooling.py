# Prototype: Tooling for Schema Induction via LLMs
# Covers A. Ontology Generation, B. Label Suggestion, C. Rule Induction

import openai
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
from openai import OpenAI, OpenAIError

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# --- Base LLM call wrapper ---
def query_llm(prompt: str, temperature: Optional[float] = None, model: str = "gpt-4o-mini", max_tokens: int = 1024) -> str:
    if not api_key:
        raise ValueError("OpenAI API Key is not set. Please set it in your .env file.")
    
    try:
        # Determine if we're using next‑gen small‑footprint models (e.g., "gpt-4o-mini", "o4-", "o3-")
        next_gen = any(prefix in model for prefix in ("o3-", "o4-", "4o"))

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
        }

        # Token limit parameter differs between model families
        token_param = "max_completion_tokens" if next_gen else "max_tokens"
        payload[token_param] = max_tokens

        # Temperature is only configurable on legacy models
        if (temperature is not None) and (not next_gen):
            payload["temperature"] = temperature

        response = client.chat.completions.create(**payload)

        # Ensure content exists
        if not response.choices:
            return "Error: No choices returned by the model."
        content = response.choices[0].message.content or ""
        return content.strip()
    except OpenAIError as e:
        error_message = str(e)
        if "chat.completions" in error_message:
            return (
                "Error in API call: chat completions endpoint failed. "
                "Check model name, parameters, or API version.\n" + error_message
            )
        return f"Error in API call: {error_message}"

# --- A. Ontology Generation ---
def generate_ontology(corpus: str) -> str:
    if not corpus or len(corpus.strip()) < 10:
        return "Error: Corpus is too short or empty."
    
    prompt = f"""
You are a knowledge engineer.

Given the following corpus, generate an OWL or RDF-style ontology. Include:
- Classes
- Subclasses
- Properties
- RDF or OWL triples

Corpus:
{corpus}
"""
    return query_llm(prompt)

# --- B. Label Suggestion ---
def suggest_labels(concepts: List[str], context_passages: Dict[str, str]) -> str:
    if not concepts or len(concepts) == 0:
        return "Error: No concepts provided."
    
    formatted_concepts = "\n".join(concepts)
    context_str = "\n".join([
        f"{k}:\n{v}" for k, v in context_passages.items()
    ])
    prompt = f"""
Given the extracted concepts and their context, propose descriptive, logical, and analytic labels.

Concepts:
{formatted_concepts}

Context:
{context_str}

Output format:
- Concept
- Labels (list)
- Justification
"""
    return query_llm(prompt)

# --- C. Rule Induction ---
def induce_rules(example_patterns: str) -> str:
    if not example_patterns or len(example_patterns.strip()) < 10:
        return "Error: Example patterns are too short or empty."
    
    prompt = f"""
You are an AI system generating symbolic logic rules for mastery tracking.

Examples:
{example_patterns}

Generate symbolic IF-THEN rules with confidence estimates.
Output format:
- Rule ID
- Description
- IF
- THEN
- Confidence
"""
    return query_llm(prompt)

# --- New: Label Suggestion Directly From Corpus ---

def suggest_labels_from_corpus(corpus: str, top_n: int = 10) -> str:
    """Extract key concepts from the corpus and suggest labels for them."""
    if not corpus or len(corpus.strip()) < 10:
        return "Error: Corpus is too short or empty."

    prompt = f"""
You are an educational data scientist.

Given the following corpus of learning materials, identify the top {top_n} key concepts and propose descriptive, logical, and analytic labels.

Corpus (truncated if long):
{corpus[:4000]}

Output JSON list where each item has:
- concept: the extracted concept name
- labels: array of suggested labels
- justification: short text explaining the choice
"""
    return query_llm(prompt)

# --- New: Rule Induction Directly From Corpus ---

def induce_rules_from_corpus(corpus: str) -> str:
    """Induce symbolic IF‑THEN rules about concept prerequisites based on corpus."""
    if not corpus or len(corpus.strip()) < 10:
        return "Error: Corpus is too short or empty."

    prompt = f"""
You are a knowledge engineer.
Analyze the following educational corpus and derive symbolic prerequisite rules between concepts mentioned.
Return a list of rules in the format:
- id: incremental number
- if: condition statement
- then: consequence statement
- confidence: percentage (0‑100)

Corpus (truncated if long):
{corpus[:4000]}
"""
    return query_llm(prompt)

# --- Example usage ---
if __name__ == "__main__":
    sample_corpus = """...
    Insert sample documents here.
    ..."""
    
    example_patterns = """...
    - Concept A is a prerequisite of Concept B.
    - Students who fail Concept A tend to also struggle with Concept B.
    ..."""

    concepts = ["Fractions", "Decimals", "Ratio"]
    context_passages = {
        "Fractions": "Used in early math curriculum, appears in assessments.",
        "Decimals": "Often introduced after fractions.",
        "Ratio": "Depends on understanding of fractions and multiplication."
    }

    # Run prototypes
    print("\n--- Ontology Output ---")
    print(generate_ontology(sample_corpus))

    print("\n--- Label Suggestions ---")
    print(suggest_labels(concepts, context_passages))

    print("\n--- Induced Rules ---")
    print(induce_rules(example_patterns))
