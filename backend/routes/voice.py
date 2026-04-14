"""
Voice API Routes — the core pipeline:
  Audio Upload → STT → Intent → Task Engine → TTS → Response
"""

import logging
from fastapi import APIRouter, File, UploadFile, HTTPException

from services.stt_service import transcribe_audio
from services.llm_service import classify_intent, build_response_text
from services.tts_service import synthesize_speech
from services import task_service
from models.schemas import VoiceUploadResponse, TranscriptResponse, IntentResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/upload", response_model=VoiceUploadResponse)
async def upload_and_process(file: UploadFile = File(...)):
    """
    Full pipeline endpoint:
    1. Receive audio file
    2. Transcribe with Whisper
    3. Classify intent with Groq (cloud LLM)
    4. Execute task action
    5. Synthesize TTS response
    6. Return everything to the frontend
    """

    # --- Validate file ---
    if not file.content_type or not any(
        ct in file.content_type for ct in ["audio", "video", "octet-stream"]
    ):
        logger.warning(f"Unexpected content type: {file.content_type}")

    logger.info(f"Received audio file: {file.filename} ({file.content_type})")

    # --- Step 1: Read audio ---
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read uploaded file: {e}")

    # --- Step 2: STT ---
    try:
        stt_result = await transcribe_audio(audio_bytes, file.filename or "audio.webm")
        transcript = stt_result["text"]

        if not transcript:
            raise HTTPException(
                status_code=422,
                detail="Speech not detected. Please speak clearly."
            )

    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # --- Step 3: Intent ---
    try:
        intent_data = await classify_intent(transcript)

        if not isinstance(intent_data, dict) or "intent" not in intent_data:
            raise ValueError("Invalid intent format")

    except Exception as e:
        logger.error(f"Intent classification failed: {e}")
        intent_data = {"intent": "unknown", "message": "Could not understand"}

    intent = intent_data.get("intent", "unknown")

    # --- Step 4: Task Engine ---
    current_tasks = []

    if intent == "create_task":
        task_title = intent_data.get("task", transcript)
        due_date = intent_data.get("due_date")
        await task_service.create_task(task_title, due_date)
        current_tasks = await task_service.list_tasks()

    elif intent == "list_tasks":
        current_tasks = await task_service.list_tasks()

    elif intent == "delete_task":
        task_ref = intent_data.get("task", "").strip()

        if not task_ref:
            intent_data["message"] = "Please specify which task to delete."
        else:
            deleted = await task_service.delete_task_by_title(task_ref)
            if not deleted:
                intent_data["message"] = f"I couldn't find a task matching '{task_ref}'"

        current_tasks = await task_service.list_tasks()

    # --- Step 5: Build response text ---
    response_text = build_response_text(intent_data, current_tasks)

    # --- Step 6: TTS ---
    audio_url = None
    try:
        audio_url = await synthesize_speech(response_text)
    except RuntimeError as e:
        logger.warning(f"TTS failed for response '{response_text}': {e}")

    # --- Step 7: Log ---
    await task_service.log_conversation(transcript, intent, response_text)

    # --- Final Response ---
    return VoiceUploadResponse(
        transcript=transcript,
        intent=intent,
        response_text=response_text,
        audio_url=audio_url,
        tasks=current_tasks,
    )


@router.post("/stt", response_model=TranscriptResponse)
async def speech_to_text_only(file: UploadFile = File(...)):
    """STT only"""
    audio_bytes = await file.read()
    try:
        result = await transcribe_audio(audio_bytes, file.filename or "audio.webm")
        return TranscriptResponse(
            text=result["text"],
            confidence=result.get("confidence")
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/intent", response_model=IntentResponse)
async def intent_only(payload: dict):
    """Intent only"""
    text = payload.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="'text' field is required")

    try:
        result = await classify_intent(text)
        return IntentResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))