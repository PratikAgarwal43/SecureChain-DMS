"""
Unit tests for SecureChain DMS Hash-Chain Engine (Module 2).
============================================================
Validates genesis creation, sequential chain building, integrity verification,
tamper detection, quorum-gated amendments, version history retrieval,
immutability enforcement, and thread-safety under concurrent appends.
"""

from __future__ import annotations

import dataclasses
import hashlib
import io
import logging
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from securechain_security.chain_engine import (
    ChainEngine,
    ChainError,
    ChainImmutabilityError,
    ChainNotFoundError,
    QuorumRequiredError,
)
from securechain_security.hash_service import HashService
from securechain_security.models import (
    GENESIS_HASH,
    ChainRecord,
    ChainState,
    ChainStatus,
    DocumentVersion,
    VerificationResult,
)


def _compute_hash(content: str) -> str:
    """Helper to compute deterministic SHA-256 for test string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class TestChainEngineGenesis(unittest.TestCase):
    """Tests for genesis link initialization and validation."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.engine = ChainEngine(hash_service=self.hash_service)

    def test_init_invalid_hash_service(self) -> None:
        with self.assertRaises(ValueError):
            ChainEngine(hash_service=None)  # type: ignore[arg-type]

    def test_create_genesis_success(self) -> None:
        case_id = "CASE-2026-001"
        doc_id = "DOC-FIR-001"
        doc_hash = _compute_hash("FIR Content: Cyber Crime under BSA Section 63")
        officer_id = "OFFICER-DSC-IND-88219"
        timestamp = "2026-09-04T05:30:00.000Z"

        record = self.engine.create_genesis(
            case_id=case_id,
            document_id=doc_id,
            doc_hash=doc_hash,
            officer_id=officer_id,
            timestamp=timestamp,
        )

        self.assertIsInstance(record, ChainRecord)
        self.assertEqual(record.case_id, case_id)
        self.assertEqual(record.document_id, doc_id)
        self.assertEqual(record.doc_hash, doc_hash)
        self.assertEqual(record.officer_id, officer_id)
        self.assertEqual(record.sequence_number, 0)
        self.assertEqual(record.version, DocumentVersion.ORIGINAL.value)
        self.assertEqual(record.prev_chain_hash, GENESIS_HASH)
        self.assertEqual(record.timestamp, timestamp)
        self.assertIsNone(record.quorum_token)
        self.assertIsNone(record.amendment_of)

        expected_chain_hash = self.hash_service.hash_chain_link(
            doc_hash=doc_hash,
            prev_chain_hash=GENESIS_HASH,
            timestamp=timestamp,
            officer_id=officer_id,
        )
        self.assertEqual(record.chain_hash, expected_chain_hash)

    def test_create_genesis_auto_timestamp(self) -> None:
        record = self.engine.create_genesis(
            case_id="CASE-AUTO-TS",
            document_id="DOC-01",
            doc_hash=_compute_hash("auto ts content"),
            officer_id="OFFICER-01",
        )
        self.assertTrue(len(record.timestamp) > 0)
        # Should be a parseable ISO timestamp
        parsed_dt = datetime.fromisoformat(record.timestamp)
        self.assertIsNotNone(parsed_dt)

    def test_create_genesis_already_exists_fails(self) -> None:
        case_id = "CASE-DUP-GENESIS"
        self.engine.create_genesis(
            case_id=case_id,
            document_id="DOC-01",
            doc_hash=_compute_hash("first"),
            officer_id="OFFICER-01",
        )

        with self.assertRaises(ChainImmutabilityError) as ctx:
            self.engine.create_genesis(
                case_id=case_id,
                document_id="DOC-02",
                doc_hash=_compute_hash("second"),
                officer_id="OFFICER-02",
            )
        self.assertIn("already has an established chain", str(ctx.exception))

    def test_create_genesis_invalid_parameters(self) -> None:
        valid_hash = _compute_hash("valid")
        with self.assertRaises(ChainError):
            self.engine.create_genesis("", "DOC-1", valid_hash, "OFFICER-1")
        with self.assertRaises(ChainError):
            self.engine.create_genesis("CASE-1", "", valid_hash, "OFFICER-1")
        with self.assertRaises(ChainError):
            self.engine.create_genesis("CASE-1", "DOC-1", "", "OFFICER-1")
        with self.assertRaises(ChainError):
            self.engine.create_genesis("CASE-1", "DOC-1", valid_hash, "")


