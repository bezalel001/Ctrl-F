from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.main import app
from app.storage.database import get_session


@pytest.fixture(name="client")
def client_fixture() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_admin_can_create_and_read_source(client: TestClient) -> None:
    token = _login(client, "admin@example.com")

    create_response = client.post(
        "/api/sources",
        headers=_auth_headers(token),
        json={
            "title": "Vacation Policy",
            "description": "Approved HR policy for paid time off.",
            "source_type": "document",
            "location": "data/approved_sources/hr/vacation.md",
            "owning_department": "Human Resources",
            "allowed_roles": ["employee", "manager"],
            "allowed_departments": [],
            "approval_status": "approved",
            "version": "2026.1",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == 1
    assert created["created_by"] == "u_admin"
    assert created["title"] == "Vacation Policy"
    assert created["allowed_roles"] == ["employee", "manager"]

    list_response = client.get("/api/sources", headers=_auth_headers(token))

    assert list_response.status_code == 200
    assert [source["title"] for source in list_response.json()] == ["Vacation Policy"]


def test_source_management_requires_permission(client: TestClient) -> None:
    token = _login(client, "employee@example.com")

    response = client.get("/api/sources", headers=_auth_headers(token))

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permission"}


def test_source_creation_rejects_unapproved_location(client: TestClient) -> None:
    token = _login(client, "admin@example.com")

    response = client.post(
        "/api/sources",
        headers=_auth_headers(token),
        json={
            "title": "Local Secret",
            "source_type": "document",
            "location": "../private/secret.md",
            "owning_department": "IT",
            "allowed_roles": ["admin"],
            "allowed_departments": [],
            "approval_status": "approved",
            "version": "1.0",
        },
    )

    assert response.status_code == 422
    assert "location must not contain parent directory references" in response.json()["detail"]


def test_approved_source_requires_access_scope(client: TestClient) -> None:
    token = _login(client, "admin@example.com")

    response = client.post(
        "/api/sources",
        headers=_auth_headers(token),
        json={
            "title": "Access Missing",
            "source_type": "document",
            "location": "data/approved_sources/hr/missing-access.md",
            "owning_department": "Human Resources",
            "allowed_roles": [],
            "allowed_departments": [],
            "approval_status": "approved",
            "version": "1.0",
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "approved sources must define role or department access"}


def test_admin_can_update_and_delete_source(client: TestClient) -> None:
    token = _login(client, "admin@example.com")
    create_response = client.post(
        "/api/sources",
        headers=_auth_headers(token),
        json={
            "title": "IT Helpdesk FAQ",
            "source_type": "document",
            "location": "data/approved_sources/it/helpdesk.md",
            "owning_department": "IT",
            "allowed_roles": ["employee"],
            "allowed_departments": [],
            "approval_status": "draft",
            "version": "1.0",
        },
    )
    source_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/sources/{source_id}",
        headers=_auth_headers(token),
        json={"approval_status": "approved", "allowed_departments": ["Engineering"]},
    )

    assert update_response.status_code == 200
    assert update_response.json()["approval_status"] == "approved"
    assert update_response.json()["allowed_departments"] == ["Engineering"]

    delete_response = client.delete(f"/api/sources/{source_id}", headers=_auth_headers(token))

    assert delete_response.status_code == 204

    read_response = client.get(f"/api/sources/{source_id}", headers=_auth_headers(token))

    assert read_response.status_code == 404


def _login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
