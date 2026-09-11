"""
SecureChain DMS — Tamper Alert System (Module 7)
================================================
Cryptographic incident detection, notification, and WORM-compliant alerting
engine for the Zero-Trust Digital Evidence Vault (SIH26190).

Legal & Forensic Compliance:
----------------------------
Under Section 65B of the Indian Evidence Act, 1872 and Section 63 of the
Bharatiya Sakshya Adhiniyam (BSA), 2023, court evidence integrity requires not
only tamper-evident chains of custody, but also immediate, non-repudiable
audit logging whenever any cryptographic inconsistency is detected.

This module provides an append-only WORM (Write-Once, Read-Many) alert ledger
and dispatch engine. Once recorded, tamper alerts can never be deleted or
purged. Every alert exported for archival storage includes a self-authenticating
canonical SHA-256 `log_hash`.

Security Architecture:
----------------------
1. Append-Only WORM Alert Store:
   The alert log strictly prohibits deletion (`clear_alerts()` raises
   `TamperAlertError`). Once an alert is raised, it remains in the permanent
   audit trail to prevent insider tampering or suppression of forensic alerts.

2. Multi-Channel Subscriber Notifications:
   Dispatches alerts to registered observers (Court Registry, WORM Audit Log,
   Security Operations Center) using an isolated fail-safe dispatch loop so
   that subscriber exceptions cannot disrupt the alerting engine.

3. Canonical Self-Verifying WORM Export:
   Serialized alert entries are bound to an immutable SHA-256 digest (`log_hash`),
   allowing downstream storage backends (e.g. AWS S3 Object Lock or optical WORM)
   to prove that the alert record itself was never modified.

4. Thread-Safe Concurrent Operations:
   Protected by `threading.RLock` ensuring race-free alert registration and
   subscriber management across concurrent worker threads.

5. Zero Sensitive Data Leakage in Logs:
   Alert messages record case IDs, document IDs, severity levels, and hash digests.
   Plaintext content and cryptographic key material are never logged.
"""

from __future__ import annotations

