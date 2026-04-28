from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field  # type: ignore


class CreateReportRequest(BaseModel):
    entity_type: Literal["track", "comment", "user"]
    entity_id: UUID
    reason: str = Field(..., min_length=5, max_length=500)


class ReviewReportRequest(BaseModel):
    status: Literal["open", "under_review", "resolved", "dismissed"]
    resolution_note: Optional[str] = Field(None, max_length=500)


class UpdateUserSuspensionRequest(BaseModel):
    is_suspended: bool
    reason: Optional[str] = Field(None, max_length=500)


class UpdateUserRoleRequest(BaseModel):
    role: Literal["user", "admin"]
