# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gradio-based web chat interface for Ollama models using OpenAI-compatible APIs.

## Commands

```bash
# Install dependencies
uv sync              # Install main + dev dependencies
uv sync --no-dev     # Install main dependencies only

# Run the app
uv run python app.py

# Lint
uv run black .
uv run ruff check .

# Test
uv run pytest
```

## Architecture

Three-layer structure:

1. **UI Layer** (`app.py`): Gradio components, event handlers, state management via `gr.State([])`
2. **Provider Layer** (`providers.py`): LLM provider abstraction with three-tier error handling (connection, timeout, status errors)
3. **Configuration Layer** (`config.py`): Immutable `Settings` dataclass with `.env` fallbacks

### Message Format

All internal communication uses:
```python
Message = Dict[str, str]  # {"role": "user" | "assistant", "content": str}
```

### Data Flow

1. User input → `on_submit()` validates and appends to history
2. `chat()` routes to provider (currently only Ollama)
3. `chat_with_ollama()` creates OpenAI client with Ollama endpoint
4. Response appended to history state and returned to UI

## Configuration

Environment variables (`.env`):
- `OLLAMA_BASE_URL`: Ollama endpoint (default: `http://localhost:11434/v1`)
- `OLLAMA_API_KEY`: Bearer token (default: `ollama`)
- `openrouter/free

## Key Patterns

- **Error handling**: Provider exceptions → `RuntimeError` → `gr.Error()` with user-friendly messages
- **Model availability**: `_safe_list_models()` lists available models when configured model is unavailable
- **No global state**: Settings passed as parameters, not accessed globally
- **Type hints**: All functions typed; use `Dict`/`List` from `typing` for Python 3.9+ compatibility

## Extension Points

### Adding a New Provider
1. Implement `chat_with_<provider>()` in `providers.py` with same signature
2. Add condition in `chat()` function
3. Add provider choice to dropdown in `app.py`

### UI Customization

CSS element IDs in `app.py`:
- `main_container`: Outer container (max-width 900px)
- `header`: Title section
- `settings_bar`: Provider/model selector row
- `chatbot_container`: Chat history display
- `input_section`: Message input area
