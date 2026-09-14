import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
from app.db.guid import GUID


class MerkleCheckpoint(Base):
    __tablename__ = "merkle_checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(), primary_key=True, default=uuid.uuid4
    )
    merkle_root: Mapped[str] = mapped_column(String(64), nullable=False)
    cases_included: Mapped[int] = mapped_column(Integer, nullable=False)
    case_chain_heads: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        GUID(), ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
