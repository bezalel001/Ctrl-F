from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import EmbeddingProviderDep, SessionDep, VectorStoreDep, require_permission
from app.core.config import Settings, get_settings
from app.models.ingestion import IndexSourceResponse
from app.models.source import SourceCreate, SourceRead, SourceUpdate
from app.models.user import UserProfile
from app.services.audit_service import create_audit_log
from app.services.ingestion_service import SourceIndexingError, index_source
from app.services.source_service import (
    SourceNotFoundError,
    SourceValidationError,
    create_source,
    delete_source,
    get_source,
    list_sources,
    update_source,
)

router = APIRouter(prefix="/api/sources", tags=["sources"])
SourceManager = Annotated[UserProfile, Depends(require_permission("sources:manage"))]


@router.get("", response_model=list[SourceRead])
def read_sources(session: SessionDep, _current_user: SourceManager) -> list[SourceRead]:
    return list_sources(session)


@router.post("", response_model=SourceRead, status_code=status.HTTP_201_CREATED)
def create_approved_source(
    source_in: SourceCreate,
    session: SessionDep,
    current_user: SourceManager,
) -> SourceRead:
    try:
        source = create_source(session, source_in, current_user)
        create_audit_log(
            session,
            event_type="source.created",
            actor=current_user,
            resource_type="source",
            resource_id=source.id,
            details={"title": source.title, "location": source.location},
        )
        return source
    except SourceValidationError as exc:
        create_audit_log(
            session,
            event_type="source.validation_failed",
            actor=current_user,
            resource_type="source",
            details={"location": source_in.location, "reason": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.get("/{source_id}", response_model=SourceRead)
def read_source(source_id: int, session: SessionDep, _current_user: SourceManager) -> SourceRead:
    try:
        return get_source(session, source_id)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found") from exc


@router.patch("/{source_id}", response_model=SourceRead)
def update_approved_source(
    source_id: int,
    source_in: SourceUpdate,
    session: SessionDep,
    current_user: SourceManager,
) -> SourceRead:
    try:
        source = update_source(session, source_id, source_in)
        create_audit_log(
            session,
            event_type="source.updated",
            actor=current_user,
            resource_type="source",
            resource_id=source.id,
            details={"title": source.title, "fields": sorted(source_in.model_dump(exclude_unset=True).keys())},
        )
        return source
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found") from exc
    except SourceValidationError as exc:
        create_audit_log(
            session,
            event_type="source.validation_failed",
            actor=current_user,
            resource_type="source",
            resource_id=source_id,
            details={"reason": str(exc)},
        )
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approved_source(source_id: int, session: SessionDep, current_user: SourceManager) -> Response:
    try:
        delete_source(session, source_id)
        create_audit_log(
            session,
            event_type="source.deleted",
            actor=current_user,
            resource_type="source",
            resource_id=source_id,
        )
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found") from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{source_id}/index", response_model=IndexSourceResponse)
def index_approved_source(
    source_id: int,
    session: SessionDep,
    current_user: SourceManager,
    embedding_provider: EmbeddingProviderDep,
    vector_store: VectorStoreDep,
    settings: Annotated[Settings, Depends(get_settings)],
) -> IndexSourceResponse:
    try:
        result = index_source(
            session=session,
            source_id=source_id,
            approved_sources_root=settings.approved_sources_root,
            embedding_provider=embedding_provider,
            vector_store=vector_store,
        )
        create_audit_log(
            session,
            event_type="source.indexed",
            actor=current_user,
            resource_type="source",
            resource_id=source_id,
            details={"chunk_count": result.chunk_count, "collection": result.collection},
        )
        return result
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found") from exc
    except SourceIndexingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
