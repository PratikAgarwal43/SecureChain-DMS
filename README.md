🔐 SecureChain DMS
A secure digital document management system for legal and investigation records featuring cryptographic hash-chaining, M-of-N quorum approval, and WORM audit trails.  🚀 Overview
Law enforcement and investigation agencies handle sensitive paperwork—such as FIRs, chargesheets, case diaries, and forensic reports—that must survive strict court scrutiny years later. SecureChain DMS is built to solve the vulnerabilities of traditional document management systems (like silent overwrites and editable audit logs) by enforcing cryptographic immutability, collective governance, and tamper-evident tracking.  


✨ Core Architecture & 6-Layer Security
Authentication & Identity: Employee ID + OTP primary login with session-bound cryptographic keypairs and optional Aadhaar e-Sign/DSC integration.  
Document Fingerprinting & Hash-Chain: SHA-256 fingerprinting on upload, Merkle-style chaining, and periodic RFC 3161 external timestamping.  
No-Overwrite Versioning & Instant Flagging: Original documents (e.g., Version 1.0) are permanently locked. Edits are drafted as separate versions while instantly flagging the document state as PENDING QUORUM.  
Adaptive M-of-N Quorum Approval: Sensitivity-based quorum thresholds (Low: 1-of-1, Medium: 2-of-3, High: 3-of-5) with a strict, enforced self-approval block (requester_id != approver_id).  
Anonymous Approver Pool: Peer-anonymous notifications and pseudonymous logging to eliminate collusion and social pressure, with instant pre-authorized access reserved for the Audit Authority.  
Tamper-Proof WORM Audit Logs: Append-only storage infrastructure hash-anchored directly into the document chain, making logs undeletable even by system administrators.  

🛠️ Technology Stack
Backend: Node.js (Express) or Python (FastAPI) 
Database & Storage: PostgreSQL (with append-only triggers and pgcrypto) + MinIO (S3-compatible object storage with WORM Object Lock)  
Cryptography: SHA-256 hashing, ECDSA/RSA digital signatures  
AI & Processing: Tesseract OCR, spaCy/Transformers for NLP sensitivity auto-classification, and Microsoft Presidio for PII redaction 
Frontend: React with role-based dashboards  

⚙️ Installation & Setup (Supabase Edition)

This project has been updated to run on **Supabase** (PostgreSQL) instead of a local PostgreSQL server.

### 1. Database Setup
1. Create a Supabase project.
2. Go to **SQL Editor** in your Supabase dashboard and paste the contents of `services/security-and-database/securechain_v03_migration.sql`. Run it to create all tables and triggers.
3. Grab your Supabase **Connection Pooler URL** (IPv4). It should look like `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`.
4. Update the database URL in the following files:
   - `services/api-gateway/config.py`
   - `seed_users.py`
   - `services/quorum-approval-engine/src/db/postgresDb.js`
5. Run the seeder to create demo users:
   ```bash
   python seed_users.py
   ```

### 2. Running the Backend Microservices
The backend consists of three separate microservices. Open a terminal for each:

**API Gateway (Port 8000)**
```bash
cd services/api-gateway
python -m venv venv
# Activate venv (e.g., venv\Scripts\activate on Windows)
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

**AI OCR Pipeline (Port 8001)**
```bash
cd services/ai-ocr-pipeline
pip install -r requirements.txt
uvicorn api:app --host 0.0.0.0 --port 8001
```

**Quorum Approval Engine**
```bash
cd services/quorum-approval-engine
npm install
npm start
```

### 3. Running the Frontend
The React frontend connects to the API Gateway on port 8000.
```bash
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173/`. Log in with one of the generated users (e.g., Username: `DL-IO-001`, Password: `IO@SecureChain1`).

---

🧪 Running Tests
To verify security constraints, execute the test suite:
```bash
npm test
```

📜 License
This project is open-source under the MIT License.
