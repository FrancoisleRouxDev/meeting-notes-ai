import asyncio
import calendar
import json
import re
from datetime import date, timedelta

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.schemas import AIActionItems, AIDecisions, AISummary

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
_MONTHS = {
    name.lower(): month
    for month in range(1, 13)
    for name in (calendar.month_name[month], calendar.month_abbr[month])
}
_MONTH_PATTERN = "|".join(
    re.escape(name) for name in sorted(_MONTHS, key=len, reverse=True)
)
_WEEKDAYS = {
    name.lower(): weekday
    for weekday, name in enumerate(calendar.day_name)
}
_WEEKDAY_PATTERN = "|".join(_WEEKDAYS)


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
        "List the decisions the group made: choices about what to do, when, or which option to take. "
        "A task someone agreed to do is not a decision, so leave it out. "
        "Scheduling the next meeting or event is not a decision, so leave it out. "
        "Example of a decision: 'We agreed not to renew until the invoice is fixed.' "
        "Examples of things that are not decisions: 'The next review is on 3 December.' "
        "and 'Priya will send the quotes.' "
        "Return an empty list if the group made no decisions.",
    ),
    "action_items": (
        AIActionItems,
        "List each task that a named person or the whole group clearly committed to doing. "
        "Leave out suggestions, wishes, and things the group said they would look at 'at some point'. "
        "Include a task that nobody was named for, with owner set to null. "
        "Include each task once, even if it was mentioned several times. "
        "Set owner only to a name the transcript gives for that task, otherwise null. "
        "For a non-null owner, include owner_evidence as an exact, contiguous quote from the transcript "
        "that names them as responsible for this task; otherwise set both owner and owner_evidence to null. "
        "Set due_date (YYYY-MM-DD) only when the transcript gives a deadline for the task itself, "
        "never the date of a meeting or event it mentions. "
        "For a non-null due_date, include due_date_evidence as an exact, contiguous quote from the transcript "
        "that states this task's deadline; otherwise set both due_date and due_date_evidence to null. "
        "If a task is to chase or follow up something that has a stated deadline, that deadline is the "
        "task's due_date. Example: 'Thabo, chase the security questionnaire, it was due on the 9th' gives "
        "owner 'Thabo', text 'Chase the security questionnaire', and due_date for the 9th. "
        "For a date given without a year or month, such as 'the 9th' or 'Friday', use the meeting date's "
        "year and month, and resolve weekdays from the meeting date. "
        "If nothing was committed to, return an empty list.",
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


def _dates_in_evidence(evidence: str, meeting_date: date) -> set[date]:
    """Resolve only unambiguous date forms from a verbatim transcript quote."""
    dates: set[date] = set()

    def add_date(year: int, month: int, day: int) -> None:
        try:
            dates.add(date(year, month, day))
        except ValueError:
            pass

    for match in re.finditer(r"(?<!\d)(\d{4})-(\d{1,2})-(\d{1,2})(?!\d)", evidence):
        add_date(*(int(part) for part in match.groups()))

    for match in re.finditer(
        rf"\b(?P<month>{_MONTH_PATTERN})\.?\s+(?P<day>\d{{1,2}})"
        rf"(?:st|nd|rd|th)?(?:,?\s+(?P<year>\d{{4}}))?\b",
        evidence,
        flags=re.IGNORECASE,
    ):
        add_date(
            int(match.group("year") or meeting_date.year),
            _MONTHS[match.group("month").lower()],
            int(match.group("day")),
        )

    for match in re.finditer(
        rf"\b(?P<day>\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?"
        rf"(?P<month>{_MONTH_PATTERN})\.?(?:,?\s+(?P<year>\d{{4}}))?\b",
        evidence,
        flags=re.IGNORECASE,
    ):
        add_date(
            int(match.group("year") or meeting_date.year),
            _MONTHS[match.group("month").lower()],
            int(match.group("day")),
        )

    has_month = re.search(rf"\b(?:{_MONTH_PATTERN})\.?\b", evidence, re.IGNORECASE)
    has_year = re.search(r"\b\d{4}\b", evidence)
    if not has_month and not has_year:
        for match in re.finditer(r"\bthe\s+(\d{1,2})(?:st|nd|rd|th)\b", evidence, re.IGNORECASE):
            add_date(meeting_date.year, meeting_date.month, int(match.group(1)))

    lowered = evidence.lower()
    if re.search(r"\btoday\b", lowered):
        dates.add(meeting_date)
    if re.search(r"\btomorrow\b", lowered):
        dates.add(meeting_date + timedelta(days=1))
    for match in re.finditer(r"\bin\s+(\d+)\s+(day|week)s?\b", lowered):
        amount = int(match.group(1)) * (7 if match.group(2) == "week" else 1)
        dates.add(meeting_date + timedelta(days=amount))

    for match in re.finditer(
        rf"\b(?:(next)\s+)?({_WEEKDAY_PATTERN})\b", lowered
    ):
        target_weekday = _WEEKDAYS[match.group(2)]
        days_ahead = (target_weekday - meeting_date.weekday()) % 7
        if match.group(1) and days_ahead == 0:
            days_ahead = 7
        dates.add(meeting_date + timedelta(days=days_ahead))

    return dates


def _owner_is_supported(owner: str, evidence: str, transcript: str) -> bool:
    return evidence in transcript and re.search(
        rf"(?<!\w){re.escape(owner)}(?!\w)", evidence, re.IGNORECASE
    ) is not None


def _ground_action_items(items: AIActionItems, transcript: str, meeting_date: date) -> None:
    for item in items.action_items:
        if item.owner and (
            not item.owner_evidence
            or not _owner_is_supported(item.owner, item.owner_evidence, transcript)
        ):
            item.owner = None

        if item.due_date:
            evidence = item.due_date_evidence
            if (
                not evidence
                or evidence not in transcript
                or _dates_in_evidence(evidence, meeting_date) != {item.due_date}
            ):
                item.due_date = None


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

    _ground_action_items(items, transcript, meeting_date)

    return summary.summary, decisions.decisions, items.action_items
