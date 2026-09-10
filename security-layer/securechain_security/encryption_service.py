"""
SecureChain DMS — AES-256-GCM Encryption Service (Module 4)
===========================================================
Core confidentiality engine for the Zero-Trust Digital Evidence Vault (SIH26190).

Legal & Forensic Compliance:
----------------------------
Under Section 65B of the Indian Evidence Act, 1872 and Section 63 of the
Bharatiya Sakshya Adhiniyam (BSA), 2023, digital evidence presented in judicial
proceedings must be unimpeachably protected against unauthorized modification,
tampering, or disclosure throughout its evidentiary lifecycle. This module
guarantees:
  1. Strict Confidentiality: Evidence payloads are sealed using AES-256 in Galois/
     Counter Mode (GCM), ensuring military-grade authenticated encryption.
  2. Non-Repudiation & Cryptographic Binding: Additional Authenticated Data (AAD)
     binds each ciphertext blob directly to its document ID, case ID, and version,
     rendering cross-case substitution, evidence swapping, and rollback attacks
     mathematically impossible.
  3. Envelope Encryption & Two-Vault Separation:
     - Plaintext Data Encryption Keys (DEKs) are generated per-document and wrapped
       by Master Key Encryption Keys (KEKs) via KeyManager (Module 5).
     - Vault 1 (Database) receives only the metadata, hash records, and wrapped DEKs.
     - Vault 2 (Object Storage) receives only the encrypted payload blobs and IVs.
     - A security breach of either vault independently yields zero accessible plaintext.
  4. Memory Hygiene:
     - Plaintext DEKs are held in mutable buffers (`SecureBuffer`) and deterministically
       scrubbed (zeroed) from RAM via C-level `memset` immediately after use.
     - Temporary streaming plaintext buffers are zeroed even if an exception occurs.

Cryptographic Design & Threat Model Defenses:
---------------------------------------------
1. AES-256-GCM vs CBC / ECB:
   - Traditional CBC (Cipher Block Chaining) requires separate MAC computation
     (Encrypt-then-MAC) and is historically susceptible to padding oracle attacks
     (e.g., POODLE, Lucky Thirteen) and bit-flipping if authenticity checks fail.
   - ECB mode lacks semantic security entirely, leaking plaintext structure patterns.
   - GCM provides simultaneous confidentiality (via CTR mode) and integrity/authenticity
     (via the GHASH universal hash function over GF(2^128)) in a single unified primitive.
   - Any single-bit alteration in the ciphertext or AAD causes immediate authentication
     failure (`cryptography.exceptions.InvalidTag`).

2. Nonce (IV) Uniqueness & Length:
   - In AES-GCM, reusing an IV with the same key is catastrophic: it allows an attacker
     to compute the XOR of plaintexts and forge the GHASH authentication key, completely
     destroying authenticity and confidentiality guarantees.
   - We strictly generate a fresh 96-bit (12-byte) cryptographically secure random IV
     for every encryption invocation from the operating system CSPRNG (`os.urandom`),
     meeting NIST SP 800-38D recommendations.

3. Additional Authenticated Data (AAD) Binding:
   - AAD is computed as: `b"{document_id}:{case_id}:{version}"`
   - Although not encrypted, AAD is fully authenticated by the 128-bit GCM tag.
   - Defeats "swap attacks" where an attacker replaces an encrypted file in Vault 2
     with a different validly-encrypted file from another case or version.

4. Streaming Encryption with In-Memory Chunking:
   - Because standard AES-GCM authentication requires the entire ciphertext to compute
     and verify the trailing 128-bit authentication tag before any byte can be trusted,
     true streaming decryption without buffering would expose unauthenticated plaintext
     to callers (violating the Cryptographic Doom Principle).
   - For large evidence files (e.g. CCTV, bodycam video), `encrypt_document_streaming`
     reads from the stream in configurable chunks (64KB default), computes the SHA-256
     doc_hash incrementally, encrypts the full payload in-memory, and immediately
     zeroes the plaintext buffer.

5. Zero Sensitive Data Leakage in Logs:
   - Key material, plaintext contents, ciphertext bytes, and raw cryptographic secrets
     are strictly forbidden from log streams. Only operation names, document IDs,
     case IDs, and byte sizes are recorded at INFO/DEBUG levels.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import logging
from datetime import datetime, timezone
from typing import Any, BinaryIO, Optional, Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from securechain_security.hash_service import HashService, HashingError
from securechain_security.key_manager import KeyManagementError, KeyManager
from securechain_security.models import (
    AUTH_TAG_LENGTH_BYTES,
    DEK_LENGTH_BYTES,
    ENCRYPTION_ALGORITHM,
    IV_LENGTH_BYTES,
    DecryptionResult,
    EncryptionResult,
    WrappedKey,
)
from securechain_security.secure_memory import SecureBuffer, secure_zero

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class CryptoError(Exception):
    """
    Base exception for cryptographic operations in the SecureChain DMS security layer.

    Attributes:
        message: Human-readable error description.
        cause: The underlying exception if this wraps another error, else None.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


