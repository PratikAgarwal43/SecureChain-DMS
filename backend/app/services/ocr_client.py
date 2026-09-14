"""
backend/app/services/ocr_client.py
-----------------------------------
Asynchronous HTTP client for integrating the AI-OCR Pipeline microservice
into the SecureChain DMS FastAPI backend.
"""

import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

FORGERY_THRESHOLD = 0.75


class OCRClient:
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OCR_SERVICE_URL).rstrip("/")
        self.timeout = timeout or settings.OCR_SERVICE_TIMEOUT

    async def scan_document(
        self,
        file_bytes: bytes,
        filename: str,
        officer_id: Optional[str] = None,
        case_mode: str = "Register New FIR (first time)",
        is_fir: bool = True,
        linked_fir_number: str = "",
        quick_mode: bool = True,
    ) -> Dict[str, Any]:
        """
        Submits file bytes to the OCR pipeline microservice for text extraction,
        forensic ELA forgery detection, and sensitivity classification.

        Returns a standardized dictionary with normalized fields:
        {
            "suggested_sensitivity": "LOW" | "MEDIUM" | "HIGH",
            "tamper_score": float,
            "forgery_detected": bool,
            "forensic_alert_level": str,
            "matched_high_risk_terms": list,
            "matched_medium_risk_terms": list,
            "ela_preview_base64_png": str | None,
            "ocr_records": list,
            "worm_log": list,
            "is_online": bool
        }
        """
        file_field = "fir_file" if is_fir else "supporting_files"

        data = {
            "case_mode": case_mode,
            "officer_id": officer_id or "",
            "linked_fir_number": linked_fir_number or "",
            "quick_mode": "true" if quick_mode else "false",
        }

        # Select appropriate mime type hint if available
        mime_type = "application/pdf" if filename.lower().endswith(".pdf") else "image/jpeg"
        files = {file_field: (filename, file_bytes, mime_type)}

        url = f"{self.base_url}/api/case/submit"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, data=data, files=files)
                response.raise_for_status()
                result = response.json()

            sensitivity = result.get("sensitivity", {})
            worm_log = result.get("worm_log", [])
            records = result.get("records", [])

            # Extract highest tamper probability across processed pages
            tamper_score = 0.0
            forensic_alert = "INTEGRITY CHECK PASSED"
            for log_entry in worm_log:
                raw_prob = log_entry.get("pixel_anomaly_coefficient", 0.0)
                try:
                    prob = float(raw_prob)
                except (ValueError, TypeError):
                    prob = 0.0

                if prob > tamper_score:
                    tamper_score = prob
                    forensic_alert = log_entry.get("forensic_alert_level", forensic_alert)

            tier_map = {"High": "HIGH", "Medium": "MEDIUM", "Low": "LOW"}
            raw_tier = sensitivity.get("suggested_sensitivity_tier", "Medium")
            suggested_tier = tier_map.get(raw_tier, "MEDIUM")

            return {
                "suggested_sensitivity": suggested_tier,
                "tamper_score": round(tamper_score, 4),
                "forgery_detected": tamper_score >= FORGERY_THRESHOLD,
                "forensic_alert_level": forensic_alert,
                "matched_high_risk_terms": sensitivity.get("matched_high_risk_terms", []),
                "matched_medium_risk_terms": sensitivity.get("matched_medium_risk_terms", []),
                "ela_preview_base64_png": result.get("ela_preview_base64_png"),
                "ocr_records": records,
                "worm_log": worm_log,
                "is_online": True,
            }

        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            logger.warning(f"AI-OCR service is offline or unreachable at {self.base_url}: {exc}")
            return self._offline_response("SERVICE_OFFLINE", f"OCR service unreachable: {exc}")

        except httpx.TimeoutException as exc:
            logger.warning(f"AI-OCR service request timed out after {self.timeout}s: {exc}")
            return self._offline_response("SERVICE_TIMEOUT", f"OCR request timed out: {exc}")

        except httpx.HTTPStatusError as exc:
            logger.error(f"AI-OCR service returned HTTP error status {exc.response.status_code}: {exc}")
            return self._offline_response(
                f"HTTP_ERROR_{exc.response.status_code}",
                f"OCR service error {exc.response.status_code}",
            )

        except (json.JSONDecodeError, KeyError, ValueError) as exc:
            logger.error(f"AI-OCR service returned malformed or unexpected response format: {exc}")
            return self._offline_response("MALFORMED_RESPONSE", f"OCR invalid JSON response: {exc}")

        except Exception as exc:
            logger.error(f"Unexpected error when communicating with AI-OCR service: {exc}")
            return self._offline_response("UNEXPECTED_ERROR", str(exc))

    def _offline_response(self, alert_level: str, detail: str) -> Dict[str, Any]:
        """
        Structured fallback response when OCR microservice is unavailable or fails.
        Crucially sets `is_online: False` and `forensic_alert_level` to an explicit status
        so callers know forensic inspection was not completed.
        """
        return {
            "suggested_sensitivity": "MEDIUM",
            "tamper_score": 0.0,
            "forgery_detected": False,
            "forensic_alert_level": alert_level,
            "matched_high_risk_terms": [],
            "matched_medium_risk_terms": [],
            "ela_preview_base64_png": None,
            "ocr_records": [],
            "worm_log": [],
            "is_online": False,
            "error_detail": detail,
        }


# Singleton instance for application-wide imports
ocr_client = OCRClient()
