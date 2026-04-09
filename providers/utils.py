"""Utility functions for LLM providers in NebulaChat.

This module contains helper functions shared across multiple providers.
"""

from typing import List

from openai import APIStatusError, OpenAI

Message = dict[str, str]


def safe_list_models(client: OpenAI) -> List[str]:
    """Safely list available models from an OpenAI-compatible client.

    Returns an empty list if the request fails.
    """
    try:
        model_list = client.models.list()
        return [item.id for item in model_list.data if getattr(item, "id", None)]
    except Exception:
        return []


def extract_status_error_text(exc: APIStatusError) -> str:
    """Extract human-readable text from an APIStatusError."""
    if getattr(exc, "response", None) is None:
        return str(exc)
    try:
        return str(exc.response.text)
    except Exception:
        return str(exc.response)


def build_status_error_message(client: OpenAI, model: str, exc: APIStatusError) -> str:
    """Build a user-friendly error message for API status errors.

    Checks available models and provides suggestions if the configured model is unavailable.
    """
    available_models = safe_list_models(client)
    if available_models and model not in available_models:
        preview = ", ".join(available_models[:5])
        suffix = " ..." if len(available_models) > 5 else ""
        return f"Configured model '{model}' is not available. Available models: {preview}{suffix}"

    status_code = getattr(exc, "status_code", "unknown")
    response_text = extract_status_error_text(exc)
    return f"API error ({status_code}): {response_text or str(exc)}"
