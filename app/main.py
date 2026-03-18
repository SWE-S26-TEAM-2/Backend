from fastapi import FastAPI
from app.routers.auth import router as auth_router
from app.database.database import engine, Base

# Create tables in database
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SoundCloud Clone API",
    version="1.0.0"
)

# Include routers
app.include_router(auth_router)


@app.get("/")
def root():
    return {"message": "API is running"}