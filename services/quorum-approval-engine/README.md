# 🔐 SecureChain DMS - M-of-N Quorum Approval Engine

A military-grade, court-admissible Digital Document Management & M-of-N Quorum Approval Engine for legal, police, and investigation records (SIH26190). Features cryptographic SHA-256 hash-chaining, double-blind peer anonymity, rank hierarchy validation, 24-hour backup escalation, 48-hour emergency override with mandatory 7-day post-hoc audit, and judicial unmasking with Digital Signature Certificate (DSC) support.

---

## 🏛️ Core SIH Rules & Architecture

### 1. Sensitivity & Criticality Based Quorum Tiers
- **Low Criticality (e.g., Minor Theft / Internal Notes)**: **1-of-1 Quorum** (Requires 1 local SHO or Senior Officer).
- **Medium Criticality (e.g., Investigation Updates / Witness Addenda)**: **2-of-3 Quorum**.
- **High Criticality (e.g., Sensitive Forensic & Ballistics Reports)**: **3-of-5 Quorum** (Superintendents & Judicial Experts).
- **Critical Criticality (e.g., High-profile crimes involving influential figures)**: **4-of-7 Quorum** (Pulling anonymously from senior leadership: Magistrates, SSPs, and FSL Heads).

### 2. Rank Hierarchy & Jurisdictional Pool Filtering
- **Rank Superiority Rule**: Approvers chosen for pool $N$ must **always** be of equal or higher rank than the requesting officer. Junior officers are blocked with `INSUFFICIENT_APPROVER_RANK`.
- **Tier Rank Floor**: Minimum rank threshold enforced per tier (e.g. LOW requires at least SHO rank level 5; CRITICAL requires Senior Leadership rank level 8+).
- **Jurisdictional Ring-Fencing**: Approvers must belong to the same police district/jurisdiction, preventing cross-district interference. Exceptions are strictly limited to State-Level/Judicial Circuit officers (Magistrates, FSL Heads, DIG) or High/Critical leadership reviews.

### 3. Double-Blind Anonymity & Self-Approval Hard Block
- **Self-Approval Hard Block**: Hard backend check (`requester_id != approver_id`). Any attempt by an officer to approve their own request is rejected with `HTTP 403 Forbidden` (`SELF_APPROVAL_FORBIDDEN`).
- **Double-Blind Mechanism**: Approvers receive generic notifications with an `anonymous_token` and assigned pseudonym (`Approver_XXXX`). The requester identity is masked (`Requester_ANON_XXXX`) and peer approver IDs are completely hidden during review to prevent bribery, collusion, coercion, or groupthink.

### 4. Time Limits, Escalation & Emergency Overrides
- **24-Hour Backup Escalation**: Evaluates approver response SLA. If an approver has not voted within 24 hours, the request automatically re-routes to their pre-mapped backup approver, logging an append-only `APPROVER_ESCALATED_24H` WORM audit record.
- **48-Hour Emergency Override**: If a request remains blocked past 48 hours, authorized senior leadership (SSP, Magistrate, DIG) can execute an emergency override. This:
  * Promotes status to `APPROVED`.
  * Flags severity to `CRITICAL`.
  * Opens a mandatory **7-day post-hoc audit tracking window** (`MANDATORY_7DAY_POST_HOC_AUDIT_PENDING`).
  * Creates an immutable hash-chained version and logs `EMERGENCY_OVERRIDE_EXECUTED`.

### 5. State Transition, Hash-Chaining & Judicial Unmasking
- **Cryptographic Hash-Chaining**: Document versions are linked via SHA-256 (`previous_version_hash`, `current_version_hash`, content digest, and DSC digital signatures).
- **Chain Verification**: Any verifier or court can audit the unbroken cryptographic chain from Genesis v1.0 to v1.1+.
- **Judicial Unmasking Trigger**: Once valid votes $\ge M$, the engine sets `identity_revealed_at = NOW()`. Judges and court officers can inspect the unmasked trial record (`/api/approval/requests/:id/judicial-record`) revealing real names, ranks, badge IDs, police districts, and cryptographic DSC signatures for court admissibility under Indian Evidence Act / BNSS.

---

## 📡 API Reference Summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/approval/officers` | Register/seed officer profile with rank, jurisdiction, backup, and DSC key |
| `POST` | `/api/approval/documents` | Create original document record (initiates Genesis v1.0 hash link) |
| `GET` | `/api/approval/documents/:id/chain-verify` | Verify cryptographic hash chain integrity across all document versions |
| `POST` | `/api/approval/requests` | Submit document edit request (evaluates rank hierarchy & jurisdictional ring-fencing) |
| `GET` | `/api/approval/requests/:id` | Double-blind sanitized view (masked requester & pseudonymous pool) |
| `GET` | `/api/approval/requests/:id/notification/:approverId` | Approver notification with generic `anonymous_token` |
| `POST` | `/api/approval/requests/:id/vote` | Cast vote with optional DSC signature and automatic quorum state promotion |
| `POST` | `/api/approval/requests/:id/escalate` | Trigger 24-hour backup approver escalation |
| `POST` | `/api/approval/requests/:id/emergency-override` | 48-Hour emergency override by Senior Leadership with 7-day post-hoc audit |
| `GET` | `/api/approval/requests/:id/judicial-record` | Court trial unmasking (reveals real names, ranks, DSC signatures post-approval) |
| `GET` | `/api/approval/audit-logs` | Query append-only WORM audit log records |

---

## 🧪 Running Tests

Execute the Jest test suite covering all 5 core security rules:

```bash
npm test
```
