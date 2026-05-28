from datetime import UTC, datetime
from typing import Literal

from pydantic import Field as PydanticField
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


FeedbackRating = Literal["helpful", "not_helpful"]


class FeedbackCreate(SQLModel):
    message_id: str = Field(min_length=1, max_length=120)
    rating: FeedbackRating
    question: str = Field(min_length=1, max_length=2000)
    answer: str = Field(min_length=1, max_length=6000)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[dict[str, object]] = PydanticField(default_factory=list)
    comment: str | None = Field(default=None, max_length=1000)


class Feedback(SQLModel, table=True):
    __tablename__ = "feedback"

    id: int | None = Field(default=None, primary_key=True)
    message_id: str = Field(index=True, max_length=120)
    user_id: str = Field(index=True, max_length=120)
    rating: str = Field(index=True, max_length=40)
    question: str = Field(max_length=2000)
    answer: str = Field(max_length=6000)
    confidence: float
    sources: list[dict[str, object]] = Field(default_factory=list, sa_column=Column(JSON))
    comment: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class FeedbackRead(SQLModel):
    id: int
    message_id: str
    user_id: str
    rating: str
    question: str
    answer: str
    confidence: float
    sources: list[dict[str, object]]
    comment: str | None
    created_at: datetime


class FeedbackStats(SQLModel):
    total: int
    helpful: int
    not_helpful: int
