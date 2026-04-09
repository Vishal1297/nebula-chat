"""Centralised constants for NebulaChat.

All environment variable keys, default values, UI strings, and provider identifiers are defined here.
This avoids scattering magic strings across the codebase and makes future refactoring easier.
"""

# Environment variable keys
ENV_KEYS = {
    "OLLAMA_BASE_URL": "OLLAMA_BASE_URL",
    "OLLAMA_API_KEY": "OLLAMA_API_KEY",
    "OPENROUTER_API_KEY": "OPENROUTER_API_KEY",
    "PROVIDER": "PROVIDER",
}

# Default values for environment variables
DEFAULTS = {
    "OLLAMA_BASE_URL": "http://localhost:11434/v1",
    "OLLAMA_API_KEY": "ollama",
    "PROVIDER": "ollama",
}

# UI string constants (centralised for easy localisation)
UI_STRINGS = {
    "ERROR_GENERIC": "An unexpected error occurred. Please try again.",
    "ERROR_PROVIDER": "The selected LLM provider is not configured correctly.",
    "LOADING": "Generating response...",
}

# Provider identifiers – keep in sync with ProviderEnum in providers/base.py
PROVIDERS = {
    "OLLAMA": "ollama",
    "OPENROUTER": "openrouter",
}

# CSS class names used in app.py (optional, for future refactor)
CSS_CLASSES = {
    "MAIN_CONTAINER": "main_container",
    "HEADER": "header",
    "SETTINGS_BAR": "settings_bar",
    "CHATBOT_CONTAINER": "chatbot_container",
    "INPUT_SECTION": "input_section",
}