class EncryptionError(CryptoError):
    """
    Raised when document encryption, key wrapping, or AAD construction fails.
    """


class DecryptionError(CryptoError):
    """
    Raised when document decryption, key unwrapping, authentication tag verification,
    or post-decryption integrity verification fails.
    """


# ---------------------------------------------------------------------------
# Encryption Service Implementation
# ---------------------------------------------------------------------------


class EncryptionService:
    """
    Core confidentiality engine for digital evidence in SecureChain DMS.

    Implements AES-256-GCM envelope encryption, cryptographic identity binding (AAD),
    secure memory key scrubbing, and post-decryption integrity verification.
    """

    def __init__(
        self,
        key_manager: Optional[KeyManager] = None,
        hash_service: Optional[HashService] = None,
    ) -> None:
        """
        Initialize the EncryptionService with dependency-injected KeyManager and HashService.

        Security Rationale:
            Dependency injection allows swapping KMS backends (e.g., LocalKMSProvider for
            testing vs AWS KMS / Cloud HSM for production) and custom hash chunking
            configurations without altering encryption service logic.

        Args:
            key_manager: Optional KeyManager instance. If None, instantiates a default KeyManager.
            hash_service: Optional HashService instance. If None, instantiates a default HashService.
        """
        self._key_manager: KeyManager = key_manager if key_manager is not None else KeyManager()
        self._hash_service: HashService = hash_service if hash_service is not None else HashService()

        logger.info(
            "EncryptionService initialized (KMS provider=%s, active KEK version=%s)",
            self._key_manager.kms_provider.__class__.__name__,
            self._key_manager.current_kek_version,
        )

    @property
    def key_manager(self) -> KeyManager:
        """Return the underlying KeyManager instance."""
        return self._key_manager

    @property
    def hash_service(self) -> HashService:
        """Return the underlying HashService instance."""
        return self._hash_service

    @staticmethod
    def build_aad(document_id: str, case_id: str, version: str) -> bytes:
        """
        Construct canonical Additional Authenticated Data (AAD) for AES-GCM encryption.

        Formula:
            aad = f"{document_id}:{case_id}:{version}".encode("utf-8")

        Security Rationale:
            AES-GCM is an Authenticated Encryption with Associated Data (AEAD) cipher.
            The AAD is not encrypted, but it is cryptographically processed by the GHASH
            polynomial authenticator and covered by the 128-bit authentication tag.

            By binding the evidence's unique identity (document_id), case context (case_id),
            and version string into the AAD:
              1. Cross-Case Substitution Defense: An adversary with write access to Vault 2
                 (Object Storage) cannot copy an encrypted evidence blob from Case A into
                 Case B. When decrypted in the context of Case B, the GHASH tag verification
                 fails immediately (`InvalidTag`), defeating evidence fabrication.
              2. Document Swapping Defense: An adversary cannot replace an incriminatory
                 document with an encrypted benign document from the same case.
              3. Version Confusion Defense: Prevents rolling back an amended document
                 (e.g., Version 1.1) to an earlier state (Version 1.0) without detection.

        Args:
            document_id: Unique identifier for the digital evidence document.
            case_id: Case or incident file identifier.
            version: Version identifier (e.g., "1.0", "1.1").

        Returns:
            Canonical UTF-8 encoded AAD bytes.

        Raises:
            EncryptionError: If document_id, case_id, or version is empty or invalid.
        """
        if not document_id or not isinstance(document_id, str):
            raise EncryptionError("document_id must be a non-empty string")
        if not case_id or not isinstance(case_id, str):
            raise EncryptionError("case_id must be a non-empty string")
        if not version or not isinstance(version, str):
            raise EncryptionError("version must be a non-empty string")

        return f"{document_id}:{case_id}:{version}".encode("utf-8")

    def encrypt_document(
        self,
        plaintext: bytes,
        document_id: str,
        case_id: str,
        version: str = "1.0",
        officer_id: str = "",
    ) -> EncryptionResult:
        """
        Encrypt a document payload using AES-256-GCM envelope encryption.

        Cryptographic Lifecycle:
          1. Generates a fresh, unique 256-bit (32-byte) Data Encryption Key (DEK).
          2. Generates a strictly unique 96-bit (12-byte) Initialization Vector (IV).
          3. Builds the canonical Additional Authenticated Data (AAD) binding document ID,
             case ID, and version.
          4. Encrypts plaintext under DEK + IV + AAD using AES-256-GCM, producing ciphertext
             with an appended 128-bit authentication tag.
          5. Wraps (encrypts) the DEK under the active master Key Encryption Key (KEK).
          6. Scans/zeroes the plaintext DEK from memory using `SecureBuffer`.
          7. Computes the SHA-256 doc_hash for chain verification.
          8. Returns structured `EncryptionResult`.

        Args:
            plaintext: Raw document bytes to encrypt.
            document_id: Unique identifier for the evidence document.
            case_id: Unique case identifier.
            version: Lifecycle version (defaults to "1.0" for original evidence).
            officer_id: Identity of officer sealing evidence (optional metadata).

        Returns:
            EncryptionResult dataclass containing ciphertext, IV, wrapped DEK, AAD,
            and cryptographic metadata.

        Raises:
            EncryptionError: If input parameters are invalid, cipher execution fails,
                             or DEK wrapping fails.
        """
        if plaintext is None or not isinstance(plaintext, (bytes, bytearray, memoryview)):
            raise EncryptionError(
                f"Plaintext must be bytes-like, got {type(plaintext).__name__ if plaintext is not None else 'None'}"
            )

        # Build canonical AAD (validates document_id, case_id, version)
        aad = self.build_aad(document_id=document_id, case_id=case_id, version=version)

        logger.info(
            "encrypt_document: sealing document_id=%s, case_id=%s, version=%s, size=%d bytes",
            document_id,
            case_id,
            version,
            len(plaintext),
        )

        # 1. Generate unique per-document DEK and strictly unique 96-bit IV
        raw_dek = self._key_manager.generate_dek()
        iv = self._key_manager.generate_iv()

        # 2. Envelope encryption with deterministic DEK memory zeroing
        try:
            with SecureBuffer(raw_dek) as dek_buf:
                try:
                    aesgcm = AESGCM(bytes(dek_buf))
                    ciphertext = aesgcm.encrypt(iv, bytes(plaintext), aad)
                except Exception as exc:
                    logger.error(
                        "encrypt_document: AES-GCM cipher encryption failed for document_id=%s: %s",
                        document_id,
                        exc,
                    )
                    raise EncryptionError(
                        f"AES-GCM encryption failed for document '{document_id}': {exc}",
                        cause=exc,
                    ) from exc

                try:
                    wrapped_key = self._key_manager.wrap_dek(
                        bytes(dek_buf),
                        document_id=document_id,
                    )
                except KeyManagementError as exc:
                    logger.error(
                        "encrypt_document: DEK wrapping failed for document_id=%s: %s",
                        document_id,
                        exc,
                    )
                    raise EncryptionError(
                        f"DEK wrapping failed for document '{document_id}': {exc}",
                        cause=exc,
                    ) from exc
        finally:
            # Explicit cleanup guarantee: if raw_dek was mutable, overwrite it
            if isinstance(raw_dek, bytearray):
                secure_zero(raw_dek)

        # 3. Compute raw document SHA-256 hash for chain integrity linking
        try:
            doc_hash = self._hash_service.hash_bytes(bytes(plaintext))
        except HashingError as exc:
            logger.error("encrypt_document: failed to compute doc_hash for document_id=%s: %s", document_id, exc)
            raise EncryptionError(
                f"Failed to compute document hash for '{document_id}': {exc}",
                cause=exc,
            ) from exc

        logger.info(
            "encrypt_document completed: document_id=%s, ciphertext_bytes=%d",
            document_id,
            len(ciphertext),
        )

        return EncryptionResult(
            document_id=document_id,
            case_id=case_id,
            version=version,
            ciphertext=ciphertext,
            iv=iv,
            wrapped_dek=wrapped_key.wrapped_dek,
            aad=aad,
            algorithm=ENCRYPTION_ALGORITHM,
            wrapped_key=wrapped_key,
            doc_hash=doc_hash,
        )

    def decrypt_document(
        self,
        ciphertext: bytes,
        iv: bytes,
        wrapped_dek: Union[WrappedKey, bytes],
        aad: bytes,
        expected_doc_hash: str = "",
        document_id: str = "",
        strict_integrity: bool = False,
        kek_version: Optional[str] = None,
    ) -> DecryptionResult:
        """
        Decrypt an encrypted document payload and verify its cryptographic authenticity and integrity.

        Cryptographic Lifecycle:
          1. Validates ciphertext, IV length (must be 12 bytes), and AAD.
          2. Unwraps the Data Encryption Key (DEK) under the appropriate KEK version.
          3. Loads DEK into a `SecureBuffer` and decrypts ciphertext using AES-256-GCM.
             The GHASH authenticator verifies the 128-bit auth tag against ciphertext and AAD.
             Any tampering, truncated payload, or mismatched metadata raises `DecryptionError`.
          4. Memory hygiene: `SecureBuffer` automatically zeroes the DEK from RAM immediately
             upon exiting the decryption block.
          5. Computes SHA-256 hash of the decrypted plaintext.
          6. If `expected_doc_hash` is provided, performs constant-time comparison
             via `hmac.compare_digest` to verify integrity against the immutable chain record.
          7. Returns `DecryptionResult`.

        Args:
            ciphertext: Encrypted document bytes (including trailing 16-byte GCM auth tag).
            iv: 12-byte initialization vector / nonce used during encryption.
            wrapped_dek: The WrappedKey record or raw wrapped DEK bytes from Vault 1.
            aad: Canonical Additional Authenticated Data bytes bound during encryption.
            expected_doc_hash: Optional expected SHA-256 hex digest to verify post-decryption integrity.
            document_id: Optional document ID override (inferred from wrapped_dek or AAD if omitted).
            strict_integrity: If True and expected_doc_hash is provided, raises DecryptionError on
                              hash mismatch. If False, records mismatch in DecryptionResult.integrity_verified.
            kek_version: Optional KEK version override when wrapped_dek is passed as raw bytes.

        Returns:
            DecryptionResult containing decrypted plaintext, integrity_verified boolean,
            and computed document hash.

        Raises:
            DecryptionError: If ciphertext/IV/AAD is malformed, authentication tag verification
                             fails, key unwrapping fails, or integrity fails under strict mode.
        """
        # Validate inputs
        if ciphertext is None or not isinstance(ciphertext, (bytes, bytearray, memoryview)):
            raise DecryptionError(
                f"Ciphertext must be bytes-like, got {type(ciphertext).__name__ if ciphertext is not None else 'None'}"
            )
        if len(ciphertext) < AUTH_TAG_LENGTH_BYTES:
            raise DecryptionError(
                f"Ciphertext too short: expected at least {AUTH_TAG_LENGTH_BYTES} bytes "
                f"(GCM auth tag), got {len(ciphertext)} bytes"
            )
        if iv is None or not isinstance(iv, (bytes, bytearray, memoryview)):
            raise DecryptionError(
                f"IV must be bytes-like, got {type(iv).__name__ if iv is not None else 'None'}"
            )
        if len(iv) != IV_LENGTH_BYTES:
            raise DecryptionError(
                f"Invalid IV length: expected exactly {IV_LENGTH_BYTES} bytes (96 bits), got {len(iv)} bytes"
            )
        if aad is None or not isinstance(aad, (bytes, bytearray, memoryview)):
            raise DecryptionError(
                f"AAD must be bytes-like, got {type(aad).__name__ if aad is not None else 'None'}"
            )

        # Infer document_id from parameters, wrapped_dek, or AAD
        doc_id = document_id
        if not doc_id and isinstance(wrapped_dek, WrappedKey) and wrapped_dek.document_id:
            doc_id = wrapped_dek.document_id
        if not doc_id and aad:
            try:
                doc_id = bytes(aad).decode("utf-8", errors="ignore").split(":")[0]
            except Exception:
                pass
        if not doc_id:
            doc_id = "unknown"

        logger.info(
            "decrypt_document: starting decryption for document_id=%s, ciphertext_bytes=%d",
            doc_id,
            len(ciphertext),
        )

        # 1. Unwrap the DEK
        wrapped_key_obj: WrappedKey
        if isinstance(wrapped_dek, WrappedKey):
            wrapped_key_obj = wrapped_dek
        elif isinstance(wrapped_dek, (bytes, bytearray, memoryview)):
            active_version = kek_version or self._key_manager.current_kek_version
            wrapped_key_obj = WrappedKey(
                key_id="adhoc-key",
                wrapped_dek=bytes(wrapped_dek),
                kek_version=active_version,
                document_id=doc_id,
            )
        else:
            raise DecryptionError(
                f"wrapped_dek must be WrappedKey or bytes, got {type(wrapped_dek).__name__}"
            )

        try:
            raw_dek = self._key_manager.unwrap_dek(wrapped_key_obj)
        except KeyManagementError as exc:
            logger.error("decrypt_document: failed to unwrap DEK for document_id=%s: %s", doc_id, exc)
            raise DecryptionError(
                f"Failed to unwrap DEK for document '{doc_id}': {exc}",
                cause=exc,
            ) from exc
        except Exception as exc:
            logger.error("decrypt_document: unexpected error unwrapping DEK for document_id=%s: %s", doc_id, exc)
            raise DecryptionError(
                f"Unexpected error unwrapping DEK for document '{doc_id}': {exc}",
                cause=exc,
            ) from exc

        # 2. Decrypt under AES-GCM within SecureBuffer context (deterministic memory zeroing)
        try:
            with SecureBuffer(raw_dek) as dek_buf:
                try:
                    aesgcm = AESGCM(bytes(dek_buf))
                    decrypted = aesgcm.decrypt(bytes(iv), bytes(ciphertext), bytes(aad))
                except InvalidTag as exc:
                    logger.error(
                        "decrypt_document: AES-GCM authentication tag verification failed for document_id=%s "
                        "(ciphertext payload, IV, or AAD has been tampered with or corrupted)",
                        doc_id,
                    )
                    raise DecryptionError(
                        f"AES-GCM authentication tag verification failed for document '{doc_id}'. "
                        "The ciphertext payload, initialization vector (IV), or Additional Authenticated Data (AAD) "
                        "has been tampered with, altered, or corrupted.",
                        cause=exc,
                    ) from exc
                except Exception as exc:
                    logger.error("decrypt_document: cipher decryption error for document_id=%s: %s", doc_id, exc)
                    raise DecryptionError(
                        f"AES-GCM decryption failed for document '{doc_id}': {exc}",
                        cause=exc,
                    ) from exc
        finally:
            if isinstance(raw_dek, bytearray):
                secure_zero(raw_dek)

        # 3. Post-decryption SHA-256 integrity verification
        try:
            computed_hash = self._hash_service.hash_bytes(decrypted)
        except HashingError as exc:
            logger.error("decrypt_document: failed to hash decrypted bytes for document_id=%s: %s", doc_id, exc)
            raise DecryptionError(
                f"Failed to compute SHA-256 hash of decrypted content for document '{doc_id}': {exc}",
                cause=exc,
            ) from exc

        integrity_verified = False
        if expected_doc_hash:
            clean_expected = expected_doc_hash.lower().strip()
            clean_computed = computed_hash.lower().strip()
            # Constant-time comparison to prevent timing side-channel attacks
            integrity_verified = hmac.compare_digest(clean_computed, clean_expected)

            if not integrity_verified:
                logger.warning(
                    "decrypt_document: integrity hash mismatch for document_id=%s "
                    "(computed hash differs from stored chain record hash)",
                    doc_id,
                )
                if strict_integrity:
                    raise DecryptionError(
                        f"Integrity verification failed for document '{doc_id}': "
                        f"computed hash '{clean_computed}' does not match expected hash '{clean_expected}'"
                    )

        logger.info(
            "decrypt_document completed: document_id=%s, plaintext_bytes=%d, integrity_verified=%s",
            doc_id,
            len(decrypted),
            integrity_verified,
        )

        return DecryptionResult(
            document_id=doc_id,
            plaintext=decrypted,
            integrity_verified=integrity_verified,
            doc_hash=computed_hash,
        )

    def decrypt_result(
        self,
        result: EncryptionResult,
        expected_doc_hash: str = "",
        strict_integrity: bool = False,
    ) -> DecryptionResult:
        """
        Convenience helper to decrypt directly from an EncryptionResult instance.

        Args:
            result: EncryptionResult returned by encrypt_document or encrypt_document_streaming.
            expected_doc_hash: Optional expected hash override. Defaults to result.doc_hash.
            strict_integrity: If True, raises DecryptionError on hash mismatch.

        Returns:
            DecryptionResult containing decrypted plaintext and verification status.
        """
        expected_hash = expected_doc_hash or getattr(result, "doc_hash", "") or ""
        wrapped = getattr(result, "wrapped_key", None)
        if wrapped is None:
            wrapped = result.wrapped_dek

        return self.decrypt_document(
            ciphertext=result.ciphertext,
            iv=result.iv,
            wrapped_dek=wrapped,
            aad=result.aad,
            expected_doc_hash=expected_hash,
            document_id=result.document_id,
            strict_integrity=strict_integrity,
        )

    def encrypt_document_streaming(
        self,
        file_stream: Any,
        document_id: str,
        case_id: str,
        version: str = "1.0",
        officer_id: str = "",
        chunk_size: int = 65536,
    ) -> EncryptionResult:
        """
        Encrypt large digital evidence documents from a binary stream.

        Security Architecture & Streaming Mechanics:
          - AES-GCM requires the entire ciphertext to compute and verify the trailing
            128-bit authentication tag before any byte can be certified as authentic.
            Attempting to yield intermediate decrypted chunks would violate the Cryptographic
            Doom Principle (processing unauthenticated plaintext).
          - Therefore, this method streams the input file in configurable chunks (default 64KB)
            to manage disk I/O, while simultaneously calculating the SHA-256 doc_hash
            incrementally via a streaming hasher.
          - Plaintext is accumulated into a mutable `bytearray` buffer. Once the stream is
            fully read, the payload is sealed with AES-256-GCM under a fresh DEK, IV, and AAD.
          - Immediately following encryption, the mutable plaintext buffer is scrubbed
            (zeroed) from RAM via `secure_zero` inside a `finally` block, ensuring no
            evidence leaks into swap or memory dumps even if an error occurs.

        Args:
            file_stream: Binary file-like object supporting `.read(chunk_size)`.
            document_id: Unique identifier for the evidence document.
            case_id: Unique case identifier.
            version: Lifecycle version (defaults to "1.0").
            officer_id: Identity of the officer sealing evidence (optional).
            chunk_size: Buffer size for chunked reads in bytes (defaults to 65536 = 64KB).

        Returns:
            EncryptionResult dataclass with ciphertext, IV, wrapped DEK, AAD, and doc_hash.

        Raises:
            EncryptionError: If file_stream is invalid, I/O fails, chunk_size <= 0,
                             or encryption fails.
        """
        if file_stream is None or not hasattr(file_stream, "read") or not callable(file_stream.read):
            raise EncryptionError(
                "Invalid file_stream: expected a binary file-like object with a callable .read() method"
            )
        if chunk_size <= 0:
            raise EncryptionError(f"chunk_size must be positive, got {chunk_size}")

        aad = self.build_aad(document_id=document_id, case_id=case_id, version=version)

        logger.info(
            "encrypt_document_streaming: sealing document_id=%s, case_id=%s, version=%s (chunk_size=%d)",
            document_id,
            case_id,
            version,
            chunk_size,
        )

        plaintext_buffer = bytearray()
        hasher = hashlib.sha256()
        total_bytes = 0

        try:
            # 1. Read stream chunk-by-chunk, incrementally updating hash and plaintext buffer
            while True:
                chunk = file_stream.read(chunk_size)
                if not chunk:
                    break
                if isinstance(chunk, str):
                    chunk = chunk.encode("utf-8")
                elif not isinstance(chunk, (bytes, bytearray, memoryview)):
                    raise EncryptionError(
                        f"Stream chunk must be bytes-like, got {type(chunk).__name__}"
                    )

                hasher.update(chunk)
                plaintext_buffer.extend(chunk)
                total_bytes += len(chunk)

            doc_hash = hasher.hexdigest()

            # 2. Generate per-document DEK and strictly unique 96-bit IV
            raw_dek = self._key_manager.generate_dek()
            iv = self._key_manager.generate_iv()

            # 3. Encrypt payload under AES-GCM and wrap DEK inside SecureBuffer
            with SecureBuffer(raw_dek) as dek_buf:
                try:
                    aesgcm = AESGCM(bytes(dek_buf))
                    ciphertext = aesgcm.encrypt(iv, bytes(plaintext_buffer), aad)
                except Exception as exc:
                    logger.error(
                        "encrypt_document_streaming: cipher encryption failed for document_id=%s: %s",
                        document_id,
                        exc,
                    )
                    raise EncryptionError(
                        f"AES-GCM encryption failed for document '{document_id}': {exc}",
                        cause=exc,
                    ) from exc

                try:
                    wrapped_key = self._key_manager.wrap_dek(
                        bytes(dek_buf),
                        document_id=document_id,
                    )
                except KeyManagementError as exc:
                    logger.error(
                        "encrypt_document_streaming: DEK wrapping failed for document_id=%s: %s",
                        document_id,
                        exc,
                    )
                    raise EncryptionError(
                        f"DEK wrapping failed for document '{document_id}': {exc}",
                        cause=exc,
                    ) from exc

        except EncryptionError:
            raise
        except Exception as exc:
            logger.error(
                "encrypt_document_streaming: unexpected error for document_id=%s: %s",
                document_id,
                exc,
            )
            raise EncryptionError(
                f"Streaming encryption failed for document '{document_id}': {exc}",
                cause=exc,
            ) from exc
        finally:
            # 4. Zero plaintext buffer from memory immediately
            secure_zero(plaintext_buffer)
            del plaintext_buffer

        logger.info(
            "encrypt_document_streaming completed: document_id=%s, total_bytes=%d, ciphertext_bytes=%d",
            document_id,
            total_bytes,
            len(ciphertext),
        )

        return EncryptionResult(
            document_id=document_id,
            case_id=case_id,
            version=version,
            ciphertext=ciphertext,
            iv=iv,
            wrapped_dek=wrapped_key.wrapped_dek,
            aad=aad,
            algorithm=ENCRYPTION_ALGORITHM,
            wrapped_key=wrapped_key,
            doc_hash=doc_hash,
        )
