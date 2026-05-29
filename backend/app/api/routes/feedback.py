from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import SessionDep, get_current_user, require_permission
from app.models.feedback import FeedbackCreate, FeedbackRating, FeedbackRead, FeedbackStats
from app.models.user import UserProfile
from app.services.feedback_service import FeedbackFilters, create_feedback, get_feedback_stats, list_feedback

router = APIRouter(tags=["feedback"])
FeedbackReviewer = Annotated[UserProfile, Depends(require_permission("feedback:review"))]


def _feedback_filters(
    rating: Annotated[FeedbackRating | None, Query()] = None,
    user_id: Annotated[str | None, Query(min_length=1, max_length=120)] = None,
    min_confidence: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    max_confidence: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
    source_id: Annotated[int | None, Query(ge=1)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
) -> FeedbackFilters:
    if min_confidence is not None and max_confidence is not None and min_confidence > max_confidence:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_confidence must be less than or equal to max_confidence",
        )

    return FeedbackFilters(
        rating=rating,
        user_id=user_id,
        min_confidence=min_confidence,
        max_confidence=max_confidence,
        source_id=source_id,
        limit=limit,
    )


@router.post("/api/feedback", response_model=FeedbackRead, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    feedback_in: FeedbackCreate,
    session: SessionDep,
    current_user: Annotated[UserProfile, Depends(get_current_user)],
) -> FeedbackRead:
    return create_feedback(session, feedback_in, current_user)


@router.get("/api/admin/feedback", response_model=list[FeedbackRead])
def read_feedback(
    session: SessionDep,
    _current_user: FeedbackReviewer,
    filters: Annotated[FeedbackFilters, Depends(_feedback_filters)],
) -> list[FeedbackRead]:
    return list_feedback(session, filters)


@router.get("/api/admin/feedback/stats", response_model=FeedbackStats)
def read_feedback_stats(
    session: SessionDep,
    _current_user: FeedbackReviewer,
    filters: Annotated[FeedbackFilters, Depends(_feedback_filters)],
) -> FeedbackStats:
    return get_feedback_stats(session, filters)
