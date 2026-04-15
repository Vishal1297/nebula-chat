"""Ollama provider implementation for NebulaChat.

This module provides a concrete implementation of ``BaseProvider`` that
handles communication with an Ollama server. It focuses on:

1. Proper API client creation with base URL and API key handling
2. Chat and streaming responses with progress tracking
3. Model listing capability
4. Consistent error handling and translation
5. Type safety throughout the provider interface
"""

from typing import Generator, List

from openai import OpenAI

from .base import BaseProvider, ProviderError

Message = dict[str, str]


class OllamaProvider(BaseProvider):
    """Concrete provider for Ollama LLM endpoints.

    This implementation handles both regular chat and streaming modes,
    providing robust error handling and progress reporting.
    """

    def _create_client(self, base_url: str | None = None) -> OpenAI:
        """Create an OpenAI client configured for Ollama.

        Args:
            base_url: Optional override for the Ollama base URL
        """
        actual_url = base_url or self.settings.ollama_base_url
        api_key = (self.settings.ollama_api_key or "").strip()
        api_key = "" if api_key.lower() == "ollama" else api_key
        return OpenAI(base_url=actual_url, api_key=api_key, timeout=30)

    def _validate_model(self, model: str) -> None:
        """Validate that the requested model appears to be non‑empty."""
        if not model or not model.strip():
            raise ProviderError("Model identifier must be a non‑empty string.")

    def chat(self, messages: List[Message], model: str, **kwargs) -> tuple[str, str]:
        """Send a chat request to Ollama and return (content, model_used).

        Args:
            messages: List of messages with ``role`` and ``content`` keys
            model: Model identifier to use for the request
            **kwargs: Additional options (ollama_base_url to override settings)

        Returns:
            Tuple of (response_content, model_used)

        Raises:
            ProviderError: If the API call fails or returns an error response
        """
        self._validate_model(model)
        base_url = kwargs.get("ollama_base_url")
        try:
            client = self._create_client(base_url=base_url)
            response = client.chat.completions.create(model=model, messages=messages)
        except Exception as exc:
            raise ProviderError(f"Ollama API error: {exc}") from exc

        if not response.choices:
            raise ProviderError("No choices returned from Ollama API")

        choice = response.choices[0]
        if not choice.message or not choice.message.content:
            raise ProviderError("Empty response from Ollama")

        return choice.message.content, model

    def chat_stream(
        self, messages: List[Message], model: str, **kwargs
    ) -> Generator[tuple[str, List[Message], List[Message], float], None, None]:
        """Stream a chat response token‑by‑token from Ollama.

        Yields tuples of (accumulated_content, history, history, progress).
        Progress is a float between 0.0 and 1.0 indicating completion.

        Args:
            **kwargs: Additional options (ollama_base_url to override settings)
        """
        self._validate_model(model)
        base_url = kwargs.get("ollama_base_url")
        base_history = list(messages)
        history = base_history + [{"role": "assistant", "content": ""}]
        acc = ""

        try:
            client = self._create_client(base_url=base_url)
            stream = client.chat.completions.create(model=model, messages=messages, stream=True)
        except Exception as exc:
            raise ProviderError(f"Ollama streaming error: {exc}") from exc

        try:
            for chunk in stream:
                delta = None
                try:
                    delta = getattr(chunk.choices[0], "delta", None)
                except Exception:
                    pass
                token = delta.get("content") if delta else None
                if not token:
                    continue
                acc += token
                history[-1]["content"] = acc
                
                # More realistic progress estimation
                # Assume average response length of 100 tokens for a typical response
                estimated_length = 100
                progress = min(1.0, len(acc) / estimated_length)
                
                yield acc, history, history, progress
        finally:
            # Ensure the generator always terminates
            progress = 1.0
            yield acc, history, history, progress

    def list_models(self) -> List[str]:
        """List models available on the Ollama server.

        Returns a list of model identifiers or an empty list if the request fails.
        """
        try:
            client = self._create_client()
            model_list = client.models.list()
            return [getattr(item, "id", None) for item in model_list.data if getattr(item, "id", None)]
        except Exception:
            return []