class TestChainEngineBuilding(unittest.TestCase):
    """Tests for multi-document chain building and traversal."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.engine = ChainEngine(hash_service=self.hash_service)
        self.case_id = "CASE-MULTI-DOC"

        self.gen_record = self.engine.create_genesis(
            case_id=self.case_id,
            document_id="DOC-GENESIS",
            doc_hash=_compute_hash("Genesis FIR"),
            officer_id="IO-SHREYESH-01",
            timestamp="2026-09-04T05:00:00.000Z",
        )

    def test_append_document_sequential(self) -> None:
        doc2_hash = _compute_hash("Seizure Memo")
        rec2 = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-SEIZURE",
            doc_hash=doc2_hash,
            officer_id="IO-SHREYESH-01",
            version="1.0",
            timestamp="2026-09-04T05:10:00.000Z",
        )

        self.assertEqual(rec2.sequence_number, 1)
        self.assertEqual(rec2.prev_chain_hash, self.gen_record.chain_hash)
        self.assertEqual(rec2.version, "1.0")

        doc3_hash = _compute_hash("Forensic Lab Report")
        rec3 = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-FORENSIC",
            doc_hash=doc3_hash,
            officer_id="EXPERT-FSL-09",
            version="1.0",
            timestamp="2026-09-04T05:20:00.000Z",
        )

        self.assertEqual(rec3.sequence_number, 2)
        self.assertEqual(rec3.prev_chain_hash, rec2.chain_hash)

        # Verify full chain list
        chain = self.engine.get_chain(self.case_id)
        self.assertEqual(len(chain), 3)
        self.assertEqual(chain[0].document_id, "DOC-GENESIS")
        self.assertEqual(chain[1].document_id, "DOC-SEIZURE")
        self.assertEqual(chain[2].document_id, "DOC-FORENSIC")

    def test_append_to_uninitialized_case_fails(self) -> None:
        with self.assertRaises(ChainNotFoundError):
            self.engine.append_document(
                case_id="CASE-NONEXISTENT",
                document_id="DOC-01",
                doc_hash=_compute_hash("test"),
                officer_id="IO-01",
            )

    def test_get_head_and_chain_state(self) -> None:
        head_initial = self.engine.get_head(self.case_id)
        self.assertEqual(head_initial.document_id, "DOC-GENESIS")

        rec2 = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-CCTV",
            doc_hash=_compute_hash("CCTV Surveillance Footage"),
            officer_id="IO-SHREYESH-01",
        )

        head_new = self.engine.get_head(self.case_id)
        self.assertEqual(head_new.document_id, "DOC-CCTV")
        self.assertEqual(head_new.chain_hash, rec2.chain_hash)

        state = self.engine.get_chain_state(self.case_id)
        self.assertIsInstance(state, ChainState)
        self.assertEqual(state.case_id, self.case_id)
        self.assertEqual(state.length, 2)
        self.assertEqual(state.head_chain_hash, rec2.chain_hash)
        self.assertEqual(state.genesis_hash, GENESIS_HASH)
        self.assertEqual(state.created_at, self.gen_record.timestamp)
        self.assertEqual(state.last_updated_at, rec2.timestamp)

    def test_get_head_and_state_nonexistent_case(self) -> None:
        with self.assertRaises(ChainNotFoundError):
            self.engine.get_head("CASE-DOES-NOT-EXIST")
        with self.assertRaises(ChainNotFoundError):
            self.engine.get_chain_state("CASE-DOES-NOT-EXIST")
        with self.assertRaises(ChainNotFoundError):
            self.engine.get_chain("CASE-DOES-NOT-EXIST")

    def test_get_document_record(self) -> None:
        self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-CHARGE-SHEET",
            doc_hash=_compute_hash("Charge Sheet"),
            officer_id="IO-SHREYESH-01",
        )

        record = self.engine.get_document_record(self.case_id, "DOC-CHARGE-SHEET")
        self.assertEqual(record.document_id, "DOC-CHARGE-SHEET")
        self.assertEqual(record.sequence_number, 1)

        with self.assertRaises(ChainNotFoundError):
            self.engine.get_document_record(self.case_id, "DOC-UNKNOWN")

        with self.assertRaises(ChainNotFoundError):
            self.engine.get_document_record("CASE-UNKNOWN", "DOC-CHARGE-SHEET")


class TestChainIntegrityAndTamperDetection(unittest.TestCase):
    """Tests for chain verification and cryptographic tamper detection."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.engine = ChainEngine(hash_service=self.hash_service)
        self.case_id = "CASE-INTEGRITY-AUDIT"

        self.doc1 = self.engine.create_genesis(
            case_id=self.case_id,
            document_id="DOC-FIR",
            doc_hash=_compute_hash("FIR"),
            officer_id="IO-01",
            timestamp="2026-09-04T01:00:00.000Z",
        )
        self.doc2 = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-INSPECTION",
            doc_hash=_compute_hash("Crime Scene Inspection"),
            officer_id="IO-01",
            timestamp="2026-09-04T02:00:00.000Z",
        )
        self.doc3 = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-POST-MORTEM",
            doc_hash=_compute_hash("Autopsy Report"),
            officer_id="MED-OFFICER-03",
            timestamp="2026-09-04T03:00:00.000Z",
        )

    def test_verify_intact_chain(self) -> None:
        self.assertTrue(self.engine.verify_chain_integrity(self.case_id))

        detailed = self.engine.verify_chain_detailed(self.case_id)
        self.assertEqual(detailed.status, ChainStatus.INTACT)
        self.assertEqual(detailed.documents_checked, 3)
        self.assertEqual(detailed.documents_valid, 3)
        self.assertIsNone(detailed.first_broken_link)
        self.assertIsNone(detailed.error_message)
        self.assertGreaterEqual(detailed.verification_time_ms, 0.0)

    def test_tamper_doc_hash_detected(self) -> None:
        # Simulate unauthorized modification of autopsy report
        chain = self.engine._chains[self.case_id]
        tampered_record = dataclasses.replace(
            chain[2],
            doc_hash=_compute_hash("Tampered Autopsy Report with Altered Cause of Death"),
        )
        chain[2] = tampered_record

        self.assertFalse(self.engine.verify_chain_integrity(self.case_id))

        detailed = self.engine.verify_chain_detailed(self.case_id)
        self.assertEqual(detailed.status, ChainStatus.TAMPERED)
        self.assertEqual(detailed.first_broken_link, "DOC-POST-MORTEM")
        self.assertEqual(detailed.documents_valid, 2)
        self.assertIn("Chain hash digest mismatch", str(detailed.error_message))

    def test_tamper_prev_chain_hash_detected(self) -> None:
        # Tamper with link continuity
        chain = self.engine._chains[self.case_id]
        tampered_record = dataclasses.replace(
            chain[1],
            prev_chain_hash="f" * 64,
        )
        chain[1] = tampered_record

        self.assertFalse(self.engine.verify_chain_integrity(self.case_id))

        detailed = self.engine.verify_chain_detailed(self.case_id)
        self.assertEqual(detailed.status, ChainStatus.TAMPERED)
        self.assertEqual(detailed.first_broken_link, "DOC-INSPECTION")
        self.assertEqual(detailed.documents_valid, 1)
        self.assertIn("Previous chain hash mismatch", str(detailed.error_message))

    def test_tamper_timestamp_detected(self) -> None:
        # Tamper with backdated timestamp
        chain = self.engine._chains[self.case_id]
        tampered_record = dataclasses.replace(
            chain[0],
            timestamp="1999-01-01T00:00:00.000Z",
        )
        chain[0] = tampered_record

        self.assertFalse(self.engine.verify_chain_integrity(self.case_id))

        detailed = self.engine.verify_chain_detailed(self.case_id)
        self.assertEqual(detailed.status, ChainStatus.TAMPERED)
        self.assertEqual(detailed.first_broken_link, "DOC-FIR")
        self.assertEqual(detailed.documents_valid, 0)

    def test_tamper_officer_id_detected(self) -> None:
        # Tamper with officer identity
        chain = self.engine._chains[self.case_id]
        tampered_record = dataclasses.replace(
            chain[1],
            officer_id="ROGUE-OFFICER-99",
        )
        chain[1] = tampered_record

        self.assertFalse(self.engine.verify_chain_integrity(self.case_id))

    def test_tamper_sequence_number_detected(self) -> None:
        # Tamper with sequence ordering
        chain = self.engine._chains[self.case_id]
        tampered_record = dataclasses.replace(
            chain[1],
            sequence_number=99,
        )
        chain[1] = tampered_record

        self.assertFalse(self.engine.verify_chain_integrity(self.case_id))
        detailed = self.engine.verify_chain_detailed(self.case_id)
        self.assertEqual(detailed.status, ChainStatus.TAMPERED)
        self.assertIn("Sequence number mismatch", str(detailed.error_message))

    def test_verify_nonexistent_case(self) -> None:
        with self.assertRaises(ChainNotFoundError):
            self.engine.verify_chain_integrity("CASE-GHOST")
        with self.assertRaises(ChainNotFoundError):
            self.engine.verify_chain_detailed("CASE-GHOST")


