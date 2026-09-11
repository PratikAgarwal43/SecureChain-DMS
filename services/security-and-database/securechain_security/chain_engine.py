"""
SecureChain DMS — Hash-Chain Engine (Module 2)
==============================================
Blockchain-lite cryptographic immutability engine for the Zero-Trust Digital
Evidence Vault (SIH26190).

Legal & Forensic Compliance:
----------------------------
Under Section 65B of the Indian Evidence Act, 1872 and Section 63 of the
Bharatiya Sakshya Adhiniyam (BSA), 2023, electronic evidence is admissible only
if its integrity from the moment of seizure through courtroom presentation
can be conclusively demonstrated.

This module provides a per-case, append-only cryptographic hash chain (WORM —
Write Once, Read Many). Each document link cryptographically seals:
  1. The raw document payload hash (`doc_hash`)
  2. The previous link's chain hash (`prev_chain_hash`)
  3. A trusted server UTC timestamp (`timestamp`)
  4. The authenticated officer's digital identity (`officer_id`)
  5. An optional multi-signature quorum token for amendments (`quorum_token`)

Security Architecture:
----------------------
1. Genesis Anchoring (Root of Trust):
   The first link of every case chain (sequence_number = 0) is bound to
   `GENESIS_HASH` (64 hex zeros). A genesis link is created exactly once per
   case and can never be re-initialized or overwritten.

2. Strict Append-Only Immutability:
   Existing chain records cannot be edited, deleted, or reordered. V1.0 original
   evidence records are permanently locked. There is no deletion or update API.

3. Quorum-Gated Document Amendments (V1.1+):
   Under judicial evidence rules, original evidence cannot be modified. If an
   amendment (e.g. supplementary charge sheet, forensic addendum, or errata) is
   required, it must be submitted as a new chain link (version != '1.0') referencing
   the original document's hash (`amendment_of`) and carrying a cryptographic
   multi-signature quorum authorization token (`quorum_token`).

4. Full Chain Walk & Tamper Detection:
   Integrity verification audits the chain from genesis to head, recomputing
   each link's SHA-256 chain hash and checking link-to-link continuity using
   constant-time comparison (`hmac.compare_digest`) to prevent timing side-channels.

5. Thread Safety & Atomicity:
   All chain mutations and state reads are protected by `threading.RLock`,
   guaranteeing race-free concurrent appends and linear sequence number assignment.

6. Zero Sensitive Data Leakage in Logs:
   Log messages record operational events, case IDs, sequence numbers, and
   document IDs. Plaintext content and cryptographic keys are strictly excluded.
"""

from __future__ import annotations

import hmac
import logging
import threading
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

