from typing import Dict, List, Generator

import gradio as gr

from config import load_settings
from providers import chat, list_models_for_provider

Message = Dict[str, str]

settings = load_settings()


def default_model(provider: str) -> str:
    if provider.lower() == "openrouter":
        return settings.openrouter_model
    return settings.ollama_model


DEFAULT_PROVIDER = "OpenRouter"
# Populate initial model choices for the default provider; will be overwritten when provider changes
initial_choices = list_models_for_provider(settings, DEFAULT_PROVIDER) or []
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
    return gr.update(choices=new_choices, value=new_value)


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
        except Exception:
            # Fallback to non-streaming if streaming fails
            pass

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
        except Exception:
            # Fall back to non-streaming if streaming fails
            pass

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
    except ValueError as exc:
        raise gr.Error(str(exc)) from exc
    except RuntimeError as exc:
        raise gr.Error(str(exc)) from exc
    except Exception as exc:
        raise gr.Error(f"Unexpected error: {exc}") from exc

    # Format assistant reply with model info for OpenRouter
    if provider.lower() == "openrouter" and model_used != model.strip():
        assistant_reply = f"{assistant_reply}\n\n---\n*Model: {model_used}*"

    updated_history = chat_history + [
        {"role": "user", "content": user_text.strip()},
        {"role": "assistant", "content": assistant_reply},
    ]
    yield "", updated_history, updated_history


def on_clear() -> tuple[List[Message], List[Message], str]:
    return [], [], ""


css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

body {
    background: var(--bg);
    min-height: 100vh;
    margin: 0;
    padding: 0;
}

#main_container {
    max-width: 860px;
    margin: 0 auto;
    background: var(--surface);
    min-height: 100vh;
    box-shadow: var(--shadow-lg);
    display: flex;
    flex-direction: column;
}

#header {
    padding: 20px 28px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

/* Responsive header for narrow screens */
@media (max-width: 560px) {
    #header {
        flex-direction: column;
        align-items: flex-start;
    }
    #header h1 {
        margin: 8px 0 4px 0;
        font-size: 22px;
    }
    #header p {
        margin: 0;
        font-size: 12px;
    }
}

#header h1 {
    color: var(--text);
    font-size: 20px;
    font-weight: 700;
    margin: 0;
    letter-spacing: -0.025em;
}

#header p {
    color: var(--text-muted);
    font-size: 13px;
    margin: 0;
    font-weight: 400;
}

#settings_bar {
    display: flex;
    gap: 10px;
    padding: 14px 28px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    align-items: center;
}

#settings_bar .gradio-dropdown,
#settings_bar .gradio-textbox {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    transition: all 0.15s ease;
}

#settings_bar .gradio-dropdown:hover,
#settings_bar .gradio-textbox:hover {
    border-color: var(--border-hover);
}

#settings_bar .gradio-dropdown:focus-within,
#settings_bar .gradio-textbox:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
}

#clear_btn {
    background: var(--accent);
    color: var(--user-text);
    border: none;
    border-radius: 12px;
    padding: 12px 20px;
    font-weight: 600;
    font-size: 14px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
}
#clear_btn:hover {
    background: var(--accent-hover);
    box-shadow: var(--shadow-md);
}
#clear_btn:active {
    transform: scale(0.98);
}
#clear_btn:focus-visible {
    outline: 2px solid var(--border-hover);
    outline-offset: 2px;
}


#chatbot_container {
    background: var(--surface);
    flex: 1;
    min-height: 400px;
    padding: 0;
}

#chatbot_container .chatbot {
    background: var(--surface);
    border: none;
}

#chatbot_container .message {
    border-radius: var(--radius-lg);
    padding: 12px 18px;
    margin: 6px 0;
    max-width: 80%;
    line-height: 1.6;
    font-size: 15px;
    border: none;
    box-shadow: var(--shadow-sm);
}

#chatbot_container .message.user {
    background: var(--user-bg);
    color: var(--user-text);
    margin-left: auto;
    border-bottom-right-radius: 6px;
}

#chatbot_container .message.assistant {
    background: var(--assistant-bg);
    color: var(--assistant-text);
    margin-right: auto;
    border-bottom-left-radius: 6px;
}

#chatbot_container .message .prose {
    font-size: 15px;
    line-height: 1.6;
}

#chatbot_container .message.user .prose {
    color: var(--user-text);
}

#chatbot_container .message.assistant .prose {
    color: var(--assistant-text);
}

#input_section {
    padding: 16px 28px 20px;
    background: var(--surface);
    border-top: 1px solid var(--border);
    display: flex;
    gap: 10px;
    align-items: flex-end;
}

#prompt {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 14px 18px;
    font-size: 15px;
    transition: all 0.15s ease;
    resize: none;
    line-height: 1.5;
}

#prompt:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    background: var(--surface);
}

#prompt::placeholder {
    color: var(--text-muted);
}

#send_btn {
    background: var(--accent);
    color: var(--user-text);
    border: none;
    border-radius: var(--radius-md);
    padding: 14px 20px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.15s ease;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 48px;
    height: 48px;
}

#send_btn:hover {
    background: var(--accent-hover);
    box-shadow: var(--shadow-md);
}

#send_btn:active {
    transform: scale(0.98);
}

/* Hide Gradio footer */
footer {
    display: none;
}

/* Scrollbar styling */
#chatbot_container::-webkit-scrollbar {
    width: 6px;
}

#chatbot_container::-webkit-scrollbar-track {
    background: transparent;
}

#chatbot_container::-webkit-scrollbar-thumb {
    background: var(--border-hover);
    border-radius: 3px;
}

#chatbot_container::-webkit-scrollbar-thumb:hover {
    background: var(--text-muted);
}

