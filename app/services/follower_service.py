"""
Service layer for follow/unfollow business logic.

Validates rules (can't follow yourself, can't follow twice)
and delegates all DB work to FollowRepository and UserRepository.
"""

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.user import User  # type: ignore
from app.repositories.follow_repo import FollowRepository  # type: ignore
from app.repositories.notification_repo import NotificationRepository  # type: ignore
from app.repositories.user_repo import UserRepository  # type: ignore


class FollowerService:

    @staticmethod
    def follow_user(db: Session, current_user: User, target_id) -> dict:
        """
        Follow a user by their UUID.

        Business rules enforced here:
        - Cannot follow yourself.
        - Cannot follow someone you already follow.
        - Target user must exist.
        - Increments follower_count and following_count atomically.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated requesting user.
            target_id: UUID of the user to follow.

        Returns:
            dict: Success message with the followed user's name.

        Raises:
            HTTPException 400: If following yourself or already following.
            HTTPException 404: If target user does not exist.
        """
        # Rule 1: Cannot follow yourself
        if current_user.user_id == target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot follow yourself.",
            )

        # Rule 2: Target must exist
        target_user = UserRepository.get_by_id(db, target_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        # Rule 3: Cannot follow someone already followed
        existing = FollowRepository.get_follow(db, current_user.user_id, target_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You are already following {target_user.display_name}.",
            )

        # Create the follow record
        FollowRepository.create_follow(db, current_user.user_id, target_id)

        # Notify the followed user
        NotificationRepository.create(
            db,
            user_id=target_user.user_id,
            actor_id=current_user.user_id,
            notification_type="follow",
            message=f"{current_user.display_name} started following you.",
        )

        # Update counters on both users
        UserRepository.update_fields(
            db,
            current_user,
            {"following_count": current_user.following_count + 1},
        )
        UserRepository.update_fields(
            db,
            target_user,
            {"follower_count": target_user.follower_count + 1},
        )

        return {
            "success": True,
            "message": f"You are now following {target_user.display_name}.",
        }

    @staticmethod
    def unfollow_user(db: Session, current_user: User, target_id) -> dict:
        """
        Unfollow a user by their UUID.

        Business rules:
        - Must currently be following the target.
        - Decrements counters, never goes below 0.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated requesting user.
            target_id: UUID of the user to unfollow.

        Returns:
            dict: Success message.

        Raises:
            HTTPException 404: If not currently following the target.
        """
        follow = FollowRepository.get_follow(db, current_user.user_id, target_id)
        if not follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not following this user.",
            )

        target_user = UserRepository.get_by_id(db, target_id)

        FollowRepository.delete_follow(db, follow)

        # Decrement counters safely (never below 0)
        UserRepository.update_fields(
            db,
            current_user,
            {"following_count": max(0, current_user.following_count - 1)},
        )
        if target_user:
            UserRepository.update_fields(
                db,
                target_user,
                {"follower_count": max(0, target_user.follower_count - 1)},
            )

        return {"success": True, "message": "Successfully unfollowed."}
