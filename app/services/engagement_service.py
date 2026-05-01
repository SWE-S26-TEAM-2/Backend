from uuid import UUID

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.user import User  # type: ignore
from app.repositories.comment_repo import CommentRepository
from app.repositories.like_repo import LikeRepository
from app.repositories.notification_repo import NotificationRepository
from app.repositories.repost_repo import RepostRepository
from app.repositories.track_repo import TrackRepository
from app.repositories.user_repo import UserRepository
from app.schemas.engagement_schema import AddCommentRequest


class EngagementService:

    @staticmethod
    def _get_track_or_404(db: Session, track_id: UUID):
        track = TrackRepository.get_by_id(db, track_id)
        if not track:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Track not found.",
            )
        return track

    @staticmethod
    def _ensure_track_access(track, current_user: User | None = None) -> None:
        if track.visibility == "private" and (
            current_user is None or str(track.user_id) != str(current_user.user_id)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Track is private.",
            )

    @staticmethod
    def like_track(db: Session, current_user: User, track_id: UUID) -> dict:
        track = EngagementService._get_track_or_404(db, track_id)
        EngagementService._ensure_track_access(track, current_user)

        existing = LikeRepository.get_like(db, current_user.user_id, track_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already liked this track.",
            )

        like = LikeRepository.create(db, current_user.user_id, track_id)

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
        track = EngagementService._get_track_or_404(db, track_id)
        EngagementService._ensure_track_access(track, current_user)

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

    @staticmethod
    def get_track_like_count(
        db: Session,
        track_id: UUID,
        current_user: User | None = None,
    ) -> dict:
        track = EngagementService._get_track_or_404(db, track_id)
        EngagementService._ensure_track_access(track, current_user)
        like_count = LikeRepository.count_by_track_id(db, track_id)

        return {
            "success": True,
            "data": {
                "track_id": str(track_id),
                "like_count": like_count,
            },
        }

    @staticmethod
    def get_track_engagement_summary(
        db: Session,
        track_id: UUID,
        current_user: User | None = None,
    ) -> dict:
        track = EngagementService._get_track_or_404(db, track_id)
        EngagementService._ensure_track_access(track, current_user)

        liked_by_me = None
        reposted_by_me = None

        if current_user is not None:
            liked_by_me = (
                LikeRepository.get_like(db, current_user.user_id, track_id) is not None
            )
            reposted_by_me = (
                RepostRepository.get_repost(db, current_user.user_id, track_id)
                is not None
            )

        return {
            "success": True,
            "data": {
                "track_id": str(track_id),
                "like_count": LikeRepository.count_by_track_id(db, track_id),
                "comment_count": CommentRepository.count_by_track_id(db, track_id),
                "repost_count": RepostRepository.count_by_track_id(db, track_id),
                "liked_by_me": liked_by_me,
                "reposted_by_me": reposted_by_me,
            },
        }

    @staticmethod
    def repost_track(db: Session, current_user: User, track_id: UUID) -> dict:
        track = EngagementService._get_track_or_404(db, track_id)
        EngagementService._ensure_track_access(track, current_user)

        existing = RepostRepository.get_repost(db, current_user.user_id, track_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You already reposted this track.",
            )

        repost = RepostRepository.create(db, current_user.user_id, track_id)

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
        track = EngagementService._get_track_or_404(db, track_id)
        EngagementService._ensure_track_access(track, current_user)

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

    @staticmethod
    def get_track_comments(
        db: Session,
        track_id: UUID,
        limit: int = 50,
        offset: int = 0,
        current_user: User | None = None,
    ) -> dict:
        track = EngagementService._get_track_or_404(db, track_id)
        EngagementService._ensure_track_access(track, current_user)

        comments = CommentRepository.get_by_track(
            db, track_id, limit=limit, offset=offset
        )

        return {
            "success": True,
            "data": {
                "comments": [
                    {
                        "comment_id": str(comment.comment_id),
                        "user_id": str(comment.user_id),
                        "username": (
                            u.username
                            if (u := UserRepository.get_by_id(db, comment.user_id))
                            else None
                        ),
                        "content": comment.content,
                        "timestamp_in_track": comment.timestamp_in_track,
                        "parent_comment_id": (
                            str(comment.parent_comment_id)
                            if comment.parent_comment_id
                            else None
                        ),
                        "created_at": comment.created_at,
                    }
                    for comment in comments
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
        track = EngagementService._get_track_or_404(db, track_id)
        EngagementService._ensure_track_access(track, current_user)

        if data.parent_comment_id:
            parent = CommentRepository.get_by_id(db, data.parent_comment_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Parent comment not found.",
                )
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

    @staticmethod
    def get_user_reposts(db: Session, username: str) -> dict:
        """
        Return all public tracks reposted by a user, identified by username.

        Args:
            db (Session): The database session.
            username (str): The username of the user whose reposts to fetch.

        Returns:
            dict: Success envelope with username and list of reposted tracks.

        Raises:
            HTTPException: 404 if the user is not found.
        """
        user = UserRepository.get_by_username(db, username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        reposts = RepostRepository.get_by_user_id(db, user.user_id)
        items = []
        for repost in reposts:
            track = TrackRepository.get_by_id(db, repost.track_id)
            if not track or track.visibility != "public":
                continue
            items.append({
                "repost_id": str(repost.repost_id),
                "track_id": str(track.track_id),
                "title": track.title,
                "stream_url": f"/api/tracks/{track.track_id}/audio",
                "cover_image_url": getattr(track, "cover_image_url", None),
                "reposted_at": repost.created_at,
            })

        return {
            "success": True,
            "data": {
                "username": user.username,
                "reposts": items,
            },
        }
