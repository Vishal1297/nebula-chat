from typing import Dict, Generator, List

import gradio as gr

from config import load_settings
from providers import chat, list_models_for_provider

PROVIDER_OPENROUTER = "openrouter"
PROVIDER_OLLAMA = "ollama"
DEFAULT_PROVIDER = "OpenRouter"
Message = Dict[str, str]
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


css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --bg: #f8fafc;
    --surface: #ffffff;
    --border: #e2e8f0;
    --border-hover: #cbd5e1;
    --text: #0f172a;
    --text-muted: #64748b;
    --accent: #4f46e5;
    --accent-hover: #4338ca;
    --user-bg: #4f46e5;
    --user-text: #ffffff;
    --assistant-bg: #f1f5f9;
    --assistant-text: #0f172a;
    --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.07);
    --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
}

@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(8px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes slideIn {
    from {
        opacity: 0;
        transform: translateX(-8px);
    }
    to {
        opacity: 1;
        transform: translateX(0);
    }
}

@keyframes typing {
    0%, 60%, 100% {
        opacity: 0.3;
    }
    30% {
        opacity: 1;
    }
}

@keyframes pulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.5;
    }
}

@keyframes spinnerRotate {
    from {
        transform: rotate(0deg);
    }
    to {
        transform: rotate(360deg);
    }
}

@keyframes scaleIn {
    from {
        opacity: 0;
        transform: scale(0.95);
    }
    to {
        opacity: 1;
        transform: scale(1);
    }
}

@keyframes shimmer {
    0% {
        background-position: -1000px 0;
    }
    100% {
        background-position: 1000px 0;
    }
}

@keyframes statusPulse {
    0%, 100% {
        opacity: 1;
    }
    50% {
        opacity: 0.6;
    }
}

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
    padding: 14px 20px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    animation: slideIn 0.5s ease-out;
}

/* Responsive Design */
@media (max-width: 768px) {
    #main_container {
        max-width: 100%;
        box-shadow: none;
    }

    #header {
        padding: 16px 20px;
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
    }

    #header h1 {
        font-size: 18px;
        margin: 0;
    }

    #header p {
        display: none;
    }

    #settings_bar {
        padding: 12px 20px;
        gap: 8px;
        flex-wrap: wrap;
    }

    #chatbot_container {
        min-height: 300px;
    }

    #chatbot_container .message {
        max-width: 90%;
        font-size: 14px;
        padding: 10px 14px;
    }

    #input_section {
        padding: 12px 20px 16px;
        gap: 8px;
    }

    #prompt {
        font-size: 15px;
        padding: 12px 14px;
    }

    #send_btn {
        min-width: 44px;
        height: 44px;
        padding: 12px 16px;
    }

    #clear_btn {
        padding: 10px 16px;
        font-size: 13px;
    }
}

@media (max-width: 480px) {
    #main_container {
        max-width: 100%;
    }

    #header {
        padding: 12px 16px;
        gap: 12px;
        flex-direction: column;
    }

    #header h1 {
        font-size: 16px;
    }

    .provider-card {
        padding: 12px;
    }

    #settings_bar {
        padding: 10px 16px;
        flex-direction: column;
    }

    #settings_bar .gradio-dropdown {
        width: 100%;
    }

    #input_section {
        padding: 10px 16px 14px;
        flex-direction: column;
    }

    #prompt {
        width: 100%;
        padding: 12px 12px;
    }

    #send_btn {
        width: 100%;
        height: 42px;
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
    gap: 8px;
    padding: 10px 20px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    align-items: center;
    flex-wrap: wrap;
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

/* Card Base Styles */
.card {
    padding: 10px 12px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.2s ease;
    animation: scaleIn 0.3s ease-out;
}

.card:hover {
    border-color: var(--accent);
    background: white;
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

.card.active {
    background: var(--accent);
    color: var(--user-text);
    border-color: var(--accent);
    box-shadow: var(--shadow-md);
}

/* Provider Card */
.provider-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
    padding: 12px 8px;
    text-align: center;
}

.provider-card-icon {
    font-size: 32px;
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.provider-card-name {
    font-size: 13px;
    font-weight: 600;
}

.provider-card-status {
    font-size: 10px;
    opacity: 0.7;
}

.provider-card.active .provider-card-status {
    opacity: 1;
}

#clear_btn {
    background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    color: var(--user-text);
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    font-weight: 600;
    font-size: 13px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    cursor: pointer;
    background-image: url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2716%27 height=%2716%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27currentColor%27 stroke-width=%272%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3E%3Cpolyline points=%273 6 5 6 21 6%27%3E%3C/polyline%3E%3Cpath d=%27M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2%27%3E%3C/path%3E%3C/svg%3E');
    background-repeat: no-repeat;
    background-position: 10px center;
    background-size: 16px 16px;
    padding-left: 32px;
}

#clear_btn:hover {
    background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%);
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
    position: relative;
    overflow-y: auto;
}

#chatbot_container .chatbot {
    background: var(--surface);
    border: none;
}

