from dataclasses import dataclass

from sqlmodel import Session, select

from app.models.feedback import Feedback, FeedbackCreate, FeedbackRating, FeedbackStats
from app.models.user import UserProfile


@dataclass(frozen=True)
class FeedbackFilters:
    rating: FeedbackRating | None = None
    user_id: str | None = None
    min_confidence: float | None = None
    max_confidence: float | None = None
    source_id: int | None = None
    limit: int | None = 50


def create_feedback(session: Session, feedback_in: FeedbackCreate, user: UserProfile) -> Feedback:
    feedback = Feedback(**feedback_in.model_dump(), user_id=user.id)
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def list_feedback(session: Session, filters: FeedbackFilters | None = None) -> list[Feedback]:
    filters = filters or FeedbackFilters()
    statement = select(Feedback)
    if filters.rating is not None:
        statement = statement.where(Feedback.rating == filters.rating)
    if filters.user_id is not None:
        statement = statement.where(Feedback.user_id == filters.user_id)
    if filters.min_confidence is not None:
        statement = statement.where(Feedback.confidence >= filters.min_confidence)
    if filters.max_confidence is not None:
        statement = statement.where(Feedback.confidence <= filters.max_confidence)

    feedback = list(session.exec(statement.order_by(Feedback.created_at.desc())).all())
    if filters.source_id is not None:
        feedback = [item for item in feedback if _contains_source(item, filters.source_id)]
    if filters.limit is not None:
        feedback = feedback[: filters.limit]

    return feedback


def get_feedback_stats(session: Session, filters: FeedbackFilters | None = None) -> FeedbackStats:
    feedback = list_feedback(session, filters)
    helpful = sum(1 for item in feedback if item.rating == "helpful")
    not_helpful = sum(1 for item in feedback if item.rating == "not_helpful")
    return FeedbackStats(total=len(feedback), helpful=helpful, not_helpful=not_helpful)


def _contains_source(feedback: Feedback, source_id: int) -> bool:
    return any(source.get("source_id") == source_id for source in feedback.sources)
