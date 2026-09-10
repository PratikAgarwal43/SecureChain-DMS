"""
Unit tests for SecureChain DMS AES-256-GCM Encryption Service (Module 4).
=========================================================================
Validates AES-256-GCM authenticated envelope encryption, AAD identity binding,
tamper detection, IV uniqueness, memory zeroing hygiene, large payload handling,
streaming chunked reads, KEK rotation support, thread safety, and log cleanliness.
"""

from __future__ import annotations

import io
import logging
import os
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import MagicMock, patch

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from securechain_security.encryption_service import (
    CryptoError,
    DecryptionError,
    EncryptionError,
    EncryptionService,
)
from securechain_security.hash_service import HashService
from securechain_security.key_manager import KeyManager, KMSProvider, LocalKMSProvider
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


class TestEncryptionService(unittest.TestCase):
    """Test suite for AES-256-GCM EncryptionService."""

    def setUp(self) -> None:
        """Set up fresh KeyManager, HashService, and EncryptionService instances."""
        self.kms_provider = LocalKMSProvider(initial_version="v1")
        self.key_manager = KeyManager(kms_provider=self.kms_provider)
        self.hash_service = HashService()
        self.service = EncryptionService(
            key_manager=self.key_manager,
            hash_service=self.hash_service,
        )

        self.sample_document_id = "DOC-FIR-2026-00123"
        self.sample_case_id = "CR-MH-2026-889"
        self.sample_version = "1.0"
        self.sample_plaintext = (
            b"First Information Report (FIR) under Section 154 CrPC / Bharatiya Nagarik "
            b"Suraksha Sanhita (BNSS), 2023. Seizure of digital storage media at crime scene."
        )

    # -----------------------------------------------------------------------
    # Initialization & Properties
    # -----------------------------------------------------------------------

    def test_default_initialization(self) -> None:
        """EncryptionService initializes with default dependencies if None are supplied."""
        service = EncryptionService()
        self.assertIsInstance(service.key_manager, KeyManager)
        self.assertIsInstance(service.hash_service, HashService)

    def test_dependency_injection(self) -> None:
        """EncryptionService honors injected KeyManager and HashService."""
        self.assertIs(self.service.key_manager, self.key_manager)
        self.assertIs(self.service.hash_service, self.hash_service)

    # -----------------------------------------------------------------------
    # AAD Construction
    # -----------------------------------------------------------------------

    def test_build_aad_format(self) -> None:
        """build_aad returns canonical UTF-8 bytes binding doc_id, case_id, and version."""
        aad = EncryptionService.build_aad("DOC-1", "CASE-A", "1.0")
        self.assertEqual(aad, b"DOC-1:CASE-A:1.0")

    def test_build_aad_validation(self) -> None:
        """build_aad raises EncryptionError on invalid or empty parameters."""
        with self.assertRaises(EncryptionError):
            EncryptionService.build_aad("", "CASE-A", "1.0")
        with self.assertRaises(EncryptionError):
            EncryptionService.build_aad("DOC-1", "", "1.0")
        with self.assertRaises(EncryptionError):
            EncryptionService.build_aad("DOC-1", "CASE-A", "")
        with self.assertRaises(EncryptionError):
            EncryptionService.build_aad(None, "CASE-A", "1.0")  # type: ignore

    # -----------------------------------------------------------------------
    # Encrypt / Decrypt Round-Trip
    # -----------------------------------------------------------------------

    def test_encrypt_decrypt_round_trip(self) -> None:
        """Full encrypt and decrypt cycle successfully recovers plaintext evidence."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
            version=self.sample_version,
            officer_id="INSPECTOR-SHARMA-DSC-4401",
        )

        # Verify EncryptionResult structure
        self.assertEqual(enc_res.document_id, self.sample_document_id)
        self.assertEqual(enc_res.case_id, self.sample_case_id)
        self.assertEqual(enc_res.version, self.sample_version)
        self.assertEqual(enc_res.algorithm, ENCRYPTION_ALGORITHM)
        self.assertEqual(len(enc_res.iv), IV_LENGTH_BYTES)
        # Ciphertext must contain plaintext + 16-byte auth tag
        self.assertEqual(len(enc_res.ciphertext), len(self.sample_plaintext) + AUTH_TAG_LENGTH_BYTES)
        self.assertIsInstance(enc_res.wrapped_dek, bytes)
        self.assertEqual(enc_res.aad, b"DOC-FIR-2026-00123:CR-MH-2026-889:1.0")
        self.assertIsNotNone(enc_res.wrapped_key)
        self.assertIsNotNone(enc_res.doc_hash)

        # Decrypt using WrappedKey object
        assert enc_res.wrapped_key is not None
        dec_res = self.service.decrypt_document(
            ciphertext=enc_res.ciphertext,
            iv=enc_res.iv,
            wrapped_dek=enc_res.wrapped_key,
            aad=enc_res.aad,
            expected_doc_hash=enc_res.doc_hash,
        )

        # Verify DecryptionResult structure
        self.assertEqual(dec_res.document_id, self.sample_document_id)
        self.assertEqual(dec_res.plaintext, self.sample_plaintext)
        self.assertTrue(dec_res.integrity_verified)
        self.assertEqual(dec_res.doc_hash, enc_res.doc_hash)

    def test_decrypt_with_raw_bytes_wrapped_dek(self) -> None:
        """decrypt_document accepts raw bytes for wrapped_dek parameter."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )

        dec_res = self.service.decrypt_document(
            ciphertext=enc_res.ciphertext,
            iv=enc_res.iv,
            wrapped_dek=enc_res.wrapped_dek,  # Raw bytes
            aad=enc_res.aad,
            expected_doc_hash=enc_res.doc_hash or "",
        )

        self.assertEqual(dec_res.plaintext, self.sample_plaintext)
        self.assertTrue(dec_res.integrity_verified)

    def test_decrypt_result_convenience_helper(self) -> None:
        """decrypt_result helper unpacks EncryptionResult seamlessly."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )

        dec_res = self.service.decrypt_result(enc_res)
        self.assertEqual(dec_res.plaintext, self.sample_plaintext)
        self.assertTrue(dec_res.integrity_verified)

    def test_empty_plaintext_encryption(self) -> None:
        """AES-GCM encrypts 0-byte payload, returning a 16-byte auth tag that decrypts back to b''."""
        enc_res = self.service.encrypt_document(
            plaintext=b"",
            document_id="DOC-EMPTY",
            case_id="CASE-EMPTY",
        )
        self.assertEqual(len(enc_res.ciphertext), AUTH_TAG_LENGTH_BYTES)
        dec_res = self.service.decrypt_result(enc_res)
        self.assertEqual(dec_res.plaintext, b"")
        self.assertTrue(dec_res.integrity_verified)

    # -----------------------------------------------------------------------
    # AAD Mismatch Detection (Swap Attacks)
    # -----------------------------------------------------------------------

    def test_aad_tampering_case_id_mismatch(self) -> None:
        """Tampering with case_id in AAD triggers GCM auth tag failure."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id="CASE-GENUINE",
        )

        # Adversary attempts to attribute evidence to a different case
        tampered_aad = EncryptionService.build_aad(
            document_id=self.sample_document_id,
            case_id="CASE-FABRICATED",
            version="1.0",
        )

        with self.assertRaises(DecryptionError) as ctx:
            self.service.decrypt_document(
                ciphertext=enc_res.ciphertext,
                iv=enc_res.iv,
                wrapped_dek=enc_res.wrapped_key,  # type: ignore
                aad=tampered_aad,
            )
        self.assertIn("authentication tag verification failed", str(ctx.exception).lower())

    def test_aad_tampering_document_id_mismatch(self) -> None:
        """Tampering with document_id in AAD triggers GCM auth tag failure."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id="DOC-ORIGINAL-001",
            case_id=self.sample_case_id,
        )

        tampered_aad = EncryptionService.build_aad(
            document_id="DOC-SWAPPED-002",
            case_id=self.sample_case_id,
            version="1.0",
        )

        with self.assertRaises(DecryptionError):
            self.service.decrypt_document(
                ciphertext=enc_res.ciphertext,
                iv=enc_res.iv,
                wrapped_dek=enc_res.wrapped_key,  # type: ignore
                aad=tampered_aad,
            )

    def test_aad_tampering_version_mismatch(self) -> None:
        """Tampering with version string in AAD triggers GCM auth tag failure (rollback defense)."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
            version="1.1",  # Amended version
        )

        # Adversary attempts to present V1.1 as original V1.0
        tampered_aad = EncryptionService.build_aad(
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
            version="1.0",
        )

        with self.assertRaises(DecryptionError):
            self.service.decrypt_document(
                ciphertext=enc_res.ciphertext,
                iv=enc_res.iv,
                wrapped_dek=enc_res.wrapped_key,  # type: ignore
                aad=tampered_aad,
            )

    # -----------------------------------------------------------------------
    # Ciphertext Tampering Detection (GCM Auth Tag Failure)
    # -----------------------------------------------------------------------

    def test_ciphertext_single_bit_flip_tampering(self) -> None:
        """Flipping a single bit in ciphertext payload triggers GCM tag verification failure."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )

        # Corrupt 1 byte in the middle of ciphertext
        corrupted = bytearray(enc_res.ciphertext)
        corrupted[5] ^= 0x01

        with self.assertRaises(DecryptionError) as ctx:
            self.service.decrypt_document(
                ciphertext=bytes(corrupted),
                iv=enc_res.iv,
                wrapped_dek=enc_res.wrapped_key,  # type: ignore
                aad=enc_res.aad,
            )
        self.assertIn("authentication tag verification failed", str(ctx.exception).lower())

    def test_auth_tag_tampering(self) -> None:
        """Corrupting the 16-byte GCM authentication tag at the end of ciphertext fails decryption."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )

        # Corrupt the very last byte (part of the 16-byte GCM tag)
        corrupted = bytearray(enc_res.ciphertext)
        corrupted[-1] ^= 0xFF

        with self.assertRaises(DecryptionError):
            self.service.decrypt_document(
                ciphertext=bytes(corrupted),
                iv=enc_res.iv,
                wrapped_dek=enc_res.wrapped_key,  # type: ignore
                aad=enc_res.aad,
            )

    def test_iv_tampering(self) -> None:
        """Altering the 12-byte IV causes AES-GCM decryption to fail authentication."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )

        tampered_iv = bytearray(enc_res.iv)
        tampered_iv[0] ^= 0x01

        with self.assertRaises(DecryptionError):
            self.service.decrypt_document(
                ciphertext=enc_res.ciphertext,
                iv=bytes(tampered_iv),
                wrapped_dek=enc_res.wrapped_key,  # type: ignore
                aad=enc_res.aad,
            )

    def test_invalid_iv_length(self) -> None:
        """Passing an IV that is not exactly 12 bytes (96 bits) is rejected immediately."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )

        with self.assertRaises(DecryptionError) as ctx:
            self.service.decrypt_document(
                ciphertext=enc_res.ciphertext,
                iv=b"short_iv",  # 8 bytes
                wrapped_dek=enc_res.wrapped_key,  # type: ignore
                aad=enc_res.aad,
            )
        self.assertIn("invalid iv length", str(ctx.exception).lower())

    def test_truncated_ciphertext_rejected(self) -> None:
        """Ciphertexts shorter than 16 bytes (auth tag length) are rejected before cipher execution."""
        with self.assertRaises(DecryptionError) as ctx:
            self.service.decrypt_document(
                ciphertext=b"too_short",  # 9 bytes < 16 bytes
                iv=os.urandom(12),
                wrapped_dek=b"dummy_wrapped_key",
                aad=b"aad",
            )
        self.assertIn("too short", str(ctx.exception).lower())

    # -----------------------------------------------------------------------
    # Post-Decryption Hash Integrity Verification
    # -----------------------------------------------------------------------

    def test_integrity_verification_success(self) -> None:
        """When expected_doc_hash matches, integrity_verified is True."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )
        dec_res = self.service.decrypt_document(
            ciphertext=enc_res.ciphertext,
            iv=enc_res.iv,
            wrapped_dek=enc_res.wrapped_key,  # type: ignore
            aad=enc_res.aad,
            expected_doc_hash=enc_res.doc_hash or "",
        )
        self.assertTrue(dec_res.integrity_verified)

    def test_integrity_verification_mismatch_non_strict(self) -> None:
        """When expected_doc_hash mismatches in non-strict mode, integrity_verified is False."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )
        fake_hash = "0" * 64
        dec_res = self.service.decrypt_document(
            ciphertext=enc_res.ciphertext,
            iv=enc_res.iv,
            wrapped_dek=enc_res.wrapped_key,  # type: ignore
            aad=enc_res.aad,
            expected_doc_hash=fake_hash,
            strict_integrity=False,
        )
        self.assertFalse(dec_res.integrity_verified)
        self.assertEqual(dec_res.plaintext, self.sample_plaintext)

    def test_integrity_verification_mismatch_strict(self) -> None:
        """When expected_doc_hash mismatches in strict mode, DecryptionError is raised."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id=self.sample_document_id,
            case_id=self.sample_case_id,
        )
        fake_hash = "0" * 64
        with self.assertRaises(DecryptionError) as ctx:
            self.service.decrypt_document(
                ciphertext=enc_res.ciphertext,
                iv=enc_res.iv,
                wrapped_dek=enc_res.wrapped_key,  # type: ignore
                aad=enc_res.aad,
                expected_doc_hash=fake_hash,
                strict_integrity=True,
            )
        self.assertIn("integrity verification failed", str(ctx.exception).lower())

    # -----------------------------------------------------------------------
    # IV Uniqueness Across Multiple Encryptions
    # -----------------------------------------------------------------------

    def test_iv_uniqueness_across_encryptions(self) -> None:
        """Every call to encrypt_document generates a strictly unique 96-bit IV."""
        num_iterations = 100
        ivs: set[bytes] = set()
        ciphertexts: set[bytes] = set()

        for _ in range(num_iterations):
            res = self.service.encrypt_document(
                plaintext=self.sample_plaintext,
                document_id=self.sample_document_id,
                case_id=self.sample_case_id,
            )
            ivs.add(res.iv)
            ciphertexts.add(res.ciphertext)

        # All 100 IVs must be unique
        self.assertEqual(len(ivs), num_iterations)
        # All 100 ciphertexts must be unique even though plaintext is identical
        self.assertEqual(len(ciphertexts), num_iterations)

    # -----------------------------------------------------------------------
    # Memory Zeroing Verification
    # -----------------------------------------------------------------------

    def test_dek_memory_zeroed_after_encryption(self) -> None:
        """The SecureBuffer holding the plaintext DEK is reliably wiped and zeroed after encryption."""
        captured_buffers: list[SecureBuffer] = []
        original_init = SecureBuffer.__init__

        def spy_init(buf_self: SecureBuffer, *args: Any, **kwargs: Any) -> None:
            original_init(buf_self, *args, **kwargs)
            captured_buffers.append(buf_self)

        with patch.object(SecureBuffer, "__init__", spy_init):
            enc_res = self.service.encrypt_document(
                plaintext=self.sample_plaintext,
                document_id="DOC-ZERO-TEST",
                case_id="CASE-ZERO-TEST",
            )

        # SecureBuffer should have been created and exited
        self.assertGreaterEqual(len(captured_buffers), 1)
        for buf in captured_buffers:
            self.assertTrue(buf.is_wiped, "SecureBuffer was not marked wiped")
            self.assertTrue(
                all(b == 0 for b in buf._buffer),
                "SecureBuffer backing memory was not zeroed",
            )

    def test_dek_memory_zeroed_after_decryption(self) -> None:
        """The SecureBuffer holding the unwrapped DEK is reliably wiped and zeroed after decryption."""
        enc_res = self.service.encrypt_document(
            plaintext=self.sample_plaintext,
            document_id="DOC-ZERO-DEC-TEST",
            case_id="CASE-ZERO-DEC-TEST",
        )

        captured_buffers: list[SecureBuffer] = []
        original_init = SecureBuffer.__init__

        def spy_init(buf_self: SecureBuffer, *args: Any, **kwargs: Any) -> None:
            original_init(buf_self, *args, **kwargs)
            captured_buffers.append(buf_self)

        with patch.object(SecureBuffer, "__init__", spy_init):
            self.service.decrypt_result(enc_res)

        self.assertGreaterEqual(len(captured_buffers), 1)
        for buf in captured_buffers:
            self.assertTrue(buf.is_wiped)
            self.assertTrue(all(b == 0 for b in buf._buffer))

    # -----------------------------------------------------------------------
    # Large Payload Handling & Streaming
    # -----------------------------------------------------------------------

    def test_large_payload_in_memory(self) -> None:
        """encrypt_document and decrypt_document handle multi-megabyte payloads correctly."""
        # 4 MB of pseudorandom forensic payload
        large_plaintext = os.urandom(4 * 1024 * 1024)

        enc_res = self.service.encrypt_document(
            plaintext=large_plaintext,
            document_id="DOC-CCTV-FOOTAGE-4MB",
            case_id="CASE-MAJOR-CRIME",
        )

        self.assertEqual(len(enc_res.ciphertext), len(large_plaintext) + AUTH_TAG_LENGTH_BYTES)

        dec_res = self.service.decrypt_result(enc_res)
        self.assertEqual(dec_res.plaintext, large_plaintext)
        self.assertTrue(dec_res.integrity_verified)

    def test_encrypt_document_streaming_round_trip(self) -> None:
        """encrypt_document_streaming reads chunked stream and produces valid EncryptionResult."""
        large_content = os.urandom(512 * 1024)  # 512 KB
        stream = io.BytesIO(large_content)

        enc_res = self.service.encrypt_document_streaming(
            file_stream=stream,
            document_id="DOC-STREAM-TEST",
            case_id="CASE-STREAM-TEST",
            version="1.0",
            chunk_size=32768,  # 32 KB chunks
        )

        self.assertEqual(len(enc_res.ciphertext), len(large_content) + AUTH_TAG_LENGTH_BYTES)
        self.assertEqual(enc_res.doc_hash, self.hash_service.hash_bytes(large_content))

        # Decrypt streaming output
        dec_res = self.service.decrypt_result(enc_res)
        self.assertEqual(dec_res.plaintext, large_content)
        self.assertTrue(dec_res.integrity_verified)

    def test_encrypt_document_streaming_zeroes_plaintext_buffer(self) -> None:
        """encrypt_document_streaming zeroes the accumulated plaintext buffer upon completion."""
        zeroed_buffers: list[bytearray] = []
        original_secure_zero = secure_zero

        def spy_secure_zero(buf: bytearray) -> None:
            zeroed_buffers.append(bytearray(buf))  # capture snapshot before wipe
            original_secure_zero(buf)

        stream = io.BytesIO(b"CONFIDENTIAL_SURVEILLANCE_TRANSCRIPT_1234567890")
        with patch("securechain_security.encryption_service.secure_zero", spy_secure_zero):
            self.service.encrypt_document_streaming(
                file_stream=stream,
                document_id="DOC-STREAM-ZERO",
                case_id="CASE-STREAM-ZERO",
            )

        self.assertGreaterEqual(len(zeroed_buffers), 1)
        self.assertIn(b"CONFIDENTIAL_SURVEILLANCE_TRANSCRIPT_1234567890", zeroed_buffers[0])

    def test_encrypt_document_streaming_invalid_stream(self) -> None:
        """encrypt_document_streaming raises EncryptionError on invalid file_stream."""
        with self.assertRaises(EncryptionError):
            self.service.encrypt_document_streaming(
                file_stream="not-a-stream",  # type: ignore
                document_id="DOC-ERR",
                case_id="CASE-ERR",
            )

    def test_encrypt_document_streaming_invalid_chunk_size(self) -> None:
        """encrypt_document_streaming raises EncryptionError when chunk_size <= 0."""
        stream = io.BytesIO(b"data")
        with self.assertRaises(EncryptionError):
            self.service.encrypt_document_streaming(
                file_stream=stream,
                document_id="DOC-ERR",
                case_id="CASE-ERR",
                chunk_size=0,
            )

    # -----------------------------------------------------------------------
    # Master KEK Rotation Support
    # -----------------------------------------------------------------------

    def test_kek_rotation_backward_compatibility(self) -> None:
        """Documents encrypted before KEK rotation remain decryptable under historical KEK versions."""
        # 1. Encrypt document under active KEK v1
        enc_doc1 = self.service.encrypt_document(
            plaintext=b"Document 1 sealed under KEK v1",
            document_id="DOC-HISTORICAL-01",
            case_id="CASE-ROTATION-TEST",
        )
        self.assertEqual(enc_doc1.wrapped_key.kek_version, "v1")  # type: ignore

        # 2. Rotate master KEK to v2
        self.key_manager.rotate_kek()
        self.assertEqual(self.key_manager.current_kek_version, "v2")

        # 3. Encrypt document under active KEK v2
        enc_doc2 = self.service.encrypt_document(
            plaintext=b"Document 2 sealed under KEK v2",
            document_id="DOC-NEW-02",
            case_id="CASE-ROTATION-TEST",
        )
        self.assertEqual(enc_doc2.wrapped_key.kek_version, "v2")  # type: ignore

        # 4. Decrypt both documents: v1 historical record and v2 current record must both succeed
        dec_doc1 = self.service.decrypt_result(enc_doc1)
        self.assertEqual(dec_doc1.plaintext, b"Document 1 sealed under KEK v1")
        self.assertTrue(dec_doc1.integrity_verified)

        dec_doc2 = self.service.decrypt_result(enc_doc2)
        self.assertEqual(dec_doc2.plaintext, b"Document 2 sealed under KEK v2")
        self.assertTrue(dec_doc2.integrity_verified)

    # -----------------------------------------------------------------------
    # Logging Hygiene (Zero Leakage)
    # -----------------------------------------------------------------------

    def test_logging_no_plaintext_or_secrets_leaked(self) -> None:
        """Log records must NEVER contain plaintext, raw DEKs, or ciphertext bytes."""
        logger = logging.getLogger("securechain_security.encryption_service")
        captured_records: list[logging.LogRecord] = []

        class ListHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured_records.append(record)

        handler = ListHandler()
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        secret_marker = "HIGHLY_CLASSIFIED_TOP_SECRET_FORENSIC_EVIDENCE_9999"
        secret_bytes = secret_marker.encode("utf-8")

        try:
            enc_res = self.service.encrypt_document(
                plaintext=secret_bytes,
                document_id="DOC-LOG-CLEAN",
                case_id="CASE-LOG-CLEAN",
            )
            self.service.decrypt_result(enc_res)
        finally:
            logger.removeHandler(handler)

        for record in captured_records:
            msg = record.getMessage()
            self.assertNotIn(
                secret_marker,
                msg,
                f"Plaintext secret was leaked in log message: {msg}",
            )
            self.assertNotIn(
                enc_res.ciphertext.hex(),
                msg,
                "Ciphertext was leaked in log message",
            )

    # -----------------------------------------------------------------------
    # Concurrency / Thread Safety
    # -----------------------------------------------------------------------

    def test_concurrent_encryption_and_decryption(self) -> None:
        """Multiple threads concurrently encrypting and decrypting must not corrupt state."""
        def worker(worker_id: int) -> bool:
            payload = f"Payload content for worker {worker_id} - test thread safety".encode("utf-8")
            doc_id = f"DOC-CONCURRENT-{worker_id}"
            case_id = f"CASE-CONCURRENT-{worker_id % 5}"

            enc_res = self.service.encrypt_document(
                plaintext=payload,
                document_id=doc_id,
                case_id=case_id,
            )
            dec_res = self.service.decrypt_result(enc_res)
            return dec_res.plaintext == payload and dec_res.integrity_verified

        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(worker, i) for i in range(40)]
            results = [f.result() for f in futures]

        self.assertTrue(all(results))


if __name__ == "__main__":
    unittest.main()
