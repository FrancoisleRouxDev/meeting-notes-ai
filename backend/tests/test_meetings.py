def create_calendar_meeting(client):
    return client.post(
        "/api/meetings",
        json={"title": "Project kickoff", "meeting_date": "2026-11-25"},
    )


def test_create_meeting_without_transcript(alice):
    response = create_calendar_meeting(alice)

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["transcript"] is None
    assert body["analysis_status"] == "pending"
    assert alice.get("/api/meetings").json()[0]["title"] == "Project kickoff"


def test_attach_transcript_to_calendar_meeting(alice):
    meeting = create_calendar_meeting(alice).json()

    response = alice.post(
        f"/api/meetings/{meeting['id']}/transcript",
        json={"transcript": "  Alex: Send the updated agenda.  "},
    )

    assert response.status_code == 200, response.text
    assert response.json()["transcript"] == "Alex: Send the updated agenda."
    assert response.json()["analysis_status"] == "pending"


def test_upload_transcript_to_calendar_meeting(alice):
    meeting = create_calendar_meeting(alice).json()

    response = alice.post(
        f"/api/meetings/{meeting['id']}/transcript/upload",
        files={"file": ("notes.md", b"Alex: Send the updated agenda.", "text/markdown")},
    )

    assert response.status_code == 200, response.text
    assert response.json()["transcript"] == "Alex: Send the updated agenda."


def test_calendar_meeting_requires_transcript_before_analysis(alice):
    meeting = create_calendar_meeting(alice).json()

    response = alice.post(f"/api/meetings/{meeting['id']}/analyse")

    assert response.status_code == 409
    assert response.json()["detail"] == "Add a transcript before analysing this meeting"


def test_transcript_cannot_be_replaced(alice):
    meeting = create_calendar_meeting(alice).json()
    alice.post(
        f"/api/meetings/{meeting['id']}/transcript",
        json={"transcript": "First transcript."},
    )

    response = alice.post(
        f"/api/meetings/{meeting['id']}/transcript",
        json={"transcript": "Replacement transcript."},
    )

    assert response.status_code == 409
    assert alice.get(f"/api/meetings/{meeting['id']}").json()["transcript"] == "First transcript."


def test_cannot_attach_transcript_to_another_users_meeting(alice, bob):
    meeting = create_calendar_meeting(alice).json()

    response = bob.post(
        f"/api/meetings/{meeting['id']}/transcript",
        json={"transcript": "Private transcript."},
    )

    assert response.status_code == 404
