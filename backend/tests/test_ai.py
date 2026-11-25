from datetime import date

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


def item(
    text,
    owner=None,
    due_date=None,
    owner_evidence=None,
    due_date_evidence=None,
    source_evidence=None,
) -> AIActionItem:
    return AIActionItem(
        text=text,
        owner=owner,
        owner_evidence=owner_evidence,
        due_date=due_date,
        due_date_evidence=due_date_evidence,
        source_evidence=source_evidence,
    )


def analyse(client, meeting_id):
    return client.post(f"/api/meetings/{meeting_id}/analyse")


def test_analysis_saves_summary_decisions_and_items(alice, ai_configured, monkeypatch):
    monkeypatch.setattr(
        ai,
        "_call",
        fake_ai([item("Send the report", source_evidence="Ann: I will send the report.")]),
    )
    meeting = new_meeting(
        alice,
        transcript="Weekly sync\nAnn: I will send the report.\n",
    )
    response = analyse(alice, meeting["id"])
    assert response.status_code == 200, response.text
    body = alice.get(f"/api/meetings/{meeting['id']}").json()
    assert body["analysis_status"] == "done"
    assert body["summary"] == "A short summary."
    assert body["decisions"] == ["Ship on Monday"]
    assert len(body["action_items"]) == 1
    assert body["action_items"][0]["text"] == "Send the report"
    assert body["action_items"][0]["source_line"] == 2


def test_invalid_source_quote_is_not_saved_as_a_line(alice, ai_configured, monkeypatch):
    monkeypatch.setattr(
        ai,
        "_call",
        fake_ai([item("Send the report", source_evidence="An invented transcript quote.")]),
    )
    meeting = new_meeting(alice)

    response = analyse(alice, meeting["id"])
    assert response.status_code == 200, response.text
    assert response.json()["action_items"][0]["source_line"] is None


def test_source_evidence_maps_to_line_number_across_line_endings():
    assert ai.source_line_for_evidence(
        "Agenda\r\nAnn: I will send the report.\r\n", "Ann: I will send the report."
    ) == 2


def test_owner_is_kept_only_when_named_in_transcript(alice, ai_configured, monkeypatch):
    monkeypatch.setattr(
        ai,
        "_call",
        fake_ai(
            [
                item("Send the report", "Zed", owner_evidence="Zed will send the report."),
                item("Book room", "Ann", owner_evidence="Ann: I will book the room."),
                item("Send the annual report", "Ann", owner_evidence="The annual report is ready."),
            ]
        ),
    )
    meeting = new_meeting(
        alice,
        transcript="Ann: I will book the room. The annual report is ready.",
    )
    analyse(alice, meeting["id"])
    items = alice.get(f"/api/meetings/{meeting['id']}").json()["action_items"]
    owners = {i["text"]: i["owner"] for i in items}
    assert owners == {
        "Send the report": None,
        "Book room": "Ann",
        "Send the annual report": None,
    }


def test_due_date_requires_an_exact_quote_with_a_matching_date(alice, ai_configured, monkeypatch):
    monkeypatch.setattr(
        ai,
        "_call",
        fake_ai(
            [
                item(
                    "Send the report",
                    due_date=date(2026, 11, 27),
                    due_date_evidence="by November 27, 2026",
                ),
                item("Prepare slides", due_date=date(2026, 11, 27)),
                item(
                    "Book the room",
                    due_date=date(2026, 11, 28),
                    due_date_evidence="by November 27, 2026",
                ),
            ]
        ),
    )
    meeting = new_meeting(
        alice,
        transcript="Send the report by November 27, 2026. Prepare slides. Book the room by November 27, 2026.",
    )

    response = analyse(alice, meeting["id"])
    assert response.status_code == 200, response.text
    items = alice.get(f"/api/meetings/{meeting['id']}").json()["action_items"]
    dates = {item["text"]: item["due_date"] for item in items}
    assert dates == {
        "Send the report": "2026-11-27",
        "Prepare slides": None,
        "Book the room": None,
    }


def test_relative_weekday_evidence_uses_the_meeting_date():
    assert ai._dates_in_evidence("Please finish by Friday.", date(2026, 11, 25)) == {
        date(2026, 11, 27)
    }


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
