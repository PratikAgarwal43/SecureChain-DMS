"""
core/sensitivity_classifier.py
--------------------------------
Member 6 scope: "AI sensitivity suggestion" — matches the Adaptive
M-of-N Quorum Approval table from the SecureChain DMS architecture doc:

    Low     -> 1 checker         (internal notes)
    Medium  -> 2-of-3 approvers  (case updates, witness statements)
    High    -> 3-of-5 approvers  (chargesheets, forensic reports, evidence)

This is a lightweight keyword-based classifier for the hackathon MVP —
the architecture doc mentions "NLP-based classifier"; this is that
first pass, easily swappable later for a trained model.
"""

HIGH_SENSITIVITY_KEYWORDS = [
    "chargesheet", "charge sheet", "forensic", "evidence", "post mortem",
    "postmortem", "ballistic", "murder", "rape", "pocso", "302", "376",
    "316", "318", "303", "witness statement", "confession"
]

MEDIUM_SENSITIVITY_KEYWORDS = [
    "fir", "first information report", "complaint", "accused", "theft",
    "chori", "investigation", "case diary", "arrest"
]


def classify_sensitivity(extracted_json: dict) -> dict:
    """
    Takes the merged extraction JSON, scans the summary + sections +
    document text for keywords, and returns a suggested quorum tier.
    """
    searchable_text = " ".join([
        str(extracted_json.get("fir_description_english", "") or ""),
        " ".join(extracted_json.get("acts_and_sections", []) or []),
        str(extracted_json.get("items_of_interest", "") or ""),
    ]).lower()

    if any(kw in searchable_text for kw in HIGH_SENSITIVITY_KEYWORDS):
        tier = "High"
        quorum = "3-of-5 approvers required"
    elif any(kw in searchable_text for kw in MEDIUM_SENSITIVITY_KEYWORDS):
        tier = "Medium"
        quorum = "2-of-3 approvers required"
    else:
        tier = "Low"
        quorum = "1 checker required"

    matched_high = [kw for kw in HIGH_SENSITIVITY_KEYWORDS if kw in searchable_text]
    matched_medium = [kw for kw in MEDIUM_SENSITIVITY_KEYWORDS if kw in searchable_text]

    return {
        "suggested_sensitivity_tier": tier,
        "suggested_quorum": quorum,
        "matched_high_risk_terms": matched_high,
        "matched_medium_risk_terms": matched_medium,
        "note": "Officer must confirm or override this suggestion with a logged justification (per architecture doc, Section 07)."
    }
