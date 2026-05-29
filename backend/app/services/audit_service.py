from sqlmodel import Session, select

from app.models.audit import AuditLog
from app.models.user import UserProfile


def create_audit_log(
    session: Session,
    *,
    event_type: str,
    actor: UserProfile | None = None,
    actor_user_id: str | None = None,
    resource_type: str | None = None,
    resource_id: str | int | None = None,
    details: dict[str, object] | None = None,
) -> AuditLog:
    audit_log = AuditLog(
        actor_user_id=actor.id if actor is not None else actor_user_id,
        event_type=event_type,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        details=details or {},
    )
    session.add(audit_log)
    session.commit()
    session.refresh(audit_log)
    return audit_log


def list_audit_logs(session: Session, *, limit: int = 100) -> list[AuditLog]:
    statement = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())
