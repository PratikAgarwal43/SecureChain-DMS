"""
Unit tests for SecureChain DMS Tamper Alert System (Module 7).
==============================================================
Validates WORM-compliant incident alerting, subscriber notification dispatch,
multi-criteria alert queries, summary telemetry, self-hashing WORM export,
deletion prohibition, and concurrent thread-safe alert storage.
"""

from __future__ import annotations

import dataclasses
import hashlib
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

from securechain_security.chain_engine import ChainEngine
from securechain_security.chain_verifier import ChainVerifier
from securechain_security.hash_service import HashService
from securechain_security.models import (
    TamperAlert,
    TamperSeverity,
)
from securechain_security.tamper_alerts import (
    TamperAlertError,
    TamperAlertSystem,
)


def _compute_hash(content: bytes | str) -> str:
    """Helper to compute deterministic SHA-256."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


class TestTamperAlertSystem(unittest.TestCase):
    """Test suite for TamperAlertSystem."""

    def setUp(self) -> None:
        self.hash_service = HashService()
        self.chain_engine = ChainEngine(hash_service=self.hash_service)
        self.chain_verifier = ChainVerifier(
            chain_engine=self.chain_engine,
            hash_service=self.hash_service,
        )
        self.alert_system = TamperAlertSystem(chain_verifier=self.chain_verifier)

        self.case_id = "CASE-2026-CRIME-001"
        self.doc_id = "DOC-CCTV-001"
        self.doc_raw = b"CCTV Footage from Crime Scene - 1080p stream"
        self.doc_hash = _compute_hash(self.doc_raw)

        # Set up a clean initial chain
        self.chain_engine.create_genesis(
            case_id=self.case_id,
            document_id=self.doc_id,
            doc_hash=self.doc_hash,
            officer_id="IO-SHREYASH-01",
        )

    def test_init_invalid_args(self) -> None:
        with self.assertRaises(ValueError):
            TamperAlertSystem(chain_verifier=None)  # type: ignore[arg-type]

    def test_clean_verification_no_alerts(self) -> None:
        alerts = self.alert_system.check_and_alert(
            case_id=self.case_id,
            document_id=self.doc_id,
            file_content=self.doc_raw,
        )
        self.assertEqual(len(alerts), 0)
        self.assertEqual(len(self.alert_system.get_alerts()), 0)

        # Clean check with only case_id
        alerts_case_only = self.alert_system.check_and_alert(case_id=self.case_id)
        self.assertEqual(len(alerts_case_only), 0)

    def test_alert_generation_on_tampered_document_content(self) -> None:
        tampered_content = b"Altered CCTV footage with missing frames"
        alerts = self.alert_system.check_and_alert(
            case_id=self.case_id,
            document_id=self.doc_id,
            file_content=tampered_content,
        )

        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.case_id, self.case_id)
        self.assertEqual(alert.document_id, self.doc_id)
        self.assertEqual(alert.severity, TamperSeverity.CRITICAL)
        self.assertEqual(alert.detected_by, "on_retrieval")
        self.assertEqual(alert.expected_hash, self.doc_hash)
        self.assertEqual(alert.actual_hash, _compute_hash(tampered_content))

        # Check that alert was persisted in internal WORM ledger
        stored = self.alert_system.get_alerts()
        self.assertEqual(len(stored), 1)
        self.assertEqual(stored[0].alert_id, alert.alert_id)

    def test_alert_generation_on_tampered_chain(self) -> None:
        # Tamper with the chain link
        chain = self.chain_engine._chains[self.case_id]
        chain[0] = dataclasses.replace(chain[0], chain_hash="f" * 64)

        alerts = self.alert_system.check_and_alert(case_id=self.case_id)
        self.assertEqual(len(alerts), 1)
        alert = alerts[0]
        self.assertEqual(alert.case_id, self.case_id)
        self.assertEqual(alert.severity, TamperSeverity.HIGH)
        self.assertEqual(alert.detected_by, "chain_walk")

        stored = self.alert_system.get_alerts(case_id=self.case_id)
        self.assertEqual(len(stored), 1)

    def test_alert_generation_both_content_and_chain_tampered(self) -> None:
        # Break chain
        chain = self.chain_engine._chains[self.case_id]
        chain[0] = dataclasses.replace(chain[0], chain_hash="0" * 64)

        # Also provide modified content
        tampered_content = b"Bad content"
        alerts = self.alert_system.check_and_alert(
            case_id=self.case_id,
            document_id=self.doc_id,
            file_content=tampered_content,
        )

        # Expect both CRITICAL (content) and HIGH (chain) alerts
        self.assertEqual(len(alerts), 2)
        severities = {a.severity for a in alerts}
        self.assertIn(TamperSeverity.CRITICAL, severities)
        self.assertIn(TamperSeverity.HIGH, severities)

    def test_subscriber_notification_dispatch(self) -> None:
        dispatched_alerts: list[TamperAlert] = []

        def mock_subscriber(alert: TamperAlert) -> None:
            dispatched_alerts.append(alert)

        def faulty_subscriber(alert: TamperAlert) -> None:
            raise RuntimeError("Subscriber network error simulated")

        self.alert_system.subscribe(mock_subscriber)
        self.alert_system.subscribe(faulty_subscriber)

        tampered_content = b"Corrupted video data"
        new_alerts = self.alert_system.check_and_alert(
            case_id=self.case_id,
            document_id=self.doc_id,
            file_content=tampered_content,
        )

        self.assertEqual(len(new_alerts), 1)
        self.assertEqual(len(dispatched_alerts), 1)
        self.assertEqual(dispatched_alerts[0].alert_id, new_alerts[0].alert_id)

    def test_subscribe_invalid(self) -> None:
        with self.assertRaises(ValueError):
            self.alert_system.subscribe("not-callable")  # type: ignore[arg-type]

    def test_check_and_alert_invalid_args(self) -> None:
        with self.assertRaises(TamperAlertError):
            self.alert_system.check_and_alert("")
        with self.assertRaises(TamperAlertError):
            self.alert_system.check_and_alert(self.case_id, document_id="DOC-1", file_content=None)
        with self.assertRaises(TamperAlertError):
            self.alert_system.check_and_alert(self.case_id, document_id=None, file_content=b"content")

    def test_alert_filtering(self) -> None:
        # Create multiple alerts
        now = datetime.now(timezone.utc)

        alert1 = TamperAlert(
            case_id="CASE-AAA",
            document_id="DOC-1",
            severity=TamperSeverity.CRITICAL,
            timestamp=(now - timedelta(hours=2)).isoformat(),
        )
        alert2 = TamperAlert(
            case_id="CASE-AAA",
            document_id="DOC-2",
            severity=TamperSeverity.HIGH,
            timestamp=(now - timedelta(hours=1)).isoformat(),
        )
        alert3 = TamperAlert(
            case_id="CASE-BBB",
            document_id="DOC-3",
            severity=TamperSeverity.MEDIUM,
            timestamp=now.isoformat(),
        )

        self.alert_system._alerts.extend([alert1, alert2, alert3])

        # Filter by case_id
        case_a_alerts = self.alert_system.get_alerts(case_id="CASE-AAA")
        self.assertEqual(len(case_a_alerts), 2)

        # Filter by severity (enum and string)
        crit_alerts = self.alert_system.get_alerts(severity=TamperSeverity.CRITICAL)
        self.assertEqual(len(crit_alerts), 1)
        self.assertEqual(crit_alerts[0].document_id, "DOC-1")

        high_alerts = self.alert_system.get_alerts(severity="HIGH")
        self.assertEqual(len(high_alerts), 1)
        self.assertEqual(high_alerts[0].document_id, "DOC-2")

        # Filter by since timestamp
        since_cutoff = (now - timedelta(minutes=90)).isoformat()
        recent_alerts = self.alert_system.get_alerts(since=since_cutoff)
        self.assertEqual(len(recent_alerts), 2)
        self.assertEqual({a.document_id for a in recent_alerts}, {"DOC-2", "DOC-3"})

        # Combined filter
        combined = self.alert_system.get_alerts(case_id="CASE-AAA", severity=TamperSeverity.HIGH)
        self.assertEqual(len(combined), 1)
        self.assertEqual(combined[0].document_id, "DOC-2")

    def test_get_alert_summary(self) -> None:
        alert1 = TamperAlert(case_id="CASE-X", severity=TamperSeverity.CRITICAL)
        alert2 = TamperAlert(case_id="CASE-X", severity=TamperSeverity.HIGH)
        alert3 = TamperAlert(case_id="CASE-Y", severity=TamperSeverity.HIGH)
        alert4 = TamperAlert(case_id="CASE-Z", severity=TamperSeverity.LOW)

        self.alert_system._alerts.extend([alert1, alert2, alert3, alert4])

        summary = self.alert_system.get_alert_summary()
        self.assertEqual(summary["total_alerts"], 4)
        self.assertEqual(summary["cases_affected"], 3)
        self.assertEqual(set(summary["affected_case_ids"]), {"CASE-X", "CASE-Y", "CASE-Z"})
        self.assertEqual(summary["by_severity"]["CRITICAL"], 1)
        self.assertEqual(summary["by_severity"]["HIGH"], 2)
        self.assertEqual(summary["by_severity"]["LOW"], 1)
        self.assertEqual(summary["by_severity"]["MEDIUM"], 0)

    def test_export_for_worm_log_and_verification(self) -> None:
        alert = TamperAlert(
            case_id="CASE-WORM-TEST",
            document_id="DOC-99",
            severity=TamperSeverity.CRITICAL,
            description="Forensic payload alteration detected",
            expected_hash="a" * 64,
            actual_hash="b" * 64,
            detected_by="on_retrieval",
        )

        entry = self.alert_system.export_for_worm_log(alert)
        self.assertIsInstance(entry, dict)
        self.assertIn("log_hash", entry)
        self.assertEqual(entry["case_id"], "CASE-WORM-TEST")
        self.assertEqual(entry["severity"], "CRITICAL")
        self.assertEqual(entry["alert_id"], alert.alert_id)

        # Verify valid log entry self-hash
        self.assertTrue(TamperAlertSystem.verify_worm_log_entry(entry))

        # Tampering with entry breaks verification
        entry["severity"] = "LOW"
        self.assertFalse(TamperAlertSystem.verify_worm_log_entry(entry))

        # Invalid entry structures
        self.assertFalse(TamperAlertSystem.verify_worm_log_entry({}))
        self.assertFalse(TamperAlertSystem.verify_worm_log_entry(None))  # type: ignore[arg-type]

    def test_worm_deletion_prohibition(self) -> None:
        # clear_alerts must be forbidden under WORM rules
        with self.assertRaises(TamperAlertError) as ctx:
            self.alert_system.clear_alerts()
        self.assertIn("cannot be deleted", str(ctx.exception))

    def test_concurrent_alert_storage_thread_safety(self) -> None:
        num_threads = 20
        alerts_per_thread = 5

        def worker(thread_idx: int) -> None:
            for i in range(alerts_per_thread):
                alert = TamperAlert(
                    case_id=f"CASE-THREAD-{thread_idx}",
                    document_id=f"DOC-{i}",
                    severity=TamperSeverity.HIGH,
                )
                with self.alert_system._lock:
                    self.alert_system._alerts.append(alert)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        stored_alerts = self.alert_system.get_alerts()
        self.assertEqual(len(stored_alerts), num_threads * alerts_per_thread)

        summary = self.alert_system.get_alert_summary()
        self.assertEqual(summary["total_alerts"], num_threads * alerts_per_thread)
        self.assertEqual(summary["cases_affected"], num_threads)


if __name__ == "__main__":
    unittest.main()
