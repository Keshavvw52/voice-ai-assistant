"""
Speech-to-text service backed by OpenAI Whisper.

The frontend uploads PCM WAV audio so we can decode it locally without
depending on an external ffmpeg binary.
"""

from __future__ import annotations

import io
import logging
import os
import wave
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

_whisper_model = None
_model_size = os.getenv("WHISPER_MODEL", "base")
_supported_suffixes = {".wav", ".wave"}


def _get_model():
    """Lazy-load the Whisper model and keep it cached."""
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper

            logger.info("Loading Whisper model '%s'...", _model_size)
            _whisper_model = whisper.load_model(_model_size)
            logger.info("Whisper model loaded successfully.")
        except ImportError as exc:
            raise RuntimeError(
                "openai-whisper is not installed. Run: pip install openai-whisper"
            ) from exc
        except Exception as exc:
            raise RuntimeError(f"Failed to load Whisper model: {exc}") from exc
    return _whisper_model


def _pcm_to_float32(samples: np.ndarray, sample_width: int) -> np.ndarray:
    """Normalise PCM samples to Whisper's expected float32 range."""
    if sample_width == 1:
        return ((samples.astype(np.float32) - 128.0) / 128.0).clip(-1.0, 1.0)

    scale = float(1 << (8 * sample_width - 1))
    return (samples.astype(np.float32) / scale).clip(-1.0, 1.0)


def _load_wav_audio(audio_bytes: bytes) -> np.ndarray:
    """Decode PCM WAV bytes to a mono float32 numpy array."""
    with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        frame_count = wav_file.getnframes()
        sample_rate = wav_file.getframerate()
        raw_frames = wav_file.readframes(frame_count)

    if sample_width not in {1, 2, 4}:
        raise RuntimeError(
            f"Unsupported WAV sample width: {sample_width * 8}-bit audio"
        )

    dtype_map = {1: np.uint8, 2: np.int16, 4: np.int32}
    samples = np.frombuffer(raw_frames, dtype=dtype_map[sample_width])

    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1)

    audio = _pcm_to_float32(samples, sample_width)

    if sample_rate <= 0:
        raise RuntimeError("Invalid sample rate in uploaded audio.")

    return audio


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """
    Transcribe uploaded WAV audio.

    Returns a dict containing transcribed text and an estimated confidence.
    """
    if not audio_bytes:
        raise ValueError("Audio bytes cannot be empty")

    suffix = Path(filename).suffix.lower()
    if suffix and suffix not in _supported_suffixes:
        raise RuntimeError(
            "Unsupported recording format. Please upload WAV audio from the frontend."
        )

    try:
        audio = _load_wav_audio(audio_bytes)
        model = _get_model()

        logger.info("Transcribing %s bytes of WAV audio", len(audio_bytes))
        result = model.transcribe(
            audio,
            language=None,
            fp16=False,
            verbose=False,
        )

        text = result.get("text", "").strip()
        logger.info("Transcription result: '%s'", text)

        segments = result.get("segments", [])
        confidence: Optional[float] = None
        if segments:
            avg_no_speech = sum(s.get("no_speech_prob", 0.0) for s in segments) / len(
                segments
            )
            confidence = round(1.0 - avg_no_speech, 3)

        return {"text": text, "confidence": confidence}
    except wave.Error as exc:
        logger.error("Invalid WAV upload: %s", exc)
        raise RuntimeError("Speech-to-text failed: invalid WAV audio upload.") from exc
    except RuntimeError:
        raise
    except Exception as exc:
        logger.exception("Transcription failed")
        raise RuntimeError(f"Speech-to-text failed: {exc}") from exc
