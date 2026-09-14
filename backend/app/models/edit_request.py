import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.guid import GUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.document import Document
    from app.models.document_version import DocumentVersion


class EditRequest(Base):
    __tablename__ = "edit_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("documents.id"), nullable=False
    )
    requester_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    source_version_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("document_versions.id"), nullable=False
    )
    proposed_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("document_versions.id"), nullable=True
    )
    quorum_policy_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("quorum_policies.id"), nullable=True
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    amendment_reason_code: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING_QUORUM"
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Property alias for compatibility
    @property
    def requested_by(self) -> uuid.UUID:
        return self.requester_id

    @requested_by.setter
    def requested_by(self, value: uuid.UUID) -> None:
        self.requester_id = value

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="edit_requests")
    requester: Mapped["User"] = relationship(
        "User", back_populates="edit_requests", foreign_keys=[requester_id]
    )
