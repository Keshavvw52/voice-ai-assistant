"""
Intent classification service.

Uses Groq when an API key is configured and falls back to local heuristics so
the assistant still works offline.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Optional

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

SYSTEM_PROMPT = """You are an intent classifier for a voice assistant.
Return ONLY valid JSON. Do not explain anything. Do not add extra text. Do not use markdown.

Supported intents and their JSON shapes:
1. create_task:    {"intent": "create_task", "task": "<task title>", "due_date": "<date or null>"}
2. list_tasks:     {"intent": "list_tasks"}
3. delete_task:    {"intent": "delete_task", "task": "<task title or id>"}
4. small_talk:     {"intent": "small_talk", "message": "<friendly response>"}
5. unknown:        {"intent": "unknown", "message": "Could not understand"}
"""

_LIST_PATTERNS = (
    "list tasks",
    "show tasks",
    "my tasks",
    "what are my tasks",
    "what's on my list",
    "whats on my list",
)
_DELETE_PREFIXES = (
    "delete",
    "remove",
    "clear",
    "mark done",
    "complete",
    "finish",
)
_CREATE_PREFIXES = (
    "add",
    "create",
    "make",
    "remember",
    "note",
    "remind me to",
    "meeting",
    "routine",
)
_SMALL_TALK = {
    "hello": "Hello! What would you like me to do?",
    "hi": "Hi! I can help you manage tasks.",
    "hey": "Hey there. Tell me a task and I will handle it.",
    "thanks": "You're welcome.",
    "thank you": "You're welcome.",
    "Love" : "Beautiful feelings",
}


async def classify_intent(text: str) -> dict:
    """Classify assistant intent using Groq or a local fallback."""
    cleaned = text.strip()
    if not cleaned:
        return {"intent": "unknown", "message": "Empty input"}

    if GROQ_API_KEY:
        remote_result = await _classify_with_groq(cleaned)
        if remote_result:
            return remote_result

    return _classify_locally(cleaned)


async def _classify_with_groq(text: str) -> Optional[dict]:
    """Attempt remote classification with Groq."""
    try:
        payload = json.dumps(
            {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": text},
                ],
                "temperature": 0,
            }
        ).encode("utf-8")
        request = Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        response_text = await asyncio.to_thread(_urlopen_text, request)
        data = json.loads(response_text)
        raw_content = data["choices"][0]["message"]["content"].strip()
        if raw_content.startswith("```"):
            raw_content = raw_content.strip("`").strip()
            if raw_content.lower().startswith("json"):
                raw_content = raw_content[4:].strip()
        parsed = json.loads(raw_content)
        if isinstance(parsed, dict) and parsed.get("intent"):
            return parsed
    except (HTTPError, URLError) as exc:
        logger.warning("Groq intent classification failed, using fallback: %s", exc)
    except Exception as exc:
        logger.warning("Groq intent classification failed, using fallback: %s", exc)
    return None


def _urlopen_text(request: Request) -> str:
    with urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8")


def _classify_locally(text: str) -> dict:
    """Offline heuristic classifier for task-focused voice commands."""
    lowered = re.sub(r"\s+", " ", text.lower()).strip()

    if lowered in _SMALL_TALK:
        return {"intent": "small_talk", "message": _SMALL_TALK[lowered]}

    if any(phrase in lowered for phrase in _LIST_PATTERNS):
        return {"intent": "list_tasks"}

    delete_task = _extract_after_prefix(lowered, _DELETE_PREFIXES)
    if delete_task:
        return {"intent": "delete_task", "task": delete_task}

    create_task = _extract_after_prefix(lowered, _CREATE_PREFIXES)
    if create_task:
        task, due_date = _extract_due_date(create_task)
        return {"intent": "create_task", "task": task, "due_date": due_date}

    if any(word in lowered for word in ("task", "todo", "to-do")):
        task, due_date = _extract_due_date(lowered)
        return {"intent": "create_task", "task": task, "due_date": due_date}

    return {"intent": "unknown", "message": "Could not understand"}


def _extract_after_prefix(text: str, prefixes: tuple[str, ...]) -> Optional[str]:
    for prefix in prefixes:
        if text.startswith(prefix):
            return text[len(prefix) :].strip(" :,-.") or None
    return None


def _extract_due_date(task_text: str) -> tuple[str, Optional[str]]:
    due_markers = (" tomorrow", " today", " tonight", " on ", " by ")
    lowered = task_text.lower()
    for marker in due_markers:
        index = lowered.find(marker)
        if index != -1:
            task = task_text[:index].strip(" ,.-")
            due_date = task_text[index + 1 :].strip(" ,.-")
            return (task or task_text.strip(), due_date or None)
    return task_text.strip(" ,.-"), None


def build_response_text(intent_data: dict, tasks: list | None = None) -> str:
    """Build a spoken response for the detected intent."""
    intent = intent_data.get("intent", "unknown")

    if intent == "create_task":
        task = intent_data.get("task", "task")
        due = intent_data.get("due_date")
        if due:
            return f"Got it! I've added '{task}' due {due} to your task list."
        return f"Done! I've added '{task}' to your task list."

    if intent == "list_tasks":
        if not tasks:
            return "You have no tasks right now. Would you like to add one?"
        task_titles = [t["title"] for t in tasks[:5]]
        joined = ", ".join(task_titles)
        plural = "s" if len(tasks) != 1 else ""
        return f"You have {len(tasks)} task{plural}. Here are some: {joined}."

    if intent == "delete_task":
        task = intent_data.get("task", "that task")
        return f"I've removed '{task}' from your task list."

    if intent == "small_talk":
        return intent_data.get("message", "I'm here to help! What would you like to do?")

    msg = intent_data.get("message", "I didn't quite catch that.")
    return f"Sorry, {msg}. Please try again."
