from fastapi import APIRouter, Depends, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user  # type: ignore
from app.database.database import get_db  # type: ignore
from app.models.user import User  # type: ignore
from app.services.block_service import BlockService  # type: ignore
from app.services.follower_service import FollowerService  # type: ignore
from app.schemas.responses import (  # type: ignore
    MessageResponse,
    FollowerListResponse,
    FollowingListResponse,
)

router = APIRouter(prefix="/users", tags=["Followers & Blocks"])


@router.post("/{username}/follow", status_code=status.HTTP_200_OK, response_model=MessageResponse)
def follow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.follow_user(db, current_user, username)


@router.delete("/{username}/follow", status_code=status.HTTP_200_OK, response_model=MessageResponse)
def unfollow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.unfollow_user(db, current_user, username)


@router.post("/{username}/block", status_code=status.HTTP_200_OK, response_model=MessageResponse)
def block_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BlockService.block_user(db, current_user, username)


@router.delete("/{username}/block", status_code=status.HTTP_200_OK, response_model=MessageResponse)
def unblock_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BlockService.unblock_user(db, current_user, username)


@router.get("/me/followers", status_code=status.HTTP_200_OK, response_model=FollowerListResponse)
def get_my_followers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_my_followers(db, current_user)


@router.get("/me/following", status_code=status.HTTP_200_OK, response_model=FollowingListResponse)
def get_my_following(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_my_following(db, current_user)


@router.get("/{username}/followers", status_code=status.HTTP_200_OK, response_model=FollowerListResponse)
def get_user_followers(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_user_followers_by_username(db, username)


@router.get("/{username}/following", status_code=status.HTTP_200_OK, response_model=FollowingListResponse)
def get_user_following(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_user_following_by_username(db, username)
