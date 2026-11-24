from fastapi.testclient import TestClient

from app.main import app
from helpers import PASSWORD, make_client


def test_register_then_see_own_account():
    client = TestClient(app)
    response = client.post("/api/auth/register", json={"email": "new@example.com", "password": PASSWORD})
    assert response.status_code == 201
    client.post("/api/auth/login", json={"email": "new@example.com", "password": PASSWORD})
    me = client.get("/api/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == "new@example.com"


def test_duplicate_email_is_rejected():
    client = TestClient(app)
    client.post("/api/auth/register", json={"email": "dup@example.com", "password": PASSWORD})
    again = client.post("/api/auth/register", json={"email": "dup@example.com", "password": PASSWORD})
    assert again.status_code == 409


def test_short_password_is_rejected():
    response = TestClient(app).post(
        "/api/auth/register", json={"email": "short@example.com", "password": "short"}
    )
    assert response.status_code == 422


def test_wrong_password_is_rejected():
    make_client("login@example.com")
    response = TestClient(app).post(
        "/api/auth/login", json={"email": "login@example.com", "password": "WrongPass999"}
    )
    assert response.status_code == 401


def test_pages_need_a_login():
    assert TestClient(app).get("/api/meetings").status_code == 401
    assert TestClient(app).get("/api/auth/me").status_code == 401


def test_logout_ends_the_session(alice):
    assert alice.post("/api/auth/logout").status_code == 204
    assert alice.get("/api/auth/me").status_code == 401


def test_deleted_account_cannot_log_in(alice):
    assert alice.delete("/api/auth/me").status_code == 204
    response = TestClient(app).post(
        "/api/auth/login", json={"email": "alice@example.com", "password": PASSWORD}
    )
    assert response.status_code == 401
