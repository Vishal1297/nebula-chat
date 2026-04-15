"""OpenRouter provider implementation for NebulaChat.

This module provides a concrete implementation of ``BaseProvider`` that
handles communication with OpenRouter's API for accessing multiple LLM providers.
"""

from typing import Generator, List

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from .base import BaseProvider, ProviderError
from .utils import build_status_error_message

Message = dict[str, str]


class OpenRouterProvider(BaseProvider):
    """Concrete provider for OpenRouter LLM endpoints.

    This implementation handles both regular chat and streaming modes,
    providing access to multiple LLM providers through a unified interface.
    """

    _BASE_URL = "https://openrouter.ai/api/v1"

    def _create_client(self, api_key: str | None = None) -> OpenAI:
        """Create an OpenAI client configured for OpenRouter.

        Args:
            api_key: Optional override for the OpenRouter API key
        """
        actual_key = api_key or self.settings.openrouter_api_key
        if not actual_key:
            raise ProviderError(
                "OpenRouter API key is required. Enter your key in the settings bar "
                "or set OPENROUTER_API_KEY in your environment."
            )
        return OpenAI(base_url=self._BASE_URL, api_key=actual_key, timeout=30)

    def _validate_model(self, model: str) -> None:
        """Validate that the requested model is non-empty."""
        if not model or not model.strip():
            raise ProviderError("Model identifier must be a non-empty string.")

    def chat(self, messages: List[Message], model: str, **kwargs) -> tuple[str, str]:
        """Send a chat request to OpenRouter and return (content, model_used).

        Args:
            messages: List of messages with ``role`` and ``content`` keys
            model: Model identifier to use for the request
            **kwargs: Additional options (openrouter_api_key to override settings)

        Returns:
            Tuple of (response_content, model_used)

        Raises:
            ProviderError: If the API call fails
        """
        self._validate_model(model)
        api_key = kwargs.get("openrouter_api_key")
        try:
            client = self._create_client(api_key=api_key)
        except ProviderError:
            raise

        try:
            response = client.chat.completions.create(model=model, messages=messages)
        except APIConnectionError as exc:
            raise ProviderError("Failed to reach OpenRouter. Check your internet connection and API key.") from exc
        except APITimeoutError as exc:
            raise ProviderError("Request to OpenRouter timed out. Try again.") from exc
        except APIStatusError as exc:
            raise ProviderError(build_status_error_message(client, model, exc)) from exc
        except Exception as exc:
            raise ProviderError(f"OpenRouter error: {exc}") from exc

        if not response.choices:
            raise ProviderError("No choices returned from OpenRouter API")

        choice = response.choices[0]
        if not choice.message or not choice.message.content:
            raise ProviderError("Empty response from OpenRouter")

        # OpenRouter returns the actual model used in the response
        model_used = getattr(response, "model", model)
        return choice.message.content, model_used

    def chat_stream(
        self, messages: List[Message], model: str, **kwargs
    ) -> Generator[tuple[str, List[Message], List[Message], float], None, None]:
        """Stream a chat response token-by-token from OpenRouter.

        Yields tuples of (accumulated_content, history, history, progress).
        Progress is a float between 0.0 and 1.0 indicating completion.

        Args:
            **kwargs: Additional options (openrouter_api_key to override settings)
        """
        self._validate_model(model)
        api_key = kwargs.get("openrouter_api_key")
        try:
            client = self._create_client(api_key=api_key)
        except ProviderError:
            raise

        base_history = list(messages)
        history = base_history + [{"role": "assistant", "content": ""}]
        acc = ""
        chunks = 0

        try:
            stream = client.chat.completions.create(model=model, messages=messages, stream=True)
        except Exception as exc:
            raise ProviderError(f"OpenRouter streaming error: {exc}") from exc

        try:
            for chunk in stream:
                token = None
                try:
                    if hasattr(chunk, "choices") and chunk.choices:
                        delta = getattr(chunk.choices[0], "delta", None)
                        if delta:
                            token = getattr(delta, "content", None)
                except Exception:
                    pass

                if not token:
                    continue
                acc += token
                history[-1]["content"] = acc
                chunks += 1
                
                # More realistic progress estimation
                # Assume average response length of 100 tokens for a typical response
                estimated_length = 100
                progress = min(1.0, chunks / estimated_length)
                
                yield acc, history, history, progress
        finally:
            # Ensure final yield with complete content
            yield acc, history, history, 1.0

    def list_models(self) -> List[str]:
        """List models available on OpenRouter.

        Returns a list of model identifiers or an empty list if the request fails.
        """
        try:
            client = self._create_client()
            model_list = client.models.list()
            return [getattr(item, "id", None) for item in model_list.data if getattr(item, "id", None)]
        except Exception:
            return []
