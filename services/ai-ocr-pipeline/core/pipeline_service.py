"""
core/pipeline_service.py
--------------------------
Member 6 scope. This module holds ALL the orchestration logic (deblur ->
forensic -> OCR -> sensitivity -> WORM tagging) that used to live directly
inside app.py. It is UI-agnostic — it returns plain Python objects (dicts,
a PIL Image or None), never Gradio components or JSON strings.

Both front-ends reuse this same code:
  - app_gradio.py  (Hugging Face Spaces deployment)
  - api_fastapi.py (REST API for a custom frontend)

This avoids maintaining two copies of the pipeline logic.
"""

import os
import time
import uuid
import datetime
import json

import torch
from pdf2image import convert_from_path

from core.ocr_engine import QwenDocumentParser
from core.forensic_engine import ForensicAnalysisEngine
from core.image_preprocessing import DocumentDeblurEngine
from core.sensitivity_classifier import classify_sensitivity
from core.case_validation import validate_case_submission, NEW_FIR_MODE, EXISTING_CASE_MODE

# PROJECT_DIR: defaults to the Kaggle path (backward compatible with the
# notebook cells), overridden with SECURECHAIN_HOME in Docker/HF Spaces.
PROJECT_DIR = os.environ.get("SECURECHAIN_HOME", "/kaggle/working/SecureChain_DMS_Member6")
WORKDIR = os.path.join(PROJECT_DIR, "work")
os.makedirs(WORKDIR, exist_ok=True)

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

_TIER_RANK = {"Low": 0, "Medium": 1, "High": 2}

# --- Lazy singletons -------------------------------------------------------
# The GPU model is loaded once, on first use, and reused across requests.
_vlm_parser = None
_forensic_analyzer = None
_deblur_engine = None


def _get_engines():
    global _vlm_parser, _forensic_analyzer, _deblur_engine
    if _vlm_parser is None:
        print("[+] Initializing Sovereign Multi-Format Framework with Allocation Controls...")
        _vlm_parser = QwenDocumentParser()
        _forensic_analyzer = ForensicAnalysisEngine()
        _deblur_engine = DocumentDeblurEngine(blur_threshold=120.0)
    return _vlm_parser, _forensic_analyzer, _deblur_engine


def pdf_to_page_images(pdf_path: str) -> list:
    print(f"[+] PDF Ingestion Hook: Converting all pages of {pdf_path}")
    pages = convert_from_path(pdf_path, dpi=130)
    page_paths = []
    for idx, page in enumerate(pages):
        page_path = os.path.join(WORKDIR, f"pdf_page_{uuid.uuid4().hex}_{idx}.jpg")
        page.save(page_path, "JPEG")
        page_paths.append(page_path)
    return page_paths


def get_input_page_paths(file_path: str) -> list:
    if file_path.lower().endswith(".pdf"):
        return pdf_to_page_images(file_path)
    return [file_path]


