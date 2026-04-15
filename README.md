# NebulaChat (nebula-chat)

A NebulaChat UI for multi-provider chat (Ollama and OpenRouter) built with Gradio.

## Features

- Multi-provider chat UI (Ollama and OpenRouter)
- Unified internal message format (`[{role, content}]`)
- Configurable model via UI and env vars
- Friendly error messages for missing cloud config or auth issues
- Streaming responses for faster interaction
- Responsive web interface with dark/light themes

## Requirements

- Python 3.10+
- Either:
  - Ollama instance (local or remote)
  - OpenRouter API key (for cloud-based models)

## Setup

1. Install `uv` (if not already installed):

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Clone/navigate to the project and install dependencies:

   ```bash
   uv sync
   ```

3. Configure environment variables:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set (at least one provider must be configured):

   **For Ollama:**
   - `OLLAMA_BASE_URL` (your Ollama endpoint, default: http://localhost:11434/v1)
   - `OLLAMA_API_KEY` (optional Bearer token for remote instances)
   - `OLLAMA_MODEL` (optional, model to use)

   **For OpenRouter:**
   - `OPENROUTER_API_KEY` (required for OpenRouter provider)
   - `OPENROUTER_MODEL` (optional, model to use)

## Provider Configuration

### Ollama

```bash
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_API_KEY=  # Optional for local instances
OLLAMA_MODEL=llama3.1:8b  # Optional
```

### OpenRouter

```bash
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=openrouter/free  # Optional
```

You can also configure providers at runtime via the UI settings panel.

## Run

```bash
uv run python app.py
```

Open the local Gradio URL in your browser.

## Usage Notes

- Provider can be Ollama or OpenRouter (selected via the UI dropdown).
- Set/adjust model in the model field.
- Enter a message and press Enter or click Send.
- Use Clear to reset conversation history.
