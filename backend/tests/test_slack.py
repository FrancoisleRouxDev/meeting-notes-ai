import httpx
import pytest

from app.services import slack
from helpers import new_meeting


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


@pytest.fixture
def slack_configured(monkeypatch):
    monkeypatch.setattr(slack.slack_settings, "slack_webhook_url", "https://hooks.example.test/abc")


@pytest.fixture
def sent(monkeypatch):
    calls = []

    async def fake_post(self, url, **kwargs):
        calls.append({"url": str(url), "json": kwargs.get("json")})
        return FakeResponse(200)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    return calls


def test_not_configured_is_reported(alice, monkeypatch):
    monkeypatch.setattr(slack.slack_settings, "slack_webhook_url", "")
    meeting = new_meeting(alice)
    response = alice.post(f"/api/meetings/{meeting['id']}/share/slack")
    assert response.status_code == 503
    assert "not configured" in response.text


def test_sends_title_items_and_escapes_formatting(alice, slack_configured, sent):
    meeting = new_meeting(alice)
    alice.post(
        f"/api/meetings/{meeting['id']}/action-items",
        json={"text": "Send <report> & more", "owner": "Ann", "due_date": "2026-11-27", "status": "to do"},
    )
    response = alice.post(f"/api/meetings/{meeting['id']}/share/slack")
    assert response.status_code == 200
    assert sent[0]["url"] == "https://hooks.example.test/abc"
    text = sent[0]["json"]["text"]
    assert "Weekly sync" in text
    assert "Send &lt;report&gt; &amp; more" in text
    assert "Owner: Ann, Due: 2026-11-27" in text


def test_other_users_cannot_share_my_meeting(alice, bob, slack_configured, sent):
    meeting = new_meeting(alice)
    assert bob.post(f"/api/meetings/{meeting['id']}/share/slack").status_code == 404
    assert sent == []


def test_slack_failure_is_reported_and_meeting_kept(alice, slack_configured, monkeypatch):
    async def fail(self, url, **kwargs):
        return FakeResponse(500)

    monkeypatch.setattr(httpx.AsyncClient, "post", fail)
    meeting = new_meeting(alice)
    assert alice.post(f"/api/meetings/{meeting['id']}/share/slack").status_code == 503
    assert alice.get(f"/api/meetings/{meeting['id']}").status_code == 200
