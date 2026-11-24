from fastapi.testclient import TestClient

from app.main import app

PASSWORD = "StrongPass123"


def make_client(email: str, password: str = PASSWORD) -> TestClient:
    """Register (if needed) and log in as a user, returning a client that holds their session."""
    client = TestClient(app)
    client.post("/api/auth/register", json={"email": email, "password": password})
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return client


def new_meeting(client: TestClient, transcript: str = "Ann: I will send the report.") -> dict:
    response = client.post(
        "/api/meetings",
        json={"title": "Weekly sync", "meeting_date": "2026-11-23", "transcript": transcript},
    )
    assert response.status_code == 201, response.text
    return response.json()
