from typing import Optional
from pydantic import BaseModel


class CreateTrackRequest(BaseModel):
    title: str
    description: Optional[str] = None
    file_url: Optional[str] = None
