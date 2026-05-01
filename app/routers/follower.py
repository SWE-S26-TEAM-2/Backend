from uuid import UUID

from fastapi import APIRouter, Depends, Response, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user  # type: ignore
from app.database.database import get_db  # type: ignore
from app.models.user import User  # type: ignore
from app.services.block_service import BlockService  # type: ignore
from app.services.follower_service import FollowerService  # type: ignore
from app.schemas.responses import (  # type: ignore
    FollowResponse,
    FollowRequestListResponse,
    MessageResponse,
    UnfollowResponse,
    FollowerListResponse,
    FollowingListResponse,
)

router = APIRouter(prefix="/users", tags=["Followers & Blocks"])


@router.post("/{username}/follow", response_model=FollowResponse)
def follow_user(
    username: str,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Follow a user. If the target account is private, a follow request is
    created instead (202 Accepted, is_pending=true). Public accounts are
    followed immediately (200 OK, is_pending=false).
    """
    result = FollowerService.follow_user(db, current_user, username)
    if result.get("is_pending"):
        response.status_code = status.HTTP_202_ACCEPTED
    return result


@router.delete(
    "/{username}/follow",
    status_code=status.HTTP_200_OK,
    response_model=UnfollowResponse,
)
def unfollow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.unfollow_user(db, current_user, username)


@router.get(
    "/me/follow-requests",
    status_code=status.HTTP_200_OK,
    response_model=FollowRequestListResponse,
)
def get_follow_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return all pending follow requests sent to the authenticated user."""
    return FollowerService.get_incoming_follow_requests(db, current_user)


@router.post(
    "/me/follow-requests/{request_id}/approve",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
def approve_follow_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Approve a pending follow request."""
    return FollowerService.approve_follow_request(db, current_user, request_id)


@router.post(
    "/me/follow-requests/{request_id}/reject",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
def reject_follow_request(
    request_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a pending follow request."""
    return FollowerService.reject_follow_request(db, current_user, request_id)


@router.post(
    "/{username}/block",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
def block_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BlockService.block_user(db, current_user, username)


@router.delete(
    "/{username}/block",
    status_code=status.HTTP_200_OK,
    response_model=MessageResponse,
)
def unblock_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BlockService.unblock_user(db, current_user, username)


@router.get(
    "/me/followers",
    status_code=status.HTTP_200_OK,
    response_model=FollowerListResponse,
)
def get_my_followers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_my_followers(db, current_user)


@router.get(
    "/me/following",
    status_code=status.HTTP_200_OK,
    response_model=FollowingListResponse,
)
def get_my_following(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_my_following(db, current_user)


@router.get(
    "/{username}/followers",
    status_code=status.HTTP_200_OK,
    response_model=FollowerListResponse,
)
def get_user_followers(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_user_followers_by_username(db, username)


@router.get(
    "/{username}/following",
    status_code=status.HTTP_200_OK,
    response_model=FollowingListResponse,
)
def get_user_following(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_user_following_by_username(db, username)
