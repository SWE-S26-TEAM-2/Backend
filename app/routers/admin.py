from uuid import UUID

from fastapi import APIRouter, Depends, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_admin, get_current_user
from app.database.database import get_db
from app.models.user import User  # type: ignore
from app.schemas.admin_schema import (
    CreateReportRequest,
    ReviewReportRequest,
    UpdateUserSuspensionRequest,
    UpdateUserRoleRequest,
)
from app.schemas.responses import (  # type: ignore
    AdminAnalyticsResponse,
    AdminReportReviewResponse,
    AdminReportsResponse,
    AdminTrackModerationResponse,
    AdminUserRoleResponse,
    AdminUserModerationResponse,
    MessageResponse,
    ReportSubmissionResponse,
)
from app.services.admin_service import AdminService

router = APIRouter(tags=["Moderation & Admin"])


@router.post("/reports", response_model=ReportSubmissionResponse)
def submit_report(
    data: CreateReportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return AdminService.submit_report(db, current_user, data)


@router.get("/admin/analytics", response_model=AdminAnalyticsResponse)
def get_admin_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.get_analytics(db)


@router.get("/admin/reports", response_model=AdminReportsResponse)
def list_reports(
    status: str | None = Query(None),
    entity_type: str | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.list_reports(
        db,
        report_status=status,
        entity_type=entity_type,
        limit=limit,
        offset=offset,
    )


@router.patch("/admin/reports/{report_id}", response_model=AdminReportReviewResponse)
def review_report(
    report_id: UUID,
    data: ReviewReportRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.review_report(db, report_id, current_admin, data)


@router.patch(
    "/admin/users/{user_id}/suspension",
    response_model=AdminUserModerationResponse,
)
def update_user_suspension(
    user_id: UUID,
    data: UpdateUserSuspensionRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.update_user_suspension(db, user_id, current_admin, data)


@router.patch("/admin/users/{user_id}/role", response_model=AdminUserRoleResponse)
def update_user_role(
    user_id: UUID,
    data: UpdateUserRoleRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.update_user_role(db, user_id, current_admin, data)


@router.delete("/admin/comments/{comment_id}", response_model=MessageResponse)
def delete_comment(
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.delete_comment(db, comment_id)


@router.delete("/admin/tracks/{track_id}", response_model=AdminTrackModerationResponse)
def delete_track(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin),
):
    return AdminService.delete_track(db, track_id)
