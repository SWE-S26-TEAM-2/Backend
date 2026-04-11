from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
)  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.track_schema import TrackUpdate
from app.services.track_service import TrackService

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.post("/")
def create_track(
    title: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return TrackService.create_track(db, user, title, description, file)


@router.delete("/{track_id}")
def delete_track(
    track_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return TrackService.delete_track(db, user, track_id)


@router.get("/{track_id}")
def get_track(track_id: UUID, db: Session = Depends(get_db)):
    track = TrackService.get_track_by_id(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")
    return {
        "success": True,
        "data": {
            "track_id": str(track.track_id),
            "title": track.title,
            "description": track.description,
            "file_url": track.file_url,
            "user_id": str(track.user_id),
            "visibility": track.visibility,
        },
    }


@router.put("/{track_id}")
def update_track(
    track_id: UUID,
    track_data: TrackUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = TrackService.update_track(db, track_id, track_data, current_user.user_id)

    if result is None:
        raise HTTPException(status_code=404, detail="Track not found")
    if result == "forbidden":
        raise HTTPException(
            status_code=403, detail="Not Authorized to update this track"
        )

    return {"success": True, "data": result}
