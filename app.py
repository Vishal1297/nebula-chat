from typing import Generator, List
import logging

import gradio as gr

from config import load_settings
from providers import chat, list_models_for_provider, chat_stream
from assets.icons import NEBULA_LOGO

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROVIDER_OPENROUTER = "openrouter"
PROVIDER_OLLAMA = "ollama"
DEFAULT_PROVIDER = "OpenRouter"
Message = dict[str, str]

# Initial setup
settings = load_settings()
initial_choices = list_models_for_provider(settings, DEFAULT_PROVIDER) or []


def default_model(provider: str) -> str:
    if provider.lower() == PROVIDER_OPENROUTER:
        return settings.openrouter_model
    return settings.ollama_model


initial_value = default_model(DEFAULT_PROVIDER)


def _make_model_dropdown(choices, value):
    return gr.Dropdown(
        label=None,
        choices=choices or [value],
        value=value,
        scale=2,
        elem_id="model_dropdown",
        show_label=False,
        filterable=True,
    )


def on_provider_change(provider: str):
    new_value = default_model(provider)
    new_choices = list_models_for_provider(settings, provider) or []

    is_visible = len(new_choices) > 0
    if is_visible:
        return gr.update(choices=new_choices, value=new_value, visible=True, interactive=True), gr.update(visible=False)
    else:
        return gr.update(
            choices=[new_value] if new_value else ["N/A"], value=new_value or "N/A", visible=False, interactive=False
        ), gr.update(visible=True)


def on_submit(
    user_text: str,
    provider: str,
    model: str,
    history: List[Message],
    openrouter_key: str = "",
    ollama_url: str = "",
    progress: gr.Progress | None = None,
) -> Generator[tuple[str, List[Message], List[Message]], None, None]:

    if not user_text or not user_text.strip():
        raise gr.Error("Please enter a message before sending.")

    if not model or not model.strip():
        raise gr.Error("Please provide a model name.")

    chat_history = history or []
    first_history = list(chat_history) + [{"role": "user", "content": user_text.strip()}]

    if progress is not None:
        progress(0.0)

    yield "", first_history, first_history

    try:
        for _content, hist, _hist2, prog in chat_stream(
            _provider=provider.lower(),
            messages=first_history,
            model=model.strip(),
            settings=settings,
            openrouter_api_key=openrouter_key.strip() if openrouter_key else None,
            ollama_base_url=ollama_url.strip() if ollama_url else None,
        ):
            if progress is not None:
                progress(prog)
            yield "", hist, hist

    except Exception as e:
        logger.error(f"Streaming failed: {e}")
        try:
            assistant_reply, model_used = chat(
                _provider=provider.lower(),
                messages=first_history,
                model=model.strip(),
                settings=settings,
                openrouter_api_key=openrouter_key.strip() if openrouter_key else None,
                ollama_base_url=ollama_url.strip() if ollama_url else None,
            )
            if provider.lower() == "openrouter" and model_used != model.strip():
                assistant_reply = f"{assistant_reply}\n\n---\n*Model: {model_used}*"
        except Exception as exc:
            logger.error(f"Fallback chat failed: {exc}")
            assistant_reply = f"**Error:** {str(exc)}"

        updated_history = first_history + [{"role": "assistant", "content": assistant_reply}]
        yield "", updated_history, updated_history


def on_clear() -> tuple[List[Message], List[Message], str]:
    return [], [], ""


# CSS Loading
with open("assets/styles/main.css", "r") as f:
    css = f.read()

with gr.Blocks(title="NebulaChat", analytics_enabled=False) as demo:
    with gr.Column(elem_id="main_container"):
        # Header
        with gr.Row(elem_id="header"):
            with gr.Column(scale=1):
                gr.HTML(
                    '<div style="display:flex; align-items:center; gap:12px;">'
                    f"{NEBULA_LOGO}"
                    '<span style="font-size:22px; font-weight:600; color:var(--text-main); letter-spacing:-0.5px;">NebulaChat</span>'
                    "</div>"
                )
            with gr.Column(scale=0):
                clear_btn = gr.Button("New Chat", elem_id="clear_btn")

        # Hidden Settings Panel
        with gr.Accordion("Settings & Model", open=False, elem_id="settings_accordion"):
            with gr.Row():
                provider = gr.Dropdown(
                    label="Provider",
                    choices=["Ollama", "OpenRouter"],
                    value="OpenRouter",
                    interactive=True,
                    elem_id="provider_dropdown",
                )
                model = _make_model_dropdown(initial_choices or [initial_value], initial_value)
                model_error_msg = gr.HTML(
                    visible=False,
                    value='<div style="padding: 8px 12px; background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; font-size: 12px; color: #92400e; margin-top: 4px; display: flex; align-items: center; gap: 6px;"><span>\u26a0\ufe0f</span><span>Configure provider in Settings to see available models</span></div>',
                    elem_id="model_error_msg",
                )

            with gr.Row():
                openrouter_key = gr.Textbox(
                    label="OpenRouter API Key",
                    placeholder="sk-...",
                    type="password",
                    interactive=True,
                )
                ollama_url = gr.Textbox(
                    label="Ollama Base URL",
                    placeholder="http://localhost:11434/v1",
                    interactive=True,
                )

        # Main Chat Area
        state = gr.State([])
        chatbot = gr.Chatbot(
            label=None,
            elem_id="chatbot_container",
            show_label=False,
            avatar_images=(None, None),
        )

        # Bottom Input Area
        with gr.Row(elem_id="input_section"):
            prompt = gr.Textbox(
                label=None,
                placeholder="Ask Nebula anything...",
                elem_id="prompt",
                scale=1,
                show_label=False,
                lines=1,
                container=False,
            )
            send_btn = gr.Button(
                "↑",
                elem_id="send_btn",
                variant="primary",
                scale=0,
            )

    # Event Handlers
    provider.change(fn=on_provider_change, inputs=[provider], outputs=[model, model_error_msg])

    submit_event = send_btn.click(
        fn=on_submit,
        inputs=[prompt, provider, model, state, openrouter_key, ollama_url],
        outputs=[prompt, chatbot, state],
        show_progress="hidden",
    )

    prompt_event = prompt.submit(
        fn=on_submit,
        inputs=[prompt, provider, model, state, openrouter_key, ollama_url],
        outputs=[prompt, chatbot, state],
        show_progress="hidden",
    )

    # UI Interactive States
    submit_event.then(fn=lambda: gr.update(interactive=True), inputs=None, outputs=[send_btn])
    prompt_event.then(fn=lambda: gr.update(interactive=True), inputs=None, outputs=[send_btn])

    send_btn.click(fn=lambda: gr.update(interactive=False), inputs=None, outputs=[send_btn])
    prompt.submit(fn=lambda: gr.update(interactive=False), inputs=None, outputs=[send_btn])

    clear_btn.click(fn=on_clear, inputs=None, outputs=[chatbot, state, prompt])

if __name__ == "__main__":
    demo.queue()
    demo.launch(
        debug=False,
        quiet=True,
        css=css,
        footer_links=[],
    )
