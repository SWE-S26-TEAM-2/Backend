"""
Router for follower and block endpoints (Module 3).

All endpoints require Bearer JWT authentication.
Uses the same /users/{id}/ prefix as the user profile router
but with action-specific suffixes (/follow, /block).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user  # type: ignore
from app.database.database import get_db  # type: ignore
from app.models.user import User  # type: ignore
from app.services.block_service import BlockService  # type: ignore
from app.services.follower_service import FollowerService  # type: ignore

router = APIRouter(prefix="/users", tags=["Followers & Blocks"])


# ── Follow Endpoints ───────────────────────────────────


@router.post("/{user_id}/follow", status_code=status.HTTP_200_OK)
def follow_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Follow a user by their UUID.

    Args:
        user_id (UUID): The target user's UUID from the URL path.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Success message with the followed user's display name.
    """
    return FollowerService.follow_user(db, current_user, user_id)


@router.delete("/{user_id}/follow", status_code=status.HTTP_200_OK)
def unfollow_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unfollow a user by their UUID.

    Args:
        user_id (UUID): The target user's UUID from the URL path.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Success message.
    """
    return FollowerService.unfollow_user(db, current_user, user_id)


# ── Block Endpoints ────────────────────────────────────


@router.post("/{user_id}/block", status_code=status.HTTP_200_OK)
def block_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Block a user by their UUID.

    Also removes any active follow relationship between the two users.

    Args:
        user_id (UUID): The target user's UUID from the URL path.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Success message.
    """
    return BlockService.block_user(db, current_user, user_id)


@router.delete("/{user_id}/block", status_code=status.HTTP_200_OK)
def unblock_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Unblock a previously blocked user.

    Args:
        user_id (UUID): The target user's UUID from the URL path.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Success message.
    """
    return BlockService.unblock_user(db, current_user, user_id)


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


@router.get(
    "/{display_name}/followers",
    status_code=status.HTTP_200_OK,
)
def get_user_followers_by_username(
    display_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all followers of any user by their display_name.

    Private profiles return an empty followers list
    with private=True in the response.

    Args:
        display_name (str): The target user's display_name
                            from the URL path.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: count, followers list, and private flag.
    """
    return FollowerService.get_user_followers_by_username(db, display_name)


@router.get("/me/following", status_code=status.HTTP_200_OK)
def get_my_following(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all users the authenticated user is following.

    Returns each following user's user_id, display_name,
    profile_picture, and the date they were followed.

    Args:
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: count and list of following profiles.
    """
    return FollowerService.get_my_following(db, current_user)


@router.get(
    "/{display_name}/following",
    status_code=status.HTTP_200_OK,
)
def get_user_following_by_username(
    display_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all users that a given user is following by display_name.

    Private profiles return an empty following list
    with private=True in the response.

    Args:
        display_name (str): The target user's display_name.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: count, following list, and private flag.
    """
    return FollowerService.get_user_following_by_username(db, display_name)
