import os
from config import load_settings, Settings
from constants import DEFAULTS

from unittest.mock import patch


def test_load_settings_defaults(monkeypatch):
    # Clear env vars to ensure defaults are used
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("PROVIDER", raising=False)

    with patch("config.load_dotenv"):
        settings = load_settings()
        assert settings.ollama_base_url == DEFAULTS["OLLAMA_BASE_URL"]
        assert settings.openrouter_api_key == ""


def test_load_settings_overrides(monkeypatch):
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://test:11434/v1")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    settings = load_settings()
    assert settings.ollama_base_url == "http://test:11434/v1"
    assert settings.openrouter_api_key == "test-key"


def test_settings_validation():
    # Test valid provider
    s = Settings(
        ollama_base_url="url",
        ollama_api_key=None,
        ollama_model="model",
        openrouter_api_key=None,
        openrouter_model="model",
        provider="ollama",
    )
    assert s.provider == "ollama"

    # Test invalid provider should ideally be handled, but current Settings class
    # uses __post_init__ to validate
    import pytest

    with pytest.raises(ValueError, match="Unsupported provider"):
        Settings(
            ollama_base_url="url",
            ollama_api_key=None,
            ollama_model="model",
            openrouter_api_key=None,
            openrouter_model="model",
            provider="invalid",
        )
