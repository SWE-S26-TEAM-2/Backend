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
    def follow_user(db: Session, current_user: User, username: str) -> dict:
        target_user = UserRepository.get_by_username(db, username)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if current_user.user_id == target_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot follow yourself.",
            )

        target_id = target_user.user_id

        existing = FollowRepository.get_follow(db, current_user.user_id, target_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"You are already following {target_user.display_name}.",
            )

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
    def unfollow_user(db: Session, current_user: User, username: str) -> dict:
        target_user = UserRepository.get_by_username(db, username)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        target_id = target_user.user_id
        follow = FollowRepository.get_follow(db, current_user.user_id, target_id)
        if not follow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You are not following this user.",
            )

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

    @staticmethod
    def get_my_followers(db: Session, current_user: User) -> dict:
        """
        Get all followers of the authenticated user.

        Resolves each follower's profile so the response
        includes display_name and profile_picture.

        Args:
            db (Session): The database session.
            current_user (User): The authenticated requesting user.

        Returns:
            dict: List of follower profiles with count.
        """
        follow_records = FollowRepository.get_followers_of_user(
            db, current_user.user_id
        )

        followers = []
        for record in follow_records:
            user = UserRepository.get_by_id(db, record.follower_id)
            if user:
                followers.append(
                    {
                        "user_id": str(user.user_id),
                        "display_name": user.display_name,
                        "is_premium": user.is_premium,
                        "billing_cycle": getattr(user, "billing_cycle", None),
                        "profile_picture": user.profile_picture,
                        "followed_at": record.created_at,
                    }
                )

        return {
            "success": True,
            "data": {
                "count": len(followers),
                "followers": followers,
            },
        }

    @staticmethod
    def get_user_followers_by_username(db: Session, username: str) -> dict:
        target_user = UserRepository.get_by_username(db, username)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        # Private profiles hide their followers list
        if target_user.is_private:
            return {
                "success": True,
                "data": {
                    "count": target_user.follower_count,
                    "followers": [],
                    "private": True,
                },
            }

        follow_records = FollowRepository.get_followers_of_user(db, target_user.user_id)

        followers = []
        for record in follow_records:
            user = UserRepository.get_by_id(db, record.follower_id)
            if user:
                followers.append(
                    {
                        "user_id": str(user.user_id),
                        "display_name": user.display_name,
                        "is_premium": user.is_premium,
                        "billing_cycle": getattr(user, "billing_cycle", None),
                        "profile_picture": user.profile_picture,
                        "followed_at": record.created_at,
                    }
                )

        return {
            "success": True,
            "data": {
                "count": len(followers),
                "followers": followers,
                "private": False,
            },
        }

    @staticmethod
    def get_my_following(db: Session, current_user: User) -> dict:
        follow_records = FollowRepository.get_following_of_user(
            db, current_user.user_id
        )

        following = []
        for record in follow_records:
            user = UserRepository.get_by_id(db, record.following_id)
            if user:
                following.append(
                    {
                        "user_id": str(user.user_id),
                        "username": user.username,
                        "display_name": user.display_name,
                        "is_premium": user.is_premium,
                        "billing_cycle": getattr(user, "billing_cycle", None),
                        "profile_picture": user.profile_picture,
                        "followed_at": record.created_at,
                    }
                )

        return {
            "success": True,
            "data": {
                "count": len(following),
                "following": following,
            },
        }

    @staticmethod
    def get_user_following_by_username(db: Session, username: str) -> dict:
        target_user = UserRepository.get_by_username(db, username)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if target_user.is_private:
            return {
                "success": True,
                "data": {
                    "count": target_user.following_count,
                    "following": [],
                    "private": True,
                },
            }

        follow_records = FollowRepository.get_following_of_user(db, target_user.user_id)

        following = []
        for record in follow_records:
            user = UserRepository.get_by_id(db, record.following_id)
            if user:
                following.append(
                    {
                        "user_id": str(user.user_id),
                        "username": user.username,
                        "display_name": user.display_name,
                        "is_premium": user.is_premium,
                        "billing_cycle": getattr(user, "billing_cycle", None),
                        "profile_picture": user.profile_picture,
                        "followed_at": record.created_at,
                    }
                )

        return {
            "success": True,
            "data": {
                "count": len(following),
                "following": following,
                "private": False,
            },
        }
