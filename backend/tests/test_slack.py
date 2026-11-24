import httpx
import pytest

from app.db import SessionLocal
from app.models_slack import SlackConnection
from helpers import new_meeting

URL = "https://hooks.slack.com/services/T000/B000/test"
STATUS = "/api/integrations/slack/connection"


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


@pytest.fixture
def sent(monkeypatch):
    calls = []

    async def fake_post(self, url, **kwargs):
        calls.append({"url": str(url), "json": kwargs.get("json")})
        return FakeResponse(200)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    return calls


def connect(client, url=URL):
    return client.put(STATUS, json={"url": url})


def test_connect_status_and_disconnect(alice):
    assert alice.get(STATUS).json() == {"connected": False}
    assert connect(alice).status_code == 200
    assert alice.get(STATUS).json() == {"connected": True}
    assert alice.delete(STATUS).status_code == 204
    assert alice.get(STATUS).json() == {"connected": False}


def test_webhook_is_stored_encrypted_and_never_returned(alice):
    connect(alice)
    with SessionLocal() as db:
        row = db.query(SlackConnection).one()
        assert "hooks.slack.com" not in row.webhook_encrypted
    assert "hooks.slack.com" not in alice.get(STATUS).text


def test_rejects_urls_that_are_not_slack_webhooks(alice):
    assert connect(alice, "https://example.com/hook").status_code == 422


def test_share_posts_to_my_own_webhook(alice, sent):
    connect(alice)
    meeting = new_meeting(alice)
    response = alice.post(f"/api/integrations/slack/share/{meeting['id']}")
    assert response.status_code == 200
    assert sent[0]["url"] == URL


def test_share_message_includes_items_and_escapes_formatting(alice, sent):
    connect(alice)
    meeting = new_meeting(alice)
    alice.post(
        f"/api/meetings/{meeting['id']}/action-items",
        json={"text": "Send <report> & more", "owner": "Ann", "due_date": "2026-11-27", "status": "to do"},
    )
    alice.post(f"/api/integrations/slack/share/{meeting['id']}")
    text = sent[0]["json"]["text"]
    assert "Weekly sync" in text
    assert "Send &lt;report&gt; &amp; more" in text
    assert "Owner: Ann, Due: 2026-11-27" in text


def test_share_needs_a_connected_channel(alice, sent):
    meeting = new_meeting(alice)
    response = alice.post(f"/api/integrations/slack/share/{meeting['id']}")
    assert response.status_code == 409
    assert sent == []


def test_connections_are_per_user(alice, bob, sent):
    connect(alice)
    assert bob.get(STATUS).json() == {"connected": False}
    meeting = new_meeting(alice)
    assert bob.post(f"/api/integrations/slack/share/{meeting['id']}").status_code == 404
    assert sent == []


def test_slack_failure_is_reported_and_meeting_kept(alice, monkeypatch):
    connect(alice)

    async def fail(self, url, **kwargs):
        return FakeResponse(500)

    monkeypatch.setattr(httpx.AsyncClient, "post", fail)
    meeting = new_meeting(alice)
    assert alice.post(f"/api/integrations/slack/share/{meeting['id']}").status_code == 503
    assert alice.get(f"/api/meetings/{meeting['id']}").status_code == 200
