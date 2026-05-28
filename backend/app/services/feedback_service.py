from sqlmodel import Session, select

from app.models.feedback import Feedback, FeedbackCreate, FeedbackStats
from app.models.user import UserProfile


def create_feedback(session: Session, feedback_in: FeedbackCreate, user: UserProfile) -> Feedback:
    feedback = Feedback(**feedback_in.model_dump(), user_id=user.id)
    session.add(feedback)
    session.commit()
    session.refresh(feedback)
    return feedback


def list_feedback(session: Session) -> list[Feedback]:
    return list(session.exec(select(Feedback).order_by(Feedback.created_at.desc())).all())


def get_feedback_stats(session: Session) -> FeedbackStats:
    feedback = list(session.exec(select(Feedback)).all())
    helpful = sum(1 for item in feedback if item.rating == "helpful")
    not_helpful = sum(1 for item in feedback if item.rating == "not_helpful")
    return FeedbackStats(total=len(feedback), helpful=helpful, not_helpful=not_helpful)

