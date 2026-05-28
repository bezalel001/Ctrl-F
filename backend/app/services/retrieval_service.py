from dataclasses import dataclass

from app.models.user import UserProfile
from app.services.embedding_service import EmbeddingProvider
from app.storage.vector_store import RetrievedVector, VectorStore


@dataclass(frozen=True)
class RetrievedChunk:
    id: str
    text: str
    source_id: int
    source_title: str
    source_location: str
    score: float


def retrieve_authorized_chunks(
    *,
    question: str,
    user: UserProfile,
    embedding_provider: EmbeddingProvider,
    vector_store: VectorStore,
    limit: int = 5,
    candidate_limit: int = 20,
) -> list[RetrievedChunk]:
    question_embedding = embedding_provider.embed_texts([question])[0]
    candidates = vector_store.query(embedding=question_embedding, limit=candidate_limit)

    authorized = [
        _to_retrieved_chunk(candidate)
        for candidate in candidates
        if _is_authorized(candidate, user)
    ]
    return authorized[:limit]


def _is_authorized(candidate: RetrievedVector, user: UserProfile) -> bool:
    metadata = candidate.metadata
    if metadata.get("approval_status") != "approved":
        return False

    allowed_roles = _split_metadata_list(metadata.get("allowed_roles"))
    allowed_departments = _split_metadata_list(metadata.get("allowed_departments"))

    if not allowed_roles and not allowed_departments:
        return False

    return user.role in allowed_roles or user.department in allowed_departments


def _to_retrieved_chunk(candidate: RetrievedVector) -> RetrievedChunk:
    metadata = candidate.metadata
    return RetrievedChunk(
        id=candidate.id,
        text=candidate.document,
        source_id=int(metadata["source_id"]),
        source_title=str(metadata["source_title"]),
        source_location=str(metadata["source_location"]),
        score=candidate.score,
    )


def _split_metadata_list(value: object) -> set[str]:
    if not isinstance(value, str):
        return set()

    return {item.strip() for item in value.split(",") if item.strip()}

