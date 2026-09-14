import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.guid import GUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.document import Document


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    
    # Vault 2 Storage pointer
    storage_key: Mapped[str] = mapped_column(Text, unique=True, nullable=False, default="")
    
    # SHA-256 Fingerprint
    doc_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="0"*64)
    
    # Hash Chain Records
    chain_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="0"*64)
    prev_chain_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="0"*64)
    quorum_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Vault 1 Key Material (AES-256-GCM Envelope Encryption)
    wrapped_dek: Mapped[str] = mapped_column(Text, nullable=False, default="")
    iv: Mapped[str] = mapped_column(String(24), nullable=False, default="")
    key_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), nullable=False, default=uuid.uuid4
    )
    kek_version: Mapped[str] = mapped_column(String(10), nullable=False, default="v1")
    aad: Mapped[str] = mapped_column(Text, nullable=False, default="")
    algorithm: Mapped[str] = mapped_column(String(20), nullable=False, default="AES-256-GCM")

    # File Metadata
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="DRAFT")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Alias properties for backwards compatibility
    @property
    def file_name(self) -> str:
        return self.original_filename or "document.bin"

    @file_name.setter
    def file_name(self, value: str) -> None:
        self.original_filename = value

    @property
    def storage_path(self) -> str:
        return self.storage_key

    @storage_path.setter
    def storage_path(self, value: str) -> None:
        self.storage_key = value

    @property
    def sha256_hash(self) -> str:
        return self.doc_hash

    @sha256_hash.setter
    def sha256_hash(self, value: str) -> None:
        self.doc_hash = value

    @property
    def previous_hash(self) -> str:
        return self.prev_chain_hash

    @previous_hash.setter
    def previous_hash(self, value: str) -> None:
        self.prev_chain_hash = value

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="versions", foreign_keys=[document_id]
    )
    creator: Mapped["User"] = relationship(
        "User", back_populates="created_versions", foreign_keys=[created_by]
    )
