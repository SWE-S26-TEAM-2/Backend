from sqlalchemy.orm import Session  # type: ignore

from app.models.comment import Comment  # type: ignore


class CommentRepository:

    @staticmethod
    def get_by_id(db: Session, comment_id):
        return db.query(Comment).filter(Comment.comment_id == comment_id).first()

    @staticmethod
    def get_by_ids(db: Session, comment_ids):
        if not comment_ids:
            return []
        return db.query(Comment).filter(Comment.comment_id.in_(comment_ids)).all()

    @staticmethod
    def get_by_track(db: Session, track_id, limit: int = 50, offset: int = 0):
        return (
            db.query(Comment)
            .filter(Comment.track_id == track_id)
            .order_by(Comment.created_at.asc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    @staticmethod
    def count_by_track_id(db: Session, track_id) -> int:
        return int(db.query(Comment).filter(Comment.track_id == track_id).count())

    @staticmethod
    def create(
        db: Session,
        user_id,
        track_id,
        content: str,
        timestamp_in_track=None,
        parent_comment_id=None,
    ) -> Comment:
        comment = Comment(
            user_id=user_id,
            track_id=track_id,
            content=content,
            timestamp_in_track=timestamp_in_track,
            parent_comment_id=parent_comment_id,
        )
        db.add(comment)
        db.commit()
        db.refresh(comment)
        return comment

    @staticmethod
    def delete(db: Session, comment: Comment) -> None:
        db.delete(comment)
        db.commit()
