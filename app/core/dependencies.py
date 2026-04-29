"""
FastAPI dependencies for authentication and database session injection.

Provides the get_current_user dependency that extracts and validates
the JWT token from the Authorization header in protected endpoints.
"""

from fastapi import Depends, HTTPException, status  # type: ignore
from fastapi.security import OAuth2PasswordBearer  # type: ignore
from jose import JWTError  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.security import decode_access_token  # type: ignore
from app.database.database import get_db  # type: ignore
from app.models.user import User  # type: ignore

# This tells FastAPI to look for a Bearer token in the Authorization header
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
optional_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False,
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the JWT access token and return the current user.

    This is a FastAPI dependency. Add it to any endpoint that
    requires authentication using Depends(get_current_user).

    Args:
        token (str): The JWT Bearer token extracted from the header.
        db (Session): The database session from get_db dependency.

    Returns:
        User: The authenticated user's SQLAlchemy model object.

    Raises:
        HTTPException: 401 if the token is invalid or user not found.
        HTTPException: 403 if the user account is suspended.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication token is missing or invalid.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.user_id == user_id).first()

    if user is None:
        raise credentials_exception

    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended.",
        )

    return user


def get_optional_current_user(
    token: str | None = Depends(optional_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    """
    Return the current user when a valid Bearer token is provided.

    Public endpoints can use this to attach user-specific behavior without
    requiring authentication for anonymous callers.
    """
    if token is None:
        return None

    return get_current_user(token=token, db=db)


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    """
    Return the current user only when they have admin privileges.
    """
    if getattr(current_user, "role", None) != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )

    return current_user
