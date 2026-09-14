import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.guid import GUID

if TYPE_CHECKING:
    from app.models.role import Role
    from app.models.case import Case
    from app.models.document import Document
    from app.models.document_version import DocumentVersion
    from app.models.edit_request import EditRequest
    from app.models.approval import Approval
    from app.models.audit_log import AuditLog


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    full_name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, index=True, nullable=True
    )
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("roles.id"), nullable=True
    )
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    jurisdiction: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    dsc_certificate: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dsc_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, default=""
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    failed_logins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Legacy/compatibility string field for role when role_id is not populated
    _role_str: Mapped[Optional[str]] = mapped_column(
        "role", String(50), nullable=True, default="OFFICER"
    )

    # Alias properties for backwards compatibility with existing endpoints and tests
    @property
    def name(self) -> str:
        return self.full_name

    @name.setter
    def name(self, value: str) -> None:
        self.full_name = value

    @property
    def hashed_password(self) -> str:
        return self.password_hash

    @hashed_password.setter
    def hashed_password(self, value: str) -> None:
        self.password_hash = value

    @property
    def role(self) -> str:
        if self.role_rel and self.role_rel.name:
            return self.role_rel.name
        return self._role_str or "OFFICER"

    @role.setter
    def role(self, value: str) -> None:
        self._role_str = value

    # Relationships
    role_rel: Mapped[Optional["Role"]] = relationship("Role", back_populates="users")
    created_cases: Mapped[List["Case"]] = relationship(
        "Case", back_populates="creator", foreign_keys="Case.created_by"
    )
    uploaded_documents: Mapped[List["Document"]] = relationship(
        "Document", back_populates="uploader", foreign_keys="Document.created_by"
    )
    created_versions: Mapped[List["DocumentVersion"]] = relationship(
        "DocumentVersion", back_populates="creator", foreign_keys="DocumentVersion.created_by"
    )
    edit_requests: Mapped[List["EditRequest"]] = relationship(
        "EditRequest", back_populates="requester", foreign_keys="EditRequest.requester_id"
    )
    audit_logs: Mapped[List["AuditLog"]] = relationship(
        "AuditLog", back_populates="user", foreign_keys="AuditLog.actor_id"
    )
