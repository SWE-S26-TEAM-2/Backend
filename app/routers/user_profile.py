"""
Router for user profile and social links endpoints (Module 2).

All endpoints that require authentication use the
get_current_user dependency to extract the user from JWT.
"""

from fastapi import (  # type: ignore
    APIRouter, Depends, File, HTTPException, Query, UploadFile, status,
)
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import (  # type: ignore
    get_current_user,
    get_optional_current_user,
)
from app.database.database import get_db  # type: ignore
from app.models.user import User  # type: ignore
from app.schemas.social_link_schema import (  # type: ignore
    UpdateSocialLinksRequest,
)
from app.schemas.user_schema import (  # type: ignore
    ChangeUsernameRequest,
    UpdatePrivacyRequest,
    UpdateProfileRequest,
)
from app.services.social_link_service import SocialLinkService  # type: ignore
from app.services.track_service import TrackService  # type: ignore
from app.repositories.user_repo import UserRepository  # type: ignore
from app.services.user_service import UserService  # type: ignore

router = APIRouter(prefix="/users", tags=["Users"])


# ── Profile Retrieval & Update ─────────────────────────


@router.get("/me", status_code=status.HTTP_200_OK)
def get_my_profile(
    current_user: User = Depends(get_current_user),
):
    """
    Get the full profile of the currently authenticated user.

    Args:
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Full profile data.
    """
    return UserService.get_my_profile(current_user)


@router.get("/me/recently-played", status_code=status.HTTP_200_OK)
def get_recently_played(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TrackService.get_listening_history(db, current_user, limit)


@router.get("/me/listening-history", status_code=status.HTTP_200_OK)
def get_listening_history(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return TrackService.get_listening_history(db, current_user, limit)


# ── External Social Links ─────────────────────────────


@router.get("/me/social-links", status_code=status.HTTP_200_OK)
def get_social_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all external social profile links for the authenticated user.

    Args:
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: List of social link objects.
    """
    return SocialLinkService.get_social_links(db, current_user)


@router.put("/me/social-links", status_code=status.HTTP_200_OK)
def update_social_links(
    data: UpdateSocialLinksRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Replace all social links for the authenticated user.

    Args:
        data (UpdateSocialLinksRequest): Full list of social links.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Updated list of social links.
    """
    return SocialLinkService.update_social_links(db, current_user, data)


@router.patch("/me", status_code=status.HTTP_200_OK)
def update_my_profile(
    data: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update profile fields for the authenticated user.

    Args:
        data (UpdateProfileRequest): Fields to update.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Updated profile data.
    """
    return UserService.update_profile(db, current_user, data)


@router.patch("/me/username", status_code=status.HTTP_200_OK)
def change_username(
    data: ChangeUsernameRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return UserService.change_username(db, current_user, data)


@router.patch("/me/privacy", status_code=status.HTTP_200_OK)
def update_privacy(
    data: UpdatePrivacyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Toggle profile visibility between public and private.

    Args:
        data (UpdatePrivacyRequest): The privacy setting.
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Updated privacy status.
    """
    return UserService.update_privacy(db, current_user, data)


# ── Media Asset Uploads ────────────────────────────────


@router.put("/me/avatar", status_code=status.HTTP_200_OK)
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a profile picture (avatar) for the authenticated user.

    Args:
        file (UploadFile): The image file (multipart/form-data).
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Path to the uploaded avatar.
    """
    return UserService.upload_avatar(db, current_user, file)


@router.put("/me/cover", status_code=status.HTTP_200_OK)
def upload_cover(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Upload a cover photo for the authenticated user.

    Args:
        file (UploadFile): The image file (multipart/form-data).
        db (Session): Database session injected by FastAPI.
        current_user (User): Injected by JWT dependency.

    Returns:
        dict: Path to the uploaded cover photo.
    """
    return UserService.upload_cover(db, current_user, file)


# ── Public user lookup ────────────────────────────────


@router.get("/{username}", status_code=status.HTTP_200_OK)
def get_user_profile(
    username: str,
    db: Session = Depends(get_db),
):
    return UserService.get_profile_by_username(db, username)


@router.get("/{username}/tracks", status_code=status.HTTP_200_OK)
def get_user_tracks(
    username: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    user = UserRepository.get_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return TrackService.get_tracks_by_user(db, user.user_id, current_user)


@router.get("/{username}/liked-tracks", status_code=status.HTTP_200_OK)
def get_user_liked_tracks(
    username: str,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    user = UserRepository.get_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return TrackService.get_liked_tracks_by_user(db, user.user_id, current_user)
