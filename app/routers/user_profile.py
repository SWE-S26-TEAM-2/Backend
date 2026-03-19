"""
Router for user profile and social links endpoints (Module 2).

All endpoints that require authentication use the
get_current_user dependency to extract the user from JWT.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user  # type: ignore
from app.database.database import get_db  # type: ignore
from app.models.user import User  # type: ignore
from app.schemas.social_link_schema import (  # type: ignore
    UpdateSocialLinksRequest,
)
from app.schemas.user_schema import (  # type: ignore
    UpdatePrivacyRequest,
    UpdateProfileRequest,
)
from app.services.social_link_service import SocialLinkService  # type: ignore
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


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_user_profile(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get any user's public profile by their UUID.

    Args:
        user_id (UUID): The target user's UUID from the URL path.
        db (Session): Database session injected by FastAPI.

    Returns:
        dict: Public profile data (limited if private).
    """
    return UserService.get_profile_by_id(db, user_id)


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
    return SocialLinkService.update_social_links(
        db, current_user, data
    )