from securechain_security.hash_service import HashService, HashingError
from securechain_security.models import (
    GENESIS_HASH,
    ChainRecord,
    ChainState,
    ChainStatus,
    DocumentVersion,
    VerificationResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class ChainError(Exception):
    """
    Base exception for all hash-chain engine operations.

    Attributes:
        message: Human-readable explanation of the error.
        cause: The underlying exception if this wraps another error, else None.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


class ChainNotFoundError(ChainError):
    """Raised when a requested case, document, or chain link is not found."""


class ChainImmutabilityError(ChainError):
    """Raised when an operation attempts to overwrite, alter, or delete an immutable chain record."""


class QuorumRequiredError(ChainError):
    """Raised when an amendment (version != 1.0) is attempted without required quorum token."""


# ---------------------------------------------------------------------------
# Hash-Chain Engine
# ---------------------------------------------------------------------------

class ChainEngine:
    """
    Cryptographic Hash-Chain Engine for SecureChain DMS.

    Manages per-case append-only hash chains providing blockchain-lite immutability,
    tamper detection, and quorum-controlled document amendments.
    """

    def __init__(self, hash_service: HashService) -> None:
        """
        Initialize the ChainEngine with dependency-injected HashService.

        Args:
            hash_service: Stateless cryptographic hashing service.

        Raises:
            ValueError: If hash_service is None.
        """
        if hash_service is None:
            raise ValueError("hash_service cannot be None")

        self._hash_service: HashService = hash_service
        self._chains: Dict[str, List[ChainRecord]] = {}
        self._lock: threading.RLock = threading.RLock()

        logger.info("ChainEngine initialized successfully")

    @property
    def hash_service(self) -> HashService:
        """Return the underlying HashService instance."""
        return self._hash_service

    def _enforce_immutability(self, case_id: str, document_id: str) -> None:
        """
        Internal check that prevents modification or replacement of existing records.

        Security Rationale:
            Under Section 65B of the Indian Evidence Act and BSA 2023 Section 63,
            digital evidence records are WORM (Write Once, Read Many). Once committed,
            original records are permanently locked. Any attempt to overwrite or
            re-append an existing document as an original violates immutability guarantees.

        Args:
            case_id: Case identifier.
            document_id: Document identifier to verify against existing records.

        Raises:
            ChainImmutabilityError: If document_id already exists in the case chain.
        """
        if case_id in self._chains:
            for record in self._chains[case_id]:
                if record.document_id == document_id:
                    raise ChainImmutabilityError(
                        f"Document '{document_id}' already exists in case '{case_id}' "
                        f"at sequence {record.sequence_number} (version '{record.version}'). "
                        f"Existing chain records are permanently immutable and cannot be modified."
                    )

    def create_genesis(
        self,
        case_id: str,
        document_id: str,
        doc_hash: str,
        officer_id: str,
        timestamp: str = "",
    ) -> ChainRecord:
        """
        Create the genesis (first) link in a case's hash chain.

        Security Rationale:
            The genesis link anchors the case's chain of custody to `GENESIS_HASH`
            (64 hex zeros). It establishes the chronological baseline and identity
            of the initiating investigating officer. Once created, a genesis link
            can NEVER be recreated or overwritten.

        Args:
            case_id: Unique case identifier (e.g. FIR / Case Number).
            document_id: Unique document identifier (e.g. FIR original file ID).
            doc_hash: SHA-256 hex digest of raw document content bytes.
            officer_id: Cryptographically verified identity (e.g. DSC Subject ID) of officer.
            timestamp: Optional ISO 8601 millisecond-precision UTC timestamp. If omitted,
                       the current server UTC time is used.

        Returns:
            The newly created genesis ChainRecord (sequence_number = 0).

        Raises:
            ChainError: If any parameter is invalid or empty.
            ChainImmutabilityError: If a genesis record already exists for this case.
        """
        if not case_id or not isinstance(case_id, str) or not case_id.strip():
            raise ChainError("case_id must be a non-empty string")
        if not document_id or not isinstance(document_id, str) or not document_id.strip():
            raise ChainError("document_id must be a non-empty string")
        if not doc_hash or not isinstance(doc_hash, str) or not doc_hash.strip():
            raise ChainError("doc_hash must be a non-empty string")
        if not officer_id or not isinstance(officer_id, str) or not officer_id.strip():
            raise ChainError("officer_id must be a non-empty string")

        effective_timestamp = (
            timestamp.strip()
            if timestamp and isinstance(timestamp, str) and timestamp.strip()
            else datetime.now(timezone.utc).isoformat()
        )

        with self._lock:
            if case_id in self._chains and len(self._chains[case_id]) > 0:
                raise ChainImmutabilityError(
                    f"Case '{case_id}' already has an established chain. "
                    f"Genesis record cannot be overwritten or recreated."
                )

            try:
                chain_hash = self._hash_service.hash_chain_link(
                    doc_hash=doc_hash,
                    prev_chain_hash=GENESIS_HASH,
                    timestamp=effective_timestamp,
                    officer_id=officer_id,
                    quorum_token=None,
                )
            except HashingError as exc:
                raise ChainError(f"Failed to compute genesis chain hash: {exc}", cause=exc) from exc

            genesis_record = ChainRecord(
                document_id=document_id,
                case_id=case_id,
                version=DocumentVersion.ORIGINAL.value,
                doc_hash=doc_hash,
                chain_hash=chain_hash,
                prev_chain_hash=GENESIS_HASH,
                timestamp=effective_timestamp,
                officer_id=officer_id,
                sequence_number=0,
                quorum_token=None,
                amendment_of=None,
            )

            self._chains[case_id] = [genesis_record]

        logger.info(
            "Genesis record created for case '%s' (doc_id: '%s', seq: 0)",
            case_id,
            document_id,
        )
        return genesis_record

    def append_document(
        self,
        case_id: str,
        document_id: str,
        doc_hash: str,
        officer_id: str,
        version: str = "1.0",
        timestamp: str = "",
        quorum_token: Optional[str] = None,
        amendment_of: Optional[str] = None,
    ) -> ChainRecord:
        """
        Append a document to the case's hash chain.

        Security Rationale:
            Extends the cryptographic chain by binding the new document to the
            previous chain head (`prev_chain_hash = head.chain_hash`).
            Original evidence (V1.0) is permanently locked and cannot overwrite
            an existing record. Amendments (version != "1.0") require multi-party
            quorum authorization and must explicitly reference the original
            document hash (`amendment_of`) that they modify or supplement.

        Args:
            case_id: Case identifier.
            document_id: Document identifier.
            doc_hash: SHA-256 hex digest of raw document bytes.
            officer_id: DSC-verified identity of uploader.
            version: Document version string (default: "1.0" for original).
            timestamp: Optional ISO 8601 millisecond-precision UTC timestamp.
            quorum_token: Cryptographic quorum approval token (mandatory if version != "1.0").
            amendment_of: doc_hash of original document being amended (mandatory if version != "1.0").

        Returns:
            The appended ChainRecord.

        Raises:
            ChainNotFoundError: If the case has not been initialized with genesis.
            ChainImmutabilityError: If attempting to overwrite an existing V1.0 document.
            QuorumRequiredError: If version != "1.0" and quorum_token is missing or empty.
            ChainError: If parameter validation fails or amendment references non-existent hash.
        """
        if not case_id or not isinstance(case_id, str) or not case_id.strip():
            raise ChainError("case_id must be a non-empty string")
        if not document_id or not isinstance(document_id, str) or not document_id.strip():
            raise ChainError("document_id must be a non-empty string")
        if not doc_hash or not isinstance(doc_hash, str) or not doc_hash.strip():
            raise ChainError("doc_hash must be a non-empty string")
        if not officer_id or not isinstance(officer_id, str) or not officer_id.strip():
            raise ChainError("officer_id must be a non-empty string")
        if not version or not isinstance(version, str) or not version.strip():
            raise ChainError("version must be a non-empty string")

        effective_timestamp = (
            timestamp.strip()
            if timestamp and isinstance(timestamp, str) and timestamp.strip()
            else datetime.now(timezone.utc).isoformat()
        )

        with self._lock:
            if case_id not in self._chains or len(self._chains[case_id]) == 0:
                raise ChainNotFoundError(
                    f"Case '{case_id}' has not been initialized. Call create_genesis first."
                )

            chain = self._chains[case_id]

            # Enforce immutability for V1.0 documents
            if version == DocumentVersion.ORIGINAL.value:
                self._enforce_immutability(case_id, document_id)
                if amendment_of is not None:
                    raise ChainError(
                        "Version 1.0 represents an original document and cannot specify 'amendment_of'"
                    )
            else:
                # Amendments (V1.1+) strictly require quorum_token and amendment_of
                if quorum_token is None or not isinstance(quorum_token, str) or not quorum_token.strip():
                    raise QuorumRequiredError(
                        f"Document amendment (version '{version}') for '{document_id}' "
                        f"requires a valid non-empty quorum_token"
                    )
                if amendment_of is None or not isinstance(amendment_of, str) or not amendment_of.strip():
                    raise ChainError(
                        f"Document amendment (version '{version}') for '{document_id}' "
                        f"requires 'amendment_of' pointing to the original document hash"
                    )

                # Verify that amendment_of refers to an actual document in this case's chain
                target_found = any(r.doc_hash == amendment_of for r in chain)
                if not target_found:
                    raise ChainError(
                        f"Original document hash '{amendment_of}' referenced by amendment "
                        f"was not found in case '{case_id}'"
                    )

            head = chain[-1]
            prev_chain_hash = head.chain_hash

            try:
                chain_hash = self._hash_service.hash_chain_link(
                    doc_hash=doc_hash,
                    prev_chain_hash=prev_chain_hash,
                    timestamp=effective_timestamp,
                    officer_id=officer_id,
                    quorum_token=quorum_token,
                )
            except HashingError as exc:
                raise ChainError(f"Failed to compute chain link hash: {exc}", cause=exc) from exc

            sequence_number = len(chain)
            record = ChainRecord(
                document_id=document_id,
                case_id=case_id,
                version=version,
                doc_hash=doc_hash,
                chain_hash=chain_hash,
                prev_chain_hash=prev_chain_hash,
                timestamp=effective_timestamp,
                officer_id=officer_id,
                sequence_number=sequence_number,
                quorum_token=quorum_token,
                amendment_of=amendment_of,
            )

            chain.append(record)

        logger.info(
            "Document appended to case '%s' (doc_id: '%s', seq: %d, version: '%s')",
            case_id,
            document_id,
            sequence_number,
            version,
        )
        return record

    def get_all_cases(self) -> List[str]:
        """
        Return a list of all initialized case identifiers.

        Returns:
            List of case_id strings currently tracked by the engine.
        """
        with self._lock:
            return list(self._chains.keys())

    def get_chain(self, case_id: str) -> List[ChainRecord]:
        """
        Return the complete cryptographic hash chain for a case.

        Security Rationale:
            Returns a shallow copy of the internal chain list to prevent external
            callers from mutating internal state while preserving thread-safety.

        Args:
            case_id: Case identifier.

        Returns:
            List of ChainRecord objects from genesis (index 0) to head (index -1).

        Raises:
            ChainNotFoundError: If case_id does not exist.
        """
        with self._lock:
            if case_id not in self._chains:
                raise ChainNotFoundError(f"Case '{case_id}' not found")
            return list(self._chains[case_id])

    def get_chain_state(self, case_id: str) -> ChainState:
        """
        Return a summary snapshot of the case's hash chain state.

        Args:
            case_id: Case identifier.

        Returns:
            ChainState dataclass with length, head chain hash, genesis hash,
            and creation/update timestamps.

        Raises:
            ChainNotFoundError: If case_id does not exist or chain is empty.
        """
        with self._lock:
            if case_id not in self._chains or len(self._chains[case_id]) == 0:
                raise ChainNotFoundError(f"Case '{case_id}' not found or chain is empty")

            chain = self._chains[case_id]
            genesis = chain[0]
            head = chain[-1]

            return ChainState(
                case_id=case_id,
                length=len(chain),
                head_chain_hash=head.chain_hash,
                genesis_hash=genesis.prev_chain_hash,
                created_at=genesis.timestamp,
                last_updated_at=head.timestamp,
            )

    def get_head(self, case_id: str) -> ChainRecord:
        """
        Return the latest link (tip) of the case's hash chain.

        Args:
            case_id: Case identifier.

        Returns:
            The most recent ChainRecord.

        Raises:
            ChainNotFoundError: If case_id does not exist or chain is empty.
        """
        with self._lock:
            if case_id not in self._chains or len(self._chains[case_id]) == 0:
                raise ChainNotFoundError(f"Case '{case_id}' not found or chain is empty")
            return self._chains[case_id][-1]

    def get_document_record(
        self,
        case_id: str,
        document_id: str,
        version: Optional[str] = None,
    ) -> ChainRecord:
        """
        Find a specific document in the case's hash chain.

        If version is specified, retrieves the record matching document_id and version.
        If version is omitted, searches backwards and returns the latest record for document_id.

        Args:
            case_id: Case identifier.
            document_id: Document identifier.
            version: Optional specific version string.

        Returns:
            The matching ChainRecord.

        Raises:
            ChainNotFoundError: If the case or document is not found.
        """
        with self._lock:
            if case_id not in self._chains:
                raise ChainNotFoundError(f"Case '{case_id}' not found")

            chain = self._chains[case_id]

            if version is not None:
                for record in reversed(chain):
                    if record.document_id == document_id and record.version == version:
                        return record
                raise ChainNotFoundError(
                    f"Document '{document_id}' with version '{version}' not found in case '{case_id}'"
                )

            for record in reversed(chain):
                if record.document_id == document_id:
                    return record

            raise ChainNotFoundError(
                f"Document '{document_id}' not found in case '{case_id}'"
            )

    def verify_chain_detailed(self, case_id: str) -> VerificationResult:
        """
        Perform a comprehensive forensic chain walk and return structured VerificationResult.

        Security Rationale:
            Walks from genesis (0) to head (N-1). At each link:
              1. Verifies sequential indexing (`sequence_number == i`).
              2. Verifies `prev_chain_hash` matches previous link's `chain_hash`
                 (or `GENESIS_HASH` for sequence 0).
              3. Recomputes `chain_hash` from constituent metadata and verifies equality
                 using constant-time comparison (`hmac.compare_digest`).
            Detects any retrospective tampering, truncation, deletion, or reordering.

        Args:
            case_id: Case identifier.

        Returns:
            VerificationResult detailing status, documents checked/valid, first broken
            link ID if any, error message, and execution time in ms.

        Raises:
            ChainNotFoundError: If case_id does not exist.
        """
        start_time = time.perf_counter()

        with self._lock:
            if case_id not in self._chains:
                raise ChainNotFoundError(f"Case '{case_id}' not found")

            chain = list(self._chains[case_id])

        if len(chain) == 0:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return VerificationResult(
                case_id=case_id,
                status=ChainStatus.EMPTY,
                documents_checked=0,
                documents_valid=0,
                error_message="Chain contains no records",
                verification_time_ms=elapsed_ms,
            )

        valid_count = 0

        for i, record in enumerate(chain):
            # 1. Verify sequence number
            if record.sequence_number != i:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                msg = f"Sequence number mismatch at index {i}: expected {i}, found {record.sequence_number}"
                logger.warning("Chain verification failed for case '%s': %s", case_id, msg)
                return VerificationResult(
                    case_id=case_id,
                    status=ChainStatus.TAMPERED,
                    documents_checked=i + 1,
                    documents_valid=valid_count,
                    first_broken_link=record.document_id,
                    error_message=msg,
                    verification_time_ms=elapsed_ms,
                )

            # 2. Verify prev_chain_hash continuity
            if i == 0:
                expected_prev = GENESIS_HASH
            else:
                expected_prev = chain[i - 1].chain_hash

            if not hmac.compare_digest(record.prev_chain_hash, expected_prev):
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                msg = f"Previous chain hash mismatch at sequence {i} (document '{record.document_id}')"
                logger.warning("Chain verification failed for case '%s': %s", case_id, msg)
                return VerificationResult(
                    case_id=case_id,
                    status=ChainStatus.TAMPERED,
                    documents_checked=i + 1,
                    documents_valid=valid_count,
                    first_broken_link=record.document_id,
                    error_message=msg,
                    verification_time_ms=elapsed_ms,
                )

            # 3. Recompute and verify link chain_hash
            try:
                recomputed_hash = self._hash_service.hash_chain_link(
                    doc_hash=record.doc_hash,
                    prev_chain_hash=record.prev_chain_hash,
                    timestamp=record.timestamp,
                    officer_id=record.officer_id,
                    quorum_token=record.quorum_token,
                )
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                msg = f"Cryptographic rehash failed at sequence {i} (document '{record.document_id}'): {exc}"
                logger.warning("Chain verification failed for case '%s': %s", case_id, msg)
                return VerificationResult(
                    case_id=case_id,
                    status=ChainStatus.TAMPERED,
                    documents_checked=i + 1,
                    documents_valid=valid_count,
                    first_broken_link=record.document_id,
                    error_message=msg,
                    verification_time_ms=elapsed_ms,
                )

            if not hmac.compare_digest(record.chain_hash, recomputed_hash):
                elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                msg = f"Chain hash digest mismatch at sequence {i} (document '{record.document_id}')"
                logger.warning("Chain verification failed for case '%s': %s", case_id, msg)
                return VerificationResult(
                    case_id=case_id,
                    status=ChainStatus.TAMPERED,
                    documents_checked=i + 1,
                    documents_valid=valid_count,
                    first_broken_link=record.document_id,
                    error_message=msg,
                    verification_time_ms=elapsed_ms,
                )

            valid_count += 1

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "Chain integrity verified for case '%s': INTACT (%d links, %.2f ms)",
            case_id,
            valid_count,
            elapsed_ms,
        )
        return VerificationResult(
            case_id=case_id,
            status=ChainStatus.INTACT,
            documents_checked=len(chain),
            documents_valid=valid_count,
            verification_time_ms=elapsed_ms,
        )

    def verify_chain_integrity(self, case_id: str) -> bool:
        """
        Verify the integrity of a case's hash chain.

        Walks the chain from genesis to head, recomputing chain_hash at each link
        and verifying link continuity.

        Args:
            case_id: Case identifier.

        Returns:
            True if all links are intact and cryptographically valid; False otherwise.

        Raises:
            ChainNotFoundError: If case_id does not exist.
        """
        result = self.verify_chain_detailed(case_id)
        return result.status == ChainStatus.INTACT

    def get_version_history(
        self,
        case_id: str,
        original_doc_hash: str,
        include_original: bool = True,
    ) -> List[ChainRecord]:
        """
        Return all version history records (original and amendments) for a specific document.

        Security Rationale:
            Under BSA Section 63 and court admissibility rules, the full forensic
            genealogy of an evidence item must be traceable from its initial seizure
            (V1.0) through all authorized supplementary reports or amendments (V1.1+).

        Args:
            case_id: Case identifier.
            original_doc_hash: SHA-256 hash of the target document (or any of its amendments).
            include_original: If True, includes the original V1.0 document record;
                             if False, returns only the subsequent amendment records.

        Returns:
            List of ChainRecord objects in chronological / sequence order.

        Raises:
            ChainNotFoundError: If case_id does not exist.
        """
        if not original_doc_hash or not isinstance(original_doc_hash, str):
            return []

        with self._lock:
            if case_id not in self._chains:
                raise ChainNotFoundError(f"Case '{case_id}' not found")

            chain = self._chains[case_id]

            # Determine the root original hash. If the caller supplied an amendment's hash,
            # traverse to find the root original doc_hash.
            root_hash = original_doc_hash
            for record in chain:
                if record.doc_hash == original_doc_hash and record.amendment_of:
                    root_hash = record.amendment_of
                    break

            history: List[ChainRecord] = []
            for record in chain:
                is_original = (record.doc_hash == root_hash and record.amendment_of is None)
                is_amendment = (record.amendment_of == root_hash)

                if is_original and include_original:
                    history.append(record)
                elif is_amendment:
                    history.append(record)

            return history

    def get_amendments(self, case_id: str, original_doc_hash: str) -> List[ChainRecord]:
        """
        Return only the amendment records (excluding the original V1.0) for a document.

        Args:
            case_id: Case identifier.
            original_doc_hash: SHA-256 hash of the original document.

        Returns:
            List of amendment ChainRecords.

        Raises:
            ChainNotFoundError: If case_id does not exist.
        """
        return self.get_version_history(case_id, original_doc_hash, include_original=False)
