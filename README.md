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

⚙️ Local Installation & Setup
Clone the Repository:Bashgit clone https://github.com/PratikAgarwal43/SecureChain-DMS.git
                            cd SecureChain-DMS

Configure Environment Variables:
Create a .env file based on the provided template, configuring your PostgreSQL database connection strings, JWT secrets, and storage keys.

Install Dependencies & Run:

Backend  :Bash  cd backend
                npm install
                npm run dev
Frontend:Bash   cd frontend
                npm install
                npm start

                
🧪 Running Tests
To verify security constraints (such as the self-approval block, duplicate vote prevention, and hash-chain integrity checks), execute the test suite:

Bash  npm test

📜 License

This project is open-source under the MIT License.
