import uuid
from typing import Optional, Union
from pydantic import BaseModel, Field


class IntegrityVerificationResponse(BaseModel):
    document_id: Union[uuid.UUID, str, int] = Field(..., description="ID of the verified document")
    version: str = Field(..., description="Version number string (e.g. 1.0)")
    stored_hash: Optional[str] = Field(None, description="SHA-256 digest stored in database")
    calculated_hash: Optional[str] = Field(None, description="SHA-256 digest calculated from actual MinIO file")
    integrity_verified: bool = Field(..., description="True if calculated hash matches stored hash")
    status: str = Field(..., description="Verification status: INTEGRITY_VERIFIED, TAMPER_DETECTED, or HASH_MISSING")
    detail: Optional[str] = Field(None, description="Detailed explanation message")
