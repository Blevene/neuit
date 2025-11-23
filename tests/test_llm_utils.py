"""
Unit tests for Enhanced LLM Utils
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from llm.llm_utils import (
    call_llm_with_prompt,
    get_provider_stats,
    estimate_cost,
    get_registry
)
from llm.provider_config import ProviderConfig, LLMProvider


class TestCallLLMWithPrompt:
    """Tests for call_llm_with_prompt function"""

    @patch('llm.llm_utils.completion')
    @patch('llm.llm_utils.get_registry')
    def test_successful_call(self, mock_get_registry, mock_completion, mock_provider_config):
        """Test successful LLM call"""
        # Setup mock registry
        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = mock_provider_config
        mock_get_registry.return_value = mock_registry

        # Setup mock completion response
        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test response'}}],
            'usage': {'total_tokens': 100}
        }

        response = call_llm_with_prompt("Test prompt")

        assert response == "Test response"
        mock_completion.assert_called_once()
        mock_registry.track_request.assert_called_once_with(100, mock_provider_config)

    @patch('llm.llm_utils.completion')
    @patch('llm.llm_utils.get_registry')
    def test_custom_temperature(self, mock_get_registry, mock_completion, mock_provider_config):
        """Test LLM call with custom temperature"""
        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = mock_provider_config
        mock_get_registry.return_value = mock_registry

        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test'}}],
            'usage': {'total_tokens': 50}
        }

        call_llm_with_prompt("Test", temperature=0.7)

        # Check that temperature was passed correctly
        call_args = mock_completion.call_args
        assert call_args[1]['temperature'] == 0.7

    @patch('llm.llm_utils.completion')
    @patch('llm.llm_utils.get_registry')
    def test_custom_max_tokens(self, mock_get_registry, mock_completion, mock_provider_config):
        """Test LLM call with custom max_tokens"""
        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = mock_provider_config
        mock_get_registry.return_value = mock_registry

        mock_completion.return_value = {
            'choices': [{'message': {'content': 'Test'}}],
            'usage': {'total_tokens': 50}
        }

        call_llm_with_prompt("Test", max_tokens=2000)

        call_args = mock_completion.call_args
        assert call_args[1]['max_tokens'] == 2000

    @patch('llm.llm_utils.completion')
    @patch('llm.llm_utils.get_registry')
    def test_no_provider_configured(self, mock_get_registry, mock_completion):
        """Test LLM call with no provider configured"""
        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = None
        mock_get_registry.return_value = mock_registry

        with pytest.raises(ValueError, match="No LLM providers configured"):
            call_llm_with_prompt("Test")

    @patch('llm.llm_utils.completion')
    @patch('llm.llm_utils.get_registry')
    @patch('llm.llm_utils.time.sleep')  # Mock sleep to speed up tests
    def test_retry_on_failure(self, mock_sleep, mock_get_registry, mock_completion, mock_provider_config):
        """Test retry logic on API failure"""
        mock_registry = MagicMock()
        mock_provider_config.max_retries = 3
        mock_registry.get_primary_provider.return_value = mock_provider_config
        mock_get_registry.return_value = mock_registry

        # First two calls fail, third succeeds
        mock_completion.side_effect = [
            Exception("API Error"),
            Exception("API Error"),
            {'choices': [{'message': {'content': 'Success'}}], 'usage': {'total_tokens': 100}}
        ]

        response = call_llm_with_prompt("Test")

        assert response == "Success"
        assert mock_completion.call_count == 3
        assert mock_sleep.call_count == 2  # Should have slept twice before success

    @patch('llm.llm_utils.completion')
    @patch('llm.llm_utils.get_registry')
    def test_fallback_to_secondary_provider(self, mock_get_registry, mock_completion):
        """Test fallback to secondary provider on failure"""
        # Setup two providers
        provider1 = ProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4", max_retries=1)
        provider2 = ProviderConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-5-sonnet-20241022", max_retries=1)

        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = provider1
        mock_registry.get_next_fallback.side_effect = [provider2, None]
        mock_get_registry.return_value = mock_registry

        # First provider fails, second succeeds
        mock_completion.side_effect = [
            Exception("Provider 1 failed"),
            {'choices': [{'message': {'content': 'Fallback success'}}], 'usage': {'total_tokens': 100}}
        ]

        response = call_llm_with_prompt("Test", use_fallback=True)

        assert response == "Fallback success"
        assert mock_completion.call_count == 2
        mock_registry.get_next_fallback.assert_called()

    @patch('llm.llm_utils.completion')
    @patch('llm.llm_utils.get_registry')
    def test_all_providers_fail(self, mock_get_registry, mock_completion):
        """Test when all providers fail"""
        provider1 = ProviderConfig(provider=LLMProvider.OPENAI, model="gpt-4", max_retries=1)

        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = provider1
        mock_registry.get_next_fallback.return_value = None
        mock_get_registry.return_value = mock_registry

        mock_completion.side_effect = Exception("API Error")

        with pytest.raises(Exception, match="All LLM providers failed"):
            call_llm_with_prompt("Test", use_fallback=True)

    @patch('llm.llm_utils.completion')
    @patch('llm.llm_utils.get_registry')
    def test_fallback_disabled(self, mock_get_registry, mock_completion, mock_provider_config):
        """Test with fallback disabled"""
        mock_registry = MagicMock()
        mock_provider_config.max_retries = 1
        mock_registry.get_primary_provider.return_value = mock_provider_config
        mock_get_registry.return_value = mock_registry

        mock_completion.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            call_llm_with_prompt("Test", use_fallback=False)

        # Should not attempt fallback
        mock_registry.get_next_fallback.assert_not_called()


class TestGetProviderStats:
    """Tests for get_provider_stats function"""

    @patch('llm.llm_utils.get_registry')
    def test_get_stats(self, mock_get_registry):
        """Test getting provider statistics"""
        mock_registry = MagicMock()
        mock_registry.get_stats.return_value = {
            'total_requests': 10,
            'total_cost': 1.50,
            'providers_configured': 2,
            'avg_cost_per_request': 0.15
        }
        mock_get_registry.return_value = mock_registry

        stats = get_provider_stats()

        assert stats['total_requests'] == 10
        assert stats['total_cost'] == 1.50
        assert stats['providers_configured'] == 2
        assert stats['avg_cost_per_request'] == 0.15


class TestEstimateCost:
    """Tests for estimate_cost function"""

    @patch('llm.llm_utils.get_registry')
    def test_estimate_cost(self, mock_get_registry, mock_provider_config):
        """Test estimating cost for text"""
        mock_provider_config.cost_per_1k_tokens = 0.03

        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = mock_provider_config
        mock_get_registry.return_value = mock_registry

        # Test with ~1000 characters (250 tokens approximately)
        text = "a" * 1000
        cost = estimate_cost(text)

        assert cost > 0
        assert cost < 0.03  # Should be less than full 1k tokens

    @patch('llm.llm_utils.get_registry')
    def test_estimate_cost_no_provider(self, mock_get_registry):
        """Test estimating cost with no provider"""
        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = None
        mock_get_registry.return_value = mock_registry

        cost = estimate_cost("test text")

        assert cost == 0.0

    @patch('llm.llm_utils.get_registry')
    def test_estimate_cost_large_text(self, mock_get_registry, mock_provider_config):
        """Test estimating cost for large text"""
        mock_provider_config.cost_per_1k_tokens = 0.03

        mock_registry = MagicMock()
        mock_registry.get_primary_provider.return_value = mock_provider_config
        mock_get_registry.return_value = mock_registry

        # Test with ~10000 characters (2500 tokens approximately)
        text = "a" * 10000
        cost = estimate_cost(text)

        # Should be around 0.075 (2500 / 1000 * 0.03)
        assert 0.05 < cost < 0.10


class TestGetRegistry:
    """Tests for get_registry function"""

    def test_get_registry_singleton(self):
        """Test that registry is a singleton"""
        import llm.llm_utils as llm_utils
        llm_utils._registry = None

        registry1 = get_registry()
        registry2 = get_registry()

        assert registry1 is registry2

    @patch('llm.llm_utils.get_provider_registry')
    def test_get_registry_initialization(self, mock_get_provider_registry):
        """Test registry initialization"""
        import llm.llm_utils as llm_utils
        llm_utils._registry = None

        mock_registry = MagicMock()
        mock_get_provider_registry.return_value = mock_registry

        registry = get_registry()

        assert registry is mock_registry
        mock_get_provider_registry.assert_called_once()
