# llm_utils.py — LLM abstraction layer for use with orchestrator

from litellm import completion
import os
import logging

# Load credentials and defaults from env
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_KEY = os.getenv("OPENAI_API_KEY")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")

# Optional: set logging for prompt auditing
logger = logging.getLogger("llm_utils")
logger.setLevel(logging.INFO)


def call_llm_with_prompt(prompt: str, temperature: float = 0.2, max_tokens: int = 4096) -> str:
    """
    Sends a prompt to the configured LLM provider via llmlite.
    Logs prompt/response pairs and returns the LLM's output.
    """
    try:
        # Still truncate very long prompts in logs
        logger.info("[LLM CALL] Model: %s | Temp: %.2f\nPrompt:\n%s", LLM_MODEL, temperature, prompt[:3000])
        response = completion(
            model=LLM_MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
            max_tokens=max_tokens
        )
        content = response['choices'][0]['message']['content'].strip()
        # Log the full response without truncation
        logger.info("[LLM RESPONSE]\n%s", content)
        return content
    except Exception as e:
        logger.error("LLM request failed: %s", str(e))
        raise
