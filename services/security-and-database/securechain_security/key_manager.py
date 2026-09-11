"""
SecureChain DMS — Key Manager (Module 5)
========================================
Manages the envelope encryption key hierarchy for the Zero-Trust Digital
Evidence Vault (SIH26190).

Legal & Forensic Compliance:
----------------------------
Under Section 65B of the Indian Evidence Act, 1872 and Section 63 of the
Bharatiya Sakshya Adhiniyam (BSA), 2023, digital evidence must be shielded
against tampering and unauthorized inspection throughout its custody lifecycle.
Envelope encryption guarantees:
  1. Forward Secrecy: Compromise of an individual document's Data Encryption
     Key (DEK) does not expose any other document in the case or system.
  2. Cryptographic Separation of Duties: Master Key Encryption Keys (KEKs)
     are managed via Hardware Security Modules (HSM) or Cloud KMS boundaries,
     preventing system administrators or database operators from decrypting
     evidence files.
  3. Seamless Key Rotation: Master KEKs can be rotated annually without requiring
     mass re-encryption of gigabytes or terabytes of underlying evidence blobs.

Security Architecture:
----------------------
1. Envelope Encryption Hierarchy:
     +-------------------------------------------------------------------+
     | Master KEK (Key Encryption Key) — AES-256 (Managed in KMS/HSM)    |
     +-------------------------------------------------------------------+
                                       |
                   wraps / unwraps (AES-256-GCM)
                                       v
     +-------------------------------------------------------------------+
     | DEK (Data Encryption Key) — AES-256 (Unique per Document)        |
     +-------------------------------------------------------------------+
                                       |
                          encrypts document payload
                                       v
     +-------------------------------------------------------------------+
     | Vault 2: Encrypted Evidence Blob (Ciphertext + IV + Auth Tag)     |
     +-------------------------------------------------------------------+

2. Two-Vault Physical Segregation:
     - Vault 1 (Database): Stores metadata, hash chains, and WrappedKey records.
     - Vault 2 (Object Store): Stores encrypted document payloads and IVs.
     - An adversary breaching either vault individually gains zero access to plaintext evidence.

3. Strict Nonce Uniqueness (AES-GCM):
     Every encryption invocation generates a cryptographically random 96-bit
     (12-byte) IV from the OS CSPRNG. In GCM mode, nonce reuse with the same key
     destroys authenticity guarantees and enables catastrophic tag forgery.

4. Versioned KEK Rotation:
     The KEK is versioned (e.g., 'v1', 'v2', ...). When rotated, historical KEKs
     are preserved in a protected version map to permit ongoing decryption of
     archived evidence records, while all new documents are encrypted under the
     latest active KEK version.

5. Zero Sensitive Data Leakage in Logs:
     Key material, plaintext, and raw DEK/KEK bytes are strictly forbidden from
     log streams. Only operation names, key UUIDs, version tags, and document IDs
     may be logged.
"""

from __future__ import annotations

import logging
import os
import re
import threading
import uuid
from abc import ABC, abstractmethod
from typing import Optional, Sequence, Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from securechain_security.models import (
    AUTH_TAG_LENGTH_BYTES,
    DEK_LENGTH_BYTES,
    IV_LENGTH_BYTES,
    WrappedKey,
)

logger = logging.getLogger(__name__)

# Minimum ciphertext length when wrapping a DEK: 12-byte IV + 16-byte GCM auth tag
_MIN_WRAPPED_KEY_CIPHERTEXT_LENGTH = IV_LENGTH_BYTES + AUTH_TAG_LENGTH_BYTES


