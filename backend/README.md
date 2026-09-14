# SecureChain DMS - Backend Foundation

Initial backend foundation for **SecureChain DMS** built with **Python**, **FastAPI**, **SQLAlchemy**, and **Pydantic**.

---

## 📁 Directory Structure

```text
SecureChain-DMS/
└── backend/
    ├── app/
    │   ├── api/
    │   │   ├── v1/
    │   │   │   └── endpoints/
    │   │   │       └── health.py    # GET /api/v1/health endpoint implementation
    │   │   └── router.py            # Central API Router bundling versioned endpoints
    │   ├── core/
    │   │   └── config.py            # Pydantic BaseSettings for environment variables
    │   ├── db/
    │   │   ├── base.py              # DeclarativeBase for SQLAlchemy models
    │   │   └── session.py           # Database engine, sessionmaker & health checks
    │   ├── models/                  # SQLAlchemy ORM models directory
    │   ├── schemas/
    │   │   └── health.py            # Pydantic schema for health endpoint response
    │   ├── services/                # Business logic services directory
    │   └── main.py                  # FastAPI application entrypoint & middleware
    ├── .env.example                 # Environment variable template
    ├── .gitignore                   # Version control ignore rules
    ├── requirements.txt             # Project dependencies
    └── README.md                    # Project setup and execution guide
```

---

## 📄 File Responsibilities

- **`app/main.py`**: Initializes the FastAPI application, registers CORS middleware for React integration, includes API routers, and configures global database connection exception handling.
- **`app/core/config.py`**: Loads environment variables dynamically using Pydantic Settings, securely computes the PostgreSQL connection string without hardcoding secrets.
- **`app/db/session.py`**: Sets up SQLAlchemy connection engine, configures `SessionLocal`, provides `get_db()` dependency for route handlers, and contains connection verification logic.
- **`app/db/base.py`**: Defines standard SQLAlchemy `DeclarativeBase` used as parent class for all future database models.
- **`app/api/v1/endpoints/health.py`**: Provides `GET /api/v1/health` returning system operational status.
- **`app/schemas/health.py`**: Defines Pydantic validation schema for the health check endpoint response.

---

## 🛠️ Installation & Setup Instructions

### Prerequisites
- Python 3.10+
- PostgreSQL (running locally or accessible via network)

### 1. Navigate to the backend folder
```bash
cd SecureChain-DMS/backend
```

### 2. Create and activate a Virtual Environment

**Using `uv` (Recommended - fast):**
```bash
uv venv .venv
.venv\Scripts\activate
```

**Or using standard Python `venv`:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
*(Or with `uv`: `uv pip install -r requirements.txt`)*

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and update your PostgreSQL credentials:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `copy .env.example .env`)*

### 5. Run Alembic Database Migrations
To apply database migrations to your PostgreSQL instance:
```bash
alembic upgrade head
```

To render static DDL SQL without connecting to a live database:
```bash
alembic upgrade head --sql
```

---

## 🚀 Running the FastAPI Server


Start the Uvicorn development server with live reload:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Once running:
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc API Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Endpoint**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

## 🔒 SHA-256 Document Integrity & Verification

SecureChain DMS calculates a **64-character hexadecimal SHA-256 cryptographic fingerprint** directly from the exact binary payload of uploaded PDF documents before storing them in MinIO and PostgreSQL.

### Verification Workflow (`GET /api/v1/documents/{document_id}/verify`)
1. Fetches the stored PDF file directly from MinIO object storage.
2. Recalculates the SHA-256 digest from the retrieved file bytes.
3. Compares the calculated hash against `sha256_hash` stored in PostgreSQL `document_versions`.
4. Returns `INTEGRITY_VERIFIED` (`integrity_verified: true`) if hashes match, or `TAMPER_DETECTED` (`integrity_verified: false`) if a mismatch occurs.


---

## 🧪 Testing the Health Check Endpoint

Using `curl` or PowerShell:

```bash
curl http://127.0.0.1:8000/api/v1/health
```

Expected Response:
```json
{
  "status": "ok",
  "service": "SecureChain DMS Backend"
}
```
