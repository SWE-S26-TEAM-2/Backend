from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.track_schema import CreateTrackRequest, TrackUpdate
from app.services.track_service import TrackService

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.post("/")
def create_track(
    data: CreateTrackRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return TrackService.create_track(db, user, data)


@router.delete("/{track_id}")
def delete_track(
    track_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return TrackService.delete_track(db, user, track_id)
