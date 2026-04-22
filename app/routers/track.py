from datetime import date
from uuid import UUID
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form,
    Request,
)  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.core.dependencies import get_current_user, get_optional_current_user
from app.database.database import get_db
from app.models.user import User
from app.schemas.track_schema import RecordPlayRequest, TrackUpdate
from app.services.track_service import TrackService

router = APIRouter(prefix="/tracks", tags=["Tracks"])


@router.post("/")
def create_track(
    title: str = Form(...),
    description: str = Form(...),
    genre: str | None = Form(None),
    tags: str | None = Form(None),
    release_date: date | None = Form(None),
    visibility: str = Form("public"),
    file: UploadFile = File(...),
    cover_image: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return TrackService.create_track(
        db,
        user,
        title,
        description,
        file,
        genre,
        tags,
        release_date,
        visibility,
        cover_image,
    )


@router.delete("/{track_id}")
def delete_track(
    track_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return TrackService.delete_track(db, user, track_id)


@router.get("/{track_id}")
def get_track(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return TrackService.get_track_details(db, track_id, current_user)


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


@router.get("/{track_id}/waveform")
def get_track_waveform(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return TrackService.get_waveform(db, track_id, current_user)


@router.get("/{track_id}/stream")
def get_track_stream(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return TrackService.get_stream(db, track_id, current_user)


@router.get("/{track_id}/audio")
def stream_track_audio(
    track_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return TrackService.stream_audio(db, track_id, request, current_user)


@router.post("/{track_id}/plays")
def record_track_play(
    track_id: UUID,
    data: RecordPlayRequest | None = None,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    duration = data.duration_listened_seconds if data else None
    return TrackService.record_play(db, track_id, current_user, duration)


@router.get("/{track_id}/playback")
def get_track_playback(
    track_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_current_user),
):
    return TrackService.get_playback(db, track_id, current_user)
