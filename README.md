# 🛡️ SecureChain DMS
A secure digital document management system for legal and investigation records featuring cryptographic hash-chaining, M-of-N quorum approval, and WORM audit trails.

## 🏛️ Overview
Law enforcement and investigation agencies handle sensitive paperwork—such as FIRs, chargesheets, case diaries, and forensic reports—that must survive strict court scrutiny years later. SecureChain DMS is built to solve the vulnerabilities of traditional document management systems (like silent overwrites and editable audit logs) by enforcing cryptographic immutability, collective governance, and tamper-evident tracking.

---

## 🚀 Setup & Installation Guide (For Humans & AI Agents)

This project consists of 3 distinct interconnected layers:
1. **Frontend**: React + Vite (Port 5173)
2. **Backend**: Python FastAPI (Port 8000)
3. **Quorum Approval Engine**: Node.js Microservice (Port 3000)

To successfully run this project on localhost, you **must run all 3 services concurrently** in 3 separate terminal windows.

### 1. Environment Variables Configuration
Before starting the services, you must create a `.env` file in the `backend/` directory. 
Here is the `.env.example` file showing the required keys. *(Note: Ask the repository owner for the live `.env` file containing the secret Supabase database connection strings).*

```env
# backend/.env
PROJECT_NAME="SecureChain DMS Backend"
API_V1_STR="/api/v1"

# Database Connections (Requires live Supabase credentials)
SUPABASE_URL="https://[YOUR-PROJECT].supabase.co"
SUPABASE_SERVICE_ROLE_KEY="[YOUR-SERVICE-ROLE-KEY]"
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[YOUR-PROJECT].supabase.co:5432/postgres"

# Storage Settings
STORAGE_PROVIDER=DB

# Authentication
JWT_SECRET_KEY="securechain_dms_jwt_secret_key_change_in_production_32_bytes_min"
JWT_ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=60
2. Start the Backend (Python FastAPI)
The main backend handles routing, storage decryption, and database operations. Open your first terminal and run:

bash


cd backend
python -m venv .venv
source .venv/bin/activate  # Or `.\.venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000
3. Start the Quorum Approval Engine (Node.js)
This isolated microservice holds the cryptographic voting logic and WORM audit ledgers. Open your second terminal and run: CRITICAL: It must be run with USE_MEMORY_DB="true" to bypass legacy schema conflicts.

bash


cd services/quorum-approval-engine
npm install
# For Linux/Mac:
USE_MEMORY_DB="true" node src/server.js
# For Windows (PowerShell):
$env:USE_MEMORY_DB="true"; node src/server.js
4. Start the Frontend (React + Vite)
The user interface connects to the FastAPI backend via a Vite proxy. Open your third terminal and run:

bash


cd frontend
npm install
npm run dev -- --host 127.0.0.1
Once all 3 services are running, open your browser to http://127.0.0.1:5173. Demo Login: Employee ID EMP001, Password 123456

🧠 Core Architecture & 6-Layer Security
Authentication & Identity: Employee ID + OTP primary login with session-bound cryptographic keypairs and optional Aadhaar e-Sign/DSC integration.
Document Fingerprinting & Hash-Chain: SHA-256 fingerprinting on upload, Merkle-style chaining, and periodic RFC 3161 external timestamping.
No-Overwrite Versioning & Instant Flagging: Original documents (e.g., Version 1.0) are permanently locked. Edits are drafted as separate versions while instantly flagging the document state as PENDING QUORUM.
Adaptive M-of-N Quorum Approval: Sensitivity-based quorum thresholds (Low: 1-of-1, Medium: 2-of-3, High: 3-of-5) with a strict, enforced self-approval block (requester_id != approver_id).
Anonymous Approver Pool: Peer-anonymous notifications and pseudonymous logging to eliminate collusion and social pressure, with instant pre-authorized access reserved for the Audit Authority.
Tamper-Proof WORM Audit Logs: Append-only storage infrastructure hash-anchored directly into the document chain, making logs undeletable even by system administrators.
📝 License
This project is open-source under the MIT License.



5. Once you paste this in, click the green **"Commit changes..."** button at the top right of the GitHub page. 
It will instantly save and format beautifully on your repository homepage!
