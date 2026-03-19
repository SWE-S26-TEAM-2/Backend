"""
FastAPI application entry point.

Initializes the FastAPI app, registers all routers,
and creates database tables on startup.
"""
from fastapi import FastAPI  # type: ignore

from app.database.database import Base, engine  # type: ignore
from app.models import email_verification, social_link, user  # type: ignore
from app.routers.auth import router as auth_router  # type: ignore
from app.routers.user_profile import router as user_router  # type: ignore

# Create all tables in the database on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SoundCloud Clone API",
    version="1.0.0",
)

# Register routers
app.include_router(auth_router)
app.include_router(user_router)


@app.get("/")
def root():
    """
    Health check endpoint.

    Returns:
        dict: Simple message confirming the API is running.
    """
    return {"message": "API is running"}