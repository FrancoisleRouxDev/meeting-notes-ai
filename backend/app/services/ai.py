import asyncio
import json
from datetime import date

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.schemas import AIActionItems, AIDecisions, AISummary

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class AIUnavailable(Exception):
    """Service down, slow, rate limited or out of budget. Retrying later may work."""


class AIInvalidOutput(Exception):
    """The AI answered, but not in the shape we asked for. Retrying may work."""


# One focused prompt per tool, rather than one large prompt. Each has its own schema.
PROMPTS = {
    "summary": (
        AISummary,
        "Summarise the meeting in 3 to 5 sentences. Use only what the transcript says.",
    ),
    "decisions": (
        AIDecisions,
        "List the decisions the group agreed on. A decision is an agreed outcome, not a "
        "suggestion or a question. Return an empty list if there are none.",
    ),
    "action_items": (
        AIActionItems,
        "List the tasks someone committed to. Set owner only to a name the transcript gives "
        "for that task, otherwise null. Set due_date (YYYY-MM-DD) only when the transcript "
        "states a deadline, worked out from the meeting date; otherwise null. Never guess.",
    ),
}


async def _call(client: httpx.AsyncClient, key: str, meeting_date: date, transcript: str):
    model_class, instruction = PROMPTS[key]
    body = {
        "model": settings.openrouter_model,
        "temperature": 0,  # same input should give the same output, which makes testing fair
        "messages": [
            {"role": "system", "content": instruction + " Reply only with JSON matching the schema."},
            {
                "role": "user",
                "content": f"Meeting date: {meeting_date.isoformat()}\n\nTranscript:\n{transcript}",
            },
        ],
        "response_format": {
            "type": "json_schema",
            # strict is off because free models support it unevenly. Pydantic is the real check.
            "json_schema": {"name": key, "strict": False, "schema": model_class.model_json_schema()},
        },
    }
    try:
        response = await client.post(OPENROUTER_URL, json=body)
    except httpx.HTTPError as exc:
        raise AIUnavailable("The AI service could not be reached") from exc
    if response.status_code != 200:
        raise AIUnavailable(f"The AI service returned status {response.status_code}")

    try:
        content = response.json()["choices"][0]["message"]["content"]
        # Some models wrap their JSON in a code fence. Remove it before parsing.
        content = content.strip().removeprefix("```json").removeprefix("```").removesuffix("```")
        return model_class.model_validate(json.loads(content))
    except (KeyError, IndexError, TypeError, ValueError, ValidationError) as exc:
        raise AIInvalidOutput(f"The AI's {key} response did not match the expected format") from exc


async def analyse_transcript(transcript: str, meeting_date: date):
    if not settings.openrouter_api_key or not settings.openrouter_model:
        raise AIUnavailable("AI is not configured. Set OPENROUTER_API_KEY and OPENROUTER_MODEL in backend/.env")

    headers = {"Authorization": f"Bearer {settings.openrouter_api_key}"}
    async with httpx.AsyncClient(headers=headers, timeout=settings.openrouter_timeout_seconds) as client:
        summary, decisions, items = await asyncio.gather(
            _call(client, "summary", meeting_date, transcript),
            _call(client, "decisions", meeting_date, transcript),
            _call(client, "action_items", meeting_date, transcript),
        )

    # Guardrail: an owner must appear in the transcript. If the name isn't there, the AI invented it.
    lowered = transcript.lower()
    for item in items.action_items:
        if item.owner and item.owner.lower() not in lowered:
            item.owner = None

    return summary.summary, decisions.decisions, items.action_items
