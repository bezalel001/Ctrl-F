from dataclasses import dataclass
from datetime import UTC, datetime

from sqlmodel import Session

from app.models.ingestion import IndexSourceResponse
from app.models.source import Source
from app.services.chunking_service import DocumentChunk, chunk_text
from app.services.document_loader import DocumentLoadError, load_source_document
from app.services.embedding_service import EmbeddingProvider
from app.services.source_service import SourceNotFoundError, get_source
from app.storage.vector_store import VectorStore


class SourceIndexingError(Exception):
    """Raised when an approved source cannot be indexed."""


@dataclass(frozen=True)
class SourceVectorRecord:
    id: str
    document: str
    embedding: list[float]
    metadata: dict[str, str | int | float | bool]


def index_source(
    *,
    session: Session,
    source_id: int,
    approved_sources_root: str,
    embedding_provider: EmbeddingProvider,
    vector_store: VectorStore,
) -> IndexSourceResponse:
    try:
        source = get_source(session, source_id)
    except SourceNotFoundError:
        raise

    if source.approval_status != "approved":
        raise SourceIndexingError("only approved sources can be indexed")

    try:
        loaded_document = load_source_document(source, approved_sources_root)
    except DocumentLoadError as exc:
        raise SourceIndexingError(str(exc)) from exc

    chunks = chunk_text(loaded_document.text)
    if not chunks:
        raise SourceIndexingError("source produced no indexable chunks")

    embeddings = embedding_provider.embed_texts([chunk.text for chunk in chunks])
    if len(embeddings) != len(chunks):
        raise SourceIndexingError("embedding provider returned the wrong number of embeddings")

    records = [
        SourceVectorRecord(
            id=_chunk_id(source, chunk),
            document=chunk.text,
            embedding=embedding,
            metadata=_chunk_metadata(source, chunk),
        )
        for chunk, embedding in zip(chunks, embeddings, strict=True)
    ]

    vector_store.delete_by_source(source.id)
    vector_store.upsert(records)

    indexed_at = datetime.now(UTC)
    source.indexed_at = indexed_at
    source.updated_at = indexed_at
    session.add(source)
    session.commit()
    session.refresh(source)

    return IndexSourceResponse(
        source_id=source.id,
        chunk_count=len(records),
        collection=vector_store.collection_name,
        indexed_at=indexed_at,
    )


def _chunk_id(source: Source, chunk: DocumentChunk) -> str:
    return f"source:{source.id}:version:{source.version}:chunk:{chunk.index}"


def _chunk_metadata(source: Source, chunk: DocumentChunk) -> dict[str, str | int | float | bool]:
    return {
        "source_id": source.id,
        "source_title": source.title,
        "source_type": source.source_type,
        "source_location": source.location,
        "owning_department": source.owning_department,
        "allowed_roles": ",".join(source.allowed_roles),
        "allowed_departments": ",".join(source.allowed_departments),
        "approval_status": source.approval_status,
        "version": source.version,
        "chunk_index": chunk.index,
    }

