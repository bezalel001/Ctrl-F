from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.source import Source, SourceCreate, SourceUpdate
from app.models.user import UserProfile

APPROVAL_STATUSES = {"draft", "approved", "archived"}
SOURCE_TYPES = {"document", "url", "repository"}
APPROVED_LOCATION_PREFIXES = ("data/approved_sources/", "https://", "http://")


class SourceValidationError(Exception):
    """Raised when source metadata fails authorization rules."""


class SourceNotFoundError(Exception):
    """Raised when a source does not exist."""


def list_sources(session: Session) -> list[Source]:
    return list(session.exec(select(Source).order_by(Source.created_at.desc())).all())


def get_source(session: Session, source_id: int) -> Source:
    source = session.get(Source, source_id)
    if source is None:
        raise SourceNotFoundError(f"Source {source_id} not found")

    return source


def create_source(session: Session, source_in: SourceCreate, actor: UserProfile) -> Source:
    _validate_source_metadata(source_in)
    source = Source(**source_in.model_dump(), created_by=actor.id)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def update_source(session: Session, source_id: int, source_in: SourceUpdate) -> Source:
    source = get_source(session, source_id)
    update_data = _normalized_update_data(source_in)

    candidate_data = source.model_dump()
    candidate_data.update(update_data)
    _validate_source_metadata(SourceCreate.model_validate(candidate_data))

    for key, value in update_data.items():
        setattr(source, key, value)

    source.updated_at = datetime.now(UTC)
    session.add(source)
    session.commit()
    session.refresh(source)
    return source


def delete_source(session: Session, source_id: int) -> None:
    source = get_source(session, source_id)
    session.delete(source)
    session.commit()


def _validate_source_metadata(source: SourceCreate) -> None:
    if source.source_type not in SOURCE_TYPES:
        raise SourceValidationError(f"source_type must be one of {sorted(SOURCE_TYPES)}")

    if source.approval_status not in APPROVAL_STATUSES:
        raise SourceValidationError(f"approval_status must be one of {sorted(APPROVAL_STATUSES)}")

    if ".." in source.location:
        raise SourceValidationError("location must not contain parent directory references")

    if not source.location.startswith(APPROVED_LOCATION_PREFIXES):
        raise SourceValidationError(
            "location must be under data/approved_sources/ or use an approved URL scheme",
        )

    if source.approval_status == "approved" and not source.allowed_roles and not source.allowed_departments:
        raise SourceValidationError("approved sources must define role or department access")


def _normalized_update_data(source_in: SourceUpdate) -> dict[str, object]:
    update_data = source_in.model_dump(exclude_unset=True)
    for key, value in list(update_data.items()):
        if isinstance(value, str):
            update_data[key] = value.strip()
        if key in {"allowed_roles", "allowed_departments"} and isinstance(value, list):
            update_data[key] = sorted({item.strip() for item in value if item.strip()})

    return update_data

