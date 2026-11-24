import pytest

from app.core.config import settings
from app.schemas import AIActionItem, AIActionItems, AIDecisions, AISummary
from app.services import ai
from helpers import new_meeting


@pytest.fixture
def ai_configured(monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "test-key")
    monkeypatch.setattr(settings, "openrouter_model", "test-model")


def fake_ai(items):
    """Stands in for the model call, so the tests need no API key or network."""

    async def _call(client, key, meeting_date, transcript):
        if key == "summary":
            return AISummary(summary="A short summary.")
        if key == "decisions":
            return AIDecisions(decisions=["Ship on Monday"])
        return AIActionItems(action_items=items)

    return _call


def item(text, owner):
    return AIActionItem(text=text, owner=owner, due_date=None)


def analyse(client, meeting_id):
    return client.post(f"/api/meetings/{meeting_id}/analyse")


def test_analysis_saves_summary_decisions_and_items(alice, ai_configured, monkeypatch):
    monkeypatch.setattr(ai, "_call", fake_ai([item("Send the report", None)]))
    meeting = new_meeting(alice)
    response = analyse(alice, meeting["id"])
    assert response.status_code == 200, response.text
    body = alice.get(f"/api/meetings/{meeting['id']}").json()
    assert body["analysis_status"] == "done"
    assert body["summary"] == "A short summary."
    assert body["decisions"] == ["Ship on Monday"]
    assert [i["text"] for i in body["action_items"]] == ["Send the report"]


def test_owner_is_kept_only_when_named_in_transcript(alice, ai_configured, monkeypatch):
    monkeypatch.setattr(ai, "_call", fake_ai([item("Send the report", "Zed"), item("Book room", "Ann")]))
    meeting = new_meeting(alice, transcript="Ann: I will book the room.")
    analyse(alice, meeting["id"])
    items = alice.get(f"/api/meetings/{meeting['id']}").json()["action_items"]
    owners = {i["text"]: i["owner"] for i in items}
    assert owners == {"Send the report": None, "Book room": "Ann"}


def test_ai_outage_keeps_the_transcript(alice, ai_configured, monkeypatch):
    async def down(*args, **kwargs):
        raise ai.AIUnavailable("down")

    monkeypatch.setattr(ai, "_call", down)
    meeting = new_meeting(alice, transcript="Ann: keep this text safe.")
    assert analyse(alice, meeting["id"]).status_code == 503
    body = alice.get(f"/api/meetings/{meeting['id']}").json()
    assert body["analysis_status"] == "failed"
    assert body["transcript"] == "Ann: keep this text safe."


def test_invalid_ai_output_is_not_saved(alice, ai_configured, monkeypatch):
    async def garbage(*args, **kwargs):
        raise ai.AIInvalidOutput("bad shape")

    monkeypatch.setattr(ai, "_call", garbage)
    meeting = new_meeting(alice)
    assert analyse(alice, meeting["id"]).status_code == 503
    assert alice.get(f"/api/meetings/{meeting['id']}").json()["action_items"] == []


def test_missing_configuration_is_reported(alice, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_api_key", "")
    meeting = new_meeting(alice)
    response = analyse(alice, meeting["id"])
    assert response.status_code == 503
    assert "not configured" in response.text


def test_cannot_analyse_twice(alice, ai_configured, monkeypatch):
    monkeypatch.setattr(ai, "_call", fake_ai([]))
    meeting = new_meeting(alice)
    assert analyse(alice, meeting["id"]).status_code == 200
    assert analyse(alice, meeting["id"]).status_code == 409
