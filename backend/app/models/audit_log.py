import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.guid import GUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.case import Case
    from app.models.document import Document
    from app.models.document_version import DocumentVersion


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="INFO")
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("cases.id"), nullable=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("documents.id"), nullable=True
    )
    version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("document_versions.id"), nullable=True
    )
    metadata_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="{}")
    previous_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="0"*64)
    log_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="0"*64)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Property aliases for backwards compatibility
    @property
    def user_id(self) -> Optional[uuid.UUID]:
        return self.actor_id

    @user_id.setter
    def user_id(self, value: Optional[uuid.UUID]) -> None:
        self.actor_id = value

    @property
    def action(self) -> str:
        return self.event_type

    @action.setter
    def action(self, value: str) -> None:
        self.event_type = value

    @property
    def details(self) -> Optional[str]:
        return self.metadata_json

    @details.setter
    def details(self, value: Optional[str]) -> None:
        self.metadata_json = value

    # Relationships
    user: Mapped[Optional["User"]] = relationship(
        "User", back_populates="audit_logs", foreign_keys=[actor_id]
    )
