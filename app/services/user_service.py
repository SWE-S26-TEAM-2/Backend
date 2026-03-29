"""
Service layer for user profile business logic.

Handles profile retrieval, updates, privacy toggling,
and avatar/cover photo uploads.
"""
import os
import shutil

from fastapi import HTTPException, UploadFile, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.user import User  # type: ignore
from app.repositories.user_repo import UserRepository  # type: ignore

ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"]
AVATAR_MAX_SIZE = 5 * 1024 * 1024       # 5 MB
COVER_MAX_SIZE = 10 * 1024 * 1024       # 10 MB
ALLOWED_PROFILE_FIELDS = [
    "display_name", "bio", "location", "account_type",
]


class UserService:
    """
    Business logic layer for user profile operations.
    """

    @staticmethod
    def get_my_profile(current_user: User) -> dict:
        """
        Return the full profile of the authenticated user.

        Args:
            current_user (User): The authenticated user object.

        Returns:
            dict: Full profile data including all fields.
        """
        return {
            "success": True,
            "data": {
                "user_id": str(current_user.user_id),
                "email": current_user.email,
                "display_name": current_user.display_name,
                "account_type": current_user.account_type,
                "is_verified": current_user.is_verified,
                "is_suspended": current_user.is_suspended,
                "bio": current_user.bio,
                "location": current_user.location,
                "is_premium": current_user.is_premium,
                "is_private": current_user.is_private,
                "profile_picture": current_user.profile_picture,
                "cover_photo": current_user.cover_photo,
                "follower_count": current_user.follower_count,
                "following_count": current_user.following_count,
                "track_count": current_user.track_count,
                "created_at": current_user.created_at,
            },
        }

    @staticmethod
    def get_profile_by_id(db: Session, user_id) -> dict:
        """
        Return the public profile of any user by their UUID.

        Private profiles return limited data.

        Args:
            db (Session): The database session.
            user_id: The UUID of the target user.

        Returns:
            dict: Public (or limited) profile data.

        Raises:
            HTTPException: 404 if the user is not found.
        """
        user = UserRepository.get_by_id(db, user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        if user.is_private:
            return {
                "success": True,
                "data": {
                    "user_id": str(user.user_id),
                    "display_name": user.display_name,
                    "profile_picture": user.profile_picture,
                    "follower_count": user.follower_count,
                },
            }

        return {
            "success": True,
            "data": {
                "user_id": str(user.user_id),
                "display_name": user.display_name,
                "bio": user.bio,
                "location": user.location,
                "account_type": user.account_type,
                "is_private": user.is_private,
                "profile_picture": user.profile_picture,
                "cover_photo": user.cover_photo,
                "follower_count": user.follower_count,
                "following_count": user.following_count,
                "track_count": user.track_count,
                "created_at": user.created_at,
            },
        }

    @staticmethod
    def update_profile(
        db: Session, current_user: User, data
    ) -> dict:
        """
        Update allowed profile fields for the authenticated user.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated user object.
            data: UpdateProfileRequest schema.

        Returns:
            dict: Updated profile data.
        """
        update_data = data.model_dump(exclude_unset=True)
        filtered = {
            k: v for k, v in update_data.items()
            if k in ALLOWED_PROFILE_FIELDS
        }

        UserRepository.update_fields(db, current_user, filtered)

        return {
            "success": True,
            "message": "Profile updated successfully.",
            "data": {
                "user_id": str(current_user.user_id),
                "display_name": current_user.display_name,
                "bio": current_user.bio,
                "location": current_user.location,
                "account_type": current_user.account_type,
                "updated_at": current_user.updated_at,
            },
        }

    @staticmethod
    def update_privacy(
        db: Session, current_user: User, data
    ) -> dict:
        """
        Toggle profile visibility between public and private.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated user object.
            data: UpdatePrivacyRequest schema.

        Returns:
            dict: Updated privacy status.
        """
        UserRepository.update_fields(
            db, current_user, {"is_private": data.is_private}
        )

        return {
            "success": True,
            "message": "Profile visibility updated.",
            "data": {
                "is_private": current_user.is_private,
            },
        }

    @staticmethod
    def upload_avatar(
        db: Session, current_user: User, file: UploadFile
    ) -> dict:
        """
        Upload a profile picture (avatar) for the authenticated user.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated user object.
            file (UploadFile): The uploaded image file.

        Returns:
            dict: URL/path to the uploaded avatar.

        Raises:
            HTTPException: 400 if file type or size is invalid.
        """
        UserService._validate_image(
            file, AVATAR_MAX_SIZE, "5 MB"
        )

        path = UserService._save_file(
            file, current_user.user_id, "Avatar"
        )

        UserRepository.update_fields(
            db, current_user, {"profile_picture": path}
        )

        return {
            "success": True,
            "message": "Avatar uploaded successfully.",
            "data": {
                "profile_picture": current_user.profile_picture,
            },
        }

    @staticmethod
    def upload_cover(
        db: Session, current_user: User, file: UploadFile
    ) -> dict:
        """
        Upload a cover photo for the authenticated user.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated user object.
            file (UploadFile): The uploaded image file.

        Returns:
            dict: URL/path to the uploaded cover photo.

        Raises:
            HTTPException: 400 if file type or size is invalid.
        """
        UserService._validate_image(
            file, COVER_MAX_SIZE, "10 MB"
        )

        path = UserService._save_file(
            file, current_user.user_id, "Cover"
        )

        UserRepository.update_fields(
            db, current_user, {"cover_photo": path}
        )

        return {
            "success": True,
            "message": "Cover photo uploaded successfully.",
            "data": {
                "cover_photo": current_user.cover_photo,
            },
        }

    # ── Private helper methods ──────────────────────────

    @staticmethod
    def _validate_image(
        file: UploadFile, max_size: int, label: str
    ) -> None:
        """
        Validate image file type and size.

        Args:
            file (UploadFile): The uploaded file.
            max_size (int): Maximum allowed file size in bytes.
            label (str): Human-readable size label for error message.

        Raises:
            HTTPException: 400 if validation fails.
        """
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPEG, PNG, and WEBP files are allowed",
            )

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > max_size:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size must not exceed {label}",
            )

    @staticmethod
    def _save_file(
        file: UploadFile, user_id, subfolder: str
    ) -> str:
        """
        Save an uploaded file to the Uploads directory.

        Args:
            file (UploadFile): The uploaded file.
            user_id: The UUID of the user.
            subfolder (str): Subfolder name (Avatar or Cover).

        Returns:
            str: Relative file path for storage in the database.
        """
        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
        upload_folder = os.path.join(base_dir, "Uploads", subfolder)
        os.makedirs(upload_folder, exist_ok=True)

        file_ext = file.filename.split(".")[-1]
        file_name = f"{user_id}.{file_ext}"

        absolute_path = os.path.join(upload_folder, file_name)
        relative_path = os.path.join("Uploads", subfolder, file_name)

        with open(absolute_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return relative_path
