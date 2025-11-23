"""
Pytest configuration and shared fixtures for NEUIToolkit tests
"""

import pytest
import os
import json
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, MagicMock


@pytest.fixture
def sample_entities() -> List[Dict[str, Any]]:
    """Sample entity data for testing"""
    return [
        {
            "name": "Mitochondria",
            "aliases": ["Powerhouse of the cell"],
            "category": "Organelle"
        },
        {
            "name": "Cell Membrane",
            "aliases": ["Plasma membrane"],
            "category": "Structure"
        },
        {
            "name": "Nucleus",
            "aliases": ["Cell nucleus"],
            "category": "Organelle"
        }
    ]


@pytest.fixture
def sample_relationships() -> List[Dict[str, Any]]:
    """Sample relationship data for testing"""
    return [
        {
            "subject": "Mitochondria",
            "predicate": "produces",
            "object": "ATP",
            "justification": "Mitochondria produce ATP through cellular respiration."
        },
        {
            "subject": "Cell Membrane",
            "predicate": "protects",
            "object": "Cell",
            "justification": "The cell membrane protects the cell from external environment."
        }
    ]


@pytest.fixture
def sample_rules() -> List[Dict[str, Any]]:
    """Sample rule data for testing"""
    return [
        {
            "id": 1,
            "if": "Cell needs energy",
            "then": "Mitochondria produces ATP",
            "confidence": 0.95
        },
        {
            "id": 2,
            "if": "External substance approaches cell",
            "then": "Cell membrane regulates entry",
            "confidence": 0.90
        }
    ]


@pytest.fixture
def low_quality_entities() -> List[Dict[str, Any]]:
    """Sample low-quality entity data for testing"""
    return [
        {
            "name": "A",  # Too short
            "aliases": [],
            "category": "Unknown"
        },
        {
            "name": "",  # Empty
            "aliases": ["test"],
            "category": "Invalid"
        },
        {
            "name": "ALLCAPS",  # All caps warning
            "aliases": [],
            "category": "Test"
        }
    ]


@pytest.fixture
def low_quality_relationships() -> List[Dict[str, Any]]:
    """Sample low-quality relationship data for testing"""
    return [
        {
            "subject": "Entity1",
            "predicate": "relates to",  # Vague predicate
            "object": "Entity2",
            "justification": "short"  # Too short
        },
        {
            "subject": "",  # Missing subject
            "predicate": "test",
            "object": "Entity3",
            "justification": "This is a test"
        },
        {
            "subject": "SelfRef",
            "predicate": "is",
            "object": "SelfRef",  # Self-referential
            "justification": "Self referential relationship"
        }
    ]


@pytest.fixture
def mock_llm_response() -> str:
    """Mock LLM response for testing"""
    return json.dumps([
        {"name": "Test Entity", "aliases": ["TE"], "category": "Test"}
    ])


@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver for testing"""
    mock_driver = MagicMock()
    mock_session = MagicMock()
    mock_result = MagicMock()

    # Configure mock behavior
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.run.return_value = mock_result
    mock_result.__iter__.return_value = []

    return mock_driver


@pytest.fixture
def mock_provider_config():
    """Mock provider configuration for testing"""
    from llm.provider_config import ProviderConfig, LLMProvider

    return ProviderConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4",
        api_key="test-key",
        temperature=0.2,
        max_tokens=4096,
        cost_per_1k_tokens=0.03
    )


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary output directory for testing"""
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_text_file(tmp_path):
    """Create a sample text file for testing"""
    file_path = tmp_path / "sample.txt"
    file_path.write_text("""
    The mitochondria is the powerhouse of the cell.
    It produces ATP through cellular respiration.
    The cell membrane protects the cell.
    """)
    return file_path


@pytest.fixture
def set_test_env_vars(monkeypatch):
    """Set test environment variables"""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.setenv("LLM_MODEL", "gpt-4")
    monkeypatch.setenv("ENABLE_QA", "true")
    monkeypatch.setenv("QA_MIN_CONFIDENCE", "0.5")
    monkeypatch.setenv("ENABLE_NEO4J", "false")


@pytest.fixture(autouse=True)
def reset_llm_registry():
    """Reset LLM registry between tests"""
    import llm.llm_utils as llm_utils
    llm_utils._registry = None
    yield
    llm_utils._registry = None


@pytest.fixture
def mock_completion_success():
    """Mock successful LiteLLM completion"""
    return {
        'choices': [
            {
                'message': {
                    'content': '{"test": "response"}'
                }
            }
        ],
        'usage': {
            'total_tokens': 100
        }
    }


@pytest.fixture
def mock_completion_failure():
    """Mock failed LiteLLM completion"""
    def raise_error(*args, **kwargs):
        raise Exception("API Error")
    return raise_error