/* Button Icons */
#send_btn {
    background-image: url(  # noqa: E501
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='22' y1='2' x2='11' y2='13'%3E%3C/line%3E%3Cpolygon points='22 2 15 22 11 13 2 9 22 2'%3E%3C/polygon%3E%3C/svg%3E"
    );
    background-repeat: no-repeat;
    background-position: center;
    background-size: 20px 20px;
    text-indent: -9999px;
    overflow: hidden;
}

#clear_btn {
    background-image: url(  # noqa: E501
        "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpolyline points='3 6 5 6 21 6'%3E%3C/polyline%3E%3Cpath d='M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'%3E%3C/path%3E%3C/svg%3E"
    );
    background-repeat: no-repeat;
    background-position: 10px center;
    background-size: 16px 16px;
    padding-left: 32px;
}

/* Gradio component overrides */
.gradio-container {
    padding: 0 !important;
    margin: 0 !important;
    max-width: 100% !important;
}

.gradio-container .wrap {
    border: none !important;
    box-shadow: none !important;
}

.gradio-dropdown .wrap,
.gradio-textbox .wrap {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    background: var(--bg) !important;
}

.gradio-dropdown .wrap:hover,
.gradio-textbox .wrap:hover {
    border-color: var(--border-hover) !important;
}

/* Empty state styling */
#chatbot_container .empty {
    color: var(--text-muted);
    font-size: 14px;
}
"""

# SVG Icons (Base64 encoded for reliable rendering)
SEND_ICON = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAiIGhlaWdodD0iMjAiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJjdXJyZW50Q29sb3IiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48bGluZSB4MT0iMjIiIHkxPSIyIiB4Mj0iMTEiIHkyPSIxMyI+PC9saW5lPjxwb2x5Z29uIHBvaW50cz0iMjIgMiAxNSAyMiAxMSAxMyAyIDkgMjIgMiI+PC9wb2x5Z29uPjwvc3ZnPg=="  # noqa: E501
CLEAR_ICON = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTgiIGhlaWdodD0iMTgiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSJjdXJyZW50Q29sb3IiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIj48cG9seWxpbmUgcG9pbnRzPSIzIDYgNSA2IDIxIDYiPjwvcG9seWxpbmU+PHBhdGggZD0iTTE5IDZ2MTRhMiAyIDAgMCAxLTIgMkg3YTIgMiAwIDAgMS0yLTJWNm0zIDBWNGEyIDIgMCAwIDEgMi0yaDRhMiAyIDAgMCAxIDIgMnYyIj48L3BhdGg+PC9zdmc+"  # noqa: E501
CHAT_ICON = "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjgiIGhlaWdodD0iMjgiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZmZmZmZmIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCI+PHBhdGggZD0iTTIxIDE1YTIgMiAwIDEgMS0yIDJIN2wtNCA0VjVhMiAyIDAgMSAyLTIgMmgxNGEyIDIgMCAwIDEgMiAyeiI+PC9wYXRoPjwvc3ZnPg=="  # noqa: E501

with gr.Blocks(title="NebulaChat") as demo:
    demo.css = css
    with gr.Column(elem_id="main_container"):
        # Header
        with gr.Row(elem_id="header"):
            gr.HTML(  # Nebula header (enhanced icon)
                '<div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">'
                '<svg width="28" height="28" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-label="Nebula" fill="none">'
                '<defs><radialGradient id="grad2" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#8b5cf6"/><stop offset="60%" stop-color="#4c1d95"/><stop offset="100%" stop-color="#2e005a"/></radialGradient></defs>'
                '<circle cx="12" cy="12" r="9" fill="url(#grad2)"/>'
                '<circle cx="8" cy="9" r="3" fill="#fff" opacity="0.5"/>'
                '<circle cx="15" cy="15" r="2.5" fill="#fff" opacity="0.4"/>'
                "</svg>"
                '<span style="font-size:28px; font-weight:700; margin-left:8px; color:#111; font-family:Inter, sans-serif;">NebulaChat</span>'
                "</div>"
            )
            gr.HTML('<p style="text-align: right;">Powered by Ollama & OpenRouter</p>')
            gr.HTML(
                '<div style="display:flex; align-items:center; padding:6px 12px 0 12px; font-size:12px; color:#64748b;">Conversations across the cloud of models.<span aria-label="Nebula badge" style="display:inline-block; width:20px; height:20px; border-radius:5px; background: linear-gradient(135deg, #6b9cff 0%, #4f46e5 100%); margin-left:6px; vertical-align:middle;"></span></div>'
            )
            gr.HTML(
                '<div style="padding: 0 12px 0 12px; font-size:12px; color:#64748b; margin-top:2px;">Nebula-enabled multi-provider orchestration across Ollama/OpenRouter.</div>'
            )
        # Settings Bar
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
            with gr.Column(scale=3):
                clear_btn = gr.Button("Clear", elem_id="clear_btn", scale=0)
                with gr.Accordion("Settings", open=False):
                    openrouter_key = gr.Textbox(
                        label=None,
                        placeholder="OpenRouter API Key (optional)",
                        type="password",
                        elem_id="openrouter_key",
                        scale=1,
                        show_label=False,
                        container=False,
                    )
                    ollama_url = gr.Textbox(
                        label=None,
                        placeholder="Ollama Base URL (optional)",
                        elem_id="ollama_url",
                        scale=1,
                        show_label=False,
                        container=False,
                    )

        # Chat history
        state = gr.State([])
        chatbot = gr.Chatbot(
            label=None,
            height=550,
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
                lines=1,
                max_lines=5,
                container=False,
            )
            send_btn = gr.Button(
                "Send",
                elem_id="send_btn",
                variant="primary",
                scale=0,
            )

    provider.change(fn=on_provider_change, inputs=[provider], outputs=[model])
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
    demo.launch()