#chatbot_container .message {
    border-radius: var(--radius-lg);
    padding: 10px 14px;
    margin: 4px 0;
    max-width: 80%;
    line-height: 1.6;
    font-size: 15px;
    border: none;
    box-shadow: var(--shadow-sm);
    animation: fadeInUp 0.4s ease-out;
    transition: box-shadow 0.2s ease;
}

#chatbot_container .message:hover {
    box-shadow: var(--shadow-md);
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

/* Code block styling */
#chatbot_container code {
    background: rgba(0, 0, 0, 0.06);
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Monaco', 'Courier New', monospace;
    font-size: 14px;
}

#chatbot_container .message.user code {
    background: rgba(255, 255, 255, 0.2);
    color: inherit;
}

#chatbot_container .message.assistant code {
    background: rgba(0, 0, 0, 0.08);
    color: #e11d48;
}

#chatbot_container pre {
    background: #1e293b;
    color: #e2e8f0;
    padding: 14px;
    border-radius: var(--radius-md);
    overflow-x: auto;
    margin: 8px 0;
    font-size: 13px;
    line-height: 1.5;
}

#chatbot_container pre code {
    background: transparent;
    padding: 0;
    color: inherit;
}

#chatbot_container blockquote {
    border-left: 3px solid var(--accent);
    padding-left: 12px;
    margin: 8px 0;
    color: var(--text-muted);
    font-style: italic;
}

#chatbot_container a {
    color: #4f46e5;
    text-decoration: none;
    border-bottom: 1px solid rgba(79, 70, 229, 0.3);
    transition: all 0.2s ease;
}

#chatbot_container a:hover {
    border-bottom-color: #4f46e5;
}

#chatbot_container strong {
    font-weight: 600;
}

#chatbot_container em {
    font-style: italic;
}

#input_section {
    padding: 12px 20px 14px;
    background: var(--surface);
    border-top: 1px solid var(--border);
    display: flex;
    gap: 8px;
    align-items: flex-end;
}

#prompt {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 12px 14px;
    font-size: 15px;
    transition: all 0.2s ease;
    resize: none;
    line-height: 1.4;
}

#prompt:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
    background: var(--surface);
    outline: none;
}

#prompt::placeholder {
    color: var(--text-muted);
}

#send_btn {
    background: var(--accent);
    color: var(--user-text);
    border: none;
    border-radius: var(--radius-md);
    padding: 12px 18px;
    font-weight: 600;
    font-size: 14px;
    transition: all 0.2s ease;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    min-width: 44px;
    height: 44px;
    background-image: url('data:image/svg+xml,%3Csvg xmlns=%27http://www.w3.org/2000/svg%27 width=%2720%27 height=%2720%27 viewBox=%270 0 24 24%27 fill=%27none%27 stroke=%27white%27 stroke-width=%272%27 stroke-linecap=%27round%27 stroke-linejoin=%27round%27%3E%3Cline x1=%2722%27 y1=%272%27 x2=%2711%27 y2=%2713%27%3E%3C/line%3E%3Cpolygon points=%2722 2 15 22 11 13 2 9 22 2%27%3E%3C/polygon%3E%3C/svg%3E');
    background-repeat: no-repeat;
    background-position: center;
    background-size: 20px 20px;
    text-indent: -9999px;
    overflow: hidden;
}

#send_btn:hover {
    background-color: var(--accent-hover);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}

#send_btn:active {
    transform: scale(0.98);
}

#send_btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
}

/* Loading spinner inside send btn */
#send_btn.loading {
    animation: pulse 1.5s ease-in-out infinite;
}

/* Hide Gradio footer */
footer {
    display: none;
}

/* Scrollbar styling - hide when not hovering */
#chatbot_container::-webkit-scrollbar {
    width: 0px;
}

#chatbot_container:hover::-webkit-scrollbar {
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

/* Accordion Styling (Settings Panel) */
#settings_accordion label {
    font-weight: 600 !important;
    color: var(--text) !important;
}

#settings_accordion .gradio-accordion-item {
    background: white !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-md) !important;
    transition: all 0.2s ease !important;
}

#settings_accordion .gradio-accordion-item:hover {
    border-color: var(--accent) !important;
    box-shadow: var(--shadow-sm) !important;
}

#settings_accordion .gradio-accordion-item-header {
    background: var(--bg) !important;
    border-bottom: 1px solid var(--border) !important;
}

#settings_accordion .gradio-accordion-item.open .gradio-accordion-item-header {
    background: var(--surface) !important;
    border-bottom: 1px solid var(--accent) !important;
}

/* Settings Textbox Styling */
#settings_accordion .gradio-textbox {
    margin-bottom: 12px !important;
}

#settings_accordion .gradio-textbox input {
    border-radius: var(--radius-sm) !important;
    border: 1px solid var(--border) !important;
    transition: all 0.2s ease !important;
}

#settings_accordion .gradio-textbox input:focus {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1) !important;
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


# Expose ASGI app for Vercel and other serverless platforms
app = demo.app

# Optional: local development support
if __name__ == "__main__":
    demo.launch()
