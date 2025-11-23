# llm_utils.py — Enhanced LLM abstraction layer with multi-provider support

from litellm import completion
import os
import logging
import time
from typing import Optional, Dict, Any

from llm.provider_config import get_provider_registry, ProviderConfig

# Optional: set logging for prompt auditing
logger = logging.getLogger("llm_utils")
logger.setLevel(logging.INFO)

# Global registry
_registry = None


def get_registry():
    """Get or initialize the global provider registry"""
    global _registry
    if _registry is None:
        _registry = get_provider_registry()
    return _registry


def call_llm_with_prompt(
    prompt: str,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    use_fallback: bool = True
) -> str:
    """
    Sends a prompt to the configured LLM provider with automatic fallback support.

    Args:
        prompt: The prompt to send to the LLM
        temperature: Temperature for response randomness (overrides provider default)
        max_tokens: Maximum tokens in response (overrides provider default)
        use_fallback: Whether to try fallback providers on failure

    Returns:
        The LLM's response text

    Raises:
        Exception: If all providers fail
    """
    registry = get_registry()
    provider = registry.get_primary_provider()

    if not provider:
        raise ValueError("No LLM providers configured. Please set up API keys in .env file.")

    # Track attempts for retry logic
    attempts = []

    while provider:
        try:
            # Use provider defaults if not specified
            temp = temperature if temperature is not None else provider.temperature
            tokens = max_tokens if max_tokens is not None else provider.max_tokens

            # Log the request
            logger.info(
                "[LLM CALL] Provider: %s | Model: %s | Temp: %.2f\nPrompt:\n%s",
                provider.provider.value,
                provider.model,
                temp,
                prompt[:3000]
            )

            # Prepare API call
            model_str = provider.to_litellm_model()
            api_kwargs = {
                "model": model_str,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temp,
                "max_tokens": tokens,
                "timeout": provider.timeout
            }

            # Add API key if available (litellm handles env vars automatically)
            if provider.api_key:
                os.environ[f"{provider.provider.value.upper()}_API_KEY"] = provider.api_key

            # Add base URL for Ollama or custom endpoints
            if provider.base_url:
                api_kwargs["api_base"] = provider.base_url

            # Make the request with retry logic
            for attempt in range(provider.max_retries):
                try:
                    response = completion(**api_kwargs)
                    break
                except Exception as retry_error:
                    if attempt < provider.max_retries - 1:
                        wait_time = 2 ** attempt  # Exponential backoff
                        logger.warning(f"Retry {attempt + 1}/{provider.max_retries} after {wait_time}s: {retry_error}")
                        time.sleep(wait_time)
                    else:
                        raise retry_error

            # Extract response
            content = response['choices'][0]['message']['content'].strip()

            # Track usage
            if 'usage' in response:
                tokens_used = response['usage'].get('total_tokens', 0)
                registry.track_request(tokens_used, provider)

            # Log the response
            logger.info("[LLM RESPONSE]\n%s", content)

            # Reset fallback on success
            registry.reset_fallback()

            return content

        except Exception as e:
            error_msg = f"Provider {provider.provider.value} ({provider.model}) failed: {str(e)}"
            attempts.append(error_msg)
            logger.error(error_msg)

            # Try fallback provider if available and enabled
            if use_fallback:
                provider = registry.get_next_fallback()
                if provider:
                    logger.warning(f"Attempting fallback to {provider.provider.value}")
                    continue

            # No more fallbacks or fallback disabled
            registry.reset_fallback()
            all_errors = "\n".join(attempts)
            raise Exception(f"All LLM providers failed:\n{all_errors}")

    raise ValueError("No LLM providers available")


def get_provider_stats() -> Dict[str, Any]:
    """Get usage statistics for all providers"""
    registry = get_registry()
    return registry.get_stats()


def estimate_cost(text: str, provider_name: Optional[str] = None) -> float:
    """
    Estimate the cost of processing a text with the current provider.

    Args:
        text: The text to estimate cost for
        provider_name: Optional specific provider name, otherwise uses primary

    Returns:
        Estimated cost in USD
    """
    registry = get_registry()
    provider = registry.get_primary_provider()

    if not provider:
        return 0.0

    # Rough estimation: ~4 characters per token
    estimated_tokens = len(text) / 4
    cost = (estimated_tokens / 1000.0) * provider.cost_per_1k_tokens

    return cost
