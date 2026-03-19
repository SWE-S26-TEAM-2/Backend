"""
Core security module for JWT token management and password hashing.

Handles access/refresh token creation, verification, and bcrypt
password hashing for the entire application.
"""
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt  # type: ignore
from jose import JWTError, jwt  # type: ignore

# ──────────────────────────────────────────────
# CONSTANTS — Change SECRET_KEY in production!
# ──────────────────────────────────────────────
SECRET_KEY = "super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using bcrypt.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        str: The bcrypt-hashed password string.
    """
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored bcrypt hash.

    Args:
        plain_password (str): The plain-text password to check.
        hashed_password (str): The stored bcrypt hash.

    Returns:
        bool: True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(user_id: str) -> str:
    """
    Create a short-lived JWT access token for a user.

    Args:
        user_id (str): The UUID of the user as a string.

    Returns:
        str: An encoded JWT access token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived JWT refresh token for a user.

    Args:
        user_id (str): The UUID of the user as a string.

    Returns:
        str: An encoded JWT refresh token string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.

    Args:
        token (str): The JWT access token string.

    Returns:
        dict: The decoded token payload containing 'sub' (user_id).

    Raises:
        JWTError: If the token is invalid, expired, or not an access token.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    if payload.get("type") != "access":
        raise JWTError("Token is not an access token")
    return payload
