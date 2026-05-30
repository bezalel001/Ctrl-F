from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.dependencies import get_answer_generator, get_embedding_provider, get_vector_store
from app.core.config import Settings, get_settings
from app.main import app
from app.services.conversation_service import ConversationTurn
from app.services.retrieval_service import RetrievedChunk
from app.storage.database import get_session
from app.storage.vector_store import RetrievedVector, VectorRecord


class FakeEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, float(len(text))] for text in texts]


class FakeAnswerGenerator:
    def generate_answer(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
        history: list[ConversationTurn],
    ) -> str:
        return f"Employees receive 25 paid vacation days. Source: {chunks[0].source_title}."


@dataclass
class InMemoryVectorRecord:
    id: str
    document: str
    embedding: list[float]
    metadata: dict[str, str | int | float | bool]


class FakeVectorStore:
    collection_name = "integration_sources"

    def __init__(self) -> None:
        self.records: list[InMemoryVectorRecord] = []

    def upsert(self, records: list[VectorRecord]) -> None:
        self.records.extend(
            InMemoryVectorRecord(
                id=record.id,
                document=record.document,
                embedding=record.embedding,
                metadata=dict(record.metadata),
            )
            for record in records
        )

    def delete_by_source(self, source_id: int) -> None:
        self.records = [record for record in self.records if record.metadata.get("source_id") != source_id]

    def query(self, *, embedding: list[float], limit: int) -> list[RetrievedVector]:
        return [
            RetrievedVector(
                id=record.id,
                document=record.document,
                metadata=record.metadata,
                distance=None,
                score=0.91,
            )
            for record in self.records[:limit]
        ]


@pytest.fixture(name="integration_client")
def integration_client_fixture(tmp_path: Path) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    approved_root = tmp_path / "approved_sources"
    policy_dir = approved_root / "hr"
    policy_dir.mkdir(parents=True)
    (policy_dir / "vacation.md").write_text(
        "# Vacation Policy\n\nFull-time employees receive 25 paid vacation days per calendar year.",
        encoding="utf-8",
    )
    vector_store = FakeVectorStore()

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    def override_get_settings() -> Settings:
        return Settings(
            approved_sources_root=str(approved_root),
            openai_api_key="test-key",
            chroma_collection=vector_store.collection_name,
        )

    app.dependency_overrides[get_session] = override_get_session
    app.dependency_overrides[get_settings] = override_get_settings
    app.dependency_overrides[get_embedding_provider] = lambda: FakeEmbeddingProvider()
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_answer_generator] = lambda: FakeAnswerGenerator()

    yield TestClient(app)
    app.dependency_overrides.clear()


def test_login_source_index_chat_feedback_review_flow(integration_client: TestClient) -> None:
    admin_token = _login(integration_client, "admin@example.com")
    employee_token = _login(integration_client, "employee@example.com")

    source_response = integration_client.post(
        "/api/sources",
        headers=_auth_headers(admin_token),
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
    source_id = source_response.json()["id"]

    index_response = integration_client.post(
        f"/api/sources/{source_id}/index",
        headers=_auth_headers(admin_token),
    )
    chat_response = integration_client.post(
        "/api/chat",
        headers=_auth_headers(employee_token),
        json={"question": "How many vacation days do I receive?"},
    )
    chat_payload = chat_response.json()
    feedback_response = integration_client.post(
        "/api/feedback",
        headers=_auth_headers(employee_token),
        json={
            "message_id": chat_payload["message_id"],
            "rating": "helpful",
            "question": "How many vacation days do I receive?",
            "answer": chat_payload["answer"],
            "confidence": chat_payload["confidence"],
            "sources": chat_payload["sources"],
            "comment": None,
        },
    )
    review_response = integration_client.get("/api/admin/feedback", headers=_auth_headers(admin_token))
    audit_response = integration_client.get("/api/admin/audit", headers=_auth_headers(admin_token))

    assert source_response.status_code == 201
    assert index_response.status_code == 200
    assert index_response.json()["chunk_count"] == 1
    assert chat_response.status_code == 200
    assert "25 paid vacation days" in chat_payload["answer"]
    assert chat_payload["sources"][0]["title"] == "Vacation Policy"
    assert chat_payload["confidence"] == 0.91
    assert feedback_response.status_code == 201
    assert review_response.status_code == 200
    assert [record["message_id"] for record in review_response.json()] == [chat_payload["message_id"]]
    assert audit_response.status_code == 200
    assert {"source.created", "source.indexed", "feedback.review_list"} <= {
        event["event_type"] for event in audit_response.json()
    }


def _login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
