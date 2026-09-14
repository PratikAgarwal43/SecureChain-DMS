"""
SQLAlchemy ORM models package for SecureChain DMS.
Imports all models to register them with Base.metadata.
"""
from app.db.base import Base
from app.models.role import Role
from app.models.user import User
from app.models.case import Case, CaseParticipant
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.edit_request import EditRequest
from app.models.approval import QuorumPolicy, ApprovalAssignment, Approval
from app.models.audit_log import AuditLog
from app.models.tamper_alert import TamperAlert
from app.models.merkle import MerkleCheckpoint

__all__ = [
    "Base",
    "Role",
    "User",
    "Case",
    "CaseParticipant",
    "Document",
    "DocumentVersion",
    "EditRequest",
    "QuorumPolicy",
    "ApprovalAssignment",
    "Approval",
    "AuditLog",
    "TamperAlert",
    "MerkleCheckpoint",
]
