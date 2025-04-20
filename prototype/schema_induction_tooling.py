# Prototype: Tooling for Schema Induction via LLMs
# Covers A. Ontology Generation, B. Label Suggestion, C. Rule Induction

import openai
import os
from dotenv import load_dotenv
from typing import List, Dict, Optional
from openai import OpenAI, OpenAIError
from pathlib import Path
import json

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# --- Prompt loading utilities ---
_PROMPT_DIR = Path(__file__).resolve().parent / "prompts"

# Fallback built‑in templates (used when external file is missing)
_FALLBACK_PROMPTS = {
    "ontology": (
        "You are a knowledge engineer.\n\nGiven the following corpus, generate an OWL or RDF-style ontology. "
        "Include:\n- Classes\n- Subclasses\n- Properties\n- RDF or OWL triples\n\nCorpus:\n{corpus}"
    ),
    "label": (
        "Given the extracted concepts and their context, propose descriptive, logical, and analytic labels.\n\n"
        "Concepts:\n{concepts}\n\nContext:\n{context}\n\nOutput format:\n- Concept\n- Labels (list)\n- Justification"
    ),
    "label_corpus": (
        "You are an educational data scientist.\n\nGiven the following corpus of learning materials, identify the top {top_n} key concepts "
        "and propose descriptive, logical, and analytic labels.\n\nCorpus (truncated if long):\n{corpus}\n\nOutput JSON list where each item has:\n- concept: the extracted concept name\n- labels: array of suggested labels\n- justification: short text explaining the choice"
    ),
    "rules": (
        "You are an AI system generating symbolic logic rules for mastery tracking.\n\nExamples:\n{examples}\n\n"
        "Generate symbolic IF-THEN rules with confidence estimates.\nOutput format:\n- Rule ID\n- Description\n- IF\n- THEN\n- Confidence"
    ),
    "rules_corpus": (
        "You are a knowledge engineer.\nAnalyze the following educational corpus and derive symbolic prerequisite rules between concepts mentioned.\n"
        "Return a list of rules in the format:\n- id: incremental number\n- if: condition statement\n- then: consequence statement\n- confidence: percentage (0‑100)\n\nCorpus (truncated if long):\n{corpus}"
    ),
}

def _load_prompt(name: str) -> str:
    """Return prompt string from `prompts/{name}.txt` or fallback."""
    file_path = _PROMPT_DIR / f"{name}.txt"
    if file_path.exists():
        return file_path.read_text(encoding="utf-8")
    return _FALLBACK_PROMPTS[name]

# --- Prompt rendering helper ---
def _render_prompt(name: str, **params) -> str:
    """Return prompt text with placeholders replaced.

    Only placeholders provided in *params* are replaced. Unknown placeholders remain
    untouched, avoiding KeyError when braces appear for illustration purposes.
    """
    template = _load_prompt(name)
    for key, value in params.items():
        placeholder = "{" + key + "}"
        template = template.replace(placeholder, str(value))
    return template

# --- Base LLM call wrapper ---
def query_llm(prompt: str, temperature: Optional[float] = None, model: str = "gpt-4o-mini", max_tokens: int = 2048) -> str:
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
    
    prompt_tpl = _load_prompt("ontology")
    prompt = prompt_tpl.replace("{corpus}", corpus[:4000])
    return query_llm(prompt, max_tokens=4096)

# --- B. Label Suggestion ---
def suggest_labels(concepts: List[str], context_passages: Dict[str, str]) -> str:
    if not concepts or len(concepts) == 0:
        return "Error: No concepts provided."
    
    formatted_concepts = "\n".join(concepts)
    context_str = "\n".join([f"{k}:\n{v}" for k, v in context_passages.items()])
    
    prompt_tpl = _load_prompt("label")
    prompt = prompt_tpl.replace("{concepts}", formatted_concepts).replace("{context}", context_str)
    return query_llm(prompt, max_tokens=4096)

# --- C. Rule Induction ---
def induce_rules(example_patterns: str) -> str:
    if not example_patterns or len(example_patterns.strip()) < 10:
        return "Error: Example patterns are too short or empty."
    
    prompt_tpl = _load_prompt("rules")
    prompt = prompt_tpl.replace("{examples}", example_patterns)
    return query_llm(prompt, max_tokens=4096)

# --- New: Label Suggestion Directly From Corpus ---

def suggest_labels_from_corpus(corpus: str, top_n: int = 10) -> str:
    """Extract key concepts from the corpus and suggest labels for them."""
    if not corpus or len(corpus.strip()) < 10:
        return "Error: Corpus is too short or empty."

    # Use string replacement to avoid format() issues with JSON braces
    prompt_tpl = _load_prompt("label_corpus")
    prompt = prompt_tpl.replace("{top_n}", str(top_n)).replace("{corpus}", corpus[:4000])
    response = query_llm(prompt, max_tokens=4096)
    
    # Ensure we're getting valid JSON
    try:
        # Try to parse as JSON to validate
        json.loads(response)
        return response
    except json.JSONDecodeError:
        # Try to extract JSON if it's embedded in other text
        import re
        json_match = re.search(r'(\[\s*\{.*\}\s*\])', response, re.DOTALL)
        if json_match:
            try:
                extracted_json = json_match.group(1)
                json.loads(extracted_json)  # Validate
                return extracted_json
            except json.JSONDecodeError:
                pass
        
        # Return the raw response if we can't extract valid JSON
        return response

# --- New: Rule Induction Directly From Corpus ---

def induce_rules_from_corpus(corpus: str) -> str:
    """Induce symbolic IF‑THEN rules about concept prerequisites based on corpus."""
    if not corpus or len(corpus.strip()) < 10:
        return "Error: Corpus is too short or empty."

    prompt_tpl = _load_prompt("rules_corpus")
    prompt = prompt_tpl.replace("{corpus}", corpus[:4000])
    return query_llm(prompt, max_tokens=4096)

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
