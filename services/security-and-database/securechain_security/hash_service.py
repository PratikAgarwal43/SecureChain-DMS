"""
SecureChain DMS — Hash Generator Service (Module 1)
====================================================
Cryptographic hash generation and hash-chain linking service for the Zero-Trust
Digital Evidence Vault (SIH26190).

Legal & Forensic Compliance:
----------------------------
Under Section 65B of the Indian Evidence Act, 1872 and Section 63 of the
Bharatiya Sakshya Adhiniyam (BSA), 2023, electronic evidence is admissible only
if its integrity from the moment of seizure to presentation in court can be
conclusively demonstrated. SHA-256 provides a mathematically irreproducible
fingerprint that detects single-bit alterations in digital evidence.

Security Architecture:
----------------------
1. Streaming SHA-256 (O(1) Memory Footprint):
   Large evidence files (e.g., multi-gigabyte body-worn camera footage, seized
   hard drives, call recordings) are hashed in fixed-size chunks (8192 bytes by
   default) to prevent Out-Of-Memory (OOM) denial-of-service vulnerabilities.

2. Constant-Time Hash Comparison (Side-Channel Defense):
   Integrity verification uses `hmac.compare_digest` to perform constant-time
   equality checks. Traditional byte-by-byte comparisons (`==`) terminate on the
   first mismatching byte, leaking timing information that enables iterative
   digest estimation attacks.

3. Cryptographic Hash Chain Linking:
   Documents are chained sequentially via:
     chain_hash = SHA-256(doc_hash + prev_chain_hash + timestamp + officer_id [+ quorum_token])
   This binds document content, chronological precedence, trusted server timestamp,
   authenticated officer identity, and optional multi-party authorization tokens into
   an immutable chain. Any retrospective tampering, deletion, or reordering breaks
   all downstream links.

4. Zero Sensitive Data Leakage in Logs:
   Log messages record operation names and byte counts at INFO level. Raw hashes
   are restricted to DEBUG level, and plaintext/key data are never logged.

5. Thread-Safety & Statelessness:
   HashService maintains no mutable instance state across calls; all hasher
   contexts are allocated locally on the execution stack.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, BinaryIO, Optional, Sequence, Tuple, Union

from securechain_security.models import (
    CHUNK_SIZE_BYTES,
    HASH_ALGORITHM,
    HashResult,
)

logger = logging.getLogger(__name__)


class HashingError(Exception):
    """
    Raised when a cryptographic hashing or hash verification operation fails.

    Attributes:
        message: Explanation of the error.
        cause: The underlying exception if this wraps another error, else None.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


