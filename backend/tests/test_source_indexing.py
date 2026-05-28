from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.dependencies import get_embedding_provider, get_vector_store
from app.core.config import Settings, get_settings
from app.main import app
from app.storage.database import get_session


class FakeEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[float(len(text)), 1.0, 0.0] for text in texts]


class FakeVectorStore:
    collection_name = "test_sources"

    def __init__(self) -> None:
        self.deleted_source_ids: list[int] = []
        self.records: list[object] = []

    def upsert(self, records: list[object]) -> None:
        self.records.extend(records)

    def delete_by_source(self, source_id: int) -> None:
        self.deleted_source_ids.append(source_id)


@pytest.fixture(name="source_index_client")
def source_index_client_fixture(tmp_path: Path) -> Generator[tuple[TestClient, FakeVectorStore, Path], None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    approved_root = tmp_path / "approved_sources"
    approved_root.mkdir()
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

    client = TestClient(app)
    yield client, vector_store, approved_root
    app.dependency_overrides.clear()


def test_admin_can_index_approved_source(
    source_index_client: tuple[TestClient, FakeVectorStore, Path],
) -> None:
    client, vector_store, approved_root = source_index_client
    policy_dir = approved_root / "hr"
    policy_dir.mkdir()
    (policy_dir / "vacation.md").write_text(
        "# Vacation Policy\n\nEmployees receive paid time off according to role and contract.",
        encoding="utf-8",
    )
    token = _login(client, "admin@example.com")
    source_id = _create_source(client, token, "approved")

    response = client.post(f"/api/sources/{source_id}/index", headers=_auth_headers(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["source_id"] == source_id
    assert payload["chunk_count"] == 1
    assert payload["collection"] == "test_sources"
    assert payload["indexed_at"]

    assert vector_store.deleted_source_ids == [source_id]
    assert len(vector_store.records) == 1
    record = vector_store.records[0]
    assert record.id == f"source:{source_id}:version:2026.1:chunk:0"
    assert "Employees receive paid time off" in record.document
    assert record.embedding == [float(len(record.document)), 1.0, 0.0]
    assert record.metadata["source_id"] == source_id
    assert record.metadata["allowed_roles"] == "employee,manager"

    read_response = client.get(f"/api/sources/{source_id}", headers=_auth_headers(token))
    assert read_response.status_code == 200
    assert read_response.json()["indexed_at"] is not None


def test_indexing_rejects_draft_source(source_index_client: tuple[TestClient, FakeVectorStore, Path]) -> None:
    client, _vector_store, approved_root = source_index_client
    policy_dir = approved_root / "hr"
    policy_dir.mkdir()
    (policy_dir / "vacation.md").write_text("Draft policy.", encoding="utf-8")
    token = _login(client, "admin@example.com")
    source_id = _create_source(client, token, "draft")

    response = client.post(f"/api/sources/{source_id}/index", headers=_auth_headers(token))

    assert response.status_code == 422
    assert response.json() == {"detail": "only approved sources can be indexed"}


def test_indexing_rejects_missing_file(source_index_client: tuple[TestClient, FakeVectorStore, Path]) -> None:
    client, _vector_store, _approved_root = source_index_client
    token = _login(client, "admin@example.com")
    source_id = _create_source(client, token, "approved")

    response = client.post(f"/api/sources/{source_id}/index", headers=_auth_headers(token))

    assert response.status_code == 422
    assert response.json() == {"detail": "source file does not exist"}


def _create_source(client: TestClient, token: str, approval_status: str) -> int:
    create_response = client.post(
        "/api/sources",
        headers=_auth_headers(token),
        json={
            "title": "Vacation Policy",
            "description": "Approved HR policy for paid time off.",
            "source_type": "document",
            "location": "data/approved_sources/hr/vacation.md",
            "owning_department": "Human Resources",
            "allowed_roles": ["manager", "employee"],
            "allowed_departments": [],
            "approval_status": approval_status,
            "version": "2026.1",
        },
    )
    assert create_response.status_code == 201
    return create_response.json()["id"]


def _login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
