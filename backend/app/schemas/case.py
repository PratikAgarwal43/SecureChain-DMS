import uuid
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict


class CaseBase(BaseModel):
    case_number: str
    title: str
    description: Optional[str] = None
    case_type: Optional[str] = None
    department: Optional[str] = None
    jurisdiction: Optional[str] = None
    status: str = "ACTIVE"


class CaseCreate(CaseBase):
    created_by: Union[uuid.UUID, str, int]


class CaseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None


class CaseResponse(CaseBase):
    id: Union[uuid.UUID, str, int]
    created_by: Union[uuid.UUID, str, int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
