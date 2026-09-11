"""
services/ocr_client.py — HTTP client for calling the AI-OCR Pipeline (Port 8001).
Calls POST /api/case/submit and returns the sensitivity + ELA tamper score.
"""
import httpx
import logging
from config import settings

logger = logging.getLogger(__name__)

# Tamper score threshold above which a document is flagged as FORGED
FORGERY_THRESHOLD = 0.75


async def scan_document(file_bytes: bytes, filename: str, officer_id: str, case_mode: str = "New FIR Registration") -> dict:
    """
    Send a document to the AI-OCR service for:
    - Text extraction (OCR)
    - Sensitivity classification (LOW/MEDIUM/HIGH)
    - ELA forgery/tamper detection (0.0 - 1.0 score)

    Returns a structured dict with the scan results.
    """
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.ocr_service_url}/api/case/submit",
                data={
                    "case_mode": case_mode,
                    "officer_id": officer_id,
                    "quick_mode": "true",
                },
                files={"fir_file": (filename, file_bytes, "application/octet-stream")}
            )
            response.raise_for_status()
            result = response.json()

        sensitivity = result.get("sensitivity", {})
        worm_log = result.get("worm_log", [])

        # Extract tamper probability from worm_log entries
        tamper_score = 0.0
        forgery_detected = False
        for log_entry in worm_log:
            prob = log_entry.get("tamper_probability", 0.0)
            if prob > tamper_score:
                tamper_score = prob
        if tamper_score >= FORGERY_THRESHOLD:
            forgery_detected = True

        # Map tier string to our DB enum
        tier_map = {
            "High": "HIGH",
            "Medium": "MEDIUM",
            "Low": "LOW",
        }
        suggested_tier = tier_map.get(
            sensitivity.get("suggested_sensitivity_tier", "Medium"), "MEDIUM"
        )

        return {
            "suggested_sensitivity": suggested_tier,
            "tamper_score": round(tamper_score, 4),
            "forgery_detected": forgery_detected,
            "matched_high_risk_terms": sensitivity.get("matched_high_risk_terms", []),
            "matched_medium_risk_terms": sensitivity.get("matched_medium_risk_terms", []),
            "ela_preview_base64_png": result.get("ela_preview_base64_png"),
            "ocr_records": result.get("records", []),
        }

    except httpx.ConnectError:
        logger.warning("AI-OCR service is offline. Skipping scan, defaulting to MEDIUM sensitivity.")
        return {
            "suggested_sensitivity": "MEDIUM",
            "tamper_score": 0.0,
            "forgery_detected": False,
            "matched_high_risk_terms": [],
            "matched_medium_risk_terms": [],
            "ela_preview_base64_png": None,
            "ocr_records": [],
        }
    except Exception as e:
        logger.error(f"AI-OCR scan failed: {e}")
        raise
