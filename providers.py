from typing import Dict, Generator, List

from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

from config import Settings

Message = Dict[str, str]


def _safe_list_models(client: OpenAI) -> List[str]:
    try:
        model_list = client.models.list()
        return [item.id for item in model_list.data if getattr(item, "id", None)]
    except Exception:
        return []


def _extract_status_error_text(exc: APIStatusError) -> str:
    if getattr(exc, "response", None) is None:
        return str(exc)
    try:
        return str(exc.response.text)
    except Exception:
        return str(exc.response)


def _build_status_error_message(client: OpenAI, model: str, exc: APIStatusError) -> str:
    available_models = _safe_list_models(client)
    if available_models and model not in available_models:
        preview = ", ".join(available_models[:5])
        suffix = " ..." if len(available_models) > 5 else ""
        return f"Configured model '{model}' is not available on this Ollama server. Available models: {preview}{suffix}"

    status_code = getattr(exc, "status_code", "unknown")
    response_text = _extract_status_error_text(exc)
    return f"Ollama API error ({status_code}): {response_text or str(exc)}"


def chat_with_ollama(
    messages: List[Message], model: str, settings: Settings, ollama_base_url: str | None = None
) -> str:
    base_url = ollama_base_url or settings.ollama_base_url
    key = (settings.ollama_api_key or "").strip()
    # Bind a proper OpenAI client with base_url and api_key
    client = OpenAI(
        base_url=base_url,
        api_key=("" if key.lower() == "ollama" else key),
    )
    try:
        response = client.chat.completions.create(model=model, messages=messages)
    except Exception as exc:
        raise RuntimeError(f"Ollama API error: {exc}") from exc

    content = ""
    try:
        if response and hasattr(response, "choices") and response.choices:
            choice = response.choices[0]
            if hasattr(choice, "message") and choice.message:
                content = choice.message.content or ""
    except Exception:
        pass

    if not content:
        raise RuntimeError("Ollama returned an empty response.")
    return content


def chat_with_ollama_stream(
    messages: List[Message], model: str, settings: Settings, ollama_base_url: str | None = None
) -> "Generator[tuple[str, List[Message], List[Message], float], None, None]":
    base_url = ollama_base_url or settings.ollama_base_url
    key = (settings.ollama_api_key or "").strip()
    api_key = "" if key.lower() == "ollama" else key
    client = OpenAI(base_url=base_url, api_key=api_key)
    # Streaming via OpenAI client
    try:
        response = client.chat.completions.create(model=model, messages=messages, stream=True)
    except Exception as exc:
        raise RuntimeError(f"Ollama streaming error: {exc}") from exc

    acc = ""
    chunks = 0
    base_history = list(messages)
    history = base_history + [{"role": "assistant", "content": ""}]

    for chunk in response:
        token = ""
        try:
            if hasattr(chunk, "choices") and chunk.choices:
                choice = chunk.choices[0]
                if hasattr(choice, "delta") and choice.delta and hasattr(choice.delta, "content"):
                    token = choice.delta.content or ""
        except Exception:
            pass

        if not token:
            continue
        acc += token
        history[-1]["content"] = acc
        chunks += 1
        prog = min(1.0, chunks / 20.0)
        yield acc, history, history, prog


def chat_with_openrouter(
    messages: List[Message],
    model: str,
    settings: Settings,
    openrouter_api_key: str | None = None,
) -> tuple[str, str]:
    """
    Chat with OpenRouter and return both the response and the actual model used.

    Returns:
        tuple[str, str]: (response_content, model_used)
    """
    api_key = openrouter_api_key or settings.openrouter_api_key
    if not api_key:
        raise RuntimeError(
            "OpenRouter API key is required. Enter your key in the settings bar "
            "or set OPENROUTER_API_KEY in your environment."
        )
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
    except APIConnectionError as exc:
        raise RuntimeError("Failed to reach OpenRouter. Check your internet connection and API key.") from exc
    except APITimeoutError as exc:
        raise RuntimeError("Request to OpenRouter timed out. Try again.") from exc
    except APIStatusError as exc:
        raise RuntimeError(_build_status_error_message(client, model, exc)) from exc
    except Exception as exc:
        raise RuntimeError(f"Unexpected OpenRouter error: {exc}") from exc

    content = response.choices[0].message.content if response.choices else ""
    if not content:
        raise RuntimeError("OpenRouter returned an empty response.")

    # OpenRouter returns the actual model used in the response
    model_used = getattr(response, "model", model)
    return content, model_used


def chat_with_openrouter_stream(
    messages: List[Message],
    model: str,
    settings: Settings,
    openrouter_api_key: str | None = None,
) -> "Generator[tuple[str, List[Message], List[Message], float], None, None]":
    """Streaming OpenRouter responses as tokens arrive."""
    api_key = openrouter_api_key or settings.openrouter_api_key
    if not api_key:
        # If streaming is requested but no key is provided, fall back to non-streaming path later
        raise RuntimeError("OpenRouter API key is required for streaming.")
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

    # Try streaming first
    try:
        stream = client.chat.completions.stream(model=model, messages=messages)
    except Exception:
        stream = None

    base_history = list(messages)
    history = base_history + [{"role": "assistant", "content": ""}]
    acc = ""
    chunks = 0

    if stream is not None:
        for chunk in stream:
            token = None
            try:
                token = getattr(chunk.choices[0].delta, "content", None)
            except Exception:
                token = None
            if not token:
                continue
            acc += token
            history[-1]["content"] = acc
            chunks += 1
            prog = min(1.0, chunks / 20.0)
            yield acc, history, history, prog
        return

    # Fallback to non-streaming if streaming isn't available
    content, model_used = chat_with_openrouter(
        messages=messages,
        model=model,
        settings=settings,
        openrouter_api_key=api_key,
    )
    history[-1]["content"] = content
    yield content, history, history, 1.0


def chat(
    _provider: str,
    messages: List[Message],
    model: str,
    settings: Settings,
    openrouter_api_key: str | None = None,
    ollama_base_url: str | None = None,
) -> tuple[str, str]:
    """
    Chat with a provider and return both the response and the model used.

    Returns:
        tuple[str, str]: (response_content, model_used)
    """
    provider = (_provider or "").strip().lower()
    if provider == "ollama":
        content = chat_with_ollama(messages=messages, model=model, settings=settings, ollama_base_url=ollama_base_url)
        return content, model
    elif provider == "openrouter":
        return chat_with_openrouter(
            messages=messages, model=model, settings=settings, openrouter_api_key=openrouter_api_key
        )
    raise ValueError(f"Unsupported provider: {_provider}")


def list_models_for_provider(settings: Settings, provider: str) -> List[str]:
    """Return a list of available models for the given provider.

    This function is a light-weight, safe helper to populate UI dropdowns.
    It gracefully returns an empty list if listing is not supported or fails.
    """
    p = (provider or "").strip().lower()
    if p == "ollama":
        client = OpenAI(base_url=settings.ollama_base_url, api_key=settings.ollama_api_key)
    elif p == "openrouter":
        client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.openrouter_api_key)
    else:
        return []

    try:
        model_list = client.models.list()
        return [getattr(item, "id", None) for item in model_list.data if getattr(item, "id", None)]
    except Exception:
        return []
