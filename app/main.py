from fastapi import FastAPI
from .database.database import engine, Base
from .models import user, social_link
from .routers import user_profile

app = FastAPI()

Base.metadata.create_all(bind=engine)
app.include_router(user_profile.router)


@app.get("/")
def root():
    return {"message": "This is the fastapi instance"}
