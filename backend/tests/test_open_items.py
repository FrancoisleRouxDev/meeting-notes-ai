from helpers import new_meeting


def add_item(client, meeting_id, text, owner, due_date, status):
    response = client.post(
        f"/api/meetings/{meeting_id}/action-items",
        json={"text": text, "owner": owner, "due_date": due_date, "status": status},
    )
    assert response.status_code == 201, response.text


def seeded(client):
    meeting = new_meeting(client)
    add_item(client, meeting["id"], "Send the report", "Ann", "2000-01-01", "to do")  # overdue
    add_item(client, meeting["id"], "Book the room", "Priya", "2999-01-01", "in progress")
    add_item(client, meeting["id"], "Old task", "Ann", None, "done")
    return client


def test_default_view_hides_done_items_and_sorts_by_due_date(alice):
    seeded(alice)
    items = alice.get("/api/action-items").json()
    assert [i["text"] for i in items] == ["Send the report", "Book the room"]


def test_items_include_their_meeting(alice):
    seeded(alice)
    item = alice.get("/api/action-items").json()[0]
    assert item["meeting_title"] == "Weekly sync"
    assert isinstance(item["meeting_id"], int)


def test_status_filter(alice):
    seeded(alice)
    items = alice.get("/api/action-items", params={"status": "done"}).json()
    assert [i["text"] for i in items] == ["Old task"]


def test_owner_filter_ignores_case(alice):
    seeded(alice)
    items = alice.get("/api/action-items", params={"owner": "PRIYA"}).json()
    assert [i["text"] for i in items] == ["Book the room"]


def test_overdue_filter(alice):
    seeded(alice)
    items = alice.get("/api/action-items", params={"overdue": "true"}).json()
    assert [i["text"] for i in items] == ["Send the report"]


def test_unknown_status_is_rejected(alice):
    assert alice.get("/api/action-items", params={"status": "blocked"}).status_code == 422
