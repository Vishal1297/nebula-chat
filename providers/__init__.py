"""LLM Providers package for NebulaChat.

This package provides an abstraction layer for multiple LLM providers,
including Ollama and OpenRouter. Each provider implements a common interface
defined by BaseProvider.

Main exports:
- chat(): Route a chat request to the appropriate provider
- chat_stream(): Stream a chat response from the appropriate provider
- list_models_for_provider(): Get available models for a provider
- BaseProvider: Abstract base class for provider implementations
- OllamaProvider: Ollama implementation
- OpenRouterProvider: OpenRouter implementation
- ProviderEnum: Provider name constants
- ProviderError: Exception for provider-specific errors
"""

from typing import Generator, List, Tuple

from config import Settings

from .base import BaseProvider, ProviderEnum, ProviderError
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider

Message = dict[str, str]


def _get_provider(provider_name: str, settings: Settings) -> BaseProvider:
    """Get a provider instance for the given provider name.

    Args:
        provider_name: Name of the provider (ollama, openrouter)
        settings: Application settings

    Returns:
        Provider instance

    Raises:
        ValueError: If provider is not supported
    """
    p = (provider_name or "").strip().lower()
    if p == ProviderEnum.OLLAMA:
        return OllamaProvider(settings)
    elif p == ProviderEnum.OPENROUTER:
        return OpenRouterProvider(settings)
    raise ValueError(f"Unsupported provider: {provider_name}")


def chat(
    _provider: str,
    messages: List[Message],
    model: str,
    settings: Settings,
    openrouter_api_key: str | None = None,
    ollama_base_url: str | None = None,
) -> tuple[str, str]:
    """Route chat request to the appropriate provider.

    Args:
        _provider: Name of the provider (ollama, openrouter)
        messages: List of chat messages
        model: Model identifier to use
        settings: Application settings
        openrouter_api_key: Optional OpenRouter API key override
        ollama_base_url: Optional Ollama base URL override

    Returns:
        Tuple of (response_content, model_used)

    Raises:
        ValueError: If provider is not supported
        RuntimeError: If the provider operation fails
    """
    try:
        provider = _get_provider(_provider, settings)
        # Build kwargs for provider-specific overrides
        kwargs = {}
        if openrouter_api_key:
            kwargs["openrouter_api_key"] = openrouter_api_key
        if ollama_base_url:
            kwargs["ollama_base_url"] = ollama_base_url
        return provider.chat(messages, model, **kwargs)
    except ProviderError as e:
        raise RuntimeError(str(e)) from e
    except Exception as e:
        raise RuntimeError(f"Provider error: {e}") from e


def chat_stream(
    _provider: str,
    messages: List[Message],
    model: str,
    settings: Settings,
    openrouter_api_key: str | None = None,
    ollama_base_url: str | None = None,
) -> Generator[Tuple[str, List[Message], List[Message], float], None, None]:
    """Stream chat response from the appropriate provider.

    Args:
        _provider: Name of the provider (ollama, openrouter)
        messages: List of chat messages
        model: Model identifier to use
        settings: Application settings
        openrouter_api_key: Optional OpenRouter API key override
        ollama_base_url: Optional Ollama base URL override

    Yields:
        Tuples of (accumulated_content, history, history, progress).

    Raises:
        ValueError: If provider is not supported
        RuntimeError: If the provider operation fails
    """
    try:
        provider = _get_provider(_provider, settings)
        # Build kwargs for provider-specific overrides
        kwargs = {}
        if openrouter_api_key:
            kwargs["openrouter_api_key"] = openrouter_api_key
        if ollama_base_url:
            kwargs["ollama_base_url"] = ollama_base_url
        yield from provider.chat_stream(messages, model, **kwargs)
    except ProviderError as e:
        raise RuntimeError(str(e)) from e
    except Exception as e:
        raise RuntimeError(f"Provider error: {e}") from e


from functools import lru_cache
from typing import Generator, List, Tuple

from config import Settings

from .base import BaseProvider, ProviderEnum, ProviderError
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider

Message = dict[str, str]


def _get_provider(provider_name: str, settings: Settings) -> BaseProvider:
    """Get a provider instance for the given provider name.

    Args:
        provider_name: Name of the provider (ollama, openrouter)
        settings: Application settings

    Returns:
        Provider instance

    Raises:
        ValueError: If provider is not supported
    """
    p = (provider_name or "").strip().lower()
    if p == ProviderEnum.OLLAMA:
        return OllamaProvider(settings)
    elif p == ProviderEnum.OPENROUTER:
        return OpenRouterProvider(settings)
    raise ValueError(f"Unsupported provider: {provider_name}")


