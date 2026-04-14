"""
Text-to-speech service with platform-aware fallbacks.
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import sys
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

BACKEND_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BACKEND_DIR / "audio_output"
OUTPUT_DIR.mkdir(exist_ok=True)

PIPER_BINARY = os.getenv("PIPER_BINARY", "piper")
PIPER_MODEL = os.getenv("PIPER_MODEL")


async def synthesize_speech(text: str) -> str:
    """Convert text to speech and return a static audio URL."""
    if not text or not text.strip():
        raise ValueError("TTS input text cannot be empty")

    output_filename = f"{uuid.uuid4().hex}.wav"
    output_path = OUTPUT_DIR / output_filename

    for engine_name, engine in _iter_tts_engines():
        try:
            await engine(text, output_path)
            logger.info("%s generated %s", engine_name, output_path)
            return f"/audio/{output_filename}"
        except Exception as exc:
            logger.warning("%s TTS failed: %s", engine_name, exc)

    raise RuntimeError(
        "No text-to-speech engine is available. Install Piper, Coqui TTS, or pyttsx3."
    )


def _iter_tts_engines():
    """Prefer system TTS first on Windows, offline engines elsewhere."""
    if sys.platform.startswith("win"):
        return (
            ("pyttsx3", _synthesize_pyttsx3),
            ("Piper", _synthesize_piper),
            ("Coqui", _synthesize_coqui),
        )

    return (
        ("Piper", _synthesize_piper),
        ("Coqui", _synthesize_coqui),
        ("pyttsx3", _synthesize_pyttsx3),
    )


async def _synthesize_piper(text: str, output_path: Path):
    """Use Piper via subprocess when both binary and model are configured."""
    if not shutil.which(PIPER_BINARY):
        raise RuntimeError("Piper binary not found on PATH.")
    if not PIPER_MODEL:
        raise RuntimeError("PIPER_MODEL is not configured.")

    model_path = Path(PIPER_MODEL)
    if not model_path.exists():
        raise RuntimeError(f"Piper model not found: {model_path}")

    proc = await asyncio.create_subprocess_exec(
        PIPER_BINARY,
        "--model",
        str(model_path),
        "--output_file",
        str(output_path),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate(input=text.encode("utf-8"))

    if proc.returncode != 0:
        raise RuntimeError(stderr.decode("utf-8", errors="ignore").strip())


async def _synthesize_coqui(text: str, output_path: Path):
    """Use Coqui TTS in a worker thread."""

    def _run():
        from TTS.api import TTS as CoquiTTS  # type: ignore

        tts = CoquiTTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
        tts.tts_to_file(text=text, file_path=str(output_path))

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run)


async def _synthesize_pyttsx3(text: str, output_path: Path):
    """Use platform TTS via pyttsx3 in a worker thread."""

    def _run():
        import pyttsx3  # type: ignore

        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        engine.setProperty("volume", 1.0)
        engine.save_to_file(text, str(output_path))
        engine.runAndWait()
        engine.stop()

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError("pyttsx3 did not produce an audio file.")

    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _run)
