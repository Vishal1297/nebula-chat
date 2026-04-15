import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Centralised constants
from constants import DEFAULTS, ENV_KEYS, PROVIDERS


@dataclass(frozen=True)
class Settings:
    """Immutable configuration loaded from environment variables.

    The values are validated on creation; missing required keys raise a clear ``ValueError``.
    """

    ollama_base_url: str
    ollama_api_key: str | None
    ollama_model: str
    openrouter_api_key: str | None
    openrouter_model: str
    provider: str

    def __post_init__(self):
        # Basic validation – ensure provider is known
        if self.provider not in PROVIDERS.values():
            raise ValueError(f"Unsupported provider '{self.provider}'. Expected one of {list(PROVIDERS.values())}.")
        # Note: We don't validate API keys here as they can be provided at runtime via UI
        # Each provider will validate its own requirements when used


def load_settings() -> Settings:
    """Load settings from ``.env`` and environment variables.

    Uses centralised ``ENV_KEYS`` and ``DEFAULTS`` for consistency.
    """
    load_dotenv()
    return Settings(
        ollama_base_url=os.getenv(ENV_KEYS["OLLAMA_BASE_URL"], DEFAULTS["OLLAMA_BASE_URL"]).strip(),
        ollama_api_key=os.getenv(ENV_KEYS["OLLAMA_API_KEY"]),
        ollama_model=os.getenv(ENV_KEYS.get("OLLAMA_MODEL", "OLLAMA_MODEL"), "").strip(),
        openrouter_api_key=os.getenv(ENV_KEYS["OPENROUTER_API_KEY"], "").strip(),
        openrouter_model=os.getenv(
            ENV_KEYS.get("OPENROUTER_MODEL", "OPENROUTER_MODEL"), DEFAULTS.get("OPENROUTER_MODEL", "openrouter/free")
        ).strip(),
        provider=os.getenv(ENV_KEYS.get("PROVIDER", "PROVIDER"), DEFAULTS.get("PROVIDER", "ollama")).strip().lower(),
    )
