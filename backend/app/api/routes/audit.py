from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import SessionDep, require_permission
from app.models.audit import AuditLogRead
from app.models.user import UserProfile
from app.services.audit_service import list_audit_logs

router = APIRouter(prefix="/api/admin/audit", tags=["audit"])
AuditReader = Annotated[UserProfile, Depends(require_permission("audit:read"))]


@router.get("", response_model=list[AuditLogRead])
def read_audit_logs(
    session: SessionDep,
    _current_user: AuditReader,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[AuditLogRead]:
    return list_audit_logs(session, limit=limit)
