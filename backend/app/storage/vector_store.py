from dataclasses import dataclass
from typing import Any, Protocol

import chromadb


class VectorStoreError(Exception):
    """Raised when vector store operations fail."""


class VectorRecord(Protocol):
    id: str
    document: str
    embedding: list[float]
    metadata: dict[str, str | int | float | bool]


@dataclass(frozen=True)
class RetrievedVector:
    id: str
    document: str
    metadata: dict[str, str | int | float | bool]
    distance: float | None
    score: float


class VectorStore(Protocol):
    collection_name: str

    def upsert(self, records: list[VectorRecord]) -> None:
        """Add or update vector records."""

    def delete_by_source(self, source_id: int) -> None:
        """Delete all vector records for a source."""

    def query(self, *, embedding: list[float], limit: int) -> list[RetrievedVector]:
        """Return relevant vectors ordered by similarity."""


class ChromaVectorStore:
    def __init__(self, *, host: str, port: int, collection_name: str) -> None:
        self.collection_name = collection_name
        self._client = chromadb.HttpClient(host=host, port=port)
        self._collection = self._client.get_or_create_collection(name=collection_name)

    def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return

        self._collection.upsert(
            ids=[record.id for record in records],
            documents=[record.document for record in records],
            embeddings=[record.embedding for record in records],
            metadatas=[record.metadata for record in records],
        )

    def delete_by_source(self, source_id: int) -> None:
        self._collection.delete(where={"source_id": source_id})

    def query(self, *, embedding: list[float], limit: int) -> list[RetrievedVector]:
        result = self._collection.query(
            query_embeddings=[embedding],
            n_results=limit,
            where={"approval_status": "approved"},
            include=["documents", "metadatas", "distances"],
        )
        return _parse_chroma_query_result(result)


def _parse_chroma_query_result(result: dict[str, Any]) -> list[RetrievedVector]:
    ids = _first_result_list(result.get("ids"))
    documents = _first_result_list(result.get("documents"))
    metadatas = _first_result_list(result.get("metadatas"))
    distances = _first_result_list(result.get("distances"))

    retrieved: list[RetrievedVector] = []
    for index, vector_id in enumerate(ids):
        document = documents[index] if index < len(documents) else ""
        metadata = metadatas[index] if index < len(metadatas) and isinstance(metadatas[index], dict) else {}
        distance = distances[index] if index < len(distances) else None
        score = _distance_to_score(distance)
        retrieved.append(
            RetrievedVector(
                id=str(vector_id),
                document=str(document),
                metadata=metadata,
                distance=float(distance) if isinstance(distance, int | float) else None,
                score=score,
            ),
        )

    return retrieved


def _first_result_list(value: object) -> list[Any]:
    if isinstance(value, list) and value and isinstance(value[0], list):
        return value[0]
    if isinstance(value, list):
        return value
    return []


def _distance_to_score(distance: object) -> float:
    if not isinstance(distance, int | float):
        return 0.0

    return max(0.0, min(1.0, 1.0 / (1.0 + float(distance))))
