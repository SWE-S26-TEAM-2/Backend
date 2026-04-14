from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field  # type: ignore


class AddCommentRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=500)
    timestamp_in_track: Optional[int] = None
    parent_comment_id: Optional[UUID] = None
