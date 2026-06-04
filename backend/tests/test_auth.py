from fastapi.testclient import TestClient

from app.main import app
from app.services import auth_service
from app.services.auth_service import DEMO_USER_NAME_POOLS


def test_login_returns_token_and_user_profile() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "employee@example.com", "password": "demo"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token_type"] == "bearer"
    assert payload["access_token"]
    assert payload["user"]["name"] in DEMO_USER_NAME_POOLS["employee"]
    assert payload["user"] == {
        "id": "u_employee",
        "name": payload["user"]["name"],
        "email": "employee@example.com",
        "role": "employee",
        "department": "People Operations",
        "permissions": ["chat:use"],
    }


def test_login_rejects_invalid_credentials() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/auth/login",
            json={"email": "employee@example.com", "password": "wrong"},
        )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_current_user_requires_bearer_token() -> None:
    with TestClient(app) as client:
        response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_current_user_returns_authenticated_profile() -> None:
    with TestClient(app) as client:
        login_response = client.post(
            "/api/auth/login",
            json={"email": "admin@example.com", "password": "demo"},
        )
        token = login_response.json()["access_token"]

        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    assert response.json()["name"] in DEMO_USER_NAME_POOLS["admin"]
    assert response.json() == {
        "id": "u_admin",
        "name": login_response.json()["user"]["name"],
        "email": "admin@example.com",
        "role": "admin",
        "department": "IT",
        "permissions": ["chat:use", "sources:manage", "feedback:review", "audit:read"],
    }


def test_authenticate_user_assigns_new_random_name_per_login(monkeypatch) -> None:
    selected_names = iter(("Maya Schneider", "Jonas Bauer"))

    def choose_name(names: tuple[str, ...]) -> str:
        assert names == DEMO_USER_NAME_POOLS["employee"]
        return next(selected_names)

    monkeypatch.setattr(auth_service.random, "choice", choose_name)

    first_login = auth_service.authenticate_user("employee@example.com", "demo")
    second_login = auth_service.authenticate_user("employee@example.com", "demo")

    assert first_login.name == "Maya Schneider"
    assert second_login.name == "Jonas Bauer"


def test_access_token_preserves_login_session_name() -> None:
    user = auth_service.DEMO_USERS["manager@example.com"].profile.model_copy(update={"name": "Clara Meier"})

    token = auth_service.create_access_token(user, "test-secret")
    resolved_user = auth_service.resolve_user_from_token(token, "test-secret")

    assert resolved_user.name == "Clara Meier"
    assert resolved_user.email == "manager@example.com"
