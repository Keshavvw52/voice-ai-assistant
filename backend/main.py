"""
Voice AI Assistant FastAPI backend.
"""

from __future__ import annotations


import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.database import init_db
from routes.tasks import router as tasks_router
from routes.voice import router as voice_router
from routes.auth import router as auth_router

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent
AUDIO_OUTPUT_DIR = BACKEND_DIR / "audio_output"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup and clean up on shutdown."""
    logger.info("Backend starting up")
    await init_db()
    AUDIO_OUTPUT_DIR.mkdir(exist_ok=True)
    logger.info("Audio output directory ready at %s", AUDIO_OUTPUT_DIR)
    yield
    logger.info("Shutting down Voice AI Assistant backend")


app = FastAPI(
    title="Voice AI Assistant API",
    description="Voice assistant using local Whisper, task management, and TTS",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/audio", StaticFiles(directory=AUDIO_OUTPUT_DIR), name="audio")
app.include_router(voice_router, prefix="/api/voice", tags=["Voice"])
app.include_router(tasks_router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "message": "Voice AI Assistant is running"}


@app.get("/")
def root():
    """Root API endpoint."""
    return {"message": "API working"}