class KeyManagementError(Exception):
    """
    Raised when a key management, key derivation, wrapping, or unwrapping operation fails.

    Attributes:
        message: Human-readable error description.
        cause: Underlying caught exception, if applicable.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


def zero_buffer(buffer: Union[bytearray, memoryview]) -> None:
    """
    Cryptographically overwrite a mutable buffer with zeros to purge sensitive key material.

    Security Rationale:
        Python's runtime garbage collection does not guarantee when discarded heap
        objects are overwritten in RAM. By explicitly zeroing mutable buffers immediately
        following cryptographic operations, the window of exposure to memory-dumping attacks,
        swap-file leakage, or cold-boot exploits is drastically reduced.

    Args:
        buffer: A mutable bytearray or writable memoryview containing sensitive key bytes.
    """
    if isinstance(buffer, (bytearray, memoryview)):
        try:
            for i in range(len(buffer)):
                buffer[i] = 0
        except TypeError:
            # If memoryview is read-only, skip in-place zeroing
            pass


class KMSProvider(ABC):
    """
    Abstract Base Class defining the Key Management Service (KMS) interface.

    Security Rationale:
        In production Zero-Trust deployments for judicial evidence, the root KEK
        must reside inside a certified Hardware Security Module (FIPS 140-2/3 Level 3)
        or an enterprise Cloud KMS (AWS KMS, GCP Cloud KMS, Azure Key Vault).
        This abstract interface abstracts the cryptographic boundary so implementations
        can be swapped seamlessly without altering business logic.
    """

    @abstractmethod
    def encrypt(
        self,
        plaintext: bytes,
        key_version: Optional[str] = None,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Encrypt sensitive plaintext (e.g., a DEK) using a versioned master key.

        Args:
            plaintext: Raw bytes to encrypt.
            key_version: Optional specific KEK version identifier. If None, uses active KEK.
            associated_data: Optional additional authenticated data (AAD) bound to the ciphertext.

        Returns:
            Opaque encrypted bytes encapsulating nonce, ciphertext, and authentication tag.

        Raises:
            KeyManagementError: If encryption fails or the specified key version does not exist.
        """
        pass

    @abstractmethod
    def decrypt(
        self,
        ciphertext: bytes,
        key_version: Optional[str] = None,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt wrapped ciphertext back to plaintext using the designated KEK version.

        Args:
            ciphertext: Opaque encrypted bytes encapsulating nonce, ciphertext, and tag.
            key_version: KEK version identifier used during encryption. If None, uses active KEK.
            associated_data: Optional additional authenticated data (AAD) to verify.

        Returns:
            Decrypted raw plaintext bytes.

        Raises:
            KeyManagementError: If decryption fails, authentication tag is invalid,
                                or the key version is not found.
        """
        pass

    @property
    @abstractmethod
    def current_version(self) -> str:
        """Return the current active KEK version identifier (e.g., 'v1')."""
        pass

    @abstractmethod
    def rotate_key(self, new_key: Optional[bytes] = None) -> str:
        """
        Rotate to a new master KEK version.

        Args:
            new_key: Optional 32-byte key for the new KEK. If backend generates keys
                     internally (e.g., Cloud KMS/HSM), this parameter may be None.

        Returns:
            The newly activated KEK version string (e.g., 'v2').

        Raises:
            KeyManagementError: If rotation fails or provided key material is invalid.
        """
        pass


class LocalKMSProvider(KMSProvider):
    """
    Thread-safe, in-memory KMS provider for development, testing, and edge nodes.

    Security Rationale:
        Simulates an external KMS / HSM boundary using AES-256-GCM.
        Maintains an internal versioned dictionary of KEKs to support key rotation drills.
        All encryption operations generate unique 96-bit nonces, ensuring standard
        GCM security guarantees.

    TODO: Production Cloud KMS / HSM Providers:
        - AWSKMSProvider: Encapsulates boto3 KMS Encrypt / Decrypt API calls.
        - GCPKMSProvider: Encapsulates google-cloud-kms KeyManagementServiceClient.
        - PKCS11KMSProvider: Direct hardware HSM integration via PyKCS11.
    """

    def __init__(
        self,
        initial_kek: Optional[bytes] = None,
        initial_version: str = "v1",
    ) -> None:
        """
        Initialize LocalKMSProvider with an initial KEK or generate one.

        Args:
            initial_kek: Optional 32-byte key for the master KEK. If None, generated
                         using os.urandom(32).
            initial_version: Version identifier for the initial key (default: 'v1').

        Raises:
            KeyManagementError: If initial_kek is provided but has invalid length or type.
        """
        self._lock = threading.RLock()
        self._keys: dict[str, bytes] = {}

        if initial_kek is None:
            kek = os.urandom(DEK_LENGTH_BYTES)
        else:
            if not isinstance(initial_kek, (bytes, bytearray)):
                raise KeyManagementError(
                    f"initial_kek must be bytes-like, got {type(initial_kek).__name__}"
                )
            if len(initial_kek) != DEK_LENGTH_BYTES:
                raise KeyManagementError(
                    f"Invalid initial KEK length: expected {DEK_LENGTH_BYTES} bytes, "
                    f"got {len(initial_kek)} bytes"
                )
            kek = bytes(initial_kek)

        self._keys[initial_version] = kek
        self._current_version = initial_version

        # Parse initial version number if in standard 'vN' format
        match = re.match(r"^v(\d+)$", initial_version)
        self._version_counter = int(match.group(1)) if match else 1

        logger.info(
            "LocalKMSProvider initialized with active KEK version=%s",
            self._current_version,
        )

    @property
    def current_version(self) -> str:
        """Return the current active KEK version identifier."""
        with self._lock:
            return self._current_version

    def get_key_versions(self) -> list[str]:
        """
        Return a list of all stored KEK version identifiers.

        Security Note:
            Only version strings are returned. Raw key material is never exposed.
        """
        with self._lock:
            return list(self._keys.keys())

    def has_version(self, version: str) -> bool:
        """Check whether a specific KEK version exists in the keystore."""
        with self._lock:
            return version in self._keys

    def rotate_key(self, new_key: Optional[bytes] = None) -> str:
        """
        Rotate to a new master KEK version.

        Security Rationale:
            Key rotation preserves existing KEKs so archived documents remain decryptable,
            while all subsequent DEK wrapping operations immediately use the new KEK version.

        Args:
            new_key: Optional 32-byte key. If None, generated via os.urandom.

        Returns:
            The new active version string (e.g., 'v2').

        Raises:
            KeyManagementError: If new_key is provided with incorrect length.
        """
        with self._lock:
            if new_key is None:
                kek = os.urandom(DEK_LENGTH_BYTES)
            else:
                if not isinstance(new_key, (bytes, bytearray)):
                    raise KeyManagementError(
                        f"new_key must be bytes-like, got {type(new_key).__name__}"
                    )
                if len(new_key) != DEK_LENGTH_BYTES:
                    raise KeyManagementError(
                        f"Invalid new KEK length: expected {DEK_LENGTH_BYTES} bytes, "
                        f"got {len(new_key)} bytes"
                    )
                kek = bytes(new_key)

            self._version_counter += 1
            new_version = f"v{self._version_counter}"

            # If version collision occurs with custom versions, find next unused
            while new_version in self._keys:
                self._version_counter += 1
                new_version = f"v{self._version_counter}"

            self._keys[new_version] = kek
            old_version = self._current_version
            self._current_version = new_version

            logger.info(
                "LocalKMSProvider rotated KEK from version=%s to version=%s (total versions: %d)",
                old_version,
                new_version,
                len(self._keys),
            )
            return new_version

    def encrypt(
        self,
        plaintext: bytes,
        key_version: Optional[str] = None,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Encrypt plaintext (e.g., a DEK) using AES-256-GCM under the designated KEK.

        Payload Format:
            [IV (12 bytes)] + [Ciphertext + GCM Auth Tag (variable)]

        Args:
            plaintext: Raw bytes to encrypt.
            key_version: KEK version to use. If None, uses the active current_version.
            associated_data: Optional additional authenticated data bound to ciphertext.

        Returns:
            Concatenated IV and GCM ciphertext bytes.

        Raises:
            KeyManagementError: If key version is invalid or encryption fails.
        """
        if not isinstance(plaintext, (bytes, bytearray)):
            raise KeyManagementError(
                f"Plaintext must be bytes-like, got {type(plaintext).__name__}"
            )

        with self._lock:
            version = key_version if key_version is not None else self._current_version
            kek = self._keys.get(version)
            if kek is None:
                raise KeyManagementError(
                    f"KEK version '{version}' not found in local keystore"
                )

        # Generate a strictly unique 96-bit IV for AES-GCM
        iv = os.urandom(IV_LENGTH_BYTES)

        try:
            aesgcm = AESGCM(kek)
            ciphertext_with_tag = aesgcm.encrypt(
                iv,
                bytes(plaintext),
                associated_data,
            )
        except Exception as exc:
            logger.error("LocalKMSProvider encryption failed under version=%s: %s", version, exc)
            raise KeyManagementError(
                f"KMS encryption failed under KEK version '{version}': {exc}",
                cause=exc,
            ) from exc

        # Return self-contained wrapped payload: IV + ciphertext (includes auth tag)
        return iv + ciphertext_with_tag

    def decrypt(
        self,
        ciphertext: bytes,
        key_version: Optional[str] = None,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt wrapped ciphertext using AES-256-GCM under the designated KEK.

        Args:
            ciphertext: Packed payload containing [12-byte IV] + [Ciphertext & Tag].
            key_version: KEK version to use. If None, uses active current_version.
            associated_data: Optional additional authenticated data to verify.

        Returns:
            Decrypted raw plaintext bytes.

        Raises:
            KeyManagementError: If ciphertext is malformed, version not found,
                                or authentication tag verification fails.
        """
        if not isinstance(ciphertext, (bytes, bytearray)):
            raise KeyManagementError(
                f"Ciphertext must be bytes-like, got {type(ciphertext).__name__}"
            )

        if len(ciphertext) < _MIN_WRAPPED_KEY_CIPHERTEXT_LENGTH:
            raise KeyManagementError(
                f"Ciphertext too short: expected at least {_MIN_WRAPPED_KEY_CIPHERTEXT_LENGTH} bytes "
                f"(IV + Auth Tag), got {len(ciphertext)} bytes"
            )

        with self._lock:
            version = key_version if key_version is not None else self._current_version
            kek = self._keys.get(version)
            if kek is None:
                raise KeyManagementError(
                    f"KEK version '{version}' not found in local keystore"
                )

        # Extract IV (first 12 bytes) and ciphertext with tag (remainder)
        iv = ciphertext[:IV_LENGTH_BYTES]
        actual_ciphertext = ciphertext[IV_LENGTH_BYTES:]

        try:
            aesgcm = AESGCM(kek)
            plaintext = aesgcm.decrypt(
                iv,
                actual_ciphertext,
                associated_data,
            )
        except InvalidTag as exc:
            logger.error(
                "LocalKMSProvider decryption failed under version=%s: authentication tag mismatch",
                version,
            )
            raise KeyManagementError(
                f"KMS decryption failed under KEK version '{version}': "
                "cryptographic authentication tag verification failed (data corrupted or key mismatch)",
                cause=exc,
            ) from exc
        except Exception as exc:
            logger.error("LocalKMSProvider decryption failed under version=%s: %s", version, exc)
            raise KeyManagementError(
                f"KMS decryption failed under KEK version '{version}': {exc}",
                cause=exc,
            ) from exc

        return plaintext


class KeyManager:
    """
    Core Key Manager service for SecureChain DMS (Module 5).

    Manages the cryptographic envelope encryption key hierarchy:
      - Generates per-document 256-bit Data Encryption Keys (DEKs)
      - Generates unique 96-bit AES-GCM Initialization Vectors (IVs)
      - Wraps DEKs under the master Key Encryption Key (KEK) via KMS
      - Unwraps DEKs on authorized court retrieval
      - Coordinates versioned master KEK rotations
      - Enforces strict key length and validation boundaries
    """

    def __init__(self, kms_provider: Optional[KMSProvider] = None) -> None:
        """
        Initialize KeyManager with a KMSProvider backend via dependency injection.

        Security Rationale:
            Decouples key lifecycle orchestration from the cryptographic hardware / cloud KMS
            implementation. In production environments, an enterprise HSM or Cloud KMS provider
            is injected to guarantee the master KEK never enters application RAM.
            For development, local edge nodes, and testing, LocalKMSProvider is used.

        Args:
            kms_provider: Concrete KMSProvider instance. If None, defaults to LocalKMSProvider.

        Raises:
            KeyManagementError: If kms_provider is provided but does not inherit from KMSProvider.
        """
        if kms_provider is None:
            self._kms_provider: KMSProvider = LocalKMSProvider()
        elif isinstance(kms_provider, KMSProvider):
            self._kms_provider = kms_provider
        else:
            raise KeyManagementError(
                f"Expected KMSProvider instance, got {type(kms_provider).__name__}"
            )

        logger.info(
            "KeyManager initialized with provider=%s (active KEK version=%s)",
            self._kms_provider.__class__.__name__,
            self._kms_provider.current_version,
        )

    @property
    def kms_provider(self) -> KMSProvider:
        """Return the underlying KMSProvider backend."""
        return self._kms_provider

    @property
    def current_kek_version(self) -> str:
        """Return the active master KEK version identifier."""
        return self._kms_provider.current_version

    def _validate_key_length(self, key: bytes, expected_length: int) -> None:
        """
        Validate that a cryptographic key buffer conforms to the expected byte length.

        Security Rationale:
            Prevents algorithmic degradation or cipher failure due to truncated or malformed
            keys (e.g., AES-256 requires exactly 32 bytes / 256 bits). Validating key lengths
            at all public and internal interfaces guarantees fail-closed defense against
            weak keys.

        Args:
            key: The raw key bytes to validate.
            expected_length: Expected key length in bytes.

        Raises:
            KeyManagementError: If key is not bytes-like or length does not match expected_length.
        """
        if key is None:
            raise KeyManagementError("Key cannot be None")

        if not isinstance(key, (bytes, bytearray)):
            raise KeyManagementError(
                f"Key must be bytes-like, got {type(key).__name__}"
            )

        if len(key) != expected_length:
            raise KeyManagementError(
                f"Invalid key length: expected {expected_length} bytes ({expected_length * 8} bits), "
                f"got {len(key)} bytes ({len(key) * 8} bits)"
            )

    def generate_dek(self) -> bytes:
        """
        Generate a random 256-bit (32-byte) Data Encryption Key (DEK).

        Security Rationale:
            Each digital evidence document uploaded to SecureChain DMS is encrypted with
            a unique DEK. Using the operating system's CSPRNG (`os.urandom`) ensures high
            entropy (CryptGenRandom/BCryptGenRandom on Windows, getrandom(2)/urandom on Linux).
            Per-document DEKs ensure compromise of one document never affects any other.

        Returns:
            32-byte cryptographically secure random Data Encryption Key.
        """
        dek = os.urandom(DEK_LENGTH_BYTES)
        logger.info("generate_dek: generated new 256-bit DEK")
        return dek

    def generate_iv(self) -> bytes:
        """
        Generate a random 96-bit (12-byte) Initialization Vector (IV) / nonce for AES-GCM.

        Security Rationale:
            NIST SP 800-38D mandates 96-bit nonces for AES-GCM to avoid GHASH computational
            overhead and collision risks. Reusing an IV with the same key under AES-GCM
            is catastrophic: it exposes the XOR of plaintexts and allows forgery of the
            authentication tag. A fresh, random IV MUST be generated for every encryption.

        Returns:
            12-byte cryptographically secure random Initialization Vector.
        """
        iv = os.urandom(IV_LENGTH_BYTES)
        logger.info("generate_iv: generated new 96-bit IV")
        return iv

    def wrap_dek(
        self,
        dek: bytes,
        document_id: str = "",
        associated_data: Optional[bytes] = None,
    ) -> WrappedKey:
        """
        Encrypt a Data Encryption Key (DEK) using the active master KEK.

        Security Rationale:
            Envelope encryption: The plaintext DEK encrypts the evidence payload and is
            immediately wrapped under the KEK. The plaintext DEK is never stored on disk.
            The resulting WrappedKey is stored in Vault 1 (Database), physically isolated
            from the encrypted blob stored in Vault 2 (Object Storage).

        Args:
            dek: Raw 32-byte Data Encryption Key to wrap.
            document_id: Optional document identifier associated with this DEK.
            associated_data: Optional authenticated data bound to the wrapped key.

        Returns:
            WrappedKey dataclass containing key_id, wrapped_dek bytes, kek_version,
            and document_id.

        Raises:
            KeyManagementError: If DEK length is invalid or KMS wrapping fails.
        """
        self._validate_key_length(dek, DEK_LENGTH_BYTES)

        key_id = str(uuid.uuid4())
        active_version = self._kms_provider.current_version

        logger.info(
            "wrap_dek: wrapping DEK key_id=%s under KEK version=%s (document_id=%s)",
            key_id,
            active_version,
            document_id or "unassigned",
        )

        wrapped_dek = self._kms_provider.encrypt(
            plaintext=dek,
            key_version=active_version,
            associated_data=associated_data,
        )

        return WrappedKey(
            key_id=key_id,
            wrapped_dek=wrapped_dek,
            kek_version=active_version,
            document_id=document_id,
        )

    def unwrap_dek(
        self,
        wrapped_key: WrappedKey,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """
        Decrypt a wrapped DEK back to plaintext using the appropriate KEK version.

        Security Rationale:
            Upon authorized court retrieval or integrity verification, the wrapped DEK
            is retrieved from Vault 1 and decrypted using the KEK version recorded when
            the document was originally sealed. Once unwrapped, the raw DEK should reside
            strictly in memory during decryption and subsequently be zeroed out.

        Args:
            wrapped_key: WrappedKey model containing the ciphertext and KEK version.
            associated_data: Optional authenticated data to verify against auth tag.

        Returns:
            Raw 32-byte plaintext Data Encryption Key.

        Raises:
            KeyManagementError: If wrapped_key is invalid, KEK version not found,
                                ciphertext corrupted, or auth tag verification fails.
        """
        if wrapped_key is None or not isinstance(wrapped_key, WrappedKey):
            raise KeyManagementError(
                f"Expected WrappedKey instance, got {type(wrapped_key).__name__ if wrapped_key is not None else 'None'}"
            )

        logger.info(
            "unwrap_dek: unwrapping DEK key_id=%s using KEK version=%s",
            wrapped_key.key_id,
            wrapped_key.kek_version,
        )

        raw_dek = self._kms_provider.decrypt(
            ciphertext=wrapped_key.wrapped_dek,
            key_version=wrapped_key.kek_version,
            associated_data=associated_data,
        )

        self._validate_key_length(raw_dek, DEK_LENGTH_BYTES)
        return raw_dek

    def rotate_kek(self, new_kek: Optional[bytes] = None) -> None:
        """
        Rotate the master Key Encryption Key (KEK).

        Security Rationale:
            Periodic master key rotation satisfies compliance mandates (NIST SP 800-57,
            ISO 27001). Rotating the master KEK does not necessitate re-encrypting the
            actual evidence files in Vault 2. Old KEK versions are retained in the KMS
            version map so previously sealed evidence remains admissible and verifiable.

        Args:
            new_kek: Optional 32-byte key for the new KEK. If None, 32 cryptographically
                     random bytes are automatically generated via CSPRNG.

        Raises:
            KeyManagementError: If new_kek is provided with invalid length or type,
                                or if rotation fails in the KMS provider.
        """
        if new_kek is not None:
            self._validate_key_length(new_kek, DEK_LENGTH_BYTES)

        old_version = self._kms_provider.current_version
        new_version = self._kms_provider.rotate_key(new_key=new_kek)

        logger.info(
            "rotate_kek: master KEK rotated from version=%s to version=%s",
            old_version,
            new_version,
        )

    def rewrap_dek(
        self,
        wrapped_key: WrappedKey,
        associated_data: Optional[bytes] = None,
    ) -> WrappedKey:
        """
        Re-encrypt a wrapped DEK under the current active KEK version without touching evidence blobs.

        Security Rationale:
            When retiring very old KEK versions, DEKs can be safely unwrapped using their
            original KEK and immediately re-wrapped under the newest active KEK.
            This updates the Vault 1 database record without requiring multi-gigabyte
            evidence blobs in Vault 2 to be downloaded or re-encrypted.

        Args:
            wrapped_key: The existing WrappedKey to re-wrap.
            associated_data: Optional authenticated data.

        Returns:
            A new WrappedKey encrypted under the latest active KEK version.

        Raises:
            KeyManagementError: If unwrapping or re-wrapping fails.
        """
        raw_dek = self.unwrap_dek(wrapped_key, associated_data=associated_data)
        dek_buffer = bytearray(raw_dek)

        try:
            new_wrapped_key = self.wrap_dek(
                dek=bytes(dek_buffer),
                document_id=wrapped_key.document_id,
                associated_data=associated_data,
            )
            logger.info(
                "rewrap_dek: re-wrapped DEK key_id=%s from KEK version=%s to version=%s",
                wrapped_key.key_id,
                wrapped_key.kek_version,
                new_wrapped_key.kek_version,
            )
            return new_wrapped_key
        finally:
            zero_buffer(dek_buffer)


__all__ = [
    "KeyManagementError",
    "KMSProvider",
    "LocalKMSProvider",
    "KeyManager",
    "zero_buffer",
]
