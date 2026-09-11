"""
Unit tests for SecureChain DMS Key Manager Service (Module 5).
==============================================================
Validates envelope encryption, key derivation, AES-256-GCM wrapping,
KEK versioning, key rotation, error handling, thread safety, and logging hygiene.
"""

from __future__ import annotations

import io
import logging
import os
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor

from securechain_security.key_manager import (
    KeyManagementError,
    KeyManager,
    KMSProvider,
    LocalKMSProvider,
    zero_buffer,
)
from securechain_security.models import (
    AUTH_TAG_LENGTH_BYTES,
    DEK_LENGTH_BYTES,
    IV_LENGTH_BYTES,
    WrappedKey,
)


class MockCloudKMSProvider(KMSProvider):
    """Mock KMS provider simulating an external Cloud KMS / HSM boundary."""

    def __init__(self) -> None:
        self._current_version = "cloud-v1"
        self._encrypt_calls = 0
        self._decrypt_calls = 0

    @property
    def current_version(self) -> str:
        return self._current_version

    def encrypt(
        self,
        plaintext: bytes,
        key_version: str | None = None,
        associated_data: bytes | None = None,
    ) -> bytes:
        self._encrypt_calls += 1
        # Simple deterministic mock ciphertext
        return b"MOCK_ENCRYPTED_" + plaintext

    def decrypt(
        self,
        ciphertext: bytes,
        key_version: str | None = None,
        associated_data: bytes | None = None,
    ) -> bytes:
        self._decrypt_calls += 1
        if not ciphertext.startswith(b"MOCK_ENCRYPTED_"):
            raise KeyManagementError("Mock decryption failure: header mismatch")
        return ciphertext[len(b"MOCK_ENCRYPTED_"):]

    def rotate_key(self, new_key: bytes | None = None) -> str:
        self._current_version = "cloud-v2"
        return self._current_version


