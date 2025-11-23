"""
LLM Provider Configuration
Supports multiple LLM providers with fallback mechanisms and cost optimization
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum
import os
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    OLLAMA = "ollama"
    AZURE = "azure"


@dataclass
class ProviderConfig:
    """Configuration for a specific LLM provider"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # For Ollama or custom endpoints
    max_tokens: int = 4096
    temperature: float = 0.2
    timeout: int = 120
    max_retries: int = 3
    cost_per_1k_tokens: float = 0.0  # For cost tracking

    def to_litellm_model(self) -> str:
        """Convert to litellm model string format"""
        if self.provider == LLMProvider.OPENAI:
            return self.model
        elif self.provider == LLMProvider.ANTHROPIC:
            return f"anthropic/{self.model}"
        elif self.provider == LLMProvider.GOOGLE:
            return f"gemini/{self.model}"
        elif self.provider == LLMProvider.OLLAMA:
            return f"ollama/{self.model}"
        elif self.provider == LLMProvider.AZURE:
            return f"azure/{self.model}"
        return self.model


class ProviderRegistry:
    """Registry of available LLM providers with fallback support"""

    def __init__(self):
        self.providers: List[ProviderConfig] = []
        self.current_provider_index = 0
        self.total_cost = 0.0
        self.request_count = 0

    def register_provider(self, config: ProviderConfig):
        """Register a new provider configuration"""
        self.providers.append(config)
        logger.info(f"Registered provider: {config.provider.value} - {config.model}")

    def get_primary_provider(self) -> Optional[ProviderConfig]:
        """Get the primary (first) provider"""
        return self.providers[0] if self.providers else None

    def get_next_fallback(self) -> Optional[ProviderConfig]:
        """Get the next fallback provider"""
        self.current_provider_index += 1
        if self.current_provider_index < len(self.providers):
            provider = self.providers[self.current_provider_index]
            logger.warning(f"Falling back to provider: {provider.provider.value} - {provider.model}")
            return provider
        return None

    def reset_fallback(self):
        """Reset to primary provider"""
        self.current_provider_index = 0

    def track_request(self, tokens_used: int, provider: ProviderConfig):
        """Track usage and cost"""
        cost = (tokens_used / 1000.0) * provider.cost_per_1k_tokens
        self.total_cost += cost
        self.request_count += 1
        logger.info(f"Request #{self.request_count} | Tokens: {tokens_used} | Cost: ${cost:.4f} | Total: ${self.total_cost:.2f}")

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_requests": self.request_count,
            "total_cost": round(self.total_cost, 2),
            "providers_configured": len(self.providers),
            "avg_cost_per_request": round(self.total_cost / max(self.request_count, 1), 4)
        }


def load_providers_from_env() -> ProviderRegistry:
    """Load provider configurations from environment variables"""
    registry = ProviderRegistry()

    # Check for primary provider
    primary_provider = os.getenv("LLM_PROVIDER", "openai").lower()
    primary_model = os.getenv("LLM_MODEL", "gpt-4")

    # OpenAI Configuration
    if primary_provider == "openai" or os.getenv("OPENAI_API_KEY"):
        openai_config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            model=primary_model if primary_provider == "openai" else os.getenv("OPENAI_MODEL", "gpt-4"),
            api_key=os.getenv("OPENAI_API_KEY"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "4096")),
            cost_per_1k_tokens=float(os.getenv("OPENAI_COST_PER_1K", "0.03"))
        )
        if openai_config.api_key:
            registry.register_provider(openai_config)

    # Anthropic (Claude) Configuration
    if primary_provider == "anthropic" or os.getenv("ANTHROPIC_API_KEY"):
        anthropic_config = ProviderConfig(
            provider=LLMProvider.ANTHROPIC,
            model=primary_model if primary_provider == "anthropic" else os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096")),
            cost_per_1k_tokens=float(os.getenv("ANTHROPIC_COST_PER_1K", "0.015"))
        )
        if anthropic_config.api_key:
            registry.register_provider(anthropic_config)

    # Google (Gemini) Configuration
    if primary_provider == "google" or os.getenv("GOOGLE_API_KEY"):
        google_config = ProviderConfig(
            provider=LLMProvider.GOOGLE,
            model=primary_model if primary_provider == "google" else os.getenv("GOOGLE_MODEL", "gemini-1.5-pro"),
            api_key=os.getenv("GOOGLE_API_KEY"),
            temperature=float(os.getenv("GOOGLE_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("GOOGLE_MAX_TOKENS", "4096")),
            cost_per_1k_tokens=float(os.getenv("GOOGLE_COST_PER_1K", "0.0125"))
        )
        if google_config.api_key:
            registry.register_provider(google_config)

    # Ollama (Local Models) Configuration
    if primary_provider == "ollama" or os.getenv("OLLAMA_BASE_URL"):
        ollama_config = ProviderConfig(
            provider=LLMProvider.OLLAMA,
            model=primary_model if primary_provider == "ollama" else os.getenv("OLLAMA_MODEL", "llama3"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
            max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "4096")),
            cost_per_1k_tokens=0.0  # Local models are free
        )
        registry.register_provider(ollama_config)

    if not registry.providers:
        logger.warning("No LLM providers configured. Please set up API keys in .env file.")

    return registry


# Global registry instance
_global_registry: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Get or create the global provider registry"""
    global _global_registry
    if _global_registry is None:
        _global_registry = load_providers_from_env()
    return _global_registry
