"""
api.py
-------
Member 6 scope. REST API exposing the OCR + forensic + sensitivity pipeline
for a CUSTOM FRONTEND (React/Vue/plain HTML/etc.) — no Gradio here. Reuses
the exact same orchestration logic as the Gradio (Hugging Face Spaces)
version via core/pipeline_service.py, so behaviour is identical.

Run locally:
    uvicorn api:app --host 0.0.0.0 --port 8000 --reload

Endpoints:
    GET  /api/health
    POST /api/case/submit   (multipart/form-data)
"""

import sys
import os

PROJECT_DIR = os.environ.get("SECURECHAIN_HOME", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_DIR)

import base64
import io
import shutil
import tempfile
from typing import List, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.pipeline_service import process_case
from core.case_validation import NEW_FIR_MODE, EXISTING_CASE_MODE

app = FastAPI(
    title="SecureChain DMS — Member 6 API",
    description="OCR + forensic tamper-check + sensitivity-tier suggestion for FIRs and supporting documents.",
    version="1.0.0",
)

# Allow the custom frontend (running on a different origin/port during dev,
# e.g. React on :3000 calling this API on :8000) to call these endpoints.
# Restrict this to your actual frontend's origin(s) in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SensitivityResponse(BaseModel):
    suggested_sensitivity_tier: str
    suggested_quorum: str
    matched_high_risk_terms: List[str] = []
    matched_medium_risk_terms: List[str] = []
    note: str = ""


class CaseSubmitResponse(BaseModel):
    records: List[dict]
    sensitivity: SensitivityResponse
    worm_log: List[dict]
    ela_preview_base64_png: Optional[str] = None  # None if no page was processed


@app.get("/api/health")
def health_check():
    return {"status": "ok", "service": "SecureChain DMS Member 6 API"}


@app.get("/api/case-modes")
def get_case_modes():
    """Lets the frontend fetch the exact mode strings without hardcoding them."""
    return {"modes": [NEW_FIR_MODE, EXISTING_CASE_MODE]}


def _save_upload_to_temp(upload: UploadFile, tmp_dir: str) -> str:
    dest_path = os.path.join(tmp_dir, upload.filename)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(upload.file, f)
    return dest_path


@app.post("/api/case/submit", response_model=CaseSubmitResponse)
async def submit_case(
    case_mode: str = Form(..., description=f"'{NEW_FIR_MODE}' or '{EXISTING_CASE_MODE}'"),
    fir_file: Optional[UploadFile] = File(None, description="Mandatory only when case_mode is the new-FIR mode"),
    supporting_files: List[UploadFile] = File(default=[], description="Always optional, any number of files"),
    quick_mode: bool = Form(True, description="Process only first 5 pages per document"),
    linked_fir_number: str = Form("", description="Optional — link a supporting doc to a known FIR number"),
    officer_id: str = Form("", description="Optional — officer employee ID for audit tagging"),
):
    with tempfile.TemporaryDirectory() as tmp_dir:
        fir_path = _save_upload_to_temp(fir_file, tmp_dir) if fir_file else None
        supporting_paths = [_save_upload_to_temp(f, tmp_dir) for f in supporting_files] if supporting_files else []

        try:
            result = process_case(
                case_mode=case_mode,
                fir_file=fir_path,
                supporting_files=supporting_paths,
                quick_mode=quick_mode,
                linked_fir_number=linked_fir_number,
                officer_id=officer_id,
            )
        except ValueError as e:
            # this is the mandatory-FIR-on-first-registration validation error
            raise HTTPException(status_code=400, detail=str(e))

    ela_b64 = None
    if result["ela_preview"] is not None:
        buf = io.BytesIO()
        result["ela_preview"].save(buf, format="PNG")
        ela_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return {
        "records": result["records"],
        "sensitivity": result["sensitivity"],
        "worm_log": result["worm_log"],
        "ela_preview_base64_png": ela_b64,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("API_PORT", 8000)))