def run_ocr_pipeline(file_path, quick_mode, document_type, linked_fir_number, officer_id):
    """
    Runs deblur -> forensic -> OCR -> sensitivity -> WORM tagging on ONE
    uploaded file. Returns a plain dict:
      {"record": {...}, "ela_preview": PIL.Image|None, "sensitivity": {...}, "worm_entry": {...}}
    """
    vlm_parser, forensic_analyzer, deblur_engine = _get_engines()
    torch.cuda.empty_cache()

    page_paths = get_input_page_paths(file_path)

    if quick_mode and len(page_paths) > 5:
        print(f"[+] Quick Mode ON: using first 5 of {len(page_paths)} pages.")
        page_paths = page_paths[:5]

    total_pages = len(page_paths)
    print(f"\n[+] === [{document_type}] Starting ingest: {total_pages} page(s) ===\n")

    clean_paths = []
    deblur_reports = []
    ela_preview = None
    worst_forensic_flag = "INTEGRITY CHECK PASSED"
    worst_probability = 0.0

    for idx, page_path in enumerate(page_paths):
        page_num = idx + 1
        print(f"[+] [{document_type}] Page {page_num}/{total_pages}: deblur + forensic check...")
        deblur_result = deblur_engine.process(page_path)
        deblur_reports.append(deblur_result)
        clean_path = deblur_result.get("output_path", page_path)
        clean_paths.append(clean_path)

        log_flag, probability, ela_img = forensic_analyzer.evaluate_integrity(clean_path)
        if probability > worst_probability:
            worst_probability = probability
            worst_forensic_flag = log_flag
            ela_preview = ela_img

        if os.path.dirname(page_path) == WORKDIR and "pdf_page_" in os.path.basename(page_path) and os.path.exists(page_path):
            os.remove(page_path)

    page_extractions = []
    for idx, clean_path in enumerate(clean_paths):
        page_num = idx + 1
        print(f"[+] [{document_type}] Page {page_num}/{total_pages}: running Qwen2-VL OCR extraction...")
        t0 = time.time()
        page_json = vlm_parser.extract_document(clean_path)
        print(f"    -> done in {time.time() - t0:.1f}s")
        page_extractions.append(page_json)
        torch.cuda.empty_cache()

    merged_record = vlm_parser.merge_page_results(page_extractions)

    for clean_path in clean_paths:
        if os.path.exists(clean_path):
            os.remove(clean_path)

    _KNOWN_SAMPLE_MARKERS = ["5106072250018", "Ajay Sharma", "Amrit Kumar Sah", "vij261167", "amr211082"]
    _record_str = json.dumps(merged_record, ensure_ascii=False)
    _leaked = [m for m in _KNOWN_SAMPLE_MARKERS if m in _record_str]
    if _leaked:
        print(f"[!!!] WARNING: [{document_type}] output contains old sample-document values {_leaked} — re-check.")

    sensitivity_suggestion = classify_sensitivity(merged_record)

    document_id = str(uuid.uuid4())
    merged_record["_document_metadata"] = {
        "document_id": document_id,
        "document_type": document_type,
        "linked_fir_number": linked_fir_number.strip() if linked_fir_number else None,
        "uploaded_by_employee_id": officer_id.strip() if officer_id else None,
        "ingested_at_utc": datetime.datetime.utcnow().isoformat() + "Z",
    }

    worm_entry = {
        "document_id": document_id,
        "document_type": document_type,
        "linked_fir_number": linked_fir_number.strip() if linked_fir_number else None,
        "event_status": "RECORD_APPEND_PENDING_QUORUM",
        "pages_processed": total_pages,
        "forensic_alert_level": worst_forensic_flag,
        "pixel_anomaly_coefficient": f"{worst_probability:.4f}",
        "per_page_blur_diagnostics": deblur_reports,
        "action_enforced": "WORM_TRAIL_TAGGED_FOR_MAGISTRATE",
        "input_format_detected": "PDF" if file_path.lower().endswith(".pdf") else "Native Image",
    }

    print(f"[+] [{document_type}] Extraction complete.\n")
    return {
        "record": merged_record,
        "ela_preview": ela_preview,
        "sensitivity": sensitivity_suggestion,
        "worm_entry": worm_entry,
    }


def process_case(case_mode, fir_file, supporting_files, quick_mode, linked_fir_number, officer_id):
    """
    Top-level entry point used by both front-ends.

    Raises ValueError with a user-facing message if the submission violates
    the mandatory-FIR-on-first-registration rule (see core/case_validation.py).

    Returns:
      {
        "records": [ {...}, ... ],       # one per uploaded document
        "ela_preview": PIL.Image|None,   # from the most suspicious page overall
        "sensitivity": {...},            # highest tier across all uploaded docs
        "worm_log": [ {...}, ... ],      # one entry per uploaded document
      }
    """
    supporting_files = supporting_files or []

    validation_error = validate_case_submission(case_mode, fir_file, supporting_files)
    if validation_error:
        raise ValueError(validation_error)

    results = []
    if fir_file:
        results.append(run_ocr_pipeline(fir_file, quick_mode, "FIR", linked_fir_number, officer_id))
    for sf in supporting_files:
        results.append(run_ocr_pipeline(sf, quick_mode, "Supporting Document", linked_fir_number, officer_id))

    combined_records = [r["record"] for r in results]

    ela_preview = None
    for r in results:
        if r["ela_preview"] is not None:
            ela_preview = r["ela_preview"]
            break

    overall_sensitivity = max(
        (r["sensitivity"] for r in results),
        key=lambda s: _TIER_RANK.get(s.get("suggested_sensitivity_tier"), 0),
        default={"suggested_sensitivity_tier": "Low", "suggested_quorum": "1 checker required"}
    )

    combined_worm_log = [r["worm_entry"] for r in results]

    return {
        "records": combined_records,
        "ela_preview": ela_preview,
        "sensitivity": overall_sensitivity,
        "worm_log": combined_worm_log,
    }
