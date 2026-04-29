from datetime import datetime

from sqlalchemy.orm import Session  # type: ignore

from app.models.report import Report  # type: ignore


class ReportRepository:
    @staticmethod
    def create(db: Session, report: Report) -> Report:
        db.add(report)
        db.commit()
        db.refresh(report)
        return report

    @staticmethod
    def get_by_id(db: Session, report_id):
        return db.query(Report).filter(Report.report_id == report_id).first()

    @staticmethod
    def get_active_by_reporter_and_entity(
        db: Session,
        reporter_id,
        entity_type: str,
        entity_id,
    ):
        return (
            db.query(Report)
            .filter(
                Report.reporter_id == reporter_id,
                Report.entity_type == entity_type,
                Report.entity_id == entity_id,
                Report.status.in_(("open", "under_review")),
            )
            .first()
        )

    @staticmethod
    def list_reports(
        db: Session,
        status: str | None = None,
        entity_type: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ):
        query = db.query(Report)

        if status:
            query = query.filter(Report.status == status)

        if entity_type:
            query = query.filter(Report.entity_type == entity_type)

        total = query.count()
        reports = (
            query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()
        )

        return reports, total

    @staticmethod
    def review(
        db: Session,
        report: Report,
        *,
        status: str,
        reviewed_by,
        reviewed_at: datetime,
        resolution_note: str | None = None,
    ) -> Report:
        report.status = status
        report.reviewed_by = reviewed_by
        report.reviewed_at = reviewed_at
        report.resolution_note = resolution_note
        db.commit()
        db.refresh(report)
        return report
