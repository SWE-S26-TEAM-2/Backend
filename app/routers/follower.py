"""
Router for follower and block endpoints (Module 3).

All endpoints require Bearer JWT authentication.
Uses the same /users/{id}/ prefix as the user profile router
but with action-specific suffixes (/follow, /block).
"""

from fastapi import APIRouter, Depends, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user  # type: ignore
from app.database.database import get_db  # type: ignore
from app.models.user import User  # type: ignore
from app.services.block_service import BlockService  # type: ignore
from app.services.follower_service import FollowerService  # type: ignore

router = APIRouter(prefix="/users", tags=["Followers & Blocks"])


# ── Follow Endpoints ───────────────────────────────────


@router.post("/{username}/follow", status_code=status.HTTP_200_OK)
def follow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.follow_user(db, current_user, username)


@router.delete("/{username}/follow", status_code=status.HTTP_200_OK)
def unfollow_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.unfollow_user(db, current_user, username)


# ── Block Endpoints ────────────────────────────────────


@router.post("/{username}/block", status_code=status.HTTP_200_OK)
def block_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BlockService.block_user(db, current_user, username)


@router.delete("/{username}/block", status_code=status.HTTP_200_OK)
def unblock_user(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return BlockService.unblock_user(db, current_user, username)


# ── Followers Retrieval Endpoints ──────────────────────


@router.get("/me/followers", status_code=status.HTTP_200_OK)
def get_my_followers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all followers of the authenticated user.

    Returns each follower's user_id, display_name,
    profile_picture, and the date they followed.

    Args:
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: count and list of follower profiles.
    """
    return FollowerService.get_my_followers(db, current_user)


@router.get("/{username}/followers", status_code=status.HTTP_200_OK)
def get_user_followers_by_username(
    username: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return FollowerService.get_user_followers_by_username(db, username)
