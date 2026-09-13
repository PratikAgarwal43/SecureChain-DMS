-- SecureChain DMS (SIH26190) - M-of-N Quorum Approval Engine Schema
-- PostgreSQL Database Schema Definition

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Documents Table
CREATE TABLE IF NOT EXISTS documents (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    current_version VARCHAR(32) NOT NULL DEFAULT '1.0',
    content TEXT NOT NULL,
    sensitivity_tier VARCHAR(16) NOT NULL CHECK (sensitivity_tier IN ('LOW', 'MEDIUM', 'HIGH')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Edit Requests Table
CREATE TABLE IF NOT EXISTS edit_requests (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    requester_id VARCHAR(64) NOT NULL,
    proposed_content TEXT NOT NULL,
    sensitivity_tier VARCHAR(16) NOT NULL CHECK (sensitivity_tier IN ('LOW', 'MEDIUM', 'HIGH')),
    threshold_m INT NOT NULL CHECK (threshold_m >= 1),
    pool_size_n INT NOT NULL CHECK (pool_size_n >= threshold_m),
    status VARCHAR(16) NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Approval Pool Members Table
CREATE TABLE IF NOT EXISTS approval_pool_members (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64) NOT NULL REFERENCES edit_requests(id) ON DELETE CASCADE,
    approver_user_id VARCHAR(64) NOT NULL,
    pseudonym VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (request_id, approver_user_id),
    UNIQUE (request_id, pseudonym)
);

-- 4. Votes Table (Immutable append-only vote log per request)
CREATE TABLE IF NOT EXISTS votes (
    id VARCHAR(64) PRIMARY KEY,
    request_id VARCHAR(64) NOT NULL REFERENCES edit_requests(id) ON DELETE CASCADE,
    voter_user_id VARCHAR(64) NOT NULL,
    voter_pseudonym VARCHAR(64) NOT NULL,
    vote_choice VARCHAR(16) NOT NULL CHECK (vote_choice IN ('APPROVE', 'REJECT')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (request_id, voter_user_id)
);

-- 5. Document Versions Table
CREATE TABLE IF NOT EXISTS document_versions (
    id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    version_number VARCHAR(32) NOT NULL,
    content TEXT NOT NULL,
    approved_by_request_id VARCHAR(64) NOT NULL REFERENCES edit_requests(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. WORM (Write Once Read Many) Audit Log Table
CREATE TABLE IF NOT EXISTS worm_audit_logs (
    id VARCHAR(64) PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    request_id VARCHAR(64) NOT NULL,
    document_id VARCHAR(64) NOT NULL,
    requester_id VARCHAR(64) NOT NULL,
    action_details JSONB NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Trigger Function: Enforce Append-Only WORM Compliance (Block UPDATE and DELETE)
CREATE OR REPLACE FUNCTION prevent_worm_tampering()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'WORM Violation: Audit logs are append-only. Modifying or deleting records is prohibited.';
END;
$$ LANGUAGE plpgsql;

-- Attach WORM Triggers
DROP TRIGGER IF EXISTS trg_worm_prevent_update ON worm_audit_logs;
CREATE TRIGGER trg_worm_prevent_update
BEFORE UPDATE ON worm_audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_worm_tampering();

DROP TRIGGER IF EXISTS trg_worm_prevent_delete ON worm_audit_logs;
CREATE TRIGGER trg_worm_prevent_delete
BEFORE DELETE ON worm_audit_logs
FOR EACH ROW EXECUTE FUNCTION prevent_worm_tampering();
