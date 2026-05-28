from typing import Protocol

import chromadb


class VectorStoreError(Exception):
    """Raised when vector store operations fail."""


class VectorRecord(Protocol):
    id: str
    document: str
    embedding: list[float]
    metadata: dict[str, str | int | float | bool]


class VectorStore(Protocol):
    collection_name: str

    def upsert(self, records: list[VectorRecord]) -> None:
        """Add or update vector records."""

    def delete_by_source(self, source_id: int) -> None:
        """Delete all vector records for a source."""


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

