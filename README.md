# NebulaChat (nebula-chat)

A NebulaChat UI for multi-provider chat (Ollama and OpenRouter) built with Gradio.

## Features

- Multi-provider chat UI (Ollama and OpenRouter)
- Unified internal message format (`[{role, content}]`)
- Configurable model via UI and env vars
- Friendly error messages for missing cloud config or auth issues

## Requirements

- Python 3.10+
- Ollama Cloud endpoint URL and model access

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

   Edit `.env` and set:
   - `OLLAMA_BASE_URL` (your Ollama Cloud host)
   - `OLLAMA_API_KEY` (Bearer token, or `OLLAMA_TOKEN`)
   - `OLLAMA_MODEL` (optional, defaults to `llama3.1:8b`)

## Ollama Cloud Configuration

```bash
OLLAMA_BASE_URL=https://your-ollama-cloud-host
OLLAMA_API_KEY=your_ollama_bearer_token_here
OLLAMA_MODEL=llama3.1:8b
```

Requests are sent to `POST {OLLAMA_BASE_URL}/api/chat` with `Authorization: Bearer <token>` when a token is provided.

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
 
