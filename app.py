from typing import Generator, List
import logging

import gradio as gr

from config import load_settings
from providers import chat, list_models_for_provider

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROVIDER_OPENROUTER = "openrouter"
PROVIDER_OLLAMA = "ollama"
DEFAULT_PROVIDER = "OpenRouter"
Message = dict[str, str]
# Populate initial model choices for the default provider
# will be overwritten when provider changes
settings = load_settings()
initial_choices = list_models_for_provider(settings, DEFAULT_PROVIDER) or []


def default_model(provider: str) -> str:
    if provider.lower() == PROVIDER_OPENROUTER:
        return settings.openrouter_model
    return settings.ollama_model


initial_value = default_model(DEFAULT_PROVIDER)


def _make_model_dropdown(choices, value):
    # Try to enable search in Gradio Dropdown if supported
    try:
        return gr.Dropdown(
            label=None,
            choices=choices or [value],
            value=value,
            scale=2,
            elem_id="model_dropdown",
            show_label=False,
            searchable=True,
        )
    except TypeError:
        return gr.Dropdown(
            label=None, choices=choices or [value], value=value, scale=2, elem_id="model_dropdown", show_label=False
        )


def on_provider_change(provider: str):
    new_value = default_model(provider)
    new_choices = list_models_for_provider(settings, provider) or []

    # Hide model dropdown if no models are available (missing config or API error)
    is_visible = len(new_choices) > 0

    if is_visible:
        # Models found: show dropdown, hide error message
        model_update = gr.update(choices=new_choices, value=new_value, visible=True, interactive=True)
        error_msg_update = gr.update(visible=False)
    else:
        # No models: hide dropdown, show error message
        model_update = gr.update(
            choices=[new_value] if new_value else ["N/A"], value=new_value or "N/A", visible=False, interactive=False
        )
        error_msg_update = gr.update(visible=True)

    return model_update, error_msg_update


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
    # Emit the user's message immediately for a snappier experience
    first_history = list(chat_history) + [{"role": "user", "content": user_text.strip()}]
    # Initialize progress if supported by Gradio
    if progress is not None:
        progress(0.0)
    yield "", first_history, first_history
    # Ollama model is controlled via environment (OLLAMA_MODEL) in deployment scenarios

    if provider.lower() == "ollama":
        # Streaming path for Ollama
        try:
            from providers import chat_with_ollama_stream

            for _content, hist, _hist2, prog in chat_with_ollama_stream(
                messages=first_history,
                model=model.strip(),
                settings=settings,
                ollama_base_url=ollama_url.strip() if ollama_url else None,
            ):
                if progress is not None:
                    progress(prog)
                yield "", hist, hist
            return
        except Exception as e:
            # Fallback to non-streaming if streaming fails
            import logging
            logging.warning(f"Ollama streaming failed, falling back to non-streaming: {e}")

    # OpenRouter streaming path (if supported)
    if provider.lower() == "openrouter":
        try:
            from providers import chat_with_openrouter_stream

            for _content, hist, _hist2, prog in chat_with_openrouter_stream(
                messages=first_history,
                model=model.strip(),
                settings=settings,
                openrouter_api_key=openrouter_key.strip() if openrouter_key else None,
            ):
                if progress is not None:
                    progress(prog)
                yield "", hist, hist
            return
        except Exception as e:
            # Fall back to non-streaming if streaming fails
            import logging
            logging.warning(f"OpenRouter streaming failed, falling back to non-streaming: {e}")

    # Non-streaming path (OpenRouter or fallback)
    try:
        assistant_reply, model_used = chat(
            _provider=provider,
            messages=first_history,
            model=model.strip(),
            settings=settings,
            openrouter_api_key=openrouter_key.strip() if openrouter_key else None,
            ollama_base_url=ollama_url.strip() if ollama_url else None,
        )
        # Format assistant reply with model info for OpenRouter
        if provider.lower() == "openrouter" and model_used != model.strip():
            assistant_reply = f"{assistant_reply}\n\n---\n*Model: {model_used}*"
    except ValueError as exc:
        assistant_reply = f"**Configuration Error:**\n\n{str(exc)}\n\nPlease check your settings and try again."
    except RuntimeError as exc:
        assistant_reply = (
            f"**Sorry, I encountered an error:**\n\n{str(exc)}\n\nYou can try again or adjust your settings."
        )
    except Exception as exc:
        assistant_reply = f"**Unexpected Error:**\n\n{str(exc)}\n\nPlease try again."

    updated_history = chat_history + [
        {"role": "user", "content": user_text.strip()},
        {"role": "assistant", "content": assistant_reply},
    ]
    yield "", updated_history, updated_history


def on_clear() -> tuple[List[Message], List[Message], str]:
    return [], [], ""


# Load external CSS
with open("assets/styles/main.css", "r") as f:
    css = f.read()