class TestChainAmendmentsAndQuorum(unittest.TestCase):
    """Tests for document amendments and multi-party quorum enforcement."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.engine = ChainEngine(hash_service=self.hash_service)
        self.case_id = "CASE-AMENDMENT-TEST"

        self.orig_doc_hash = _compute_hash("Original Seizure Memo V1.0")
        self.gen_record = self.engine.create_genesis(
            case_id=self.case_id,
            document_id="DOC-SEIZURE-01",
            doc_hash=self.orig_doc_hash,
            officer_id="IO-01",
        )

    def test_amendment_with_quorum_success(self) -> None:
        amended_doc_hash = _compute_hash("Supplementary Seizure Memo V1.1 with corrected serial numbers")
        quorum_token = "QUORUM-SIG:JUDGE-01+PROSECUTOR-04+FORENSIC-02"

        amend_record = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-SEIZURE-01-A1",
            doc_hash=amended_doc_hash,
            officer_id="IO-01",
            version="1.1",
            quorum_token=quorum_token,
            amendment_of=self.orig_doc_hash,
        )

        self.assertEqual(amend_record.sequence_number, 1)
        self.assertEqual(amend_record.version, "1.1")
        self.assertEqual(amend_record.quorum_token, quorum_token)
        self.assertEqual(amend_record.amendment_of, self.orig_doc_hash)
        self.assertEqual(amend_record.prev_chain_hash, self.gen_record.chain_hash)

        # Integrity check should pass with quorum token factored into the link hash
        self.assertTrue(self.engine.verify_chain_integrity(self.case_id))

    def test_amendment_without_quorum_token_fails(self) -> None:
        amended_doc_hash = _compute_hash("Amended Report")

        # Missing quorum token
        with self.assertRaises(QuorumRequiredError):
            self.engine.append_document(
                case_id=self.case_id,
                document_id="DOC-SEIZURE-01-A1",
                doc_hash=amended_doc_hash,
                officer_id="IO-01",
                version="1.1",
                quorum_token=None,
                amendment_of=self.orig_doc_hash,
            )

        # Empty quorum token
        with self.assertRaises(QuorumRequiredError):
            self.engine.append_document(
                case_id=self.case_id,
                document_id="DOC-SEIZURE-01-A1",
                doc_hash=amended_doc_hash,
                officer_id="IO-01",
                version="1.1",
                quorum_token="   ",
                amendment_of=self.orig_doc_hash,
            )

    def test_amendment_without_amendment_of_fails(self) -> None:
        amended_doc_hash = _compute_hash("Amended Report")
        quorum_token = "QUORUM-SIG-VALID"

        # Missing amendment_of
        with self.assertRaises(ChainError) as ctx:
            self.engine.append_document(
                case_id=self.case_id,
                document_id="DOC-SEIZURE-01-A1",
                doc_hash=amended_doc_hash,
                officer_id="IO-01",
                version="1.1",
                quorum_token=quorum_token,
                amendment_of=None,
            )
        self.assertIn("requires 'amendment_of'", str(ctx.exception))

    def test_amendment_referencing_nonexistent_hash_fails(self) -> None:
        amended_doc_hash = _compute_hash("Amended Report")
        quorum_token = "QUORUM-SIG-VALID"
        ghost_hash = _compute_hash("Nonexistent Document Content")

        with self.assertRaises(ChainError) as ctx:
            self.engine.append_document(
                case_id=self.case_id,
                document_id="DOC-SEIZURE-01-A1",
                doc_hash=amended_doc_hash,
                officer_id="IO-01",
                version="1.1",
                quorum_token=quorum_token,
                amendment_of=ghost_hash,
            )
        self.assertIn("was not found in case", str(ctx.exception))

    def test_v1_cannot_specify_amendment_of(self) -> None:
        with self.assertRaises(ChainError) as ctx:
            self.engine.append_document(
                case_id=self.case_id,
                document_id="DOC-ORIGINAL-02",
                doc_hash=_compute_hash("New Original"),
                officer_id="IO-01",
                version="1.0",
                amendment_of=self.orig_doc_hash,
            )
        self.assertIn("cannot specify 'amendment_of'", str(ctx.exception))


class TestVersionHistoryRetrieval(unittest.TestCase):
    """Tests for document version history and amendment tracking."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.engine = ChainEngine(hash_service=self.hash_service)
        self.case_id = "CASE-VERSION-HISTORY"

        # Doc 1: FIR (V1.0)
        self.doc1_hash = _compute_hash("FIR Content V1.0")
        self.doc1_rec = self.engine.create_genesis(
            case_id=self.case_id,
            document_id="DOC-FIR",
            doc_hash=self.doc1_hash,
            officer_id="IO-01",
        )

        # Doc 2: Unrelated Seizure Memo (V1.0)
        self.doc2_hash = _compute_hash("Seizure Memo V1.0")
        self.doc2_rec = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-SEIZURE",
            doc_hash=self.doc2_hash,
            officer_id="IO-01",
            version="1.0",
        )

        # Doc 1 Amendment 1 (V1.1)
        self.doc1_v11_hash = _compute_hash("FIR Supplementary Information V1.1")
        self.doc1_v11_rec = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-FIR-A1",
            doc_hash=self.doc1_v11_hash,
            officer_id="IO-01",
            version="1.1",
            quorum_token="QUORUM-1",
            amendment_of=self.doc1_hash,
        )

        # Doc 1 Amendment 2 (V1.2)
        self.doc1_v12_hash = _compute_hash("FIR Court Errata Correction V1.2")
        self.doc1_v12_rec = self.engine.append_document(
            case_id=self.case_id,
            document_id="DOC-FIR-A2",
            doc_hash=self.doc1_v12_hash,
            officer_id="REGISTRAR-COURT-02",
            version="1.2",
            quorum_token="QUORUM-2",
            amendment_of=self.doc1_hash,
        )

    def test_get_version_history_full(self) -> None:
        history = self.engine.get_version_history(self.case_id, self.doc1_hash)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].version, "1.0")
        self.assertEqual(history[0].doc_hash, self.doc1_hash)
        self.assertEqual(history[1].version, "1.1")
        self.assertEqual(history[1].doc_hash, self.doc1_v11_hash)
        self.assertEqual(history[2].version, "1.2")
        self.assertEqual(history[2].doc_hash, self.doc1_v12_hash)

        # Ensure unrelated Doc 2 is NOT in Doc 1's version history
        for rec in history:
            self.assertNotEqual(rec.document_id, "DOC-SEIZURE")

    def test_get_version_history_amendments_only(self) -> None:
        amendments = self.engine.get_amendments(self.case_id, self.doc1_hash)
        self.assertEqual(len(amendments), 2)
        self.assertEqual(amendments[0].version, "1.1")
        self.assertEqual(amendments[1].version, "1.2")

    def test_query_version_history_via_amendment_hash(self) -> None:
        # Querying using V1.1 hash should automatically resolve to full lineage
        history = self.engine.get_version_history(self.case_id, self.doc1_v11_hash)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0].version, "1.0")
        self.assertEqual(history[1].version, "1.1")
        self.assertEqual(history[2].version, "1.2")

    def test_get_version_history_unrelated_hash(self) -> None:
        history = self.engine.get_version_history(self.case_id, _compute_hash("Unrelated"))
        self.assertEqual(history, [])

    def test_get_version_history_nonexistent_case(self) -> None:
        with self.assertRaises(ChainNotFoundError):
            self.engine.get_version_history("CASE-NONEXISTENT", self.doc1_hash)


