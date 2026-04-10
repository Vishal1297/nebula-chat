from fastapi import FastAPI
import gradio as gr
import sys
from pathlib import Path

# Ensure app.py is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import demo

fastapi_app = FastAPI()

# Properly mount Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/")
