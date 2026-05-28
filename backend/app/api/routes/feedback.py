from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.dependencies import SessionDep, get_current_user, require_permission
from app.models.feedback import FeedbackCreate, FeedbackRead, FeedbackStats
from app.models.user import UserProfile
from app.services.feedback_service import create_feedback, get_feedback_stats, list_feedback

router = APIRouter(tags=["feedback"])
FeedbackReviewer = Annotated[UserProfile, Depends(require_permission("feedback:review"))]


@router.post("/api/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback_in: FeedbackCreate,
    session: SessionDep,
    current_user: Annotated[UserProfile, Depends(get_current_user)],
) -> FeedbackRead:
    return create_feedback(session, feedback_in, current_user)


@router.get("/api/admin/feedback", response_model=list[FeedbackRead])
def read_feedback(session: SessionDep, _current_user: FeedbackReviewer) -> list[FeedbackRead]:
    return list_feedback(session)


@router.get("/api/admin/feedback/stats", response_model=FeedbackStats)
def read_feedback_stats(session: SessionDep, _current_user: FeedbackReviewer) -> FeedbackStats:
    return get_feedback_stats(session)

