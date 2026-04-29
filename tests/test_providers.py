import pytest
from unittest.mock import MagicMock, patch
from providers.ollama import OllamaProvider
from providers.openrouter import OpenRouterProvider
from providers.base import ProviderError
from config import Settings


@pytest.fixture
def mock_settings():
    return Settings(
        ollama_base_url="http://localhost:11434/v1",
        ollama_api_key=None,
        ollama_model="llama3",
        openrouter_api_key="sk-test",
        openrouter_model="openai/gpt-3.5-turbo",
        provider="ollama",
    )


def test_ollama_provider_chat(mock_settings):
    provider = OllamaProvider(mock_settings)

    with patch("providers.ollama.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello from Ollama"))]
        mock_client.chat.completions.create.return_value = mock_response

        content, model = provider.chat([{"role": "user", "content": "hi"}], "llama3")

        assert content == "Hello from Ollama"
        assert model == "llama3"
        mock_client.chat.completions.create.assert_called_once()


def test_openrouter_provider_chat(mock_settings):
    provider = OpenRouterProvider(mock_settings)

    with patch("providers.openrouter.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Hello from OpenRouter"))]
        mock_response.model = "anthropic/claude-3-opus"
        mock_client.chat.completions.create.return_value = mock_response

        content, model = provider.chat([{"role": "user", "content": "hi"}], "anthropic/claude-3")

        assert content == "Hello from OpenRouter"
        assert model == "anthropic/claude-3-opus"


def test_ollama_provider_chat_stream(mock_settings):
    provider = OllamaProvider(mock_settings)

    with patch("providers.ollama.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock streaming chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock(delta=MagicMock(content="Hello"))]
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock(delta=MagicMock(content=" world"))]

        mock_client.chat.completions.create.return_value = [mock_chunk1, mock_chunk2]

        stream = provider.chat_stream([{"role": "user", "content": "hi"}], "llama3")
        results = list(stream)

        assert results[-1][0] == "Hello world"
        assert results[-1][1][-1]["content"] == "Hello world"


def test_openrouter_provider_chat_stream(mock_settings):
    provider = OpenRouterProvider(mock_settings)

    with patch("providers.openrouter.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        # Mock streaming chunks
        mock_chunk1 = MagicMock()
        mock_chunk1.choices = [MagicMock(delta=MagicMock(content="Hi"))]
        mock_chunk2 = MagicMock()
        mock_chunk2.choices = [MagicMock(delta=MagicMock(content=" there"))]

        mock_client.chat.completions.create.return_value = [mock_chunk1, mock_chunk2]

        stream = provider.chat_stream([{"role": "user", "content": "hi"}], "gpt-3.5")
        results = list(stream)

        assert results[-1][0] == "Hi there"
        assert results[-1][1][-1]["content"] == "Hi there"


def test_provider_validation_error(mock_settings):
    provider = OllamaProvider(mock_settings)
    with pytest.raises(ProviderError, match="Model identifier must be a non‑empty string"):
        provider.chat([{"role": "user", "content": "hi"}], "")
