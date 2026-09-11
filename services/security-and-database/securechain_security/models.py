"""
SecureChain DMS — Data Models
=============================
Pydantic models and dataclasses for the security layer. These define the
canonical schemas for hash chain records, encryption results, verification
reports, and tamper alerts used across all modules.
"""

from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GENESIS_HASH = "0" * 64  # 64-char hex string of all zeros — the chain root
HASH_ALGORITHM = "SHA-256"
ENCRYPTION_ALGORITHM = "AES-256-GCM"
IV_LENGTH_BYTES = 12       # 96-bit nonce for GCM
AUTH_TAG_LENGTH_BYTES = 16  # 128-bit GCM authentication tag
DEK_LENGTH_BYTES = 32      # 256-bit AES key
CHUNK_SIZE_BYTES = 8192    # Streaming hash/encryption chunk size


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DocumentVersion(str, enum.Enum):
    """Document version lifecycle states."""
    ORIGINAL = "1.0"      # Permanently locked — never overwritable


class ChainStatus(str, enum.Enum):
    """Result of a chain integrity verification."""
    INTACT = "INTACT"
    TAMPERED = "TAMPERED"
    PARTIAL = "PARTIAL"      # Chain is intact up to a point, then broken
    EMPTY = "EMPTY"          # No documents in the chain yet


class TamperSeverity(str, enum.Enum):
    """Severity levels for tamper detection alerts."""
    CRITICAL = "CRITICAL"    # Document content was modified
    HIGH = "HIGH"            # Chain link broken (hash mismatch)
    MEDIUM = "MEDIUM"        # Metadata inconsistency
    LOW = "LOW"              # Non-critical anomaly (e.g., clock skew)


class VaultTarget(str, enum.Enum):
    """Which vault a piece of data routes to."""
    DATABASE = "VAULT_1_DATABASE"           # Metadata, hashes, wrapped DEKs
    OBJECT_STORAGE = "VAULT_2_OBJECT_STORE" # Encrypted blobs


# ---------------------------------------------------------------------------
# Hash & Chain Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class HashResult:
    """Output of hashing a single document."""
    document_id: str
    doc_hash: str           # SHA-256 hex digest of raw document bytes
    algorithm: str = HASH_ALGORITHM
    file_size_bytes: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class ChainRecord:
    """
    A single link in a case's hash chain.

    chain_hash = SHA-256(doc_hash + prev_chain_hash + timestamp + officer_id [+ quorum_token])

    This record is stored in Vault 1 (Database).
    """
    document_id: str
    case_id: str
    version: str              # "1.0" for original, "1.1", "1.2" for amendments
    doc_hash: str             # SHA-256 of raw document bytes
    chain_hash: str           # SHA-256 of the chain link (includes prev hash)
    prev_chain_hash: str      # Previous link's chain_hash (GENESIS_HASH for first)
    timestamp: str            # ISO 8601 millisecond-precision, server-side
    officer_id: str           # DSC-verified uploader identity
    sequence_number: int      # Position in the case chain (0-indexed)
    quorum_token: Optional[str] = None  # Present only for amendments (V1.1+)
    amendment_of: Optional[str] = None  # doc_hash of the original, if this is an amendment


@dataclass(frozen=True)
class ChainState:
    """Current state of a case's hash chain — used by the chain engine."""
    case_id: str
    length: int                  # Number of links
    head_chain_hash: str         # Most recent chain_hash (tip of the chain)
    genesis_hash: str = GENESIS_HASH
    created_at: str = ""
    last_updated_at: str = ""


# ---------------------------------------------------------------------------
# Encryption Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EncryptionResult:
    """
    Output of encrypting a single document with AES-256-GCM.

    The ciphertext and IV go to Vault 2 (Object Storage).
    The wrapped DEK and AAD go to Vault 1 (Database).
    """
    document_id: str
    case_id: str
    version: str

    # → Vault 2 (Object Storage)
    ciphertext: bytes         # Encrypted document bytes (includes GCM auth tag)
    iv: bytes                 # 12-byte initialization vector / nonce

    # → Vault 1 (Database)
    wrapped_dek: bytes        # DEK encrypted by KEK (envelope encryption)
    aad: bytes                # Additional Authenticated Data: "doc_id:case_id:version"

    algorithm: str = ENCRYPTION_ALGORITHM
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    wrapped_key: Optional[WrappedKey] = None
    doc_hash: Optional[str] = None


@dataclass(frozen=True)
class DecryptionResult:
    """Output of decrypting a document — includes integrity verification."""
    document_id: str
    plaintext: bytes          # Decrypted document bytes
    integrity_verified: bool  # True if SHA-256(plaintext) == stored doc_hash
    doc_hash: str             # Re-computed hash of the decrypted content
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass(frozen=True)
class WrappedKey:
    """A DEK wrapped (encrypted) by the KEK — stored in Vault 1."""
    key_id: str               # Unique identifier for this wrapped key
    wrapped_dek: bytes        # The encrypted DEK bytes
    kek_version: str          # Which KEK version was used to wrap this DEK
    document_id: str          # Which document this DEK belongs to
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Verification & Alert Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VerificationResult:
    """Output of a chain integrity verification."""
    case_id: str
    status: ChainStatus
    documents_checked: int
    documents_valid: int
    first_broken_link: Optional[str] = None    # document_id where chain broke
    error_message: Optional[str] = None
    verification_time_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class TamperAlert:
    """
    Generated when any integrity check fails. Written to WORM audit log
    and dispatched to the court registry notification system.
    """
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    case_id: str = ""
    document_id: str = ""
    severity: TamperSeverity = TamperSeverity.CRITICAL
    description: str = ""
    expected_hash: str = ""
    actual_hash: str = ""
    detected_by: str = ""           # "on_retrieval" | "chain_walk" | "merkle_audit"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# Vault Routing Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class VaultPackage:
    """
    The split payload that the vault router produces. Ensures encrypted blobs
    and their decryption keys are NEVER stored in the same location.
    """
    document_id: str
    case_id: str

    # Vault 1 payload (Database)
    vault1_metadata: dict       # chain_record, wrapped_dek, aad, doc_hash
    vault1_target: VaultTarget = VaultTarget.DATABASE

    # Vault 2 payload (Object Storage)
    vault2_blob: bytes = b""    # ciphertext + IV concatenated
    vault2_blob_ref: str = ""   # Storage key / path for the blob
    vault2_target: VaultTarget = VaultTarget.OBJECT_STORAGE


# ---------------------------------------------------------------------------
# Merkle Tree Models
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MerkleCheckpoint:
    """
    Periodic checkpoint that anchors all case chains into a single root hash.
    Written to the global anchor chain.
    """
    checkpoint_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    merkle_root: str = ""             # SHA-256 root of the Merkle tree
    case_chain_heads: dict = field(default_factory=dict)  # {case_id: head_chain_hash}
    cases_included: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
