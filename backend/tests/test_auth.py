from fastapi.testclient import TestClient

from app.main import app


def test_login_returns_token_and_user_profile() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/auth/login",
        json={"email": "employee@example.com", "password": "demo"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"] == {
        "id": "u_employee",
        "name": "Demo Employee",
        "email": "employee@example.com",
        "role": "employee",
        "department": "People Operations",
        "permissions": ["chat:use"],
    }


def test_login_rejects_invalid_credentials() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/auth/login",
        json={"email": "employee@example.com", "password": "wrong"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_current_user_requires_bearer_token() -> None:
    client = TestClient(app)

    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_current_user_returns_authenticated_profile() -> None:
    client = TestClient(app)
    login_response = client.post(
        "/api/auth/login",
        json={"email": "admin@example.com", "password": "demo"},
    )
    token = login_response.json()["access_token"]

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json() == {
        "id": "u_admin",
        "name": "Demo Admin",
        "email": "admin@example.com",
        "role": "admin",
        "department": "IT",
        "permissions": ["chat:use", "sources:manage", "feedback:review", "audit:read"],
    }