import dataclasses
import hashlib
import hmac
import json
import logging
import threading
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from securechain_security.chain_verifier import ChainVerifier, VerificationError
from securechain_security.models import (
    ChainStatus,
    TamperAlert,
    TamperSeverity,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class TamperAlertError(Exception):
    """
    Raised when an alerting, dispatch, or WORM immutability violation occurs.

    Attributes:
        message: Human-readable error description.
        cause: Underlying caught exception, if applicable.
    """

    def __init__(self, message: str, cause: Optional[Exception] = None) -> None:
        super().__init__(message)
        self.message = message
        self.cause = cause


# ---------------------------------------------------------------------------
# Tamper Alert System
# ---------------------------------------------------------------------------

class TamperAlertSystem:
    """
    WORM-compliant notification and alerting engine for cryptographic
    integrity violations across digital evidence vaults.
    """

    def __init__(self, chain_verifier: ChainVerifier) -> None:
        """
        Initialize the TamperAlertSystem.

        Args:
            chain_verifier: Dependency-injected ChainVerifier service.

        Raises:
            ValueError: If chain_verifier is None.
        """
        if chain_verifier is None:
            raise ValueError("chain_verifier cannot be None")

        self._chain_verifier: ChainVerifier = chain_verifier
        self._alerts: List[TamperAlert] = []
        self._subscribers: List[Callable[[TamperAlert], None]] = []
        self._lock: threading.RLock = threading.RLock()

        logger.info("TamperAlertSystem initialized successfully")

    @property
    def chain_verifier(self) -> ChainVerifier:
        """Return the underlying ChainVerifier instance."""
        return self._chain_verifier

    def subscribe(self, callback: Callable[[TamperAlert], None]) -> None:
        """
        Register a notification listener callback (e.g. Court Registry, WORM log writer).

        Args:
            callback: Callable accepting a single TamperAlert argument.

        Raises:
            ValueError: If callback is not callable.
        """
        if not callable(callback):
            raise ValueError("Subscriber callback must be callable")

        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)
                logger.info("Registered new tamper alert subscriber: %r", callback)

    def _dispatch_notifications(self, alert: TamperAlert) -> None:
        """
        Dispatch a tamper alert to all registered subscribers.

        Security Rationale:
            Subscriber errors are caught and logged so that an exception in one
            notification handler (e.g., webhook timeout) cannot abort notification
            to other critical observers (e.g., local WORM log writer).

        Args:
            alert: The TamperAlert to broadcast.
        """
        with self._lock:
            subscribers = list(self._subscribers)

        for subscriber in subscribers:
            try:
                subscriber(alert)
            except Exception as exc:
                logger.error(
                    "Subscriber %r failed during notification for alert '%s': %s",
                    subscriber,
                    alert.alert_id,
                    exc,
                    exc_info=True,
                )

    def check_and_alert(
        self,
        case_id: str,
        document_id: Optional[str] = None,
        file_content: Optional[bytes] = None,
    ) -> List[TamperAlert]:
        """
        Perform an integrity audit and generate, store, and dispatch alerts if tampered.

        Security Rationale:
            Coordinates dual-layer verification:
              1. Physical content verification (if document_id and file_content provided).
              2. Cryptographic hash chain verification for the entire case.
            Any detected anomaly produces an immediate, immutable TamperAlert
            dispatched to judicial subscribers.

        Args:
            case_id: Unique case identifier.
            document_id: Optional document identifier to verify raw bytes for.
            file_content: Optional raw physical document bytes.

        Returns:
            List of newly generated TamperAlert objects (empty if all checks pass).

        Raises:
            TamperAlertError: If parameters are invalid or verification crashes unexpectedly.
        """
        if not case_id or not isinstance(case_id, str) or not case_id.strip():
            raise TamperAlertError("case_id must be a non-empty string")

        if (document_id is not None and file_content is None) or (
            document_id is None and file_content is not None
        ):
            raise TamperAlertError(
                "Both document_id and file_content must be provided together for content verification"
            )

        new_alerts: List[TamperAlert] = []

        # 1. Verify physical document content if provided
        if document_id is not None and file_content is not None:
            try:
                doc_result = self._chain_verifier.verify_document_content(
                    case_id=case_id,
                    document_id=document_id,
                    file_stream_or_bytes=file_content,
                )
                if not doc_result.is_match:
                    doc_alert = TamperAlert(
                        case_id=case_id,
                        document_id=document_id,
                        severity=TamperSeverity.CRITICAL,
                        description=(
                            f"Document payload integrity violation for document '{document_id}' "
                            f"in case '{case_id}'. Content altered since registration."
                        ),
                        expected_hash=doc_result.stored_hash,
                        actual_hash=doc_result.computed_hash,
                        detected_by="on_retrieval",
                    )
                    new_alerts.append(doc_alert)
            except VerificationError as exc:
                doc_alert = TamperAlert(
                    case_id=case_id,
                    document_id=document_id,
                    severity=TamperSeverity.CRITICAL,
                    description=f"Document content audit failed for '{document_id}' in case '{case_id}': {exc}",
                    detected_by="on_retrieval",
                )
                new_alerts.append(doc_alert)

        # 2. Verify hash chain integrity for the case
        try:
            chain_result = self._chain_verifier.verify_case(case_id)
            if chain_result.status != ChainStatus.INTACT:
                chain_alert = self._chain_verifier.generate_tamper_report(case_id, chain_result)
                new_alerts.append(chain_alert)
        except VerificationError as exc:
            chain_alert = TamperAlert(
                case_id=case_id,
                document_id=document_id or "",
                severity=TamperSeverity.HIGH,
                description=f"Cryptographic chain verification failure for case '{case_id}': {exc}",
                detected_by="chain_walk",
            )
            new_alerts.append(chain_alert)

        # 3. Store new alerts in WORM alert ledger
        with self._lock:
            for alert in new_alerts:
                self._alerts.append(alert)

        # 4. Dispatch notifications to all subscribers
        for alert in new_alerts:
            self._dispatch_notifications(alert)

        logger.info(
            "check_and_alert finished for case '%s' (new_alerts: %d)",
            case_id,
            len(new_alerts),
        )
        return new_alerts

    def get_alerts(
        self,
        case_id: Optional[str] = None,
        severity: Optional[Union[TamperSeverity, str]] = None,
        since: Optional[Union[str, datetime]] = None,
    ) -> List[TamperAlert]:
        """
        Query recorded tamper alerts with optional filters.

        Args:
            case_id: Filter by case identifier.
            severity: Filter by TamperSeverity enum or severity string.
            since: Filter by ISO 8601 timestamp string or datetime (inclusive).

        Returns:
            List of matching TamperAlert objects.
        """
        target_severity_str: Optional[str] = None
        if severity is not None:
            target_severity_str = (
                severity.value if hasattr(severity, "value") else str(severity).upper()
            )

        since_dt: Optional[datetime] = None
        if since is not None:
            if isinstance(since, datetime):
                since_dt = since if since.tzinfo else since.replace(tzinfo=timezone.utc)
            elif isinstance(since, str):
                try:
                    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
                except Exception:
                    since_dt = None

        with self._lock:
            results: List[TamperAlert] = []
            for alert in self._alerts:
                # Filter by case_id
                if case_id is not None and alert.case_id != case_id:
                    continue

                # Filter by severity
                if target_severity_str is not None:
                    alert_severity_str = (
                        alert.severity.value
                        if hasattr(alert.severity, "value")
                        else str(alert.severity).upper()
                    )
                    if alert_severity_str != target_severity_str:
                        continue

                # Filter by timestamp
                if since_dt is not None:
                    try:
                        alert_dt = datetime.fromisoformat(alert.timestamp.replace("Z", "+00:00"))
                        if alert_dt < since_dt:
                            continue
                    except Exception:
                        if alert.timestamp < str(since):
                            continue
                elif since is not None and alert.timestamp < str(since):
                    continue

                results.append(alert)

            return list(results)

    def get_alert_summary(self) -> Dict[str, Any]:
        """
        Return summary statistics of recorded alerts.

        Returns:
            Dictionary containing:
              - 'total_alerts': total number of alerts
              - 'by_severity': count mapping for CRITICAL, HIGH, MEDIUM, LOW
              - 'cases_affected': count of unique affected cases
              - 'affected_case_ids': list of affected case IDs
        """
        with self._lock:
            by_severity: Dict[str, int] = {
                TamperSeverity.CRITICAL.value: 0,
                TamperSeverity.HIGH.value: 0,
                TamperSeverity.MEDIUM.value: 0,
                TamperSeverity.LOW.value: 0,
            }
            unique_cases: set[str] = set()

            for alert in self._alerts:
                sev_str = (
                    alert.severity.value
                    if hasattr(alert.severity, "value")
                    else str(alert.severity).upper()
                )
                if sev_str in by_severity:
                    by_severity[sev_str] += 1
                else:
                    by_severity[sev_str] = 1

                if alert.case_id:
                    unique_cases.add(alert.case_id)

            return {
                "total_alerts": len(self._alerts),
                "by_severity": by_severity,
                "cases_affected": len(unique_cases),
                "affected_case_ids": sorted(list(unique_cases)),
            }

    def export_for_worm_log(self, alert: TamperAlert) -> Dict[str, Any]:
        """
        Serialize a TamperAlert into an immutable dictionary with a canonical self-hash.

        Security Rationale:
            Under Section 65B and BSA 2023 §63, tamper alert logs presented in court
            must be tamper-proof themselves. The returned dictionary includes a
            `log_hash` calculated over all other fields using canonical JSON encoding.

        Args:
            alert: The TamperAlert to serialize.

        Returns:
            Dictionary with all alert attributes plus a SHA-256 `log_hash`.
        """
        sev_str = (
            alert.severity.value
            if hasattr(alert.severity, "value")
            else str(alert.severity).upper()
        )

        entry: Dict[str, Any] = {
            "alert_id": alert.alert_id,
            "case_id": alert.case_id,
            "document_id": alert.document_id,
            "severity": sev_str,
            "description": alert.description,
            "expected_hash": alert.expected_hash,
            "actual_hash": alert.actual_hash,
            "detected_by": alert.detected_by,
            "timestamp": alert.timestamp,
        }

        canonical_json = json.dumps(entry, sort_keys=True).encode("utf-8")
        entry["log_hash"] = hashlib.sha256(canonical_json).hexdigest()
        return entry

    @staticmethod
    def verify_worm_log_entry(entry: Dict[str, Any]) -> bool:
        """
        Verify the mathematical integrity of a WORM log entry's self-hash.

        Args:
            entry: WORM log entry dictionary containing `log_hash`.

        Returns:
            True if `log_hash` matches the recomputed digest; False otherwise.
        """
        if not isinstance(entry, dict) or "log_hash" not in entry:
            return False

        expected_hash = entry["log_hash"]
        payload_dict = {k: v for k, v in entry.items() if k != "log_hash"}
        canonical_json = json.dumps(payload_dict, sort_keys=True).encode("utf-8")
        recomputed_hash = hashlib.sha256(canonical_json).hexdigest()

        return hmac.compare_digest(
            recomputed_hash.lower().strip(),
            expected_hash.lower().strip(),
        )

    def clear_alerts(self) -> None:
        """
        Attempting to clear or delete WORM audit alerts is strictly prohibited.

        Raises:
            TamperAlertError: Always raised to enforce append-only WORM compliance.
        """
        raise TamperAlertError("WORM audit log entries cannot be deleted")
