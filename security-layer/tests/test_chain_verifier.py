"""
Unit tests for SecureChain DMS Chain Verifier Service (Module 3).
=================================================================
Validates forensic chain verification, raw document content matching,
WORM tamper alert generation, batch case auditing, and court certificate
production under BSA 2023 §63 / 65B requirements.
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import unittest

from securechain_security.chain_engine import ChainEngine
from securechain_security.chain_verifier import (
    ChainVerifier,
    DocumentVerificationResult,
    VerificationError,
)
from securechain_security.hash_service import HashService
from securechain_security.models import (
    GENESIS_HASH,
    ChainStatus,
    TamperAlert,
    TamperSeverity,
    VerificationResult,
)


def _compute_hash(content: bytes | str) -> str:
    """Helper to compute deterministic SHA-256 digest."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class TestChainVerifier(unittest.TestCase):
    """Test suite for ChainVerifier."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.chain_engine = ChainEngine(hash_service=self.hash_service)
        self.verifier = ChainVerifier(
            chain_engine=self.chain_engine,
            hash_service=self.hash_service,
        )

        self.case_id = "CASE-2026-BSA-001"
        self.doc1_id = "DOC-FIR-001"
        self.doc1_raw = b"First Information Report: Alleged cyber fraud under IPC 420 and IT Act 66D"
        self.doc1_hash = _compute_hash(self.doc1_raw)

        # Initialize Genesis link
        self.chain_engine.create_genesis(
            case_id=self.case_id,
            document_id=self.doc1_id,
            doc_hash=self.doc1_hash,
            officer_id="IO-SHREYASH-101",
            timestamp="2026-09-04T01:00:00.000Z",
        )

        # Append second document (Seizure Memo)
        self.doc2_id = "DOC-SEIZURE-002"
        self.doc2_raw = b"Seizure Memo: Seized 1TB NVMe SSD from suspect premises"
        self.doc2_hash = _compute_hash(self.doc2_raw)
        self.chain_engine.append_document(
            case_id=self.case_id,
            document_id=self.doc2_id,
            doc_hash=self.doc2_hash,
            officer_id="IO-SHREYASH-101",
            version="1.0",
            timestamp="2026-09-04T02:00:00.000Z",
        )

    def test_init_invalid_args(self) -> None:
        with self.assertRaises(ValueError):
            ChainVerifier(chain_engine=None, hash_service=self.hash_service)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            ChainVerifier(chain_engine=self.chain_engine, hash_service=None)  # type: ignore[arg-type]

    def test_verify_case_intact_chain(self) -> None:
        result = self.verifier.verify_case(self.case_id)
        self.assertIsInstance(result, VerificationResult)
        self.assertEqual(result.status, ChainStatus.INTACT)
        self.assertEqual(result.documents_checked, 2)
        self.assertEqual(result.documents_valid, 2)
        self.assertIsNone(result.first_broken_link)
        self.assertEqual(len(self.verifier.alerts), 0)

    def test_verify_case_tampered_chain(self) -> None:
        # Manually alter a link in the chain
        chain = self.chain_engine._chains[self.case_id]
        tampered_rec = dataclasses.replace(
            chain[1],
            doc_hash=_compute_hash(b"Tampered seizure memo with removed serial numbers"),
        )
        chain[1] = tampered_rec

        result = self.verifier.verify_case(self.case_id)
        self.assertEqual(result.status, ChainStatus.TAMPERED)
        self.assertEqual(result.first_broken_link, self.doc2_id)
        self.assertEqual(result.documents_valid, 1)

        # An alert should have been generated and recorded
        alerts = self.verifier.alerts
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.case_id, self.case_id)
        self.assertEqual(alert.document_id, self.doc2_id)
        self.assertEqual(alert.severity, TamperSeverity.HIGH)
        self.assertEqual(alert.detected_by, "chain_walk")

    def test_verify_case_nonexistent(self) -> None:
        with self.assertRaises(VerificationError):
            self.verifier.verify_case("NONEXISTENT-CASE")

        with self.assertRaises(VerificationError):
            self.verifier.verify_case("")

    def test_verify_document_content_matching(self) -> None:
        # Test with raw bytes
        res_bytes = self.verifier.verify_document_content(
            case_id=self.case_id,
            document_id=self.doc1_id,
            file_stream_or_bytes=self.doc1_raw,
        )
        self.assertIsInstance(res_bytes, DocumentVerificationResult)
        self.assertTrue(res_bytes.is_match)
        self.assertEqual(res_bytes.stored_hash, self.doc1_hash)
        self.assertEqual(res_bytes.computed_hash, self.doc1_hash)

        # Test with file stream
        stream = io.BytesIO(self.doc1_raw)
        res_stream = self.verifier.verify_document_content(
            case_id=self.case_id,
            document_id=self.doc1_id,
            file_stream_or_bytes=stream,
        )
        self.assertTrue(res_stream.is_match)

    def test_verify_document_content_modified(self) -> None:
        altered_content = b"Altered First Information Report: Fraud amount reduced"
        res = self.verifier.verify_document_content(
            case_id=self.case_id,
            document_id=self.doc1_id,
            file_stream_or_bytes=altered_content,
        )
        self.assertFalse(res.is_match)
        self.assertEqual(res.stored_hash, self.doc1_hash)
        self.assertNotEqual(res.computed_hash, self.doc1_hash)

        # CRITICAL TamperAlert must be logged
        alerts = self.verifier.alerts
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.severity, TamperSeverity.CRITICAL)
        self.assertEqual(alert.document_id, self.doc1_id)
        self.assertEqual(alert.case_id, self.case_id)
        self.assertEqual(alert.expected_hash, self.doc1_hash)
        self.assertEqual(alert.actual_hash, res.computed_hash)
        self.assertEqual(alert.detected_by, "on_retrieval")

    def test_verify_document_content_invalid_inputs(self) -> None:
        with self.assertRaises(VerificationError):
            self.verifier.verify_document_content("", self.doc1_id, self.doc1_raw)
        with self.assertRaises(VerificationError):
            self.verifier.verify_document_content(self.case_id, "", self.doc1_raw)
        with self.assertRaises(VerificationError):
            self.verifier.verify_document_content(self.case_id, self.doc1_id, None)
        with self.assertRaises(VerificationError):
            self.verifier.verify_document_content(self.case_id, "NONEXISTENT-DOC", self.doc1_raw)
        with self.assertRaises(VerificationError):
            self.verifier.verify_document_content(self.case_id, self.doc1_id, 12345)  # type: ignore[arg-type]

    def test_verify_multiple_cases(self) -> None:
        # Create second case
        case2_id = "CASE-2026-BSA-002"
        self.chain_engine.create_genesis(
            case_id=case2_id,
            document_id="DOC-CASE2-001",
            doc_hash=_compute_hash("Case 2 Evidence"),
            officer_id="IO-MEERA-202",
        )

        results = self.verifier.verify_multiple_cases([self.case_id, case2_id, "CASE-DOES-NOT-EXIST"])
        self.assertEqual(len(results), 3)

        self.assertEqual(results[0].status, ChainStatus.INTACT)
        self.assertEqual(results[0].case_id, self.case_id)

        self.assertEqual(results[1].status, ChainStatus.INTACT)
        self.assertEqual(results[1].case_id, case2_id)

        self.assertEqual(results[2].status, ChainStatus.EMPTY)
        self.assertEqual(results[2].case_id, "CASE-DOES-NOT-EXIST")

    def test_verify_multiple_cases_none_arg(self) -> None:
        with self.assertRaises(VerificationError):
            self.verifier.verify_multiple_cases(None)  # type: ignore[arg-type]

    def test_generate_tamper_report(self) -> None:
        tampered_result = VerificationResult(
            case_id=self.case_id,
            status=ChainStatus.TAMPERED,
            documents_checked=2,
            documents_valid=1,
            first_broken_link=self.doc2_id,
            error_message="Chain hash digest mismatch at sequence 1",
        )

        alert = self.verifier.generate_tamper_report(self.case_id, tampered_result)
        self.assertIsInstance(alert, TamperAlert)
        self.assertEqual(alert.case_id, self.case_id)
        self.assertEqual(alert.document_id, self.doc2_id)
        self.assertEqual(alert.severity, TamperSeverity.HIGH)
        self.assertIn("Chain hash digest mismatch", alert.description)
        self.assertEqual(alert.detected_by, "chain_walk")

        # Intact result should raise ValueError
        intact_result = VerificationResult(
            case_id=self.case_id,
            status=ChainStatus.INTACT,
            documents_checked=2,
            documents_valid=2,
        )
        with self.assertRaises(ValueError):
            self.verifier.generate_tamper_report(self.case_id, intact_result)

    def test_generate_court_certificate_intact(self) -> None:
        cert = self.verifier.generate_court_certificate(
            case_id=self.case_id,
            document_id=self.doc1_id,
            file_stream_or_bytes=self.doc1_raw,
        )

        self.assertIsInstance(cert, dict)
        self.assertEqual(cert["case_id"], self.case_id)
        self.assertEqual(cert["document_id"], self.doc1_id)
        self.assertEqual(cert["chain_status"], "INTACT")
        self.assertTrue(cert["content_hash_verified"])
        self.assertEqual(cert["stored_doc_hash"], self.doc1_hash)
        self.assertEqual(cert["computed_doc_hash"], self.doc1_hash)
        self.assertEqual(cert["chain_length"], 2)
        self.assertEqual(cert["sequence_number"], 0)
        self.assertEqual(cert["version"], "1.0")
        self.assertEqual(cert["officer_id"], "IO-SHREYASH-101")
        self.assertIn("certificate_hash", cert)

        # Verify self-authenticating certificate hash
        self.assertTrue(ChainVerifier.verify_court_certificate(cert))

    def test_generate_court_certificate_tampered_content(self) -> None:
        tampered_content = b"Forged document bytes"
        cert = self.verifier.generate_court_certificate(
            case_id=self.case_id,
            document_id=self.doc1_id,
            file_stream_or_bytes=tampered_content,
        )

        self.assertEqual(cert["chain_status"], "INTACT")
        self.assertFalse(cert["content_hash_verified"])
        self.assertNotEqual(cert["computed_doc_hash"], cert["stored_doc_hash"])
        self.assertTrue(ChainVerifier.verify_court_certificate(cert))

    def test_generate_court_certificate_tampered_chain(self) -> None:
        # Break chain link 1
        chain = self.chain_engine._chains[self.case_id]
        chain[1] = dataclasses.replace(chain[1], prev_chain_hash="0" * 64)

        cert = self.verifier.generate_court_certificate(
            case_id=self.case_id,
            document_id=self.doc1_id,
            file_stream_or_bytes=self.doc1_raw,
        )

        self.assertEqual(cert["chain_status"], "TAMPERED")
        self.assertTrue(cert["content_hash_verified"])
        self.assertTrue(ChainVerifier.verify_court_certificate(cert))

    def test_verify_court_certificate_tampered(self) -> None:
        cert = self.verifier.generate_court_certificate(
            case_id=self.case_id,
            document_id=self.doc1_id,
            file_stream_or_bytes=self.doc1_raw,
        )
        self.assertTrue(ChainVerifier.verify_court_certificate(cert))

        # Tamper with the certificate dictionary (e.g. changing chain_status or hash)
        cert["chain_status"] = "FORGED_STATUS"
        self.assertFalse(ChainVerifier.verify_court_certificate(cert))

        # Invalid certificate inputs
        self.assertFalse(ChainVerifier.verify_court_certificate({}))
        self.assertFalse(ChainVerifier.verify_court_certificate(None))  # type: ignore[arg-type]

    def test_clear_alerts(self) -> None:
        # Trigger an alert
        self.verifier.verify_document_content(
            case_id=self.case_id,
            document_id=self.doc1_id,
            file_stream_or_bytes=b"bad content",
        )
        self.assertEqual(len(self.verifier.alerts), 1)

        self.verifier.clear_alerts()
        self.assertEqual(len(self.verifier.alerts), 0)


if __name__ == "__main__":
    unittest.main()
