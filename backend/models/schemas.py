"""
Pydantic models for request/response validation.
"""

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = None


class TaskResponse(BaseModel):
    id: int
    title: str
    due_date: Optional[str]
    status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class TranscriptResponse(BaseModel):
    text: str
    confidence: Optional[float] = None


class IntentResponse(BaseModel):
    intent: str
    task: Optional[str] = None
    due_date: Optional[str] = None
    message: Optional[str] = None


class VoiceUploadResponse(BaseModel):
    transcript: str
    intent: str
    response_text: str
    audio_url: Optional[str] = None
    tasks: Optional[list] = None