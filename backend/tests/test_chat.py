from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass

from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app.api.dependencies import get_answer_generator, get_embedding_provider, get_vector_store
from app.main import app
from app.services.conversation_service import ConversationTurn
from app.services.retrieval_service import RetrievedChunk
from app.storage.database import get_session
from app.storage.vector_store import RetrievedVector


class FakeEmbeddingProvider:
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [[1.0, 0.0, float(len(texts[0]))]]


@dataclass
class FakeAnswerGenerator:
    calls: int = 0
    last_history: list[ConversationTurn] | None = None

    def generate_answer(
        self,
        *,
        question: str,
        chunks: list[RetrievedChunk],
        history: list[ConversationTurn],
    ) -> str:
        self.calls += 1
        self.last_history = list(history)
        return f"Grounded answer for: {question}. Source: {chunks[0].source_title}."


class FakeVectorStore:
    collection_name = "test_sources"

    def __init__(self, results: list[RetrievedVector]) -> None:
        self.results = results

    def upsert(self, records: list[object]) -> None:
        raise NotImplementedError

    def delete_by_source(self, source_id: int) -> None:
        raise NotImplementedError

    def query(self, *, embedding: list[float], limit: int) -> list[RetrievedVector]:
        assert embedding[:2] == [1.0, 0.0]
        assert limit == 20
        return self.results


def test_chat_returns_grounded_answer_with_authorized_sources() -> None:
    vector_store = FakeVectorStore(
        [
            _retrieved_vector(
                source_id=1,
                title="Vacation Policy",
                allowed_roles="employee,manager",
                allowed_departments="",
                score=0.88,
            ),
            _retrieved_vector(
                source_id=2,
                title="Manager Compensation",
                allowed_roles="manager",
                allowed_departments="",
                score=0.97,
            ),
        ],
    )
    answer_generator = FakeAnswerGenerator()

    with _client(vector_store, answer_generator) as client:
        token = _login(client, "employee@example.com")
        response = client.post(
            "/api/chat",
            headers=_auth_headers(token),
            json={"question": "How much vacation do I get?"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["conversation_id"]
    assert payload["answer"].startswith("Grounded answer for")
    assert payload["confidence"] == 0.88
    assert payload["warning"] is None
    assert payload["suggested_contacts"] == []
    assert [source["title"] for source in payload["sources"]] == ["Vacation Policy"]
    assert answer_generator.calls == 1


def test_chat_returns_fallback_when_no_authorized_sources_exist() -> None:
    vector_store = FakeVectorStore(
        [
            _retrieved_vector(
                source_id=2,
                title="Manager Compensation",
                allowed_roles="manager",
                allowed_departments="",
                score=0.97,
            ),
        ],
    )
    answer_generator = FakeAnswerGenerator()

    with _client(vector_store, answer_generator) as client:
        token = _login(client, "employee@example.com")
        response = client.post(
            "/api/chat",
            headers=_auth_headers(token),
            json={"question": "How much vacation do I get?"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "I don't know based on the approved company sources available to me."
    assert payload["sources"] == []
    assert payload["confidence"] == 0.0
    assert payload["warning"] is not None
    assert payload["suggested_contacts"] == ["Human Resources", "IT Support"]
    assert answer_generator.calls == 0


def test_chat_uses_recent_conversation_history_for_followups() -> None:
    vector_store = FakeVectorStore(
        [
            _retrieved_vector(
                source_id=1,
                title="Vacation Policy",
                allowed_roles="employee",
                allowed_departments="",
                score=0.91,
            ),
        ],
    )
    answer_generator = FakeAnswerGenerator()

    with _client(vector_store, answer_generator) as client:
        token = _login(client, "employee@example.com")
        first_response = client.post(
            "/api/chat",
            headers=_auth_headers(token),
            json={"question": "How much vacation do I get?"},
        )
        conversation_id = first_response.json()["conversation_id"]

        second_response = client.post(
            "/api/chat",
            headers=_auth_headers(token),
            json={
                "question": "Can I carry it over?",
                "conversation_id": conversation_id,
            },
        )

    assert second_response.status_code == 200
    assert second_response.json()["conversation_id"] == conversation_id
    assert answer_generator.calls == 2
    assert answer_generator.last_history is not None
    assert [(turn.role, turn.content) for turn in answer_generator.last_history] == [
        ("user", "How much vacation do I get?"),
        (
            "assistant",
            "Grounded answer for: How much vacation do I get?. Source: Vacation Policy.",
        ),
    ]


def test_chat_does_not_expose_another_users_conversation() -> None:
    vector_store = FakeVectorStore(
        [
            _retrieved_vector(
                source_id=1,
                title="Vacation Policy",
                allowed_roles="employee,manager",
                allowed_departments="",
                score=0.91,
            ),
        ],
    )
    answer_generator = FakeAnswerGenerator()

    with _client(vector_store, answer_generator) as client:
        employee_token = _login(client, "employee@example.com")
        manager_token = _login(client, "manager@example.com")
        first_response = client.post(
            "/api/chat",
            headers=_auth_headers(employee_token),
            json={"question": "How much vacation do I get?"},
        )

        response = client.post(
            "/api/chat",
            headers=_auth_headers(manager_token),
            json={
                "question": "What did they ask?",
                "conversation_id": first_response.json()["conversation_id"],
            },
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Conversation not found"}


def test_chat_requires_authentication() -> None:
    with _client(FakeVectorStore([]), FakeAnswerGenerator()) as client:
        response = client.post("/api/chat", json={"question": "Hello?"})

    assert response.status_code == 401


@contextmanager
def _client(
    vector_store: FakeVectorStore,
    answer_generator: FakeAnswerGenerator,
) -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)

    def override_get_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_embedding_provider] = lambda: FakeEmbeddingProvider()
    app.dependency_overrides[get_vector_store] = lambda: vector_store
    app.dependency_overrides[get_answer_generator] = lambda: answer_generator
    app.dependency_overrides[get_session] = override_get_session
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def _retrieved_vector(
    *,
    source_id: int,
    title: str,
    allowed_roles: str,
    allowed_departments: str,
    score: float,
) -> RetrievedVector:
    return RetrievedVector(
        id=f"source:{source_id}:version:1.0:chunk:0",
        document=f"{title} says employees receive paid vacation.",
        metadata={
            "source_id": source_id,
            "source_title": title,
            "source_location": f"data/approved_sources/{source_id}.md",
            "approval_status": "approved",
            "allowed_roles": allowed_roles,
            "allowed_departments": allowed_departments,
        },
        distance=None,
        score=score,
    )


def _login(client: TestClient, email: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": "demo"})
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