class TestKeyManager(unittest.TestCase):
    """Test suite for KeyManager and LocalKMSProvider."""

    def setUp(self) -> None:
        self.km = KeyManager()

    def test_generate_dek_length_and_uniqueness(self) -> None:
        """DEK must be exactly 32 bytes (256 bits) and unique per generation."""
        dek1 = self.km.generate_dek()
        dek2 = self.km.generate_dek()

        self.assertIsInstance(dek1, bytes)
        self.assertEqual(len(dek1), DEK_LENGTH_BYTES)
        self.assertEqual(len(dek2), DEK_LENGTH_BYTES)
        self.assertNotEqual(dek1, dek2)

        # Statistical collision check over 500 samples
        deks = {self.km.generate_dek() for _ in range(500)}
        self.assertEqual(len(deks), 500)

    def test_generate_iv_length_and_uniqueness(self) -> None:
        """IV must be exactly 12 bytes (96 bits) and unique per operation."""
        iv1 = self.km.generate_iv()
        iv2 = self.km.generate_iv()

        self.assertIsInstance(iv1, bytes)
        self.assertEqual(len(iv1), IV_LENGTH_BYTES)
        self.assertEqual(len(iv2), IV_LENGTH_BYTES)
        self.assertNotEqual(iv1, iv2)

        # Statistical collision check over 500 samples
        ivs = {self.km.generate_iv() for _ in range(500)}
        self.assertEqual(len(ivs), 500)

    def test_validate_key_length(self) -> None:
        """_validate_key_length must pass for matching lengths and reject mismatches/types."""
        valid_key = os.urandom(32)
        # Should not raise
        self.km._validate_key_length(valid_key, 32)
        self.km._validate_key_length(bytearray(valid_key), 32)

        # Wrong lengths
        with self.assertRaises(KeyManagementError):
            self.km._validate_key_length(os.urandom(16), 32)

        with self.assertRaises(KeyManagementError):
            self.km._validate_key_length(os.urandom(64), 32)

        with self.assertRaises(KeyManagementError):
            self.km._validate_key_length(b"", 32)

        # Invalid types
        with self.assertRaises(KeyManagementError):
            self.km._validate_key_length("string-not-bytes", 32)  # type: ignore

        with self.assertRaises(KeyManagementError):
            self.km._validate_key_length(None, 32)  # type: ignore

    def test_wrap_and_unwrap_dek_roundtrip(self) -> None:
        """DEK wrapped by KEK must successfully unwrap to identical plaintext."""
        original_dek = self.km.generate_dek()
        document_id = "FIR-2026-MH-9812-EVID-01"

        wrapped_key = self.km.wrap_dek(original_dek, document_id=document_id)

        # Validate WrappedKey attributes
        self.assertIsInstance(wrapped_key, WrappedKey)
        self.assertEqual(wrapped_key.document_id, document_id)
        self.assertEqual(wrapped_key.kek_version, "v1")
        self.assertTrue(uuid.UUID(wrapped_key.key_id))
        self.assertIsInstance(wrapped_key.wrapped_dek, bytes)
        # Expected size: 12-byte IV + 32-byte DEK + 16-byte Auth Tag = 60 bytes
        self.assertEqual(
            len(wrapped_key.wrapped_dek),
            IV_LENGTH_BYTES + DEK_LENGTH_BYTES + AUTH_TAG_LENGTH_BYTES,
        )

        # Unwrap and verify equality
        unwrapped_dek = self.km.unwrap_dek(wrapped_key)
        self.assertEqual(unwrapped_dek, original_dek)

    def test_wrap_dek_invalid_length(self) -> None:
        """wrap_dek must reject invalid DEK sizes."""
        with self.assertRaises(KeyManagementError):
            self.km.wrap_dek(b"short-key")

        with self.assertRaises(KeyManagementError):
            self.km.wrap_dek(os.urandom(64))

    def test_unwrap_dek_tampered_ciphertext(self) -> None:
        """Tampering with wrapped ciphertext must trigger authentication tag mismatch."""
        original_dek = self.km.generate_dek()
        wrapped_key = self.km.wrap_dek(original_dek, document_id="DOC-TAMPER")

        # Mutate the last byte of ciphertext (part of GCM auth tag)
        tampered_bytes = bytearray(wrapped_key.wrapped_dek)
        tampered_bytes[-1] ^= 0xFF
        tampered_key = WrappedKey(
            key_id=wrapped_key.key_id,
            wrapped_dek=bytes(tampered_bytes),
            kek_version=wrapped_key.kek_version,
            document_id=wrapped_key.document_id,
        )

        with self.assertRaises(KeyManagementError) as ctx:
            self.km.unwrap_dek(tampered_key)
        self.assertIn("authentication tag", str(ctx.exception).lower())

    def test_unwrap_dek_truncated_ciphertext(self) -> None:
        """Ciphertext shorter than IV + Tag must fail validation."""
        short_key = WrappedKey(
            key_id="short-id",
            wrapped_dek=b"too-short",
            kek_version="v1",
            document_id="DOC-SHORT",
        )
        with self.assertRaises(KeyManagementError) as ctx:
            self.km.unwrap_dek(short_key)
        self.assertIn("too short", str(ctx.exception).lower())

    def test_unwrap_dek_invalid_wrapped_key_type(self) -> None:
        """unwrap_dek must reject non-WrappedKey arguments."""
        with self.assertRaises(KeyManagementError):
            self.km.unwrap_dek(None)  # type: ignore

        with self.assertRaises(KeyManagementError):
            self.km.unwrap_dek("not-a-wrapped-key")  # type: ignore

    def test_rotate_kek_auto_generated(self) -> None:
        """Key rotation increments version and retains ability to unwrap older keys."""
        self.assertEqual(self.km.current_kek_version, "v1")

        # Seal document under v1
        dek_v1 = self.km.generate_dek()
        wrapped_v1 = self.km.wrap_dek(dek_v1, document_id="DOC-V1")
        self.assertEqual(wrapped_v1.kek_version, "v1")

        # Rotate KEK (generates v2)
        self.km.rotate_kek()
        self.assertEqual(self.km.current_kek_version, "v2")

        # Seal document under v2
        dek_v2 = self.km.generate_dek()
        wrapped_v2 = self.km.wrap_dek(dek_v2, document_id="DOC-V2")
        self.assertEqual(wrapped_v2.kek_version, "v2")

        # Verify BOTH documents can still be unwrapped
        self.assertEqual(self.km.unwrap_dek(wrapped_v1), dek_v1)
        self.assertEqual(self.km.unwrap_dek(wrapped_v2), dek_v2)

        # Rotate again (generates v3)
        self.km.rotate_kek()
        self.assertEqual(self.km.current_kek_version, "v3")

        # All historical keys still unwrap correctly
        self.assertEqual(self.km.unwrap_dek(wrapped_v1), dek_v1)
        self.assertEqual(self.km.unwrap_dek(wrapped_v2), dek_v2)

    def test_rotate_kek_with_explicit_key(self) -> None:
        """Explicitly provided new KEK must be accepted and validated."""
        new_kek = os.urandom(DEK_LENGTH_BYTES)
        self.km.rotate_kek(new_kek=new_kek)
        self.assertEqual(self.km.current_kek_version, "v2")

        dek = self.km.generate_dek()
        wrapped = self.km.wrap_dek(dek, document_id="DOC-EXPLICIT")
        self.assertEqual(wrapped.kek_version, "v2")
        self.assertEqual(self.km.unwrap_dek(wrapped), dek)

    def test_rotate_kek_invalid_key_length(self) -> None:
        """rotate_kek must reject invalid key lengths."""
        with self.assertRaises(KeyManagementError):
            self.km.rotate_kek(new_kek=b"invalid-16-bytes")

    def test_unwrap_dek_unknown_version(self) -> None:
        """Unwrapping with a non-existent KEK version must raise KeyManagementError."""
        dek = self.km.generate_dek()
        wrapped = self.km.wrap_dek(dek, document_id="DOC-01")
        corrupted_version_key = WrappedKey(
            key_id=wrapped.key_id,
            wrapped_dek=wrapped.wrapped_dek,
            kek_version="v9999",
            document_id=wrapped.document_id,
        )

        with self.assertRaises(KeyManagementError) as ctx:
            self.km.unwrap_dek(corrupted_version_key)
        self.assertIn("v9999", str(ctx.exception))

    def test_rewrap_dek(self) -> None:
        """rewrap_dek should transition a DEK from an old KEK to the current active KEK."""
        dek = self.km.generate_dek()
        wrapped_v1 = self.km.wrap_dek(dek, document_id="DOC-REWRAP")
        self.assertEqual(wrapped_v1.kek_version, "v1")

        # Rotate to v2
        self.km.rotate_kek()
        self.assertEqual(self.km.current_kek_version, "v2")

        # Re-wrap
        wrapped_v2 = self.km.rewrap_dek(wrapped_v1)
        self.assertEqual(wrapped_v2.kek_version, "v2")
        self.assertEqual(wrapped_v2.document_id, "DOC-REWRAP")

        # Both unwrap to the exact same plaintext DEK
        self.assertEqual(self.km.unwrap_dek(wrapped_v1), dek)
        self.assertEqual(self.km.unwrap_dek(wrapped_v2), dek)

    def test_kms_associated_data_binding(self) -> None:
        """Associated authenticated data (AAD) must match during unwrapping if specified."""
        dek = self.km.generate_dek()
        aad = b"FIR-2026-DL-001:VER-1.0"

        wrapped = self.km.wrap_dek(dek, document_id="DOC-AAD", associated_data=aad)

        # Unwrapping with matching AAD succeeds
        unwrapped = self.km.unwrap_dek(wrapped, associated_data=aad)
        self.assertEqual(unwrapped, dek)

        # Unwrapping with altered AAD fails auth check
        with self.assertRaises(KeyManagementError):
            self.km.unwrap_dek(wrapped, associated_data=b"TAMPERED-AAD")

    def test_dependency_injection_custom_kms(self) -> None:
        """Custom KMS provider can be injected cleanly."""
        cloud_kms = MockCloudKMSProvider()
        km = KeyManager(kms_provider=cloud_kms)

        self.assertIs(km.kms_provider, cloud_kms)
        self.assertEqual(km.current_kek_version, "cloud-v1")

        dek = km.generate_dek()
        wrapped = km.wrap_dek(dek, document_id="DOC-CLOUD")
        self.assertEqual(wrapped.kek_version, "cloud-v1")
        self.assertEqual(cloud_kms._encrypt_calls, 1)

        unwrapped = km.unwrap_dek(wrapped)
        self.assertEqual(unwrapped, dek)
        self.assertEqual(cloud_kms._decrypt_calls, 1)

        km.rotate_kek()
        self.assertEqual(km.current_kek_version, "cloud-v2")

    def test_init_invalid_provider_type(self) -> None:
        """KeyManager rejects provider that is not a KMSProvider."""
        with self.assertRaises(KeyManagementError):
            KeyManager(kms_provider="not-a-provider")  # type: ignore

    def test_local_kms_provider_initial_kek_validation(self) -> None:
        """LocalKMSProvider validates initial_kek length and type."""
        # Valid custom initial KEK
        custom_kek = os.urandom(32)
        provider = LocalKMSProvider(initial_kek=custom_kek, initial_version="v5")
        self.assertEqual(provider.current_version, "v5")
        self.assertTrue(provider.has_version("v5"))
        self.assertEqual(provider.get_key_versions(), ["v5"])

        # Invalid initial KEK length
        with self.assertRaises(KeyManagementError):
            LocalKMSProvider(initial_kek=b"short-kek")

        # Invalid type
        with self.assertRaises(KeyManagementError):
            LocalKMSProvider(initial_kek=12345)  # type: ignore

    def test_zero_buffer(self) -> None:
        """zero_buffer must overwrite bytearray with zeros."""
        buf = bytearray(b"SENSITIVE_KEY_BYTES_TO_PURGE_99")
        self.assertTrue(any(b != 0 for b in buf))
        zero_buffer(buf)
        self.assertTrue(all(b == 0 for b in buf))

    def test_thread_safety_concurrent_wrapping(self) -> None:
        """Multiple threads concurrently wrapping and unwrapping keys must not corrupt state."""
        km = KeyManager()

        def worker(worker_id: int) -> bool:
            dek = km.generate_dek()
            doc_id = f"CONCURRENT-DOC-{worker_id}"
            wrapped = km.wrap_dek(dek, document_id=doc_id)
            unwrapped = km.unwrap_dek(wrapped)
            return unwrapped == dek

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(worker, i) for i in range(50)]
            results = [f.result() for f in futures]

        self.assertTrue(all(results))

    def test_logging_no_key_material(self) -> None:
        """Log records must NEVER contain raw key material or hex-encoded secrets."""
        logger = logging.getLogger("securechain_security.key_manager")
        captured_records: list[logging.LogRecord] = []

        class ListHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured_records.append(record)

        handler = ListHandler()
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        try:
            dek = self.km.generate_dek()
            dek_hex = dek.hex()
            iv = self.km.generate_iv()
            iv_hex = iv.hex()
            wrapped = self.km.wrap_dek(dek, document_id="DOC-LOG-TEST")
            self.km.unwrap_dek(wrapped)
            self.km.rotate_kek()

            self.assertGreater(len(captured_records), 0)
            for record in captured_records:
                msg = record.getMessage()
                # Ensure raw DEK hex representation is nowhere in logs
                self.assertNotIn(dek_hex, msg)
                self.assertNotIn(iv_hex, msg)
        finally:
            logger.removeHandler(handler)


if __name__ == "__main__":
    unittest.main()
