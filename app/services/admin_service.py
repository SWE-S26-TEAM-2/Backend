from datetime import datetime, time, timezone
from uuid import UUID

from fastapi import HTTPException, status  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.models.comment import Comment
from app.models.listening_history import ListeningHistory
from app.models.report import Report
from app.models.track import Track
from app.models.user import User
from app.repositories.comment_repo import CommentRepository
from app.repositories.refresh_token_repo import RefreshTokenRepository
from app.repositories.report_repo import ReportRepository
from app.repositories.track_repo import TrackRepository
from app.repositories.user_repo import UserRepository
from app.services.track_service import TrackService

REPORTABLE_ENTITY_TYPES = {"track", "comment", "user"}
REPORT_STATUSES = {"open", "under_review", "resolved", "dismissed"}


class AdminService:
    @staticmethod
    def _get_report_target_or_404(db: Session, entity_type: str, entity_id: UUID):
        if entity_type == "track":
            entity = TrackRepository.get_by_id(db, entity_id)
        elif entity_type == "comment":
            entity = CommentRepository.get_by_id(db, entity_id)
        elif entity_type == "user":
            entity = UserRepository.get_by_id(db, entity_id)
        else:
            entity = None

        if entity is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"{entity_type.title()} not found.",
            )

        return entity

    @staticmethod
    def _count_rows(db: Session, model) -> int:
        return int(db.query(model).count())

    @staticmethod
    def _count_reports(db: Session, report_status: str | None = None) -> int:
        query = db.query(Report)
        if report_status is not None:
            query = query.filter(Report.status == report_status)
        return int(query.count())

    @staticmethod
    def _count_listening_history_since(db: Session, started_at: datetime) -> int:
        return int(
            db.query(ListeningHistory)
            .filter(ListeningHistory.played_at >= started_at)
            .count()
        )

    @staticmethod
    def _serialize_actor(user: User | None):
        if user is None:
            return None

        return {
            "user_id": str(user.user_id),
            "username": user.username,
            "display_name": user.display_name,
        }

    @staticmethod
    def _serialize_entity_preview(
        report,
        track_map: dict,
        comment_map: dict,
        user_map: dict,
    ):
        if report.entity_type == "track":
            track = track_map.get(report.entity_id)
            if not track:
                return None
            return {
                "track_id": str(track.track_id),
                "title": track.title,
                "user_id": str(track.user_id),
                "visibility": track.visibility,
                "play_count": int(track.play_count or 0),
            }

        if report.entity_type == "comment":
            comment = comment_map.get(report.entity_id)
            if not comment:
                return None
            return {
                "comment_id": str(comment.comment_id),
                "user_id": str(comment.user_id),
                "track_id": str(comment.track_id),
                "content": comment.content,
                "parent_comment_id": (
                    str(comment.parent_comment_id) if comment.parent_comment_id else None
                ),
            }

        user = user_map.get(report.entity_id)
        if not user:
            return None

        return {
            "user_id": str(user.user_id),
            "username": user.username,
            "display_name": user.display_name,
            "account_type": user.account_type,
            "is_suspended": bool(user.is_suspended),
        }

    @staticmethod
    def _serialize_report(report, users_by_id: dict, tracks_by_id: dict, comments_by_id: dict):
        reporter = users_by_id.get(report.reporter_id)
        reviewer = users_by_id.get(report.reviewed_by) if report.reviewed_by else None

        return {
            "report_id": str(report.report_id),
            "entity_type": report.entity_type,
            "entity_id": str(report.entity_id),
            "reason": report.reason,
            "status": report.status,
            "created_at": report.created_at,
            "reporter": AdminService._serialize_actor(reporter),
            "reviewed_by": AdminService._serialize_actor(reviewer),
            "reviewed_at": report.reviewed_at,
            "resolution_note": report.resolution_note,
            "entity_preview": AdminService._serialize_entity_preview(
                report,
                tracks_by_id,
                comments_by_id,
                users_by_id,
            ),
        }

    @staticmethod
    def submit_report(db: Session, current_user: User, data) -> dict:
        if data.entity_type not in REPORTABLE_ENTITY_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported entity_type.",
            )

        AdminService._get_report_target_or_404(db, data.entity_type, data.entity_id)

        existing = ReportRepository.get_active_by_reporter_and_entity(
            db,
            current_user.user_id,
            data.entity_type,
            data.entity_id,
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You already have an active report for this entity.",
            )

        report = Report(
            reporter_id=current_user.user_id,
            entity_type=data.entity_type,
            entity_id=data.entity_id,
            reason=data.reason.strip(),
        )
        ReportRepository.create(db, report)

        return {
            "success": True,
            "message": "Report submitted successfully.",
            "data": {
                "report_id": str(report.report_id),
                "entity_type": report.entity_type,
                "entity_id": str(report.entity_id),
                "status": report.status,
                "created_at": report.created_at,
            },
        }

    @staticmethod
    def update_user_suspension(
        db: Session,
        user_id: UUID,
        current_admin: User,
        data,
    ) -> dict:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if str(user.user_id) == str(current_admin.user_id) and data.is_suspended:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admins cannot suspend themselves.",
            )

        UserRepository.update_fields(db, user, {"is_suspended": data.is_suspended})

        if data.is_suspended:
            RefreshTokenRepository.revoke_all_for_user(db, str(user.user_id))

        return {
            "success": True,
            "message": (
                "User suspended successfully."
                if data.is_suspended
                else "User unsuspended successfully."
            ),
            "data": {
                "user_id": str(user.user_id),
                "username": user.username,
                "display_name": user.display_name,
                "is_suspended": bool(user.is_suspended),
                "reason": data.reason.strip() if data.reason else None,
            },
        }

    @staticmethod
    def update_user_role(
        db: Session,
        user_id: UUID,
        current_admin: User,
        data,
    ) -> dict:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if data.role != "admin" and str(user.user_id) == str(current_admin.user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admins cannot remove their own admin role.",
            )

        if user.role == "admin" and data.role != "admin":
            if UserRepository.count_by_role(db, "admin") <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin.",
                )

        UserRepository.update_fields(db, user, {"role": data.role})

        return {
            "success": True,
            "message": "User role updated successfully.",
            "data": {
                "user_id": str(user.user_id),
                "username": user.username,
                "display_name": user.display_name,
                "role": user.role,
            },
        }

    @staticmethod
    def get_analytics(db: Session) -> dict:
        now_utc = datetime.now(timezone.utc)
        start_of_today = datetime.combine(now_utc.date(), time.min, tzinfo=timezone.utc)

        return {
            "success": True,
            "data": {
                "total_users": AdminService._count_rows(db, User),
                "total_tracks": AdminService._count_rows(db, Track),
                "total_comments": AdminService._count_rows(db, Comment),
                "total_reports": AdminService._count_reports(db),
                "open_reports": AdminService._count_reports(db, "open"),
                "under_review_reports": AdminService._count_reports(db, "under_review"),
                "resolved_reports": AdminService._count_reports(db, "resolved"),
                "dismissed_reports": AdminService._count_reports(db, "dismissed"),
                "suspended_users": int(
                    db.query(User).filter(User.is_suspended.is_(True)).count()
                ),
                "active_streams_today": AdminService._count_listening_history_since(
                    db, start_of_today
                ),
            },
        }

    @staticmethod
    def list_reports(
        db: Session,
        *,
        report_status: str | None = None,
        entity_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        if report_status and report_status not in REPORT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report status.",
            )

        if entity_type and entity_type not in REPORTABLE_ENTITY_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid entity type.",
            )

        reports, total = ReportRepository.list_reports(
            db,
            status=report_status,
            entity_type=entity_type,
            limit=limit,
            offset=offset,
        )

        user_ids = {
            report.reporter_id for report in reports if report.reporter_id is not None
        }
        user_ids.update(
            report.reviewed_by for report in reports if report.reviewed_by is not None
        )
        user_ids.update(
            report.entity_id for report in reports if report.entity_type == "user"
        )

        track_ids = [report.entity_id for report in reports if report.entity_type == "track"]
        comment_ids = [
            report.entity_id for report in reports if report.entity_type == "comment"
        ]

        users_by_id = {
            user.user_id: user for user in UserRepository.get_by_ids(db, list(user_ids))
        }
        tracks_by_id = {
            track.track_id: track for track in TrackRepository.get_by_ids(db, track_ids)
        }
        comments_by_id = {
            comment.comment_id: comment
            for comment in CommentRepository.get_by_ids(db, comment_ids)
        }

        return {
            "success": True,
            "data": {
                "total": total,
                "reports": [
                    AdminService._serialize_report(
                        report,
                        users_by_id,
                        tracks_by_id,
                        comments_by_id,
                    )
                    for report in reports
                ],
            },
        }

    @staticmethod
    def review_report(db: Session, report_id: UUID, current_admin: User, data) -> dict:
        if data.status not in REPORT_STATUSES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid report status.",
            )

        report = ReportRepository.get_by_id(db, report_id)
        if not report:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found.",
            )

        report = ReportRepository.review(
            db,
            report,
            status=data.status,
            reviewed_by=current_admin.user_id,
            reviewed_at=datetime.now(timezone.utc),
            resolution_note=(
                data.resolution_note.strip() if data.resolution_note else None
            ),
        )

        user_ids = [report.reporter_id, current_admin.user_id]
        if report.entity_type == "user":
            user_ids.append(report.entity_id)

        users_by_id = {
            user.user_id: user for user in UserRepository.get_by_ids(db, user_ids)
        }
        tracks_by_id = {}
        comments_by_id = {}

        if report.entity_type == "track":
            tracks_by_id = {
                track.track_id: track
                for track in TrackRepository.get_by_ids(db, [report.entity_id])
            }
        elif report.entity_type == "comment":
            comments_by_id = {
                comment.comment_id: comment
                for comment in CommentRepository.get_by_ids(db, [report.entity_id])
            }

        return {
            "success": True,
            "message": "Report updated successfully.",
            "data": AdminService._serialize_report(
                report,
                users_by_id,
                tracks_by_id,
                comments_by_id,
            ),
        }

    @staticmethod
    def delete_comment(db: Session, comment_id: UUID) -> dict:
        comment = CommentRepository.get_by_id(db, comment_id)
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found.",
            )

        CommentRepository.delete(db, comment)

        return {
            "success": True,
            "message": "Comment deleted successfully.",
        }

    @staticmethod
    def delete_track(db: Session, track_id: UUID) -> dict:
        track = TrackService.admin_delete_track(db, track_id)

        return {
            "success": True,
            "message": "Track deleted successfully.",
            "data": {
                "track_id": str(track.track_id),
                "title": track.title,
            },
        }
