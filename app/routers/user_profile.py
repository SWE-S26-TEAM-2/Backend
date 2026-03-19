from uuid import UUID
import os
import shutil
from fastapi import APIRouter, status, Depends, HTTPException, UploadFile, File
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


@router.put("/me/avatar", status_code=status.HTTP_200_OK)
def upload_profile_picture(file: UploadFile = File(...), db: Session = Depends(get_db)):
    current_user = (
        db.query(models.user.User)
        .filter(models.user.User.email == "user1@example.com")
        .first()
    )

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    allowed_types = ["image/jpeg", "image/png", "image/webp"]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WEBP files are allowed",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 5 MB",
        )

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_folder = os.path.join(base_dir, "Uploads", "Avatar")
    os.makedirs(upload_folder, exist_ok=True)

    file_extension = file.filename.split(".")[-1]
    file_name = f"{current_user.user_id}.{file_extension}"

    absolute_file_path = os.path.join(upload_folder, file_name)
    relative_file_path = os.path.join("Uploads", "Avatar", file_name)

    with open(absolute_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.profile_picture = relative_file_path

    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Profile picture uploaded successfully",
        "data": {
            "user_id": str(current_user.user_id),
            "profile_picture": current_user.profile_picture,
        },
    }


@router.put("/me/cover", status_code=status.HTTP_200_OK)
def upload_cover_photo(file: UploadFile = File(...), db: Session = Depends(get_db)):
    current_user = (
        db.query(models.user.User)
        .filter(models.user.User.email == "user1@example.com")
        .first()
    )

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    allowed_types = ["image/jpeg", "image/png", "image/webp"]

    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG, PNG, and WEBP files are allowed",
        )

    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 10 MB",
        )

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_folder = os.path.join(base_dir, "Uploads", "Cover")
    os.makedirs(upload_folder, exist_ok=True)

    file_extension = file.filename.split(".")[-1]
    file_name = f"{current_user.user_id}.{file_extension}"

    absolute_file_path = os.path.join(upload_folder, file_name)
    relative_file_path = os.path.join("Uploads", "Cover", file_name)

    with open(absolute_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.cover_photo = relative_file_path

    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "message": "Cover photo uploaded successfully",
        "data": {
            "user_id": str(current_user.user_id),
            "cover_photo": current_user.cover_photo,
        },
    }


@router.get("/me/social-links", status_code=status.HTTP_200_OK)
def get_my_social_links(db: Session = Depends(get_db)):
    current_user = (
        db.query(models.user.User)
        .filter(models.user.User.email == "user3@example.com")
        .first()
    )

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    social_links = (
        db.query(models.social_link.SocialLink)
        .filter(models.social_link.SocialLink.user_id == current_user.user_id)
        .all()
    )

    return {
        "success": True,
        "data": {
            "user_id": str(current_user.user_id),
            "social_links": [
                {"platform": link.platform, "url": link.url} for link in social_links
            ],
        },
    }


@router.put("/me/social-links", status_code=status.HTTP_200_OK)
def update_my_social_links(payload: dict = Body(...), db: Session = Depends(get_db)):
    current_user = (
        db.query(models.user.User)
        .filter(models.user.User.email == "user1@example.com")
        .first()
    )

    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No user found"
        )

    if "social_links" not in payload:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="social_links is required",
        )

    if type(payload["social_links"]) is not list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="social_links must be a list",
        )

    if len(payload["social_links"]) > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5 social links are allowed",
        )

    allowed_platforms = ["instagram", "twitter", "facebook", "youtube", "website"]

    for link in payload["social_links"]:
        if type(link) is not dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each social link must be an object",
            )

        if "platform" not in link or "url" not in link:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Each social link must contain platform and url",
            )

        if link["platform"] not in allowed_platforms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid platform",
            )

        if not str(link["url"]).startswith("https://"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="URL must start with https://",
            )

    old_links = (
        db.query(models.social_link.SocialLink)
        .filter(models.social_link.SocialLink.user_id == current_user.user_id)
        .all()
    )

    for old_link in old_links:
        db.delete(old_link)

    for link in payload["social_links"]:
        new_link = models.social_link.SocialLink(
            user_id=current_user.user_id,
            platform=link["platform"],
            url=link["url"],
        )
        db.add(new_link)

    db.commit()

    updated_links = (
        db.query(models.social_link.SocialLink)
        .filter(models.social_link.SocialLink.user_id == current_user.user_id)
        .all()
    )

    return {
        "success": True,
        "message": "Social links updated successfully",
        "data": {
            "user_id": str(current_user.user_id),
            "social_links": [
                {"platform": link.platform, "url": link.url} for link in updated_links
            ],
        },
    }
