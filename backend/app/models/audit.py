from datetime import UTC, datetime

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"

    id: int | None = Field(default=None, primary_key=True)
    actor_user_id: str | None = Field(default=None, index=True, max_length=120)
    event_type: str = Field(index=True, max_length=120)
    resource_type: str | None = Field(default=None, index=True, max_length=80)
    resource_id: str | None = Field(default=None, index=True, max_length=120)
    details: dict[str, object] = Field(default_factory=dict, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)


class AuditLogRead(SQLModel):
    id: int
    actor_user_id: str | None
    event_type: str
    resource_type: str | None
    resource_id: str | None
    details: dict[str, object]
    created_at: datetime
