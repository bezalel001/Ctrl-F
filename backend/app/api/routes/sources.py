from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import SessionDep, require_permission
from app.models.source import SourceCreate, SourceRead, SourceUpdate
from app.models.user import UserProfile
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
        return create_source(session, source_in, current_user)
    except SourceValidationError as exc:
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
    _current_user: SourceManager,
) -> SourceRead:
    try:
        return update_source(session, source_id, source_in)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found") from exc
    except SourceValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_approved_source(source_id: int, session: SessionDep, _current_user: SourceManager) -> Response:
    try:
        delete_source(session, source_id)
    except SourceNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found") from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
