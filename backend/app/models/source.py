from datetime import UTC, datetime

from pydantic import field_validator
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class SourceBase(SQLModel):
    title: str = Field(min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    source_type: str = Field(default="document", max_length=40)
    location: str = Field(min_length=1, max_length=500)
    owning_department: str = Field(min_length=1, max_length=120)
    allowed_roles: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    allowed_departments: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    approval_status: str = Field(default="draft", max_length=40)
    version: str = Field(default="1.0", max_length=40)

    @field_validator("title", "source_type", "location", "owning_department", "approval_status", "version")
    @classmethod
    def strip_required_strings(cls, value: str) -> str:
        return value.strip()

    @field_validator("description")
    @classmethod
    def strip_optional_string(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None

    @field_validator("allowed_roles", "allowed_departments")
    @classmethod
    def normalize_string_list(cls, values: list[str]) -> list[str]:
        return sorted({value.strip() for value in values if value.strip()})


class Source(SourceBase, table=True):
    __tablename__ = "sources"

    id: int | None = Field(default=None, primary_key=True)
    created_by: str = Field(max_length=120)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    indexed_at: datetime | None = None


class SourceCreate(SourceBase):
    pass


class SourceUpdate(SQLModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(default=None, max_length=500)
    source_type: str | None = Field(default=None, max_length=40)
    location: str | None = Field(default=None, min_length=1, max_length=500)
    owning_department: str | None = Field(default=None, min_length=1, max_length=120)
    allowed_roles: list[str] | None = None
    allowed_departments: list[str] | None = None
    approval_status: str | None = Field(default=None, max_length=40)
    version: str | None = Field(default=None, max_length=40)


class SourceRead(SourceBase):
    id: int
    created_by: str
    created_at: datetime
    updated_at: datetime
    indexed_at: datetime | None

