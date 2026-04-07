# AGENTS.md

## Commands

```bash
uv sync              # Install dependencies
uv run python app.py  # Run app
uv run black .       # Format
uv run ruff check .  # Lint
uv run pytest        # Test (no tests exist yet)
```

## Architecture

- **app.py**: Gradio UI, event handlers, state via `gr.State([])`
- **providers.py**: LLM provider abstraction (Ollama, OpenRouter)
- **config.py**: Immutable `Settings` dataclass with `.env` fallback

## Message Format

```python
Message = Dict[str, str]  # {"role": "user" | "assistant", "content": str}
```

## Providers

- **Ollama**: Local or remote Ollama via OpenAI-compatible API
- **OpenRouter**: Cloud LLM access (default provider)

## Error Handling

Provider exceptions → `RuntimeError` → `gr.Error()` with user-friendly messages.

## UI Customization

CSS element IDs: `main_container`, `header`, `settings_bar`, `chatbot_container`, `input_section`

## Known Issues

- **README.md is outdated**: Claims Ollama-only, but OpenRouter support exists

## Favicon
- Use the Nebula-inspired favicon provided at `assets/favicon.svg` by deploying it as the site favicon.
- Deployment notes:
  - If your hosting platform serves static assets from the repo root, copy assets/favicon.svg to the site's root as favicon.svg and configure the host to serve it at /favicon.svg.
  - If your hosting requires a dedicated static assets path, point the favicon URL in the hosting config accordingly (most hosts support this).
- Alternative (not preferred): a head-injection approach can be tried, but it is unreliable across Gradio deployments; prefer hosting-based favicon inclusion.

## Branding
- NebulaChat branding is now the default for the UI. The branding assets live in `assets/` and `branding.json` at repository root for centralized usage.
- The header uses Nebula-inspired inline SVG; the branding name is NebulaChat.
