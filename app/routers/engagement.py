from uuid import UUID

from fastapi import APIRouter, Depends, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user, get_optional_current_user
from app.database.database import get_db
from app.models.user import User  # type: ignore
from app.schemas.engagement_schema import AddCommentRequest
from app.schemas.responses import (  # type: ignore
    AddCommentResponse,
    CommentsListResponse,
    LikeResponse,
    MessageResponse,
    RepostResponse,
    TrackEngagementSummaryResponse,
    TrackLikeCountResponse,
    UserRepostsResponse,
)
from app.services.engagement_service import EngagementService

router = APIRouter(tags=["Engagement"])


@router.post("/likes/tracks/{track_id}", response_model=LikeResponse)
def like_track(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngagementService.like_track(db, current_user, track_id)


@router.delete("/likes/tracks/{track_id}", response_model=MessageResponse)
def unlike_track(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngagementService.unlike_track(db, current_user, track_id)


@router.get("/tracks/{track_id}/likes/count", response_model=TrackLikeCountResponse)
def get_track_like_count(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return EngagementService.get_track_like_count(db, track_id, current_user)


@router.get(
    "/tracks/{track_id}/engagement-summary",
    response_model=TrackEngagementSummaryResponse,
)
def get_track_engagement_summary(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return EngagementService.get_track_engagement_summary(db, track_id, current_user)


@router.post("/reposts/tracks/{track_id}", response_model=RepostResponse)
def repost_track(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngagementService.repost_track(db, current_user, track_id)


@router.delete("/reposts/tracks/{track_id}", response_model=MessageResponse)
def remove_repost(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngagementService.remove_repost(db, current_user, track_id)


@router.get(
    "/reposts/users/{username}", response_model=UserRepostsResponse
)
def get_user_reposts(
    username: str,
    db: Session = Depends(get_db),
):
    """
    Get all public tracks reposted by a user, identified by username.
    No authentication required.
    """
    return EngagementService.get_user_reposts(db, username)


@router.get("/tracks/{track_id}/comments", response_model=CommentsListResponse)
def get_track_comments(
    track_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return EngagementService.get_track_comments(
        db, track_id, limit=limit, offset=offset, current_user=current_user
    )


@router.post("/tracks/{track_id}/comments", response_model=AddCommentResponse)
def add_comment(
    track_id: UUID,
    data: AddCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return EngagementService.add_comment(db, current_user, track_id, data)
