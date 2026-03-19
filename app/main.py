from fastapi import FastAPI
from app.database.database import engine, Base

# Import all models so SQLAlchemy knows about them
from app.models import user, social_link 

# Import routers
from app.routers.auth import router as auth_router
from app.routers import user_profile

# Create tables in database (Alembic handles this now, it's safe to keep)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SoundCloud Clone API",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(user_profile.router)

@app.get("/")
def root():
    return {"message": "API is running"}