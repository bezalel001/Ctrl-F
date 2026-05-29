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


def test_user_can_submit_feedback(client: TestClient) -> None:
    token = _login(client, "employee@example.com")

    response = client.post(
        "/api/feedback",
        headers=_auth_headers(token),
        json=_feedback_payload("helpful"),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["id"] == 1
    assert payload["user_id"] == "u_employee"
    assert payload["rating"] == "helpful"
    assert payload["message_id"] == "msg-1"
    assert payload["sources"][0]["title"] == "Vacation Policy"


def test_reviewer_can_list_feedback_and_stats(client: TestClient) -> None:
    employee_token = _login(client, "employee@example.com")
    reviewer_token = _login(client, "hr@example.com")

    client.post("/api/feedback", headers=_auth_headers(employee_token), json=_feedback_payload("helpful"))
    client.post("/api/feedback", headers=_auth_headers(employee_token), json=_feedback_payload("not_helpful"))

    list_response = client.get("/api/admin/feedback", headers=_auth_headers(reviewer_token))
    stats_response = client.get("/api/admin/feedback/stats", headers=_auth_headers(reviewer_token))

    assert list_response.status_code == 200
    assert [item["rating"] for item in list_response.json()] == ["not_helpful", "helpful"]
    assert stats_response.status_code == 200
    assert stats_response.json() == {"total": 2, "helpful": 1, "not_helpful": 1}


def test_reviewer_can_filter_feedback(client: TestClient) -> None:
    employee_token = _login(client, "employee@example.com")
    reviewer_token = _login(client, "hr@example.com")

    client.post(
        "/api/feedback",
        headers=_auth_headers(employee_token),
        json=_feedback_payload("helpful", message_id="msg-1", confidence=0.91, source_id=1),
    )
    client.post(
        "/api/feedback",
        headers=_auth_headers(employee_token),
        json=_feedback_payload("not_helpful", message_id="msg-2", confidence=0.42, source_id=2),
    )

    list_response = client.get(
        "/api/admin/feedback",
        headers=_auth_headers(reviewer_token),
        params={"rating": "not_helpful", "max_confidence": 0.5, "source_id": 2},
    )
    stats_response = client.get(
        "/api/admin/feedback/stats",
        headers=_auth_headers(reviewer_token),
        params={"rating": "not_helpful", "max_confidence": 0.5, "source_id": 2},
    )

    assert list_response.status_code == 200
    assert [item["message_id"] for item in list_response.json()] == ["msg-2"]
    assert stats_response.status_code == 200
    assert stats_response.json() == {"total": 1, "helpful": 0, "not_helpful": 1}


def test_feedback_filter_rejects_invalid_confidence_range(client: TestClient) -> None:
    reviewer_token = _login(client, "hr@example.com")

    response = client.get(
        "/api/admin/feedback",
        headers=_auth_headers(reviewer_token),
        params={"min_confidence": 0.9, "max_confidence": 0.5},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "min_confidence must be less than or equal to max_confidence"}


def test_feedback_review_requires_permission(client: TestClient) -> None:
    token = _login(client, "employee@example.com")

    response = client.get("/api/admin/feedback", headers=_auth_headers(token))

    assert response.status_code == 403
    assert response.json() == {"detail": "Insufficient permission"}


def _feedback_payload(
    rating: str,
    *,
    message_id: str = "msg-1",
    confidence: float = 0.91,
    source_id: int = 1,
) -> dict[str, object]:
    return {
        "message_id": message_id,
        "rating": rating,
        "question": "How much vacation do I get?",
        "answer": "Employees receive 25 paid vacation days.",
        "confidence": confidence,
        "sources": [{"source_id": source_id, "title": "Vacation Policy"}],
        "comment": None,
    }


def _login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