class TestImmutabilityEnforcement(unittest.TestCase):
    """Tests verifying WORM append-only immutability guarantees."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.engine = ChainEngine(hash_service=self.hash_service)
        self.case_id = "CASE-IMMUTABLE"

        self.doc_hash = _compute_hash("Locked Evidence V1.0")
        self.record = self.engine.create_genesis(
            case_id=self.case_id,
            document_id="DOC-LOCKED-01",
            doc_hash=self.doc_hash,
            officer_id="IO-01",
        )

    def test_cannot_overwrite_v1_document(self) -> None:
        # Re-appending document with same document_id as V1.0 must fail
        with self.assertRaises(ChainImmutabilityError) as ctx:
            self.engine.append_document(
                case_id=self.case_id,
                document_id="DOC-LOCKED-01",
                doc_hash=_compute_hash("Attempted Overwrite Content"),
                officer_id="ROGUE-01",
                version="1.0",
            )
        self.assertIn("already exists in case", str(ctx.exception))
        self.assertIn("permanently immutable", str(ctx.exception))

    def test_enforce_immutability_method(self) -> None:
        # Direct check on existing doc raises ChainImmutabilityError
        with self.assertRaises(ChainImmutabilityError):
            self.engine._enforce_immutability(self.case_id, "DOC-LOCKED-01")

        # Direct check on new/non-existing doc does not raise
        try:
            self.engine._enforce_immutability(self.case_id, "DOC-NEW-ID")
        except Exception as exc:
            self.fail(f"_enforce_immutability raised unexpectedly on new doc: {exc}")

    def test_frozen_dataclass_prevents_attribute_mutation(self) -> None:
        # ChainRecord must be frozen and throw FrozenInstanceError
        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.record.doc_hash = "modified_hash"  # type: ignore[misc]

        with self.assertRaises(dataclasses.FrozenInstanceError):
            self.record.officer_id = "new_officer"  # type: ignore[misc]

    def test_get_chain_defensive_copy(self) -> None:
        # External modification of returned chain list does not affect engine
        chain = self.engine.get_chain(self.case_id)
        self.assertEqual(len(chain), 1)

        chain.clear()  # Mutate external list
        self.assertEqual(len(chain), 0)

        # Engine chain must remain untouched
        internal_chain = self.engine.get_chain(self.case_id)
        self.assertEqual(len(internal_chain), 1)
        self.assertEqual(internal_chain[0].document_id, "DOC-LOCKED-01")


class TestConcurrentChainAppends(unittest.TestCase):
    """Tests verifying thread safety and race-free serialized appends."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.engine = ChainEngine(hash_service=self.hash_service)
        self.case_id = "CASE-CONCURRENCY-STRESS"

        self.engine.create_genesis(
            case_id=self.case_id,
            document_id="DOC-GENESIS",
            doc_hash=_compute_hash("Genesis link"),
            officer_id="IO-CHIEF",
        )

    def test_concurrent_appends_atomic_ordering(self) -> None:
        num_threads = 20
        num_docs_per_thread = 5
        total_expected_appends = num_threads * num_docs_per_thread

        def append_task(thread_idx: int, doc_idx: int) -> ChainRecord:
            doc_id = f"DOC-T{thread_idx:02d}-D{doc_idx:02d}"
            doc_hash = _compute_hash(f"Concurrent evidence from thread {thread_idx} doc {doc_idx}")
            officer_id = f"IO-THREAD-{thread_idx}"
            return self.engine.append_document(
                case_id=self.case_id,
                document_id=doc_id,
                doc_hash=doc_hash,
                officer_id=officer_id,
            )

        tasks = [
            (t, d)
            for t in range(num_threads)
            for d in range(num_docs_per_thread)
        ]

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(append_task, t, d) for t, d in tasks]
            results = [f.result() for f in futures]

        self.assertEqual(len(results), total_expected_appends)

        # Full chain should have 1 (genesis) + total_expected_appends links
        chain = self.engine.get_chain(self.case_id)
        self.assertEqual(len(chain), total_expected_appends + 1)

        # Sequence numbers must be strictly sequential 0..N-1
        seq_numbers = [r.sequence_number for r in chain]
        self.assertEqual(seq_numbers, list(range(len(chain))))

        # Continuity: each link's prev_chain_hash must equal preceding chain_hash
        for i in range(1, len(chain)):
            self.assertEqual(chain[i].prev_chain_hash, chain[i - 1].chain_hash)

        # Entire chain must cryptographically verify as intact
        self.assertTrue(self.engine.verify_chain_integrity(self.case_id))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    unittest.main()
