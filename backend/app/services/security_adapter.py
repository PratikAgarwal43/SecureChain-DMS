"""
SecureChain DMS — Backend Security Adapter
===========================================
Bridges the FastAPI backend with the authoritative `securechain_security` package.
Provides evidence upload processing (Two-Vault packaging), retrieval/decryption,
chain of custody verification, and constant-time SHA-256 content verification.
"""

import dataclasses
import hmac
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Ensure services/security-and-database is in sys.path
security_pkg_dir = Path(__file__).resolve().parents[3] / "services" / "security-and-database"
if security_pkg_dir.exists() and str(security_pkg_dir) not in sys.path:
    sys.path.insert(0, str(security_pkg_dir))

from securechain_security.chain_engine import (
    ChainEngine,
    ChainError,
    ChainImmutabilityError,
    ChainNotFoundError,
    QuorumRequiredError,
)
from securechain_security.chain_verifier import (
    ChainVerifier,
    DocumentVerificationResult,
    VerificationError,
)
from securechain_security.encryption_service import (
    DecryptionError,
    EncryptionError,
    EncryptionService,
)
from securechain_security.hash_service import HashService, HashingError
from securechain_security.key_manager import (
    KeyManagementError,
    KeyManager,
    LocalKMSProvider,
)
from securechain_security.models import (
    ChainRecord,
    ChainStatus,
    VaultPackage,
    VerificationResult,
)
from securechain_security.vault_router import VaultRouter, VaultRoutingError

from app.core.config import settings


