import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Environment variable keys
OLLAMA_BASE_URL_KEY = "OLLAMA_BASE_URL"
OLLAMA_API_KEY_KEY = "OLLAMA_API_KEY"
OLLAMA_MODEL_KEY = "OLLAMA_MODEL"
OPENROUTER_API_KEY_KEY = "OPENROUTER_API_KEY"
OPENROUTER_MODEL_KEY = "OPENROUTER_MODEL"

# Default values
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_OPENROUTER_MODEL = "openrouter/free"


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
        ollama_base_url=os.getenv(OLLAMA_BASE_URL_KEY, DEFAULT_OLLAMA_BASE_URL).strip(),
        ollama_api_key=os.getenv(OLLAMA_API_KEY_KEY),
        ollama_model=os.getenv(OLLAMA_MODEL_KEY, "").strip(),
        openrouter_api_key=os.getenv(OPENROUTER_API_KEY_KEY, "").strip(),
        openrouter_model=os.getenv(OPENROUTER_MODEL_KEY, DEFAULT_OPENROUTER_MODEL).strip(),
    )
