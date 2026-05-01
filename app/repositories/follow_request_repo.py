from sqlalchemy.orm import Session

from app.models.follow_request import FollowRequest


class FollowRequestRepository:

    @staticmethod
    def get(db: Session, requester_id, target_id):
        return (
            db.query(FollowRequest)
            .filter(
                FollowRequest.requester_id == requester_id,
                FollowRequest.target_id == target_id,
            )
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, request_id):
        return (
            db.query(FollowRequest)
            .filter(FollowRequest.request_id == request_id)
            .first()
        )

    @staticmethod
    def get_pending_for_target(db: Session, target_id):
        return (
            db.query(FollowRequest)
            .filter(FollowRequest.target_id == target_id)
            .order_by(FollowRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def create(db: Session, requester_id, target_id) -> FollowRequest:
        req = FollowRequest(requester_id=requester_id, target_id=target_id)
        db.add(req)
        db.commit()
        db.refresh(req)
        return req

    @staticmethod
    def delete(db: Session, follow_request: FollowRequest) -> None:
        db.delete(follow_request)
        db.commit()