class HashService:
    """
    Stateless and thread-safe cryptographic hashing service for SecureChain DMS.

    Provides streaming SHA-256 calculation for large digital evidence, in-memory
    hashing, hash-chain link computation, and constant-time integrity verification.
    """

    def __init__(self, chunk_size: int = CHUNK_SIZE_BYTES) -> None:
        """
        Initialize the HashService.

        Args:
            chunk_size: Default buffer size in bytes for chunked streaming reads.
                        Defaults to CHUNK_SIZE_BYTES (8192 bytes).

        Raises:
            ValueError: If chunk_size is less than or equal to 0.
        """
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, got {chunk_size}")
        self._chunk_size = chunk_size

    @property
    def chunk_size(self) -> int:
        """Return the configured streaming chunk size in bytes."""
        return self._chunk_size

    def _hash_stream_with_size(
        self,
        file_stream: Any,
        chunk_size: Optional[int] = None,
    ) -> Tuple[str, int]:
        """
        Internal streaming hash generator that returns both the SHA-256 hex digest
        and the total number of bytes read.

        Args:
            file_stream: Binary file-like object with a callable `.read()` method.
            chunk_size: Optional override for buffer chunk size.

        Returns:
            Tuple of (hex_digest, total_bytes_read).

        Raises:
            HashingError: If file_stream is invalid or an I/O read error occurs.
        """
        if file_stream is None or not hasattr(file_stream, "read") or not callable(file_stream.read):
            raise HashingError(
                "Invalid file_stream: expected a file-like object with a callable .read() method"
            )

        effective_chunk_size = chunk_size if chunk_size is not None else self._chunk_size
        if effective_chunk_size <= 0:
            raise HashingError(f"Effective chunk_size must be positive, got {effective_chunk_size}")

        hasher = hashlib.sha256()
        total_bytes = 0

        try:
            while True:
                chunk = file_stream.read(effective_chunk_size)
                if not chunk:
                    break
                if isinstance(chunk, str):
                    # Defensive conversion if a text stream was accidentally passed
                    chunk = chunk.encode("utf-8")
                elif not isinstance(chunk, (bytes, bytearray, memoryview)):
                    raise HashingError(
                        f"Stream chunk must be bytes-like, got {type(chunk).__name__}"
                    )

                hasher.update(chunk)
                total_bytes += len(chunk)
        except HashingError:
            raise
        except Exception as exc:
            logger.error("I/O error during stream hashing: %s", exc)
            raise HashingError(f"Error reading file stream during hashing: {exc}", cause=exc) from exc

        digest = hasher.hexdigest()
        return digest, total_bytes

    def hash_document(
        self,
        file_stream: Any,
        chunk_size: Optional[int] = None,
    ) -> str:
        """
        Generate SHA-256 hex digest of a document via streaming reads.

        Security Rationale:
            Digital evidence in criminal investigations frequently includes large
            surveillance videos or disk images exceeding available system RAM.
            Streaming in fixed 8192-byte blocks maintains an O(1) memory footprint,
            preventing Out-Of-Memory (OOM) denial-of-service vulnerabilities.

        Args:
            file_stream: File-like object opened in binary mode supporting `.read()`.
            chunk_size: Optional chunk size override (in bytes).

        Returns:
            64-character lowercase hexadecimal SHA-256 digest string.

        Raises:
            HashingError: If reading from the stream fails or the stream is invalid.
        """
        digest, total_bytes = self._hash_stream_with_size(file_stream, chunk_size=chunk_size)
        logger.info("hash_document completed (bytes processed: %d)", total_bytes)
        logger.debug("hash_document SHA-256 digest: %s", digest)
        return digest

    def hash_bytes(self, data: bytes) -> str:
        """
        Compute SHA-256 hex digest of an in-memory byte buffer.

        Security Rationale:
            Fast cryptographic hashing for small, in-memory payloads such as
            serialized metadata records, wrapped key descriptors, or DSC signatures.

        Args:
            data: Raw bytes to hash.

        Returns:
            64-character lowercase hexadecimal SHA-256 digest string.

        Raises:
            HashingError: If the input data is not bytes-like or hashing fails.
        """
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise HashingError(f"Expected bytes-like object, got {type(data).__name__}")

        try:
            hasher = hashlib.sha256()
            hasher.update(data)
            digest = hasher.hexdigest()
        except Exception as exc:
            logger.error("Failed to hash raw bytes: %s", exc)
            raise HashingError(f"Error hashing byte buffer: {exc}", cause=exc) from exc

        logger.info("hash_bytes completed (bytes processed: %d)", len(data))
        logger.debug("hash_bytes SHA-256 digest: %s", digest)
        return digest

    def hash_chain_link(
        self,
        doc_hash: str,
        prev_chain_hash: str,
        timestamp: str,
        officer_id: str,
        quorum_token: Optional[str] = None,
    ) -> str:
        """
        Compute the cryptographic chain hash for a document link.

        Formula:
            chain_hash = SHA-256(doc_hash + prev_chain_hash + timestamp + officer_id [+ quorum_token])

        Security Rationale:
            Chain linking binds the document content (`doc_hash`), chronological
            preceding state (`prev_chain_hash`), trusted server timestamp (`timestamp`),
            authenticated officer identity (`officer_id`), and optional multi-signature
            authorization token (`quorum_token`) into an immutable cryptographic chain.
            This prevents backdating, document deletion, reordering, or unauthorized
            amendments without detection.

        Args:
            doc_hash: SHA-256 hex digest of the raw document bytes.
            prev_chain_hash: Chain hash of the preceding link (or GENESIS_HASH for root).
            timestamp: ISO 8601 millisecond-precision server timestamp.
            officer_id: Cryptographically verified identity (e.g. DSC subject ID) of uploader.
            quorum_token: Optional cryptographic quorum approval token for amendments (V1.1+).

        Returns:
            64-character lowercase hexadecimal SHA-256 chain hash string.

        Raises:
            HashingError: If any parameter is invalid or empty.
        """
        if not doc_hash or not isinstance(doc_hash, str):
            raise HashingError("doc_hash must be a non-empty string")
        if not prev_chain_hash or not isinstance(prev_chain_hash, str):
            raise HashingError("prev_chain_hash must be a non-empty string")
        if not timestamp or not isinstance(timestamp, str):
            raise HashingError("timestamp must be a non-empty string")
        if not officer_id or not isinstance(officer_id, str):
            raise HashingError("officer_id must be a non-empty string")
        if quorum_token is not None and not isinstance(quorum_token, str):
            raise HashingError("quorum_token must be a string if provided")

        if quorum_token is not None:
            payload = f"{doc_hash}{prev_chain_hash}{timestamp}{officer_id}{quorum_token}"
        else:
            payload = f"{doc_hash}{prev_chain_hash}{timestamp}{officer_id}"

        try:
            hasher = hashlib.sha256(payload.encode("utf-8"))
            chain_hash = hasher.hexdigest()
        except Exception as exc:
            logger.error("Failed to compute chain link hash: %s", exc)
            raise HashingError(f"Error computing chain link hash: {exc}", cause=exc) from exc

        logger.info(
            "hash_chain_link completed (officer_id: %s, has_quorum: %s, payload_len: %d)",
            officer_id,
            quorum_token is not None,
            len(payload),
        )
        logger.debug("hash_chain_link digest computed: %s", chain_hash)
        return chain_hash

    def verify_hash(
        self,
        file_stream: Any,
        expected_hash: str,
        chunk_size: Optional[int] = None,
    ) -> bool:
        """
        Re-hash a file stream and verify against an expected hash using constant-time comparison.

        Security Rationale:
            Standard string comparison (`a == b`) terminates execution at the
            first unequal character. In network-facing or untrusted environments,
            an attacker can measure the microsecond response time difference to
            infer which characters matched, reconstructing hashes side-channel by
            side-channel. `hmac.compare_digest` executes in constant time regardless
            of where mismatches occur, completely neutralizing timing attacks.

        Args:
            file_stream: Binary file-like object with a `.read()` method.
            expected_hash: Expected 64-character SHA-256 hex string to verify against.
            chunk_size: Optional chunk size override (in bytes).

        Returns:
            True if the computed hash exactly matches expected_hash; False otherwise.

        Raises:
            HashingError: If expected_hash is invalid or file reading fails.
        """
        if not expected_hash or not isinstance(expected_hash, str):
            raise HashingError("expected_hash must be a non-empty string")

        computed_hash = self.hash_document(file_stream, chunk_size=chunk_size)
        is_valid = hmac.compare_digest(
            computed_hash.lower().strip(),
            expected_hash.lower().strip(),
        )

        logger.info("verify_hash completed (match: %s)", is_valid)
        logger.debug(
            "verify_hash comparison (expected: %s, computed: %s)",
            expected_hash,
            computed_hash,
        )
        return is_valid

    def hash_multiple(
        self,
        file_streams: Sequence[Any],
    ) -> list[HashResult]:
        """
        Batch hash multiple file streams and return structured HashResult models.

        Security Rationale:
            Evidence packages often contain multiple related artifacts (e.g.,
            multi-camera CCTV recordings or crime scene photograph sequences).
            Batch hashing generates standardized metadata records with cryptographic
            digests and exact byte sizes for downstream atomic chain ingestion.

        Supported input formats for elements in `file_streams`:
            1. BinaryIO / file-like objects: Document ID inferred from `.name` or UUID.
            2. Tuple `(document_id, file_stream)`.
            3. Dict `{"document_id": "...", "stream": file_stream}`.

        Args:
            file_streams: Sequence of file streams, (doc_id, stream) tuples, or dicts.

        Returns:
            List of HashResult dataclasses containing document_id, doc_hash,
            algorithm, file_size_bytes, and UTC timestamp.

        Raises:
            HashingError: If file_streams is invalid or any file fails to hash.
        """
        if file_streams is None:
            raise HashingError("file_streams cannot be None")

        results: list[HashResult] = []
        total_batch_bytes = 0

        for idx, item in enumerate(file_streams):
            doc_id: str
            stream: Any

            if isinstance(item, tuple) and len(item) == 2:
                doc_id = str(item[0])
                stream = item[1]
            elif isinstance(item, dict):
                stream = item.get("stream") or item.get("file_stream")
                doc_id = str(
                    item.get("document_id")
                    or item.get("id")
                    or getattr(stream, "name", "")
                    or uuid.uuid4()
                )
            else:
                stream = item
                doc_id = str(
                    getattr(stream, "document_id", "")
                    or getattr(stream, "name", "")
                    or uuid.uuid4()
                )

            if not doc_id:
                doc_id = str(uuid.uuid4())

            try:
                doc_hash, file_size = self._hash_stream_with_size(stream)
            except Exception as exc:
                logger.error("Batch hashing failed at index %d (doc_id: %s): %s", idx, doc_id, exc)
                raise HashingError(
                    f"Failed to hash evidence item at index {idx} (document_id='{doc_id}'): {exc}",
                    cause=exc,
                ) from exc

            total_batch_bytes += file_size
            result = HashResult(
                document_id=doc_id,
                doc_hash=doc_hash,
                algorithm=HASH_ALGORITHM,
                file_size_bytes=file_size,
                timestamp=datetime.now(timezone.utc).isoformat(),
            )
            results.append(result)

        logger.info(
            "hash_multiple completed (files processed: %d, total bytes: %d)",
            len(results),
            total_batch_bytes,
        )
        return results
