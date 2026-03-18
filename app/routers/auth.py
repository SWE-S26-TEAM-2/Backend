from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.schemas.auth_schema import RegisterRequest
from app.services.auth_service import AuthService
from app.database.database import get_db

router = APIRouter()


@router.post("/auth/register")
def register_user(request: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService.register_user(db, request)