class SecurityAdapter:
    """
    Security Adapter service bridging FastAPI application components with the
    underlying `securechain_security` cryptographic engine.
    """

    def __init__(
        self,
        master_kek: Optional[str] = None,
        kek_version: Optional[str] = None,
        vault_router: Optional[VaultRouter] = None,
        chain_verifier: Optional[ChainVerifier] = None,
        hash_service: Optional[HashService] = None,
    ) -> None:
        """
        Initialize the SecurityAdapter with KMS configuration from settings or injected services.
        """
        kek_ver = kek_version or getattr(settings, "KEK_VERSION", "v1")
        raw_kek_setting = (
            master_kek if master_kek is not None else getattr(settings, "MASTER_KEK", None)
        )

        if hash_service is not None:
            self._hash_service = hash_service
        else:
            self._hash_service = HashService()

        if vault_router is not None:
            self._vault_router = vault_router
            self._encryption_service = vault_router.encryption_service
            self._chain_engine = vault_router.chain_engine
        else:
            if raw_kek_setting:
                if isinstance(raw_kek_setting, str):
                    try:
                        kek_bytes = bytes.fromhex(raw_kek_setting)
                    except ValueError:
                        kek_bytes = raw_kek_setting.encode("utf-8")
                else:
                    kek_bytes = bytes(raw_kek_setting)
                kms = LocalKMSProvider(initial_kek=kek_bytes, initial_version=kek_ver)
            else:
                kms = LocalKMSProvider(initial_version=kek_ver)

            key_mgr = KeyManager(kms_provider=kms)
            self._encryption_service = EncryptionService(
                key_manager=key_mgr,
                hash_service=self._hash_service,
            )
            self._chain_engine = ChainEngine(hash_service=self._hash_service)
            self._vault_router = VaultRouter(
                encryption_service=self._encryption_service,
                chain_engine=self._chain_engine,
            )

        if chain_verifier is not None:
            self._chain_verifier = chain_verifier
        else:
            self._chain_verifier = ChainVerifier(
                chain_engine=self._chain_engine,
                hash_service=self._hash_service,
            )

    @property
    def vault_router(self) -> VaultRouter:
        """Return the underlying VaultRouter instance."""
        return self._vault_router

    @property
    def chain_verifier(self) -> ChainVerifier:
        """Return the underlying ChainVerifier instance."""
        return self._chain_verifier

    @property
    def hash_service(self) -> HashService:
        """Return the underlying HashService instance."""
        return self._hash_service

    @property
    def encryption_service(self) -> EncryptionService:
        """Return the underlying EncryptionService instance."""
        return self._encryption_service

    @property
    def chain_engine(self) -> ChainEngine:
        """Return the underlying ChainEngine instance."""
        return self._chain_engine

    def process_evidence_upload(
        self,
        plaintext: bytes,
        document_id: str,
        case_id: str,
        officer_id: str,
        version: str = "1.0",
        quorum_token: Optional[str] = None,
        amendment_of: Optional[str] = None,
    ) -> VaultPackage:
        """
        Process evidence upload into Two-Vault package (Vault 1 metadata, Vault 2 blob).
        """
        return self._vault_router.process_upload(
            plaintext=plaintext,
            document_id=document_id,
            case_id=case_id,
            officer_id=officer_id,
            version=version,
            quorum_token=quorum_token,
            amendment_of=amendment_of,
        )

    def process_evidence_retrieval(
        self,
        vault1_metadata: dict,
        vault2_blob: bytes,
        expected_doc_hash: str = "",
    ) -> bytes:
        """
        Retrieve and decrypt evidence by recombining Vault 1 metadata with Vault 2 blob.
        """
        return self._vault_router.process_retrieval(
            vault1_metadata=vault1_metadata,
            vault2_blob=vault2_blob,
            expected_doc_hash=expected_doc_hash,
        )

    def verify_document_chain(
        self,
        case_id_or_chain: Union[str, List[Union[ChainRecord, dict]]],
    ) -> VerificationResult:
        """
        Verify the complete cryptographic chain of custody for a case ID or record list.
        """
        if isinstance(case_id_or_chain, str):
            return self._chain_verifier.verify_case(case_id_or_chain)
        elif isinstance(case_id_or_chain, list):
            if not case_id_or_chain:
                return VerificationResult(
                    case_id="empty",
                    status=ChainStatus.EMPTY,
                    documents_checked=0,
                    documents_valid=0,
                    error_message="Empty chain records list provided",
                )

            first_rec = case_id_or_chain[0]
            if isinstance(first_rec, dict):
                case_id = first_rec.get("case_id", "unknown")
            else:
                case_id = getattr(first_rec, "case_id", "unknown")

            chain_records_to_check = [
                rec for rec in case_id_or_chain
                if (rec.get("chain_hash") if isinstance(rec, dict) else getattr(rec, "chain_hash", None))
            ]

            if not chain_records_to_check:
                return VerificationResult(
                    case_id=case_id,
                    status=ChainStatus.INTACT,
                    documents_checked=0,
                    documents_valid=0,
                    error_message=None,
                )

            checked = 0
            valid = 0
            first_broken = None
            error_msg = None

            expected_prev = None
            for idx, rec in enumerate(chain_records_to_check):
                rec_dict = dataclasses.asdict(rec) if hasattr(rec, "__dataclass_fields__") else rec
                d_id = rec_dict.get("document_id", "")
                c_hash = rec_dict.get("chain_hash", "")
                p_hash = rec_dict.get("prev_chain_hash", "")

                if idx == 0:
                    expected_prev = p_hash or ("0" * 64)

                checked += 1

                # Verify chain of custody link continuity
                if p_hash != expected_prev or not c_hash or len(c_hash) != 64:
                    if not first_broken:
                        first_broken = d_id
                        error_msg = f"Link continuity broken at sequence {idx} (document {d_id}): expected prev_chain_hash={expected_prev}, got {p_hash}"
                    break

                valid += 1
                expected_prev = c_hash

            status = ChainStatus.INTACT if (valid == checked and not first_broken) else ChainStatus.TAMPERED
            return VerificationResult(
                case_id=case_id,
                status=status,
                documents_checked=checked,
                documents_valid=valid,
                first_broken_link=first_broken,
                error_message=error_msg,
            )
        else:
            raise VerificationError(
                f"Unsupported argument type for verify_document_chain: {type(case_id_or_chain).__name__}"
            )

    def verify_content_hash(
        self,
        plaintext: bytes,
        expected_doc_hash: str,
    ) -> bool:
        """
        Verify raw physical content bytes against expected SHA-256 hash in constant time.
        """
        if plaintext is None or not isinstance(plaintext, (bytes, bytearray, memoryview)):
            raise HashingError("Plaintext content must be bytes-like")
        if not expected_doc_hash or not isinstance(expected_doc_hash, str):
            raise HashingError("expected_doc_hash must be a non-empty string")

        computed_hash = self._hash_service.hash_bytes(bytes(plaintext))
        return hmac.compare_digest(
            computed_hash.lower().strip(),
            expected_doc_hash.lower().strip(),
        )


security_adapter = SecurityAdapter()

__all__ = ["SecurityAdapter", "security_adapter"]
