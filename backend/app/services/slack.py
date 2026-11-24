import httpx
from pydantic_settings import BaseSettings, SettingsConfigDict


class SlackSettings(BaseSettings):
    # Read from the environment or backend/.env. The URL is a secret, so it never reaches the browser.
    slack_webhook_url: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


slack_settings = SlackSettings()

# Slack rejects messages over 40,000 characters. Stay well under that.
MAX_MESSAGE_LENGTH = 35_000


class SlackUnavailable(Exception):
    """Slack is not configured, could not be reached, or refused the message."""


def _escape(text: str) -> str:
    # Slack reads these three characters as formatting, so they are escaped.
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_message(meeting) -> str:
    lines = [f"*{_escape(meeting.title)}* ({meeting.meeting_date.isoformat()})"]
    if meeting.summary:
        lines += ["", "*Summary*", _escape(meeting.summary)]
    if meeting.decisions:
        lines += ["", "*Decisions*"] + [f"- {_escape(decision)}" for decision in meeting.decisions]
    if meeting.action_items:
        lines += ["", "*Action items*"]
        for item in meeting.action_items:
            owner = item.owner or "not stated"
            due = item.due_date.isoformat() if item.due_date else "not stated"
            lines.append(f"- {_escape(item.text)} | Owner: {_escape(owner)}, Due: {due}, {item.status}")
    return "\n".join(lines)[:MAX_MESSAGE_LENGTH]


async def post_meeting_to_slack(meeting) -> None:
    url = slack_settings.slack_webhook_url
    if not url:
        raise SlackUnavailable("Slack is not configured. Set SLACK_WEBHOOK_URL in backend/.env")

    text = build_message(meeting)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json={"text": text})
    except httpx.HTTPError as exc:
        # The URL is never put in an error message, so it can't leak into logs or responses.
        raise SlackUnavailable("Could not reach Slack") from exc
    if response.status_code != 200:
        raise SlackUnavailable(f"Slack returned status {response.status_code}")
