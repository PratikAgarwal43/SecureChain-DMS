from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ApprovalBase(BaseModel):
    decision: str
    comments: Optional[str] = None


class ApprovalCreate(ApprovalBase):
    edit_request_id: int
    reviewer_id: int


class ApprovalResponse(ApprovalBase):
    id: int
    edit_request_id: int
    reviewer_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
