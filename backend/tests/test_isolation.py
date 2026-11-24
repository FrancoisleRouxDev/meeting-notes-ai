from helpers import new_meeting

ITEM = {"text": "Send the report", "owner": None, "due_date": None, "status": "to do"}


def test_user_cannot_read_another_users_meeting(alice, bob):
    meeting = new_meeting(alice)
    assert bob.get(f"/api/meetings/{meeting['id']}").status_code == 404
    assert alice.get(f"/api/meetings/{meeting['id']}").status_code == 200


def test_user_cannot_change_or_delete_another_users_meeting(alice, bob):
    meeting = new_meeting(alice)
    url = f"/api/meetings/{meeting['id']}"
    assert bob.patch(url, json={"title": "Hijacked"}).status_code == 404
    assert bob.delete(url + "?confirm=true").status_code == 404
    assert alice.get(url).json()["title"] == "Weekly sync"


def test_user_cannot_add_items_to_another_users_meeting(alice, bob):
    meeting = new_meeting(alice)
    response = bob.post(f"/api/meetings/{meeting['id']}/action-items", json=ITEM)
    assert response.status_code == 404


def test_user_cannot_change_or_delete_another_users_action_item(alice, bob):
    meeting = new_meeting(alice)
    item = alice.post(f"/api/meetings/{meeting['id']}/action-items", json=ITEM).json()
    assert bob.patch(f"/api/action-items/{item['id']}", json={"status": "done"}).status_code == 404
    assert bob.delete(f"/api/action-items/{item['id']}").status_code == 404
    assert alice.get("/api/action-items").json()[0]["status"] == "to do"


def test_lists_only_show_own_data(alice, bob):
    meeting = new_meeting(alice)
    alice.post(f"/api/meetings/{meeting['id']}/action-items", json=ITEM)
    assert bob.get("/api/meetings").json() == []
    assert bob.get("/api/action-items").json() == []
    assert len(alice.get("/api/action-items").json()) == 1
