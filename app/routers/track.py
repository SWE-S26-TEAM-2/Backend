from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.track_schema import CreateTrackRequest, TrackUpdate
from app.services import track_service
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

@router.get("/{track_id}")
def get_track(track_id: str, db: Session = Depends(get_db)):
    track = track_service.get_track_by_id(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return {"success": True, "data": track}

@router.put("/{track_id}")
def update_track(
    track_id: str,
    track_data: TrackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = track_service.update_track(db, track_id, track_data, current_user.id)

    if not updated:
        raise HTTPException(status_code=403, detail="Not authorized or track not found")

    return {"success": True, "data": updated}