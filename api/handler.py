from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import gradio as gr
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure app.py is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Attempt to import the Gradio app
try:
    from app import demo
    logger.info("Successfully loaded Gradio app")
except Exception as e:
    logger.error(f"Failed to load Gradio app: {e}")
    raise

# Create FastAPI app
fastapi_app = FastAPI(
    title="NebulaChat API",
    description="API for NebulaChat - Multi-provider chat interface",
    version="0.1.0"
)

# Add health check endpoint
@fastapi_app.get("/health")
async def health_check():
    return {"status": "ok", "message": "NebulaChat is running"}

# Add error handlers
@fastapi_app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Mount Gradio app
app = gr.mount_gradio_app(fastapi_app, demo, path="/")

# Log startup
@fastapi_app.on_event("startup")
async def startup_event():
    logger.info("NebulaChat API started successfully")
