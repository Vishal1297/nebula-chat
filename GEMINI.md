# NebulaChat Instructions

## Core Architecture
- **Provider Pattern**: All LLM integrations must implement the `BaseProvider` interface in `providers/base.py`.
- **Backend**: FastAPI manages the server lifecycle, with Gradio mounted as an app in `api/handler.py`.
- **Configuration**: Use `config.py` and `constants.py` for all environment variables and default strings. Avoid magic strings in business logic.

## Version Compatibility (Gradio 6.x+)
- **Parameter Placement**: `css`, `js`, and `head` parameters must be passed to `demo.launch()`, not the `gr.Blocks()` constructor.
- **Component Arguments**:
  - `gr.Dropdown`: Use `filterable=True` instead of `searchable=True`.
  - `gr.Chatbot`: `bubble_full_width` is deprecated; remove it to avoid `TypeError`.
- **API Privacy**: To hide the "Use via API" link, set `footer_links=[]` in `demo.launch()`.

## Performance & Reliability
- **Caching**: Use `@lru_cache` on functions that fetch models from external providers (Ollama/OpenRouter) to minimize redundant network latency and API costs.
- **Streaming Reliability**: Always set `maxDuration` to at least `60` in `vercel.json` for any serverless function handling LLM streams.
- **Rate Limiting**: Use `slowapi` to protect public endpoints (like `/health`) and prevent potential API key abuse.

## UI & Aesthetics
- **Theme**: Modern, minimalist UI inspired by ChatGPT/Claude. Colors and spacing are defined in `assets/styles/theme.css`.
- **Input Pattern**: Use the "floating pill" input layout (`elem_id="prompt"`) centered at the bottom of the viewport.
- **Interactive UX**: 
  - Always disable the "Send" button during generation using `.then()` to prevent redundant/double API calls.
  - Use `show_progress="hidden"` on events to maintain the clean, "invisible" UI aesthetic.
- **Responsive Design**: Ensure all UI changes are tested on mobile viewports. Use the established sticky input bar pattern.
- **Icons**: Store all SVG icons in `assets/icons.py` as Base64 or raw SVG strings.

## Development Workflow
- **Standard Lifecycle**:
  1. **Plan (Double-Check)**: Formulate a strategy and then review/validate the approach before writing code.
  2. **Implement**: Apply surgical, idiomatic changes.
  3. **Verify**: 
     - Perform manual UI testing.
     - Add/update automated test cases in `tests/`.
     - **Critical**: Ensure the app starts without errors by running `uv run app.py` and checking for immediate tracebacks.
  4. **Lint & Format**: Run `black` and `pylint` (or `ruff`) to ensure code quality.
- **Dependency Management**: Use `uv` for all package management (`uv sync`, `uv add`).
- **Formatting**: Adhere to `black` (120 line length) and `ruff` standards.
- **Testing**: Run tests with `uv run pytest`.

## Deployment
- **Platform**: Vercel.
- **Configuration**: Use `functions` and `rewrites` in `vercel.json`. Ensure `"version": 2` is present.
- **Dependencies**: Keep `requirements.txt` in sync with `uv` using `uv export --format requirements-txt > requirements.txt`. Vercel relies on this file for build-time installation.
- **Python Version**: Specified in `.python-version` (set to `3.12`).
- **Timeouts**: LLM streaming requires `maxDuration: 60` in `vercel.json`.
- **Troubleshooting**: If you see "Function Runtimes must have a valid version", ensure the Vercel Dashboard project settings are set to **"Framework: Other"** and not a legacy builder.
