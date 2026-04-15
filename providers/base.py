"""Abstract base class for LLM providers in NebulaChat.

This module defines the common interface that all LLM providers must implement,
enabling easy extension with new providers (Anthropic, Groq, etc.) while
maintaining a clean separation of concerns.
"""

from abc import ABC, abstractmethod
from typing import Generator, List, Tuple

from config import Settings

Message = dict[str, str]


class ProviderError(RuntimeError):
    """Base exception for provider-specific errors."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BaseProvider(ABC):
    """Abstract base class defining the interface for all LLM providers."""

    def __init__(self, settings: Settings):
        self.settings = settings

    @abstractmethod
    def chat(self, messages: List[Message], model: str, **kwargs) -> Tuple[str, str]:
        """Send a chat request and return (content, model_used).

        Args:
            messages: List of chat messages with role and content
            model: Model identifier to use
            **kwargs: Provider-specific options

        Returns:
            Tuple of (response_content, model_used)

        Raises:
            ProviderError: For provider-specific errors
        """
        pass

    @abstractmethod
    def chat_stream(
        self, messages: List[Message], model: str, **kwargs
    ) -> Generator[Tuple[str, List[Message], List[Message], float], None, None]:
        """Stream a chat request token by token.

        Yields tuples of (accumulated_content, history, history, progress)
        where progress is a float between 0.0 and 1.0.
        """
        pass

    @abstractmethod
    def list_models(self) -> List[str]:
        """Return a list of available models for this provider.

        Returns:
            List of model identifiers. Empty list if listing fails.
        """
        pass


# Provider enum for type safety and consistency
class ProviderEnum:
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"

    ALL = [OLLAMA, OPENROUTER]
