import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.guid import GUID


class TamperAlert(Base):
    __tablename__ = "tamper_alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    case_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("cases.id"), nullable=True
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("documents.id"), nullable=True
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="CRITICAL")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    expected_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    actual_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    detected_by: Mapped[str] = mapped_column(String(50), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
