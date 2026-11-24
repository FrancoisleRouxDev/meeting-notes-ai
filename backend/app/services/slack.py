import httpx

# Slack rejects messages over 40,000 characters. Stay well under that.
MAX_MESSAGE_LENGTH = 35_000


class SlackUnavailable(Exception):
    """Slack refused the message or could not be reached."""


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


async def post_meeting_to_slack(meeting, webhook_url: str) -> None:
    text = build_message(meeting)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json={"text": text})
    except httpx.HTTPError as exc:
        # The URL is never put in an error message, so it can't leak into logs or responses.
        raise SlackUnavailable("Could not reach Slack") from exc
    if response.status_code != 200:
        raise SlackUnavailable(f"Slack returned status {response.status_code}")
