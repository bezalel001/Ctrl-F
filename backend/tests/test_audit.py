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
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_admin_can_read_audit_logs_for_source_events(client: TestClient) -> None:
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

    response = client.get("/api/admin/audit", headers=_auth_headers(token))

    assert create_response.status_code == 201
    assert response.status_code == 200
    events = response.json()
    assert any(event["event_type"] == "auth.login_succeeded" for event in events)
    source_event = next(event for event in events if event["event_type"] == "source.created")
    assert source_event["actor_user_id"] == "u_admin"
    assert source_event["resource_type"] == "source"
    assert source_event["resource_id"] == str(create_response.json()["id"])
    assert source_event["details"]["title"] == "Vacation Policy"


def test_feedback_review_access_is_audited(client: TestClient) -> None:
    employee_token = _login(client, "employee@example.com")
    reviewer_token = _login(client, "admin@example.com")

    client.post("/api/feedback", headers=_auth_headers(employee_token), json=_feedback_payload())
    review_response = client.get(
        "/api/admin/feedback",
        headers=_auth_headers(reviewer_token),
        params={"rating": "helpful", "limit": 25},
    )
    audit_response = client.get("/api/admin/audit", headers=_auth_headers(reviewer_token))

    assert review_response.status_code == 200
    assert audit_response.status_code == 200
    review_event = next(event for event in audit_response.json() if event["event_type"] == "feedback.review_list")
    assert review_event["actor_user_id"] == "u_admin"
    assert review_event["details"] == {"rating": "helpful", "limit": 25}


def test_audit_logs_require_permission(client: TestClient) -> None:
    token = _login(client, "employee@example.com")

    response = client.get("/api/admin/audit", headers=_auth_headers(token))

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permission"}


def _feedback_payload() -> dict[str, object]:
    return {
        "message_id": "msg-1",
        "rating": "helpful",
        "question": "How much vacation do I get?",
        "answer": "Employees receive 25 paid vacation days.",
        "confidence": 0.91,
        "sources": [{"source_id": 1, "title": "Vacation Policy"}],
        "comment": None,
    }


def _login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
