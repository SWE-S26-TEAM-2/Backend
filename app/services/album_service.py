from uuid import UUID

from fastapi import HTTPException, UploadFile, status  # type: ignore

from app.models.album import Album
from app.repositories.album_repo import AlbumRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.track_repo import TrackRepository
from app.utils.cloudinary_upload import upload_image

FREE_ALBUM_LIMIT = 1
COVER_PHOTO_MAX_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}
ALLOWED_VISIBILITIES = {"public", "private"}


class AlbumService:

    @staticmethod
    def _serialize_album(album) -> dict:
        return {
            "album_id": str(album.album_id),
            "user_id": str(album.user_id),
            "title": album.title,
            "description": album.description,
            "genre": album.genre,
            "tags": album.tags,
            "release_date": (
                album.release_date.isoformat() if album.release_date else None
            ),
            "cover_photo_url": album.cover_photo_url,
            "visibility": album.visibility,
            "upc": album.upc,
            "label": album.label,
            "like_count": int(album.like_count or 0),
            "track_count": int(album.track_count or 0),
            "created_at": album.created_at,
        }

    @staticmethod
    def _serialize_track_in_album(track, position: int) -> dict:
        return {
            "track_id": str(track.track_id),
            "user_id": str(track.user_id),
            "title": track.title,
            "description": track.description,
            "genre": track.genre,
            "tags": track.tags,
            "release_date": (
                track.release_date.isoformat() if track.release_date else None
            ),
            "stream_url": f"/api/tracks/{track.track_id}/audio",
            "cover_image_url": getattr(track, "cover_image_url", None),
            "visibility": track.visibility,
            "play_count": int(track.play_count or 0),
            "duration_seconds": track.duration_seconds,
            "position": position,
        }

    @staticmethod
    def _assert_owner(album, user):
        if str(album.user_id) != str(user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only modify your own albums",
            )

    @staticmethod
    def _get_album_or_404(db, album_id):
        album = AlbumRepository.get_by_id(db, album_id)
        if not album:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Album not found",
            )
        return album

    @staticmethod
    def _check_album_visibility(album, user):
        if album.visibility == "private" and (
            user is None or str(album.user_id) != str(user.user_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This album is private",
            )

    @staticmethod
    def create_album(db, user, data):
        if not user.is_premium:
            count = AlbumRepository.count_by_user_id(db, user.user_id)
            if count >= FREE_ALBUM_LIMIT:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        "Free plan limit reached. "
                        "Upgrade to Premium to create more albums."
                    ),
                )

        album = Album(
            user_id=user.user_id,
            title=data.title,
            description=data.description,
            genre=data.genre,
            tags=data.tags,
            release_date=data.release_date,
            visibility=data.visibility,
            upc=data.upc,
            label=data.label,
            like_count=0,
            track_count=0,
        )
        AlbumRepository.create(db, album)

        if data.track_ids:
            AlbumService._bulk_add_tracks(db, user, album, data.track_ids)

        return {
            "success": True,
            "message": "Album created successfully.",
            "data": AlbumService._serialize_album(album),
        }

    @staticmethod
    def _bulk_add_tracks(db, user, album, track_ids: list):
        """Add multiple tracks to a newly created album."""
        for i, track_id_str in enumerate(track_ids, start=1):
            try:
                track_id = UUID(track_id_str)
            except (ValueError, AttributeError):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid track_id: {track_id_str}",
                )

            track = TrackRepository.get_by_id(db, track_id)
            if not track:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Track {track_id_str} not found",
                )

            if str(track.user_id) != str(user.user_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=(
                        f"Track {track_id_str} does not belong to you. "
                        "Albums can only contain your own tracks."
                    ),
                )

            existing = AlbumRepository.get_track_album(db, track_id)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Track {track_id_str} already belongs to another album. "
                        "A track can only be in one album at a time."
                    ),
                )

            AlbumRepository.add_track(db, album.album_id, track_id, position=i)

        album.track_count = len(track_ids)
        db.commit()
        db.refresh(album)

    @staticmethod
    def get_album(db, album_id, user=None):
        album = AlbumService._get_album_or_404(db, album_id)
        AlbumService._check_album_visibility(album, user)

        album_tracks = AlbumRepository.get_album_tracks(db, album_id)
        tracks = []
        for at in album_tracks:
            track = TrackRepository.get_by_id(db, at.track_id)
            if track:
                # Skip private tracks if viewer is not the owner
                if track.visibility == "private" and (
                    user is None or str(track.user_id) != str(user.user_id)
                ):
                    continue
                tracks.append(AlbumService._serialize_track_in_album(track, at.position))

        data = AlbumService._serialize_album(album)
        data["tracks"] = tracks

        return {"success": True, "data": data}

    @staticmethod
    def update_album(db, user, album_id, data):
        album = AlbumService._get_album_or_404(db, album_id)
        AlbumService._assert_owner(album, user)

        update_data = data.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields provided for update",
            )

        updated = AlbumRepository.update(db, album, update_data)

        return {
            "success": True,
            "message": "Album updated successfully.",
            "data": {
                "album_id": str(updated.album_id),
                "title": updated.title,
                "description": updated.description,
                "genre": updated.genre,
                "visibility": updated.visibility,
            },
        }

    @staticmethod
    def delete_album(db, user, album_id):
        album = AlbumService._get_album_or_404(db, album_id)
        AlbumService._assert_owner(album, user)

        AlbumRepository.delete(db, album)

        return {
            "success": True,
            "message": "Album deleted successfully.",
        }

    @staticmethod
    def upload_cover_photo(db, user, album_id, file: UploadFile):
        album = AlbumService._get_album_or_404(db, album_id)
        AlbumService._assert_owner(album, user)

        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file uploaded",
            )

        if not file.content_type or file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only image files are allowed (JPEG, PNG, GIF, WebP)",
            )

        file.file.seek(0, 2)
        file_size = file.file.tell()
        file.file.seek(0)

        if file_size > COVER_PHOTO_MAX_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size must not exceed 5 MB",
            )

        cover_photo_url = upload_image(
            file.file,
            folder="streamline/albums",
            public_id=f"album_{album_id}",
        )

        AlbumRepository.update(db, album, {"cover_photo_url": cover_photo_url})

        return {
            "success": True,
            "message": "Cover photo uploaded successfully.",
            "data": {
                "album_id": str(album.album_id),
                "cover_photo_url": cover_photo_url,
            },
        }

    @staticmethod
    def add_track(db, user, album_id, data):
        album = AlbumService._get_album_or_404(db, album_id)
        AlbumService._assert_owner(album, user)

        try:
            track_id = UUID(data.track_id)
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid track_id format",
            )

        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found",
            )

        # Track must belong to the album owner
        if str(track.user_id) != str(user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only add your own tracks to your album",
            )

        # Track can't be added to this album twice
        existing_in_album = AlbumRepository.get_album_track(db, album_id, track_id)
        if existing_in_album:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Track is already in this album",
            )

        # Track can't already belong to another album
        existing_album_membership = AlbumRepository.get_track_album(db, track_id)
        if existing_album_membership:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "This track already belongs to another album. "
                    "A track can only be in one album at a time."
                ),
            )

        position = data.position
        if position is None:
            position = AlbumRepository.get_max_position(db, album_id) + 1

        AlbumRepository.add_track(db, album_id, track_id, position)

        album.track_count = (album.track_count or 0) + 1
        db.commit()

        return {
            "success": True,
            "message": "Track added to album successfully.",
        }

    @staticmethod
    def remove_track(db, user, album_id, track_id):
        album = AlbumService._get_album_or_404(db, album_id)
        AlbumService._assert_owner(album, user)

        album_track = AlbumRepository.get_album_track(db, album_id, track_id)
        if not album_track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found in this album",
            )

        AlbumRepository.remove_track(db, album_track)

        album.track_count = max(0, (album.track_count or 0) - 1)
        db.commit()

        return {
            "success": True,
            "message": "Track removed from album successfully.",
        }

    @staticmethod
    def reorder_tracks(db, user, album_id, data):
        album = AlbumService._get_album_or_404(db, album_id)
        AlbumService._assert_owner(album, user)

        # Verify all provided track_ids actually belong to this album
        existing_track_ids = {
            str(at.track_id)
            for at in AlbumRepository.get_album_tracks(db, album_id)
        }
        for track_id_str in data.track_ids:
            if track_id_str not in existing_track_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Track {track_id_str} is not in this album",
                )

        if len(set(data.track_ids)) != len(existing_track_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="track_ids must contain all tracks currently in the album",
            )

        try:
            ordered_uuids = [UUID(tid) for tid in data.track_ids]
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="One or more track_ids are invalid",
            )

        AlbumRepository.reorder_tracks(db, album_id, ordered_uuids)

        return {
            "success": True,
            "message": "Album tracks reordered successfully.",
        }

    @staticmethod
    def like_album(db, user, album_id):
        album = AlbumService._get_album_or_404(db, album_id)
        AlbumService._check_album_visibility(album, user)

        existing = AlbumRepository.get_album_like(db, user.user_id, album_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already liked this album",
            )

        album_like = AlbumRepository.create_album_like(db, user.user_id, album_id)

        album.like_count = (album.like_count or 0) + 1
        db.commit()

        if str(album.user_id) != str(user.user_id):
            NotificationRepository.create(
                db,
                user_id=album.user_id,
                actor_id=user.user_id,
                notification_type="like",
                message=f'{user.display_name} liked your album "{album.title}".',
                target_id=album_id,
            )

        return {
            "success": True,
            "message": "Album liked successfully.",
            "data": {
                "album_like_id": str(album_like.album_like_id),
                "album_id": str(album_id),
            },
        }

    @staticmethod
    def unlike_album(db, user, album_id):
        album = AlbumService._get_album_or_404(db, album_id)

        existing = AlbumRepository.get_album_like(db, user.user_id, album_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have not liked this album",
            )

        AlbumRepository.delete_album_like(db, existing)

        album.like_count = max(0, (album.like_count or 0) - 1)
        db.commit()

        return {
            "success": True,
            "message": "Album unliked successfully.",
        }

    @staticmethod
    def get_liked_albums(db, user):
        albums = AlbumRepository.get_liked_albums(db, user.user_id)

        return {
            "success": True,
            "data": [AlbumService._serialize_album(a) for a in albums],
        }

    @staticmethod
    def get_albums_by_user(db, user_id, current_user=None):
        include_private = (
            current_user is not None
            and str(current_user.user_id) == str(user_id)
        )
        albums = AlbumRepository.get_by_user_id(db, user_id, include_private=include_private)

        return {
            "success": True,
            "data": [AlbumService._serialize_album(a) for a in albums],
        }
