from fastapi import APIRouter, Depends, Query  # type: ignore
from sqlalchemy.orm import Session  # type: ignore

from app.database.database import get_db
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("/")
def global_search(
    keyword: str = Query(...),
    db: Session = Depends(get_db),
):
    return SearchService.global_search(db, keyword)