def chat(
    _provider: str,
    messages: List[Message],
    model: str,
    settings: Settings,
    openrouter_api_key: str | None = None,
    ollama_base_url: str | None = None,
) -> tuple[str, str]:
    """Route chat request to the appropriate provider.

    Args:
        _provider: Name of the provider (ollama, openrouter)
        messages: List of chat messages
        model: Model identifier to use
        settings: Application settings
        openrouter_api_key: Optional OpenRouter API key override
        ollama_base_url: Optional Ollama base URL override

    Returns:
        Tuple of (response_content, model_used)

    Raises:
        ValueError: If provider is not supported
        RuntimeError: If the provider operation fails
    """
    try:
        provider = _get_provider(_provider, settings)
        # Build kwargs for provider-specific overrides
        kwargs = {}
        if openrouter_api_key:
            kwargs["openrouter_api_key"] = openrouter_api_key
        if ollama_base_url:
            kwargs["ollama_base_url"] = ollama_base_url
        return provider.chat(messages, model, **kwargs)
    except ProviderError as e:
        raise RuntimeError(str(e)) from e
    except Exception as e:
        raise RuntimeError(f"Provider error: {e}") from e


def chat_stream(
    _provider: str,
    messages: List[Message],
    model: str,
    settings: Settings,
    openrouter_api_key: str | None = None,
    ollama_base_url: str | None = None,
) -> Generator[Tuple[str, List[Message], List[Message], float], None, None]:
    """Stream chat response from the appropriate provider.

    Args:
        _provider: Name of the provider (ollama, openrouter)
        messages: List of chat messages
        model: Model identifier to use
        settings: Application settings
        openrouter_api_key: Optional OpenRouter API key override
        ollama_base_url: Optional Ollama base URL override

    Yields:
        Tuples of (accumulated_content, history, history, progress).

    Raises:
        ValueError: If provider is not supported
        RuntimeError: If the provider operation fails
    """
    try:
        provider = _get_provider(_provider, settings)
        # Build kwargs for provider-specific overrides
        kwargs = {}
        if openrouter_api_key:
            kwargs["openrouter_api_key"] = openrouter_api_key
        if ollama_base_url:
            kwargs["ollama_base_url"] = ollama_base_url
        yield from provider.chat_stream(messages, model, **kwargs)
    except ProviderError as e:
        raise RuntimeError(str(e)) from e
    except Exception as e:
        raise RuntimeError(f"Provider error: {e}") from e


@lru_cache(maxsize=16)
def _list_models_cached(provider_name: str, ollama_url: str, openrouter_key: str) -> List[str]:
    """Internal helper for cached model listing."""
    # We re-import load_settings to avoid circular dependencies if needed,
    # but since it's already imported at top level of config, we use a mock-like approach
    # In a real app, you might pass a hashable version of settings
    from config import load_settings

    settings = load_settings()
    try:
        provider = _get_provider(provider_name, settings)
        return provider.list_models()
    except Exception:
        return []


def list_models_for_provider(settings: Settings, provider_name: str) -> List[str]:
    """Return available models for the given provider with caching.

    This is a lightweight, safe helper to populate UI dropdowns.
    Returns an empty list if listing is not supported or fails.
    """
    # Use config values as cache keys
    return _list_models_cached(provider_name, settings.ollama_base_url, settings.openrouter_api_key or "")


# Backward compatibility wrappers for app.py
def chat_with_ollama_stream(
    messages: List[Message],
    model: str,
    settings: Settings,
    ollama_base_url: str | None = None,
) -> Generator[Tuple[str, List[Message], List[Message], float], None, None]:
    """Stream a chat response from Ollama.

    Args:
        messages: List of chat messages
        model: Model identifier to use
        settings: Application settings
        ollama_base_url: Optional Ollama base URL override

    Yields:
        Tuples of (accumulated_content, history, history, progress).
    """
    return chat_stream("ollama", messages, model, settings, ollama_base_url=ollama_base_url)


def chat_with_openrouter_stream(
    messages: List[Message],
    model: str,
    settings: Settings,
    openrouter_api_key: str | None = None,
) -> Generator[Tuple[str, List[Message], List[Message], float], None, None]:
    """Stream a chat response from OpenRouter.

    Args:
        messages: List of chat messages
        model: Model identifier to use
        settings: Application settings
        openrouter_api_key: Optional OpenRouter API key override

    Yields:
        Tuples of (accumulated_content, history, history, progress).
    """
    return chat_stream("openrouter", messages, model, settings, openrouter_api_key=openrouter_api_key)


__all__ = [
    "chat",
    "chat_stream",
    "chat_with_ollama_stream",
    "chat_with_openrouter_stream",
    "list_models_for_provider",
    "BaseProvider",
    "OllamaProvider",
    "OpenRouterProvider",
    "ProviderEnum",
    "ProviderError",
]
