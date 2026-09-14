import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base
from app.db.guid import GUID

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.edit_request import EditRequest


class QuorumPolicy(Base):
    __tablename__ = "quorum_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    sensitivity_level: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    required_approvals: Mapped[int] = mapped_column(Integer, nullable=False)
    pool_size: Mapped[int] = mapped_column(Integer, nullable=False)
    eligible_roles: Mapped[Optional[str]] = mapped_column(Text, nullable=True, default="[]")


class ApprovalAssignment(Base):
    __tablename__ = "approval_assignments"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    edit_request_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("edit_requests.id"), nullable=False
    )
    approver_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=False
    )
    anonymous_token: Mapped[uuid.UUID] = mapped_column(
        GUID(), unique=True, nullable=False, default=uuid.uuid4
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="PENDING"
    )
    identity_revealed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    assignment_id: Mapped[uuid.UUID] = mapped_column(
        GUID(), ForeignKey("approval_assignments.id"), unique=True, nullable=False
    )
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dsc_signature: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
