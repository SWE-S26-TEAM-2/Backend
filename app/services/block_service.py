"""
Service layer for block/unblock business logic.

Enforces block rules and delegates DB work to BlockRepository.
When a user is blocked, any existing follow relationship
between them is also removed automatically.
"""

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.user import User  # type: ignore
from app.repositories.block_repo import BlockRepository  # type: ignore
from app.repositories.follow_repo import FollowRepository  # type: ignore
from app.repositories.user_repo import UserRepository  # type: ignore


class BlockService:

    @staticmethod
    def block_user(db: Session, current_user: User, target_id) -> dict:
        """
        Block a user by their UUID.

        Business rules:
        - Cannot block yourself.
        - Cannot block someone already blocked.
        - Automatically removes any follow relationship
          in either direction between the two users.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated requesting user.
            target_id: UUID of the user to block.

        Returns:
            dict: Success message.

        Raises:
            HTTPException 400: If blocking yourself or already blocked.
            HTTPException 404: If target user does not exist.
        """
        if current_user.user_id == target_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot block yourself.",
            )

        target_user = UserRepository.get_by_id(db, target_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        existing = BlockRepository.get_block(db, current_user.user_id, target_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have already blocked this user.",
            )

        # Auto-remove follow in both directions when blocking
        follow_a = FollowRepository.get_follow(db, current_user.user_id, target_id)
        if follow_a:
            FollowRepository.delete_follow(db, follow_a)
            UserRepository.update_fields(
                db,
                current_user,
                {"following_count": max(0, current_user.following_count - 1)},
            )
            UserRepository.update_fields(
                db,
                target_user,
                {"follower_count": max(0, target_user.follower_count - 1)},
            )

        follow_b = FollowRepository.get_follow(db, target_id, current_user.user_id)
        if follow_b:
            FollowRepository.delete_follow(db, follow_b)
            UserRepository.update_fields(
                db,
                target_user,
                {"following_count": max(0, target_user.following_count - 1)},
            )
            UserRepository.update_fields(
                db,
                current_user,
                {"follower_count": max(0, current_user.follower_count - 1)},
            )

        BlockRepository.create_block(db, current_user.user_id, target_id)

        return {"success": True, "message": "User blocked successfully."}

    @staticmethod
    def unblock_user(db: Session, current_user: User, target_id) -> dict:
        """
        Unblock a previously blocked user.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated requesting user.
            target_id: UUID of the user to unblock.

        Returns:
            dict: Success message.

        Raises:
            HTTPException 404: If no block record exists.
        """
        block = BlockRepository.get_block(db, current_user.user_id, target_id)
        if not block:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You have not blocked this user.",
            )

        BlockRepository.delete_block(db, block)

        return {"success": True, "message": "User unblocked successfully."}
