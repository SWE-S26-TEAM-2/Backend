"""
Repository for User database operations.

Handles all direct database queries related to the User model,
including lookups, creation, and field updates.
"""
from sqlalchemy.orm import Session  # type: ignore

from app.models.user import User  # type: ignore


class UserRepository:
    """
    Database interaction layer for the User model.
    """

    @staticmethod
    def get_by_email(db: Session, email: str):
        """
        Find a user by their email address.

        Args:
            db (Session): The database session.
            email (str): The email address to search for.

        Returns:
            User or None: The user if found, None otherwise.
        """
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id):
        """
        Find a user by their UUID.

        Args:
            db (Session): The database session.
            user_id: The UUID of the user.

        Returns:
            User or None: The user if found, None otherwise.
        """
        return (
            db.query(User).filter(User.user_id == user_id).first()
        )

    @staticmethod
    def create(db: Session, user: User) -> User:
        """
        Insert a new user into the database.

        Args:
            db (Session): The database session.
            user (User): The user object to insert.

        Returns:
            User: The created user with generated fields populated.
        """
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_verification_status(
        db: Session, user: User, verified: bool
    ) -> User:
        """
        Update a user's email verification status.

        Args:
            db (Session): The database session.
            user (User): The user to update.
            verified (bool): The new verification status.

        Returns:
            User: The updated user object.
        """
        user.is_verified = verified
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_fields(db: Session, user: User, fields: dict) -> User:
        """
        Update specific fields on a user record.

        Args:
            db (Session): The database session.
            user (User): The user to update.
            fields (dict): Dictionary of field names and new values.

        Returns:
            User: The updated user object.
        """
        for key, value in fields.items():
            setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_password(
        db: Session, user: User, new_hash: str
    ) -> User:
        """
        Update a user's password hash.

        Args:
            db (Session): The database session.
            user (User): The user to update.
            new_hash (str): The new bcrypt-hashed password.

        Returns:
            User: The updated user object.
        """
        user.password_hash = new_hash
        db.commit()
        db.refresh(user)
        return user