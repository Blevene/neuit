"""
Unit tests for LLM Provider Configuration
"""

import pytest
import os
from llm.provider_config import (
    LLMProvider,
    ProviderConfig,
    ProviderRegistry,
    load_providers_from_env
)


class TestProviderConfig:
    """Tests for ProviderConfig dataclass"""

    def test_provider_config_creation(self):
        """Test creating a provider configuration"""
        config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            api_key="test-key",
            temperature=0.2,
            max_tokens=4096,
            cost_per_1k_tokens=0.03
        )

        assert config.provider == LLMProvider.OPENAI
        assert config.model == "gpt-4"
        assert config.api_key == "test-key"
        assert config.temperature == 0.2
        assert config.max_tokens == 4096

    def test_to_litellm_model_openai(self):
        """Test converting OpenAI config to litellm model string"""
        config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4"
        )
        assert config.to_litellm_model() == "gpt-4"

    def test_to_litellm_model_anthropic(self):
        """Test converting Anthropic config to litellm model string"""
        config = ProviderConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-5-sonnet-20241022"
        )
        assert config.to_litellm_model() == "anthropic/claude-3-5-sonnet-20241022"

    def test_to_litellm_model_google(self):
        """Test converting Google config to litellm model string"""
        config = ProviderConfig(
            provider=LLMProvider.GOOGLE,
            model="gemini-1.5-pro"
        )
        assert config.to_litellm_model() == "gemini/gemini-1.5-pro"

    def test_to_litellm_model_ollama(self):
        """Test converting Ollama config to litellm model string"""
        config = ProviderConfig(
            provider=LLMProvider.OLLAMA,
            model="llama3"
        )
        assert config.to_litellm_model() == "ollama/llama3"


class TestProviderRegistry:
    """Tests for ProviderRegistry"""

    def test_register_provider(self):
        """Test registering a provider"""
        registry = ProviderRegistry()
        config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4"
        )

        registry.register_provider(config)
        assert len(registry.providers) == 1
        assert registry.get_primary_provider() == config

    def test_register_multiple_providers(self):
        """Test registering multiple providers"""
        registry = ProviderRegistry()

        openai_config = ProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4")
        claude_config = ProviderConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-5-sonnet-20241022")

        registry.register_provider(openai_config)
        registry.register_provider(claude_config)

        assert len(registry.providers) == 2
        assert registry.get_primary_provider() == openai_config

    def test_fallback_mechanism(self):
        """Test fallback to next provider"""
        registry = ProviderRegistry()

        openai_config = ProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4")
        claude_config = ProviderConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-5-sonnet-20241022")

        registry.register_provider(openai_config)
        registry.register_provider(claude_config)

        # Get fallback
        fallback = registry.get_next_fallback()
        assert fallback == claude_config
        assert registry.current_provider_index == 1

    def test_reset_fallback(self):
        """Test resetting fallback to primary"""
        registry = ProviderRegistry()

        openai_config = ProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4")
        claude_config = ProviderConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-5-sonnet-20241022")

        registry.register_provider(openai_config)
        registry.register_provider(claude_config)

        # Move to fallback
        registry.get_next_fallback()
        assert registry.current_provider_index == 1

        # Reset
        registry.reset_fallback()
        assert registry.current_provider_index == 0

    def test_track_request(self):
        """Test tracking request usage and cost"""
        registry = ProviderRegistry()
        config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            cost_per_1k_tokens=0.03
        )
        registry.register_provider(config)

        # Track a request
        registry.track_request(1000, config)

        assert registry.request_count == 1
        assert registry.total_cost == 0.03

    def test_get_stats(self):
        """Test getting usage statistics"""
        registry = ProviderRegistry()
        config = ProviderConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            cost_per_1k_tokens=0.03
        )
        registry.register_provider(config)

        # Track some requests
        registry.track_request(1000, config)
        registry.track_request(2000, config)

        stats = registry.get_stats()
        assert stats['total_requests'] == 2
        assert stats['total_cost'] == 0.09
        assert stats['providers_configured'] == 1

    def test_no_fallback_available(self):
        """Test when no fallback is available"""
        registry = ProviderRegistry()
        config = ProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4")
        registry.register_provider(config)

        # Try to get fallback
        fallback = registry.get_next_fallback()
        assert fallback is None


class TestLoadProvidersFromEnv:
    """Tests for loading providers from environment variables"""

    def test_load_openai_provider(self, monkeypatch):
        """Test loading OpenAI provider from env"""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_MODEL", "gpt-4")

        registry = load_providers_from_env()

        assert len(registry.providers) == 1
        primary = registry.get_primary_provider()
        assert primary.provider == LLMProvider.OPENAI
        assert primary.model == "gpt-4"
        assert primary.api_key == "test-key"

    def test_load_anthropic_provider(self, monkeypatch):
        """Test loading Anthropic provider from env"""
        # Clear OpenAI key to ensure Anthropic is primary
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "anthropic")
        monkeypatch.setenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")

        registry = load_providers_from_env()

        assert len(registry.providers) >= 1
        primary = registry.get_primary_provider()
        assert primary.provider == LLMProvider.ANTHROPIC
        assert primary.model == "claude-3-5-sonnet-20241022"

        # Verify Anthropic provider is in the list
        anthropic_providers = [p for p in registry.providers if p.provider == LLMProvider.ANTHROPIC]
        assert len(anthropic_providers) == 1
        assert anthropic_providers[0].model == "claude-3-5-sonnet-20241022"

    def test_load_multiple_providers(self, monkeypatch):
        """Test loading multiple providers from env"""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "anthropic-key")

        registry = load_providers_from_env()

        # Should have both providers registered
        assert len(registry.providers) >= 2

    def test_no_providers_configured(self, monkeypatch):
        """Test when no providers are configured"""
        # Clear all API keys
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "openai")

        registry = load_providers_from_env()

        # Should have no providers
        assert len(registry.providers) == 0

    def test_load_with_custom_temperature(self, monkeypatch):
        """Test loading with custom temperature"""
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")
        monkeypatch.setenv("OPENAI_TEMPERATURE", "0.7")

        registry = load_providers_from_env()

        primary = registry.get_primary_provider()
        assert primary.temperature == 0.7

    def test_load_ollama_provider(self, monkeypatch):
        """Test loading Ollama provider from env"""
        # Clear OpenAI key to ensure Ollama is primary
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("LLM_PROVIDER", "ollama")
        monkeypatch.setenv("LLM_MODEL", "llama3")
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
        monkeypatch.setenv("OLLAMA_MODEL", "llama3")

        registry = load_providers_from_env()

        assert len(registry.providers) >= 1
        primary = registry.get_primary_provider()
        assert primary.provider == LLMProvider.OLLAMA
        assert primary.model == "llama3"
        assert primary.base_url == "http://localhost:11434"
        assert primary.cost_per_1k_tokens == 0.0  # Local models are free

        # Verify Ollama provider is in the list
        ollama_providers = [p for p in registry.providers if p.provider == LLMProvider.OLLAMA]
        assert len(ollama_providers) == 1
        assert ollama_providers[0].model == "llama3"
