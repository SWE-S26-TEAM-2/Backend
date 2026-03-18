from uuid import UUID

from fastapi import APIRouter, status, Depends, HTTPException
from fastapi.params import Body
from sqlalchemy.orm import Session

from app import models
from ..database.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


# @router.get("/")
# def main():
#     return {"message": "hello user"}
@router.get("/me", status_code=status.HTTP_200_OK)
def get_my_profile(db: Session = Depends(get_db)):
    current_user = (
        db.query(models.user.User)
        .filter(models.user.User.email == "user1@example.com")
        .first()
    )

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

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
            "updated_at": current_user.updated_at,
        },
    }


@router.get("/{user_id}", status_code=status.HTTP_200_OK)
def get_user_profile(user_id: UUID, db: Session = Depends(get_db)):
    user = (
        db.query(models.user.User).filter(models.user.User.user_id == user_id).first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
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


@router.patch("/me", status_code=status.HTTP_200_OK)
def update_my_profile(payload: dict = Body(...), db: Session = Depends(get_db)):
    current_user = (
        db.query(models.user.User)
        .filter(models.user.User.email == "user1@example.com")
        .first()
    )

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    allowed_fields = ["display_name", "bio", "location", "account_type"]

    for field in allowed_fields:
        if field in payload:
            setattr(current_user, field, payload[field])

    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": {
            "user_id": str(current_user.user_id),
            "display_name": current_user.display_name,
            "bio": current_user.bio,
            "location": current_user.location,
            "account_type": current_user.account_type,
            "updated_at": current_user.updated_at,
        },
    }


@router.patch("/me/privacy", status_code=status.HTTP_200_OK)
def update_profile_privacy(payload: dict = Body(...), db: Session = Depends(get_db)):
    current_user = (
        db.query(models.user.User)
        .filter(models.user.User.email == "user1@example.com")
        .first()
    )

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    if "is_private" not in payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="is_private is required"
        )

    if type(payload["is_private"]) is not bool:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="is_private must be true or false",
        )

    current_user.is_private = payload["is_private"]

    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Profile visibility updated",
        "data": {
            "user_id": str(current_user.user_id),
            "is_private": current_user.is_private,
        },
    }
