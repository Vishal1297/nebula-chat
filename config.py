import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    ollama_base_url: str
    ollama_api_key: str | None
    ollama_model: str
    openrouter_api_key: str
    openrouter_model: str


def load_settings() -> Settings:
    load_dotenv()
    return Settings(
        # Default to local Ollama's OpenAI-compatible endpoint
        ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1").strip(),
        # Ollama API key is optional; do not provide a default so we don't send a dummy key
        ollama_api_key=os.getenv("OLLAMA_API_KEY"),
        ollama_model=os.getenv("OLLAMA_MODEL", "").strip(),
        # OpenRouter configuration
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
        openrouter_model=os.getenv("OPENROUTER_MODEL", "openrouter/free").strip(),
    )
