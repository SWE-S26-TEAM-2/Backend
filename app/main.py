"""
FastAPI application entry point.

Initializes the FastAPI app, registers all routers,
and creates database tables on startup.
"""

import os
from fastapi import FastAPI  # type: ignore
from fastapi.staticfiles import StaticFiles  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from sqlalchemy import inspect, text  # type: ignore

from app.database.database import Base, engine  # type: ignore
from app.models import (  # noqa: F401
    email_verification,
    password_reset,
    social_link,
    user,
    track,
    playlist,
    playlist_track,
    playlist_like,
    follow,
    block,
    listening_history,
    refresh_token,
)
from app.routers.auth import router as auth_router  # type: ignore
from app.routers.user_profile import router as user_router  # type: ignore
from app.routers.messaging import router as messaging_router
from app.routers.follower import router as follower_router
from app.routers.notification import router as notification_router
from app.routers.playlist import router as playlist_router
from app.routers.search import router as search_router
from app.routers.subscription import router as subscription_router
from app.routers.track import router as track_router
from app.routers.feed import router as feed_router

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.environ.get("UPLOAD_DIR", os.path.join(BASE_DIR, "uploads"))


app = FastAPI(
    title="SoundCloud Clone API",
    version="1.0.0",
    root_path="/api",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.on_event("startup")
def startup():
    """Create database tables on startup."""
    Base.metadata.create_all(bind=engine)

    existing_columns = [col["name"] for col in inspect(engine).get_columns("tracks")]
    if "created_at" not in existing_columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE tracks ADD COLUMN created_at TIMESTAMPTZ DEFAULT now()"))
            conn.commit()


app.include_router(auth_router)
app.include_router(user_router)
app.include_router(messaging_router)
app.include_router(notification_router)
app.include_router(follower_router)
app.include_router(playlist_router)
app.include_router(search_router)
app.include_router(subscription_router)
app.include_router(track_router)
app.include_router(feed_router)


@app.get("/")
def root():
    """
    Health check endpoint.

    Returns:
        dict: Simple message confirming the API is running.
    """
    return {"message": "API is running"}
