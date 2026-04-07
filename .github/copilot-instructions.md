# AI Coding Agent Instructions for ChatApp

## Project Overview

**ChatApp** is a Gradio-based web chat interface for Ollama models using OpenAI-compatible APIs. The architecture separates concerns into three layers:

1. **UI Layer** (`app.py`): Gradio components and event handlers
2. **Provider Layer** (`providers.py`): LLM provider abstraction and error handling
3. **Configuration Layer** (`config.py`): Environment-based settings management

## Architecture & Data Flow

### Message Format
All internal message communication uses a standardized format:
```python
Message = Dict[str, str]  # {"role": "user" | "assistant", "content": str}
```
This format is consistent across `app.py` history state, `providers.py` API calls, and OpenAI client requests.

### Data Flow: User Message to Response
1. **User Input** → `on_submit()` validates and appends to message list
2. **Provider Call** → `chat()` routes to provider (currently only Ollama)
3. **API Request** → `chat_with_ollama()` creates OpenAI client with Ollama endpoint
4. **Response** → Assistant reply appended to history state and returned to UI
5. **State Management** → Gradio's `gr.State([])` maintains persistent history across sessions

### Settings & Initialization
- Settings loaded once at startup via `config.load_settings()` with `.env` fallback defaults
- Settings passed to `chat()` function (not stored globally except for UI defaults)
- Environment variables: `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, `OLLAMA_MODEL`

## Key Patterns & Conventions

### Error Handling Strategy
**Three-tier error handling** in `providers.py`:
- **Network errors** (APIConnectionError) → User-friendly message about Ollama server connectivity
- **Timeout errors** (APITimeoutError) → Suggest model loading or retry
- **API errors** (APIStatusError) → Enhanced with model availability checking
- **Empty responses** → Explicit RuntimeError for debugging

All exceptions converted to `RuntimeError` for `app.py` to catch and wrap in `gr.Error()`.

### Model Availability Intelligence
`_safe_list_models()` gracefully handles API failures when checking available models. If the configured model is unavailable, the error message lists the first 5 available models, making troubleshooting immediate.

### UI/Event Binding Convention
- Gradio callbacks follow pattern: `on_<action>(inputs...) -> outputs`
- Event binding specifies: `fn=callback, inputs=[...], outputs=[...]` (explicit, not inferred)
- Textbox submit triggers same handler as button click (`prompt.submit()` and `send_btn.click()`)

### Modern Chat Interface Design
The UI is structured with a clean, Claude/ChatGPT-style layout:
- **Header**: Centered title and subtitle
- **Settings Bar**: Provider and model selector in a light-colored row
- **Chat Area**: Tall chatbot component with scrollable history
- **Input Section**: Full-width textbox with Send button, supports multi-line input (Shift+Enter)
- **CSS Theming**: Custom CSS with element IDs for styling (main_container, settings_bar, chatbot_container, input_section)
- **Max Width**: Constrained to 900px for optimal readability

## Development Workflows

### Running the App
```bash
uv run python app.py
```
Opens at local Gradio URL (typically `http://localhost:7860`).

### Dependencies
This project uses `uv` for fast, reliable Python package management with `pyproject.toml`:
- `gradio`: UI framework
- `python-dotenv`: Environment variable loading
- `openai`: API client (configured to use Ollama's OpenAI-compatible endpoint)

Install dependencies with:
```bash
uv sync              # Install main + dev dependencies
uv sync --no-dev     # Install main dependencies only
```

### Configuration Testing
Always test with a running Ollama instance and verify `.env` values:
```bash
export OLLAMA_BASE_URL="http://localhost:11434/v1"
export OLLAMA_API_KEY="ollama"
export OLLAMA_MODEL="llama3.1:8b"
uv run python app.py
```

## Common Extension Points

### Adding a New Provider
1. Implement `chat_with_<provider>()` in `providers.py` with same signature as `chat_with_ollama()`
2. Add condition in `chat()` function: `elif provider == "<name>": return chat_with_<provider>(...)`
3. Add provider choice to `provider` dropdown in `app.py`
4. Document new env vars in README.md

### Modifying Error Messages
User-facing errors are in `app.py` (`gr.Error()`) and provider-specific messages in `providers.py`. Keep messages actionable and non-technical.

### Extending Message History Features
History is stored in Gradio's `gr.State()` object. To add features like persistence, modify the `updated_history` tuple return in `on_submit()` and the state initialization in the `gr.Blocks` context.

### UI Customization
CSS styling is defined in the `css` string in `app.py` and applied via `demo.css`. Modify element IDs to adjust layout:
- `main_container`: Outer container (max-width 900px)
- `header`: Title section
- `settings_bar`: Provider/model selector row
- `chatbot_container`: Chat history display
- `input_section`: Message input area

## Type Hints & Code Style

- Use `from typing import Dict, List` for Python 3.9 compatibility (dataclass with frozen=True pattern in config.py)
- Type all function parameters and returns (see `chat_with_ollama(messages: List[Message], model: str, settings: Settings) -> str`)
- Use `@dataclass(frozen=True)` for immutable configuration objects
- Avoid global state; pass dependencies as parameters (settings passed to chat functions, not accessed globally)

## File Responsibilities

| File | Purpose |
|------|---------|
| `app.py` | Gradio UI, event handling, user input validation, state management |
| `config.py` | Settings dataclass, environment loading via `load_dotenv()` |
| `providers.py` | Provider abstraction, API client instantiation, comprehensive error handling |
| `pyproject.toml` | Project metadata, dependencies, and tool configuration |
| `.env` | Runtime configuration (excluded from version control) |
