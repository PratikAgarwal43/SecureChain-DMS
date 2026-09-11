# SecureChain DMS — Member 6 Module (API Backend)

**Scope (Team Roles table):** OCR/document classification, AI sensitivity
suggestion, Docker/setup, integration testing.

This is a **REST API** (FastAPI, no Gradio) meant to be called by a custom
frontend (Member 1's React/whatever UI). It ingests a scanned FIR or
supporting document (PDF or image, Hindi/English), and produces:
1. Deblurred/contrast-enhanced page images
2. A forensic tamper-check score (Error Level Analysis + CNN)
3. Structured, English-translated fields via Qwen2-VL (OCR + extraction)
4. An AI-suggested sensitivity tier (Low / Medium / High → quorum size)
5. A WORM-style audit telemetry entry

> **Looking for the Gradio / Hugging Face Spaces version instead?** That's a
> separate package (`SecureChain_DMS_Member6_HF/`) — same core logic, but
> with a built-in Gradio UI instead of a bare API, meant for quick demos
> without needing a frontend.

## Officer workflow (enforced server-side in `core/case_validation.py`)

- **Register New FIR (first time):** FIR upload is **mandatory**. Supporting
  documents are optional.
- **Existing Case Folder (update / add documents):** both upload options are
  still valid, but the FIR upload is now **optional** — the frontend can let
  an officer just add/update supporting documents without re-uploading the FIR.

## Project structure

```
SecureChain_DMS_Member6/
├── api.py                       # FastAPI app — the actual HTTP entrypoint
├── core/
│   ├── pipeline_service.py       # Shared orchestration logic (used by api.py)
│   ├── ocr_engine.py             # Qwen2-VL extraction + merge/normalize logic
│   ├── forensic_engine.py        # ELA + CNN tamper detection
│   ├── image_preprocessing.py    # Blur detection + deblurring
│   ├── sensitivity_classifier.py # Quorum-tier suggestion
│   └── case_validation.py        # Mandatory-FIR-on-first-registration rule
├── tests/
│   └── test_pipeline.py          # GPU-free unit/integration tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .github/workflows/tests.yml   # CI
```

## Running with Docker (recommended)

Requirements: Docker, NVIDIA drivers, [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

```bash
docker compose up --build
```

The API is now live at `http://localhost:8000`.
Interactive Swagger docs (useful for manual testing without any frontend
at all): **http://localhost:8000/docs**

First run downloads Qwen2-VL-7B (~15GB) into a named Docker volume
(`huggingface_cache`), so subsequent restarts are fast.

## Running locally without Docker (needs a local GPU + CUDA)

```bash
pip install -r requirements.txt
export SECURECHAIN_HOME=$(pwd)
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

## API reference

### `GET /api/health`
Simple liveness check.

### `GET /api/case-modes`
Returns the exact case-mode strings the frontend should send (so they never
go out of sync with the backend's validation logic).

### `POST /api/case/submit`  (multipart/form-data)

| Field | Type | Required | Notes |
|---|---|---|---|
| `case_mode` | string | yes | One of the values from `/api/case-modes` |
| `fir_file` | file | conditional | Mandatory only when `case_mode` is "Register New FIR" |
| `supporting_files` | file[] | no | Any number of files, always optional |
| `quick_mode` | bool | no | Default `true` — only first 5 pages/document |
| `linked_fir_number` | string | no | Tag a supporting doc to a known FIR |
| `officer_id` | string | no | Audit tagging |

**Example (curl):**
```bash
curl -X POST http://localhost:8000/api/case/submit \
  -F "case_mode=Register New FIR (first time)" \
  -F "fir_file=@/path/to/fir.pdf" \
  -F "supporting_files=@/path/to/evidence1.jpg" \
  -F "supporting_files=@/path/to/evidence2.jpg" \
  -F "quick_mode=true"
```

**Example (frontend fetch/JS):**
```js
const formData = new FormData();
formData.append("case_mode", "Register New FIR (first time)");
formData.append("fir_file", firFileInput.files[0]);
for (const f of supportingFilesInput.files) {
  formData.append("supporting_files", f);
}
formData.append("quick_mode", "true");

const res = await fetch("http://localhost:8000/api/case/submit", {
  method: "POST",
  body: formData,
});
const data = await res.json();
// data.records         -> array of extracted document JSONs
// data.sensitivity      -> { suggested_sensitivity_tier, suggested_quorum, ... }
// data.worm_log         -> array of audit entries
// data.ela_preview_base64_png -> base64 PNG string, or null
```

**Response shape:**
```json
{
  "records": [ { "district": "...", "complainant_name": "...", "...": "..." } ],
  "sensitivity": { "suggested_sensitivity_tier": "Medium", "suggested_quorum": "2-of-3 approvers required", "...": "..." },
  "worm_log": [ { "document_id": "...", "document_type": "FIR", "...": "..." } ],
  "ela_preview_base64_png": "iVBORw0KGgoAAAANSUhEUgAA..."
}
```

If the mandatory-FIR rule is violated, the API returns **HTTP 400** with a
`detail` message explaining what's missing.

## Running tests

```bash
pip install pytest opencv-python-headless pillow numpy
python -m pytest tests/ -v
```

These tests do **not** require a GPU or `torch`/`transformers`/`fastapi`
installed — they stub the heavy imports and only test deterministic logic
(sensitivity classification, null normalization, multi-page merge behaviour,
and the new/existing-case validation rule). This is what runs in CI.

## Pushing this to GitHub

```bash
cd SecureChain_DMS_Member6
git init
git add .
git commit -m "Member 6: OCR + forensic + sensitivity API (Docker + tests)"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

For a team monorepo, push to a feature branch instead:
```bash
git checkout -b member6/ocr-forensic-api
git add SecureChain_DMS_Member6/
git commit -m "Member 6: OCR + forensic + sensitivity API (Docker + tests)"
git push -u origin member6/ocr-forensic-api
```

**Do not commit:** `models/*.pth` (untrained placeholder CNN weights),
`work/`, or any real case documents — see `.gitignore`.

## Known limitations

- The forensic tamper-detection CNN ships with **untrained/random weights**
  — it produces a score but is not yet a validated tamper detector.
- OCR accuracy: ~95% on clear scans, ~75% on blurred/handwritten-heavy pages
  (measured manually during development).
- The sensitivity classifier is keyword-based (fast, transparent, easy to
  demo) rather than a trained NLP model.
- CORS is wide open (`*`) by default for development — restrict
  `CORS_ALLOWED_ORIGINS` to your actual frontend's origin in production.