# SVG Icons (Base64 encoded for reliable rendering)
SEND_ICON = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJjdXJyZW50Q29sb3IiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48bGluZSB4MT0iMjIiIHkxPSIyIiB4Mj0iMTEiIHkyPSIxMyI+PC9saW5lPjxwb2x5Z29uIHBvaW50cz0iMjIgMiAxNSAyMiAxMSAxMyAyIDkgMjIgMiI+PC9wb2x5Z29uPjwvc3ZnPg=="  # noqa: E501
CLEAR_ICON = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJjdXJyZW50Q29sb3IiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSIzIDYgNSA2IDIxIDYiPjwvcG9seWxpbmU+PHBhdGggZD0iTTE5IDZ2MTRhMiAyIDAgMCAxLTIgMkg3YTIgMiAwIDAgMS0yLTJWNm0zIDBWNGEyIDIgMCAwIDEgMi0yaDRhMiAyIDAgMCAxIDIgMnYyIj48L3BhdGg+PC9zdmc+"  # noqa: E501
CHAT_ICON = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjgiIGhlaWdodD0iMjgiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmZmZmIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIxIDE1YTIgMiAwIDEgMS0yIDJIN2wtNCA0VjVhMiAyIDAgMSAyLTIgMmgxNGEyIDIgMCAwIDEgMiAyeiI+PC9wYXRoPjwvc3ZnPg=="  # noqa: E501

with gr.Blocks(title="NebulaChat") as demo:
    with gr.Column(elem_id="main_container"):
        # Header
        with gr.Row(elem_id="header"):
            gr.HTML(  # Nebula header (enhanced icon)
                '<div style="display:flex; align-items:center; gap:8px;">'
                '<svg width="40" height="40" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-label="Nebula" fill="none">'
                '<defs><radialGradient id="grad2" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#8b5cf6"/><stop offset="60%" stop-color="#4c1d95"/><stop offset="100%" stop-color="#2e005a"/></radialGradient></defs>'
                '<circle cx="12" cy="12" r="9" fill="url(#grad2)"/>'
                '<circle cx="8" cy="9" r="3" fill="#fff" opacity="0.5"/>'
                '<circle cx="15" cy="15" r="2.5" fill="#fff" opacity="0.4"/>'
                "</svg>"
                '<span style="font-size:28px; font-weight:700; color:#111; font-family:Inter, sans-serif;">NebulaChat</span>'
                "</div>"
            )
        # Settings Bar with Controls
        with gr.Row(elem_id="settings_bar"):
            with gr.Column(scale=2):
                provider = gr.Dropdown(
                    label=None,
                    choices=["Ollama", "OpenRouter"],
                    value="OpenRouter",
                    interactive=True,
                    scale=1,
                    elem_id="provider_dropdown",
                    show_label=False,
                )
                model = _make_model_dropdown(initial_choices or [initial_value], initial_value)
                model_error_msg = gr.HTML(
                    visible=False,
                    value='<div style="padding: 8px 12px; background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; font-size: 12px; color: #92400e; margin-top: 4px; display: flex; align-items: center; gap: 6px;"><span>⚠️</span><span>Configure provider in Settings to see available models</span></div>',
                    elem_id="model_error_msg",
                )
            with gr.Column(scale=3):
                clear_btn = gr.Button("Clear Chat", elem_id="clear_btn", scale=0)
                with gr.Accordion("⚙️ Settings", open=False, elem_id="settings_accordion"):
                    gr.HTML(
                        '<div style="padding: 4px 0; font-size: 12px; color: #64748b; margin-bottom: 8px; font-weight: 500;">API Configuration</div>'
                    )
                    with gr.Row():
                        with gr.Column():
                            openrouter_key = gr.Textbox(
                                label=None,
                                placeholder="OpenRouter API Key",
                                type="password",
                                elem_id="openrouter_key",
                                scale=1,
                                show_label=False,
                                container=False,
                                info="Get from openrouter.ai",
                            )
                        with gr.Column():
                            ollama_url = gr.Textbox(
                                label=None,
                                placeholder="Ollama Base URL",
                                elem_id="ollama_url",
                                scale=1,
                                show_label=False,
                                container=False,
                                info="Default: http://localhost:11434/v1",
                            )
                    gr.HTML(
                        '<div style="padding: 12px 0; margin-top: 8px; font-size: 12px; border-top: 1px solid #e2e8f0; color: #64748b;">'
                        "<strong>💡 Tips:</strong><br>"
                        "• Ollama requires a local instance running<br>"
                        "• OpenRouter provides cloud-based LLMs<br>"
                        "• Leave blank to use defaults from .env"
                        "</div>"
                    )

        # Chat history
        state = gr.State([])
        chatbot = gr.Chatbot(
            label=None,
            height=700,
            elem_id="chatbot_container",
            show_label=False,
            avatar_images=(None, None),
        )

        # Input section
        with gr.Row(elem_id="input_section"):
            prompt = gr.Textbox(
                label=None,
                placeholder="Message NebulaChat...",
                elem_id="prompt",
                scale=9,
                show_label=False,
                lines=4,
                max_lines=10,
                container=False,
            )
            send_btn = gr.Button(
                "Send",
                elem_id="send_btn",
                variant="primary",
                scale=0,
            )

    provider.change(fn=on_provider_change, inputs=[provider], outputs=[model, model_error_msg])
    send_btn.click(
        fn=on_submit,
        inputs=[prompt, provider, model, state, openrouter_key, ollama_url],
        outputs=[prompt, chatbot, state],
    )
    prompt.submit(
        fn=on_submit,
        inputs=[prompt, provider, model, state, openrouter_key, ollama_url],
        outputs=[prompt, chatbot, state],
    )
    clear_btn.click(fn=on_clear, inputs=None, outputs=[chatbot, state, prompt])

if __name__ == "__main__":
    demo.queue()
    demo.launch()
