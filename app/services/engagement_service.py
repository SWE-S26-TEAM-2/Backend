from uuid import UUID

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.user import User  # type: ignore
from app.repositories.comment_repo import CommentRepository
from app.repositories.like_repo import LikeRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.repost_repo import RepostRepository
from app.repositories.track_repo import TrackRepository
from app.schemas.engagement_schema import AddCommentRequest


class EngagementService:

    # ── Likes ─────────────────────────────────────────────

    @staticmethod
    def like_track(db: Session, current_user: User, track_id: UUID) -> dict:
        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found.",
            )

        existing = LikeRepository.get_like(db, current_user.user_id, track_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already liked this track.",
            )

        like = LikeRepository.create(db, current_user.user_id, track_id)

        # Notify track owner (skip if liking own track)
        if str(track.user_id) != str(current_user.user_id):
            NotificationRepository.create(
                db,
                user_id=track.user_id,
                actor_id=current_user.user_id,
                notification_type="like",
                message=(
                    f"{current_user.display_name} liked your track" f' "{track.title}".'
                ),
                target_id=track_id,
            )

        return {
            "success": True,
            "message": "Track liked.",
            "data": {
                "like_id": str(like.like_id),
                "track_id": str(track_id),
            },
        }

    @staticmethod
    def unlike_track(db: Session, current_user: User, track_id: UUID) -> dict:
        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found.",
            )

        existing = LikeRepository.get_like(db, current_user.user_id, track_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have not liked this track.",
            )

        LikeRepository.delete(db, existing)

        return {
            "success": True,
            "message": "Track unliked.",
        }

    # ── Reposts ───────────────────────────────────────────

    @staticmethod
    def repost_track(db: Session, current_user: User, track_id: UUID) -> dict:
        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found.",
            )

        existing = RepostRepository.get_repost(db, current_user.user_id, track_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already reposted this track.",
            )

        repost = RepostRepository.create(db, current_user.user_id, track_id)

        # Notify track owner (skip if reposting own track)
        if str(track.user_id) != str(current_user.user_id):
            NotificationRepository.create(
                db,
                user_id=track.user_id,
                actor_id=current_user.user_id,
                notification_type="repost",
                message=(
                    f"{current_user.display_name} reposted your track"
                    f' "{track.title}".'
                ),
                target_id=track_id,
            )

        return {
            "success": True,
            "message": "Track reposted.",
            "data": {
                "repost_id": str(repost.repost_id),
                "track_id": str(track_id),
            },
        }

    @staticmethod
    def remove_repost(db: Session, current_user: User, track_id: UUID) -> dict:
        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found.",
            )

        existing = RepostRepository.get_repost(db, current_user.user_id, track_id)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You have not reposted this track.",
            )

        RepostRepository.delete(db, existing)

        return {
            "success": True,
            "message": "Repost removed.",
        }

    # ── Comments ──────────────────────────────────────────

    @staticmethod
    def get_track_comments(
        db: Session,
        track_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found.",
            )

        comments = CommentRepository.get_by_track(
            db, track_id, limit=limit, offset=offset
        )

        return {
            "success": True,
            "data": {
                "comments": [
                    {
                        "comment_id": str(c.comment_id),
                        "user_id": str(c.user_id),
                        "content": c.content,
                        "timestamp_in_track": c.timestamp_in_track,
                        "parent_comment_id": (
                            str(c.parent_comment_id) if c.parent_comment_id else None
                        ),
                        "created_at": c.created_at,
                    }
                    for c in comments
                ],
            },
        }

    @staticmethod
    def add_comment(
        db: Session,
        current_user: User,
        track_id: UUID,
        data: AddCommentRequest,
    ) -> dict:
        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found.",
            )

        # Validate parent comment if provided
        if data.parent_comment_id:
            parent = CommentRepository.get_by_id(db, data.parent_comment_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent comment not found.",
                )
            # Only one level of replies allowed
            if parent.parent_comment_id is not None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot reply to a reply (max 1 level).",
                )

        comment = CommentRepository.create(
            db,
            user_id=current_user.user_id,
            track_id=track_id,
            content=data.content,
            timestamp_in_track=data.timestamp_in_track,
            parent_comment_id=data.parent_comment_id,
        )

        # Notify track owner (skip if commenting on own track)
        if str(track.user_id) != str(current_user.user_id):
            NotificationRepository.create(
                db,
                user_id=track.user_id,
                actor_id=current_user.user_id,
                notification_type="comment",
                message=(
                    f"{current_user.display_name} commented on your"
                    f' track "{track.title}".'
                ),
                target_id=track_id,
            )

        # Notify parent comment author on a reply (skip if replying to yourself
        # or if they are the track owner who was already notified above)
        if data.parent_comment_id:
            parent = CommentRepository.get_by_id(db, data.parent_comment_id)
            is_self = (
                str(parent.user_id) == str(current_user.user_id) if parent else True
            )
            is_owner = str(parent.user_id) == str(track.user_id) if parent else True
            if parent and not is_self and not is_owner:
                NotificationRepository.create(
                    db,
                    user_id=parent.user_id,
                    actor_id=current_user.user_id,
                    notification_type="reply",
                    message=(
                        f"{current_user.display_name} replied to your comment"
                        f' on "{track.title}".'
                    ),
                    target_id=track_id,
                )

        return {
            "success": True,
            "message": "Comment added.",
            "data": {
                "comment_id": str(comment.comment_id),
                "track_id": str(track_id),
                "content": comment.content,
                "timestamp_in_track": comment.timestamp_in_track,
                "parent_comment_id": (
                    str(comment.parent_comment_id)
                    if comment.parent_comment_id
                    else None
                ),
                "created_at": comment.created_at,
            },
        }
