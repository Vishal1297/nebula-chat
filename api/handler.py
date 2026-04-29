from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import gradio as gr
import sys
from pathlib import Path
import logging

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)

# Ensure app.py is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

# Attempt to import the Gradio app
try:
    from app import demo, css

    logger.info("Successfully loaded Gradio app")
except Exception as e:
    logger.error(f"Failed to load Gradio app: {e}")
    raise

# Create FastAPI app
fastapi_app = FastAPI(
    title="NebulaChat API", description="API for NebulaChat - Multi-provider chat interface", version="0.1.0"
)

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production to specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limit error handler
fastapi_app.state.limiter = limiter
fastapi_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# Add health check endpoint with rate limiting
@fastapi_app.get("/health")
@limiter.limit("5/minute")
async def health_check(request: Request):
    return {"status": "ok", "message": "NebulaChat is running"}


# Add error handlers
@fastapi_app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Mount Gradio app
app = gr.mount_gradio_app(fastapi_app, demo, path="/", css=css)


# Log startup
@fastapi_app.on_event("startup")
async def startup_event():
    logger.info("NebulaChat API started successfully")
