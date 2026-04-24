"""
Repository for Follow database operations.

All raw queries for the follows table live here.
The service layer calls these methods — never queries directly.
"""

from sqlalchemy.orm import Session  # type: ignore

from app.models.follow import Follow  # type: ignore


class FollowRepository:

    @staticmethod
    def get_follow(db: Session, follower_id, following_id):
        """
        Find an existing follow relationship between two users.

        Args:
            db (Session): The database session.
            follower_id: UUID of the user who is following.
            following_id: UUID of the user being followed.

        Returns:
            Follow or None: The follow record if it exists.
        """
        return (
            db.query(Follow)
            .filter(
                Follow.follower_id == follower_id,
                Follow.following_id == following_id,
            )
            .first()
        )

    @staticmethod
    def create_follow(db: Session, follower_id, following_id) -> Follow:
        """
        Insert a new follow record into the database.

        Args:
            db (Session): The database session.
            follower_id: UUID of the user who is following.
            following_id: UUID of the user being followed.

        Returns:
            Follow: The newly created follow record.
        """
        follow = Follow(
            follower_id=follower_id,
            following_id=following_id,
        )
        db.add(follow)
        db.commit()
        db.refresh(follow)
        return follow

    @staticmethod
    def get_followers_of(db: Session, user_id) -> list:
        """
        Return all Follow records where following_id == user_id.

        Used to fan-out notifications when a user uploads a new track.

        Args:
            db (Session): The database session.
            user_id: UUID of the user whose followers are needed.

        Returns:
            list[Follow]: All follow records pointing at this user.
        """
        return db.query(Follow).filter(Follow.following_id == user_id).all()

    @staticmethod
    def delete_follow(db: Session, follow: Follow) -> None:
        """
        Delete an existing follow record.

        Args:
            db (Session): The database session.
            follow (Follow): The follow object to delete.
        """
        db.delete(follow)
        db.commit()

    @staticmethod
    def get_followers_of_user(db: Session, user_id) -> list:
        """
        Get all follow records where following_id == user_id.
        These are the people who follow the given user.

        Args:
            db (Session): The database session.
            user_id: UUID of the user whose followers we want.

        Returns:
            list[Follow]: All follow records pointing to this user.
        """
        return db.query(Follow).filter(Follow.following_id == user_id).all()

    @staticmethod
    def get_following_of_user(db: Session, user_id) -> list:
        """
        Get all follow records where follower_id == user_id.
        These are the people the given user follows.

        Args:
            db (Session): The database session.
            user_id: UUID of the user whose following list we want.

        Returns:
            list[Follow]: All follow records from this user.
        """
        return db.query(Follow).filter(Follow.follower_id == user_id).all()
