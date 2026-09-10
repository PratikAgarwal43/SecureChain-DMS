"""
Unit tests for SecureChain DMS Two-Vault Router (Module 6).
===========================================================
Validates the physical and cryptographic separation between Vault 1 (Database)
and Vault 2 (Object Storage), upload pipeline, retrieval pipeline, round-trip
integrity, multi-document case chains, and quorum-gated amendments.
"""

from __future__ import annotations

import logging
import os
import unittest
from unittest.mock import patch

from securechain_security.chain_engine import ChainEngine
from securechain_security.encryption_service import EncryptionService
from securechain_security.key_manager import KeyManager, LocalKMSProvider
from securechain_security.models import (
    IV_LENGTH_BYTES,
    VaultPackage,
    VaultTarget,
)
from securechain_security.vault_router import VaultRouter, VaultRoutingError


class TestVaultRouter(unittest.TestCase):
    """Test suite for VaultRouter (Two-Vault Router)."""

    def setUp(self) -> None:
        """Set up fresh dependencies and VaultRouter instance for each test."""
        self.kms_provider = LocalKMSProvider(initial_version="v1")
        self.key_manager = KeyManager(kms_provider=self.kms_provider)
        self.hash_service = self.encryption_service = EncryptionService(key_manager=self.key_manager)
        self.chain_engine = ChainEngine(hash_service=self.encryption_service.hash_service)
        self.router = VaultRouter(
            encryption_service=self.encryption_service,
            chain_engine=self.chain_engine,
        )

        self.case_id = "CR-DELHI-2026-0044"
        self.doc_fir_id = "DOC-FIR-001"
        self.officer_id = "POLICE-INSPECTOR-VERMA-DSC-77"
        self.sample_fir_plaintext = (
            b"First Information Report: Alleged cyber fraud under Section 66D IT Act, 2000 "
            b"and Section 318 BNS, 2023. Seized mobile device serial number IMEI-99281726."
        )

    # -----------------------------------------------------------------------
    # Initialization & Configuration
    # -----------------------------------------------------------------------

    def test_default_initialization(self) -> None:
        """VaultRouter initializes with default instances if None are passed."""
        router = VaultRouter()
        self.assertIsInstance(router.encryption_service, EncryptionService)
        self.assertIsInstance(router.chain_engine, ChainEngine)

    def test_dependency_injection(self) -> None:
        """VaultRouter correctly stores injected service dependencies."""
        self.assertIs(self.router.encryption_service, self.encryption_service)
        self.assertIs(self.router.chain_engine, self.chain_engine)

    def test_generate_blob_reference(self) -> None:
        """generate_blob_reference constructs deterministic S3/object store paths."""
        ref = VaultRouter.generate_blob_reference("CASE-10", "DOC-20", "1.0")
        self.assertEqual(ref, "CASE-10/DOC-20/1.0.enc")

    def test_generate_blob_reference_validation(self) -> None:
        """generate_blob_reference raises VaultRoutingError on empty or invalid arguments."""
        with self.assertRaises(VaultRoutingError):
            VaultRouter.generate_blob_reference("", "DOC-1", "1.0")
        with self.assertRaises(VaultRoutingError):
            VaultRouter.generate_blob_reference("CASE-1", "", "1.0")
        with self.assertRaises(VaultRoutingError):
            VaultRouter.generate_blob_reference("CASE-1", "DOC-1", "")

    # -----------------------------------------------------------------------
    # Full Upload Pipeline
    # -----------------------------------------------------------------------

    def test_full_upload_pipeline(self) -> None:
        """Upload pipeline produces a compliant VaultPackage with segregated metadata and ciphertext."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
            version="1.0",
        )

        # Verify VaultPackage container
        self.assertIsInstance(pkg, VaultPackage)
        self.assertEqual(pkg.document_id, self.doc_fir_id)
        self.assertEqual(pkg.case_id, self.case_id)
        self.assertEqual(pkg.vault1_target, VaultTarget.DATABASE)
        self.assertEqual(pkg.vault2_target, VaultTarget.OBJECT_STORAGE)
        self.assertEqual(pkg.vault2_blob_ref, f"{self.case_id}/{self.doc_fir_id}/1.0.enc")

        # Verify Vault 1 payload (Database)
        v1 = pkg.vault1_metadata
        self.assertIn("chain_record", v1)
        self.assertIn("wrapped_dek", v1)
        self.assertIn("aad", v1)
        self.assertIn("doc_hash", v1)
        self.assertIn("iv", v1)

        # Ensure hex encoding
        self.assertIsInstance(v1["wrapped_dek"], str)
        self.assertIsInstance(v1["aad"], str)
        self.assertIsInstance(v1["iv"], str)
        self.assertEqual(len(bytes.fromhex(v1["iv"])), IV_LENGTH_BYTES)

        # Verify ChainRecord in Vault 1 metadata
        rec = v1["chain_record"]
        self.assertEqual(rec["document_id"], self.doc_fir_id)
        self.assertEqual(rec["case_id"], self.case_id)
        self.assertEqual(rec["sequence_number"], 0)
        self.assertEqual(rec["version"], "1.0")
        self.assertEqual(rec["officer_id"], self.officer_id)

        # Verify Vault 2 payload (Object Storage)
        self.assertIsInstance(pkg.vault2_blob, bytes)
        self.assertGreater(len(pkg.vault2_blob), len(self.sample_fir_plaintext))

        # Verify chain in ChainEngine has genesis record
        chain = self.chain_engine.get_chain(self.case_id)
        self.assertEqual(len(chain), 1)
        self.assertEqual(chain[0].document_id, self.doc_fir_id)

    # -----------------------------------------------------------------------
    # Full Retrieval Pipeline & Round-Trip Integrity
    # -----------------------------------------------------------------------

    def test_full_retrieval_pipeline(self) -> None:
        """Retrieval pipeline recovers authentic plaintext from Vault 1 and Vault 2 payloads."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        decrypted = self.router.process_retrieval(
            vault1_metadata=pkg.vault1_metadata,
            vault2_blob=pkg.vault2_blob,
            expected_doc_hash=pkg.vault1_metadata["doc_hash"],
        )

        self.assertEqual(decrypted, self.sample_fir_plaintext)

    def test_round_trip_binary_payload(self) -> None:
        """Arbitrary binary evidence (e.g. disk image, forensic dump) round-trips byte-for-byte."""
        binary_payload = os.urandom(128 * 1024)  # 128 KB of binary data
        doc_id = "DOC-FORENSIC-DUMP-002"

        pkg = self.router.process_upload(
            plaintext=binary_payload,
            document_id=doc_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        recovered = self.router.process_retrieval(
            vault1_metadata=pkg.vault1_metadata,
            vault2_blob=pkg.vault2_blob,
        )

        self.assertEqual(recovered, binary_payload)

    def test_retrieval_expected_hash_mismatch_raises_error(self) -> None:
        """If caller provides a mismatched expected_doc_hash, retrieval fails closed."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        tampered_expected_hash = "f" * 64
        with self.assertRaises(VaultRoutingError) as ctx:
            self.router.process_retrieval(
                vault1_metadata=pkg.vault1_metadata,
                vault2_blob=pkg.vault2_blob,
                expected_doc_hash=tampered_expected_hash,
            )
        self.assertIn("integrity verification failed", str(ctx.exception).lower())

    def test_retrieval_tampered_ciphertext_fails(self) -> None:
        """Tampering with a single bit in vault2_blob triggers GCM tag verification failure."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        corrupted_blob = bytearray(pkg.vault2_blob)
        corrupted_blob[10] ^= 0x01

        with self.assertRaises(VaultRoutingError) as ctx:
            self.router.process_retrieval(
                vault1_metadata=pkg.vault1_metadata,
                vault2_blob=bytes(corrupted_blob),
            )
        self.assertIn("decryption failed", str(ctx.exception).lower())

    def test_retrieval_tampered_aad_fails(self) -> None:
        """Tampering with AAD hex in vault1_metadata fails GCM authentication."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        # Tamper with AAD by modifying case context in AAD hex
        tampered_v1 = dict(pkg.vault1_metadata)
        tampered_v1["aad"] = b"DOC-TAMPER:CASE-TAMPER:1.0".hex()

        with self.assertRaises(VaultRoutingError):
            self.router.process_retrieval(
                vault1_metadata=tampered_v1,
                vault2_blob=pkg.vault2_blob,
            )

    def test_retrieval_fallback_packed_iv_in_blob(self) -> None:
        """If 'iv' is omitted from vault1_metadata, retrieval extracts IV from prefix of vault2_blob."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        # Pack IV into blob prefix and remove 'iv' from metadata
        raw_iv = bytes.fromhex(pkg.vault1_metadata["iv"])
        packed_blob = raw_iv + pkg.vault2_blob
        legacy_v1 = dict(pkg.vault1_metadata)
        del legacy_v1["iv"]

        decrypted = self.router.process_retrieval(
            vault1_metadata=legacy_v1,
            vault2_blob=packed_blob,
        )
        self.assertEqual(decrypted, self.sample_fir_plaintext)

    # -----------------------------------------------------------------------
    # Vault Separation Validation
    # -----------------------------------------------------------------------

    def test_vault_separation_valid(self) -> None:
        """A freshly generated VaultPackage cleanly satisfies all separation invariants."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )
        self.assertTrue(self.router.validate_vault_separation(pkg))

    def test_vault_separation_detects_plaintext_in_vault1(self) -> None:
        """validate_vault_separation fails if plaintext is leaked into Vault 1 metadata."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        tampered_v1 = dict(pkg.vault1_metadata)
        tampered_v1["plaintext"] = self.sample_fir_plaintext.decode("utf-8")
        tampered_pkg = VaultPackage(
            document_id=pkg.document_id,
            case_id=pkg.case_id,
            vault1_metadata=tampered_v1,
            vault1_target=pkg.vault1_target,
            vault2_blob=pkg.vault2_blob,
            vault2_blob_ref=pkg.vault2_blob_ref,
            vault2_target=pkg.vault2_target,
        )

        self.assertFalse(self.router.validate_vault_separation(tampered_pkg))

    def test_vault_separation_detects_ciphertext_in_vault1(self) -> None:
        """validate_vault_separation fails if ciphertext is stored in Vault 1 metadata."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        tampered_v1 = dict(pkg.vault1_metadata)
        tampered_v1["ciphertext"] = pkg.vault2_blob.hex()
        tampered_pkg = VaultPackage(
            document_id=pkg.document_id,
            case_id=pkg.case_id,
            vault1_metadata=tampered_v1,
            vault1_target=pkg.vault1_target,
            vault2_blob=pkg.vault2_blob,
            vault2_blob_ref=pkg.vault2_blob_ref,
            vault2_target=pkg.vault2_target,
        )

        self.assertFalse(self.router.validate_vault_separation(tampered_pkg))

    def test_vault_separation_detects_metadata_in_vault2(self) -> None:
        """validate_vault_separation fails if metadata markers or doc_hash leak into Vault 2."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        # Contaminate vault2_blob by appending plaintext doc_hash
        doc_hash = pkg.vault1_metadata["doc_hash"]
        tampered_blob = pkg.vault2_blob + doc_hash.encode("ascii")
        tampered_pkg = VaultPackage(
            document_id=pkg.document_id,
            case_id=pkg.case_id,
            vault1_metadata=pkg.vault1_metadata,
            vault1_target=pkg.vault1_target,
            vault2_blob=tampered_blob,
            vault2_blob_ref=pkg.vault2_blob_ref,
            vault2_target=pkg.vault2_target,
        )

        self.assertFalse(self.router.validate_vault_separation(tampered_pkg))

    def test_vault_separation_invalid_target_enums(self) -> None:
        """validate_vault_separation fails if target vault enums are mismatched."""
        pkg = self.router.process_upload(
            plaintext=self.sample_fir_plaintext,
            document_id=self.doc_fir_id,
            case_id=self.case_id,
            officer_id=self.officer_id,
        )

        # Invert target routing
        mismatched_pkg = VaultPackage(
            document_id=pkg.document_id,
            case_id=pkg.case_id,
            vault1_metadata=pkg.vault1_metadata,
            vault1_target=VaultTarget.OBJECT_STORAGE,  # Error
            vault2_blob=pkg.vault2_blob,
            vault2_blob_ref=pkg.vault2_blob_ref,
            vault2_target=VaultTarget.DATABASE,        # Error
        )

        self.assertFalse(self.router.validate_vault_separation(mismatched_pkg))

    # -----------------------------------------------------------------------
    # Multi-Document Case (FIR -> Evidence -> Charge Sheet)
    # -----------------------------------------------------------------------

    def test_multi_document_case_pipeline(self) -> None:
        """Sequential upload of FIR, CCTV Evidence, and Final Charge Sheet forms unbroken chain."""
        # 1. Document 1: Initial FIR (genesis, seq 0)
        fir_bytes = b"FIR #101: Initial complaint regarding stolen vehicle."
        fir_pkg = self.router.process_upload(
            plaintext=fir_bytes,
            document_id="DOC-FIR-01",
            case_id=self.case_id,
            officer_id=self.officer_id,
            version="1.0",
        )
        self.assertEqual(fir_pkg.vault1_metadata["chain_record"]["sequence_number"], 0)

        # 2. Document 2: CCTV Video Footage (seq 1)
        cctv_bytes = b"MPEG-4 binary stream: Traffic camera footage timestamped 14:22:00."
        cctv_pkg = self.router.process_upload(
            plaintext=cctv_bytes,
            document_id="DOC-CCTV-02",
            case_id=self.case_id,
            officer_id="FORENSIC-EXPERT-DSC-12",
            version="1.0",
        )
        self.assertEqual(cctv_pkg.vault1_metadata["chain_record"]["sequence_number"], 1)

        # 3. Document 3: Police Final Report / Charge Sheet (seq 2)
        chargesheet_bytes = b"Charge Sheet under Section 173 CrPC / Section 193 BNSS, 2023."
        cs_pkg = self.router.process_upload(
            plaintext=chargesheet_bytes,
            document_id="DOC-CHARGESHEET-03",
            case_id=self.case_id,
            officer_id=self.officer_id,
            version="1.0",
        )
        self.assertEqual(cs_pkg.vault1_metadata["chain_record"]["sequence_number"], 2)

        # 4. Verify chain integrity in ChainEngine
        chain = self.chain_engine.get_chain(self.case_id)
        self.assertEqual(len(chain), 3)
        self.assertTrue(self.chain_engine.verify_chain_integrity(self.case_id))

        # 5. Retrieve all three documents independently
        rec_fir = self.router.process_retrieval(fir_pkg.vault1_metadata, fir_pkg.vault2_blob)
        rec_cctv = self.router.process_retrieval(cctv_pkg.vault1_metadata, cctv_pkg.vault2_blob)
        rec_cs = self.router.process_retrieval(cs_pkg.vault1_metadata, cs_pkg.vault2_blob)

        self.assertEqual(rec_fir, fir_bytes)
        self.assertEqual(rec_cctv, cctv_bytes)
        self.assertEqual(rec_cs, chargesheet_bytes)

    # -----------------------------------------------------------------------
    # Amendment Upload with Quorum Token
    # -----------------------------------------------------------------------

    def test_amendment_upload_with_quorum_token(self) -> None:
        """Document amendment (V1.1+) strictly requires quorum token and references original doc_hash."""
        # 1. Upload original Seizure Memo (v1.0)
        orig_bytes = b"Seizure Memo: Seized 1 HP Laptop serial 5CD8927."
        orig_pkg = self.router.process_upload(
            plaintext=orig_bytes,
            document_id="DOC-SEIZURE-MEMO",
            case_id=self.case_id,
            officer_id=self.officer_id,
            version="1.0",
        )
        orig_hash = orig_pkg.vault1_metadata["doc_hash"]

        # 2. Upload supplementary seizure memo addendum (v1.1)
        addendum_bytes = b"Addendum to Seizure Memo: Seized charger and encrypted USB drive found with laptop."
        quorum_token = "QUORUM-SIG-CHIEF-JUDICIAL-MAGISTRATE-KEY-9901"

        amend_pkg = self.router.process_upload(
            plaintext=addendum_bytes,
            document_id="DOC-SEIZURE-MEMO-ADDENDUM",
            case_id=self.case_id,
            officer_id=self.officer_id,
            version="1.1",
            quorum_token=quorum_token,
            amendment_of=orig_hash,
        )

        rec = amend_pkg.vault1_metadata["chain_record"]
        self.assertEqual(rec["sequence_number"], 1)
        self.assertEqual(rec["version"], "1.1")
        self.assertEqual(rec["quorum_token"], quorum_token)
        self.assertEqual(rec["amendment_of"], orig_hash)

        # 3. Retrieve both records cleanly
        dec_orig = self.router.process_retrieval(orig_pkg.vault1_metadata, orig_pkg.vault2_blob)
        dec_amend = self.router.process_retrieval(amend_pkg.vault1_metadata, amend_pkg.vault2_blob)

        self.assertEqual(dec_orig, orig_bytes)
        self.assertEqual(dec_amend, addendum_bytes)

    def test_amendment_missing_quorum_token_fails(self) -> None:
        """Amendment upload (V1.1+) without quorum_token is rejected by VaultRouter."""
        orig_pkg = self.router.process_upload(
            plaintext=b"Original content",
            document_id="DOC-ORIG-10",
            case_id=self.case_id,
            officer_id=self.officer_id,
            version="1.0",
        )

        with self.assertRaises(VaultRoutingError) as ctx:
            self.router.process_upload(
                plaintext=b"Amendment content without quorum",
                document_id="DOC-AMEND-11",
                case_id=self.case_id,
                officer_id=self.officer_id,
                version="1.1",
                quorum_token=None,  # Missing
                amendment_of=orig_pkg.vault1_metadata["doc_hash"],
            )
        self.assertIn("chain engine rejected", str(ctx.exception).lower())

    def test_amendment_invalid_amendment_of_hash_fails(self) -> None:
        """Amendment referencing non-existent doc_hash is rejected by VaultRouter."""
        self.router.process_upload(
            plaintext=b"Original content",
            document_id="DOC-ORIG-20",
            case_id=self.case_id,
            officer_id=self.officer_id,
            version="1.0",
        )

        with self.assertRaises(VaultRoutingError) as ctx:
            self.router.process_upload(
                plaintext=b"Amendment content",
                document_id="DOC-AMEND-21",
                case_id=self.case_id,
                officer_id=self.officer_id,
                version="1.1",
                quorum_token="QUORUM-SIG-1234",
                amendment_of="0" * 64,  # Non-existent hash
            )
        self.assertIn("chain engine rejected", str(ctx.exception).lower())

    # -----------------------------------------------------------------------
    # Logging Hygiene
    # -----------------------------------------------------------------------

    def test_logging_no_plaintext_or_secrets_leaked(self) -> None:
        """VaultRouter logs operation metadata but NEVER logs plaintext or ciphertext."""
        logger = logging.getLogger("securechain_security.vault_router")
        captured_records: list[logging.LogRecord] = []

        class ListHandler(logging.Handler):
            def emit(self, record: logging.LogRecord) -> None:
                captured_records.append(record)

        handler = ListHandler()
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        secret_text = "CONFIDENTIAL_INFORMANT_IDENTITY_ALPHA_OMEGA"
        try:
            pkg = self.router.process_upload(
                plaintext=secret_text.encode("utf-8"),
                document_id="DOC-SECRET-01",
                case_id=self.case_id,
                officer_id=self.officer_id,
            )
            self.router.process_retrieval(pkg.vault1_metadata, pkg.vault2_blob)
            self.router.validate_vault_separation(pkg)
        finally:
            logger.removeHandler(handler)

        for record in captured_records:
            msg = record.getMessage()
            self.assertNotIn(
                secret_text,
                msg,
                f"Plaintext secret was leaked in log message: {msg}",
            )


if __name__ == "__main__":
    unittest.main()
