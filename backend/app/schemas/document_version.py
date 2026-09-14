import uuid
from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, ConfigDict


class DocumentVersionBase(BaseModel):
    version_number: int = 1
    file_name: str
    storage_path: str
    sha256_hash: str
    previous_hash: Optional[str] = None
    is_locked: bool = False


class DocumentVersionCreate(DocumentVersionBase):
    document_id: Union[uuid.UUID, str, int]
    created_by: Union[uuid.UUID, str, int]


class DocumentVersionResponse(DocumentVersionBase):
    id: Union[uuid.UUID, str, int]
    document_id: Union[uuid.UUID, str, int]
    created_by: Union[uuid.UUID, str, int]
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentVersionHistoryResponse(BaseModel):
    id: Union[uuid.UUID, str, int]
    document_id: Union[uuid.UUID, str, int]
    version_number: int
    version: str
    original_filename: Optional[str] = None
    doc_hash: str
    chain_hash: str
    prev_chain_hash: str
    quorum_token: Optional[str] = None
    status: str = "LOCKED"
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    created_by: Union[uuid.UUID, str, int]
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
