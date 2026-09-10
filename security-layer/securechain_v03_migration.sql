-- =============================================================================
-- SECURECHAIN DMS -- PostgreSQL Migration v0.3
-- SIH26190 | Zero-Trust Legal Evidence Vault
-- 17 Tables | 8 Triggers | 22 Indexes | Seed Data
-- =============================================================================
-- DEEP DESIGN NOTES:
--
-- 1. CIRCULAR FK BETWEEN documents AND document_versions
--    documents.current_version_id -> document_versions.id
--    document_versions.document_id -> documents.id
--    Solved by: Create both tables without circular FK first.
--    Add current_version_id as DEFERRABLE FK after both tables exist.
--    Upload flow: INSERT document (NULL), INSERT version, UPDATE document.
--
-- 2. WORM AUDIT LOG
--    Uses RULES (not triggers) because rules fire BEFORE triggers and
--    completely replace the operation making it impossible to bypass.
--
-- 3. APPROVER ANONYMITY + JUDICIAL REVEAL
--    During quorum: identity_revealed_at IS NULL (anonymous).
--    After APPROVED/REJECTED: trigger sets identity_revealed_at = NOW().
--    JUDGE/AUDITOR can see real approver_id only after reveal.
--
-- 4. CASE ACCESS CONTROL via case_participants
--    No user sees a case unless they have a row in case_participants.
--    SHO adds Police/Forensic/Judiciary participants when creating case.
--
-- 5. HASH CHAIN DESIGN
--    chain_hash = SHA256(doc_hash || prev_chain_hash || created_at ||
--                        created_by || COALESCE(quorum_token,''))
--    Computed in chain_engine.py before INSERT. DB stores result only.
-- =============================================================================

BEGIN;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- TABLE 1: roles
CREATE TABLE roles (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(50) NOT NULL UNIQUE,
    pillar      VARCHAR(30) NOT NULL CHECK (pillar IN ('POLICE','FORENSIC','JUDICIARY','ADMIN')),
    description TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 2: users
CREATE TABLE users (
    id              UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id     VARCHAR(50)  NOT NULL UNIQUE,
    full_name       VARCHAR(150) NOT NULL,
    email           VARCHAR(255) UNIQUE,
    phone           VARCHAR(20),
    role_id         UUID         NOT NULL REFERENCES roles(id),
    department      VARCHAR(100),
    jurisdiction    VARCHAR(150),
    dsc_certificate TEXT,
    dsc_expires_at  TIMESTAMPTZ,
    password_hash   VARCHAR(255) NOT NULL DEFAULT '',
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    last_login_at   TIMESTAMPTZ,
    failed_logins   SMALLINT     NOT NULL DEFAULT 0,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- TABLE 3: cases
CREATE TABLE cases (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    case_number  VARCHAR(100) NOT NULL UNIQUE,
    title        VARCHAR(255) NOT NULL,
    case_type    VARCHAR(100),
    department   VARCHAR(100),
    jurisdiction VARCHAR(150),
    created_by   UUID         NOT NULL REFERENCES users(id),
    status       VARCHAR(30)  NOT NULL DEFAULT 'ACTIVE'
                     CHECK (status IN ('ACTIVE','UNDER_REVIEW','CLOSED','STAYED')),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- TABLE 4: documents (current_version_id added after document_versions)
CREATE TABLE documents (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id           UUID         NOT NULL REFERENCES cases(id),
    title             VARCHAR(255) NOT NULL,
    document_type     VARCHAR(100) NOT NULL
                          CHECK (document_type IN (
                              'FIR','CHARGESHEET','FORENSIC_REPORT',
                              'WITNESS_STATEMENT','CASE_DIARY',
                              'PROGRESS_NOTE','COURT_ORDER','EVIDENCE'
                          )),
    sensitivity_level VARCHAR(20)  NOT NULL
                          CHECK (sensitivity_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    status            VARCHAR(30)  NOT NULL DEFAULT 'LOCKED'
                          CHECK (status IN (
                              'DRAFT','LOCKED','PENDING_QUORUM',
                              'UNDER_AMENDMENT','ARCHIVED'
                          )),
    created_by        UUID         NOT NULL REFERENCES users(id),
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- TABLE 5: document_versions (VAULT 1 key material lives here)
CREATE TABLE document_versions (
    id               UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id      UUID         NOT NULL REFERENCES documents(id),
    version_number   INTEGER      NOT NULL CHECK (version_number >= 1),
    -- VAULT 2 POINTER
    storage_key      TEXT         NOT NULL UNIQUE,
    -- SHA-256 FINGERPRINT
    doc_hash         CHAR(64)     NOT NULL,
    -- HASH CHAIN
    chain_hash       CHAR(64)     NOT NULL UNIQUE,
    prev_chain_hash  CHAR(64)     NOT NULL DEFAULT repeat('0',64),
    quorum_token     TEXT,
    -- AES-256-GCM ENVELOPE ENCRYPTION (VAULT 1 KEY MATERIAL)
    wrapped_dek      TEXT         NOT NULL,
    iv               VARCHAR(24)  NOT NULL,
    key_id           UUID         NOT NULL,
    kek_version      VARCHAR(10)  NOT NULL,
    aad              TEXT         NOT NULL,
    algorithm        VARCHAR(20)  NOT NULL DEFAULT 'AES-256-GCM',
    -- METADATA
    file_size        BIGINT       CHECK (file_size > 0),
    mime_type        VARCHAR(100),
    original_filename VARCHAR(255),
    created_by       UUID         NOT NULL REFERENCES users(id),
    status           VARCHAR(30)  NOT NULL DEFAULT 'DRAFT'
                         CHECK (status IN ('DRAFT','LOCKED','APPROVED','REJECTED')),
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    UNIQUE (document_id, version_number)
);

-- Circular FK (DEFERRABLE to allow insert-then-update pattern)
ALTER TABLE documents
    ADD COLUMN current_version_id UUID
    REFERENCES document_versions(id) DEFERRABLE INITIALLY DEFERRED;

-- TABLE 6: quorum_policies
CREATE TABLE quorum_policies (
    id                 UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    sensitivity_level  VARCHAR(20) NOT NULL UNIQUE
                           CHECK (sensitivity_level IN ('LOW','MEDIUM','HIGH','CRITICAL')),
    required_approvals INTEGER     NOT NULL CHECK (required_approvals > 0),
    pool_size          INTEGER     NOT NULL,
    eligible_roles     TEXT[]      NOT NULL DEFAULT '{}',
    CONSTRAINT pool_ge_required CHECK (pool_size >= required_approvals)
);

-- TABLE 7: case_participants (THE ACCESS CONTROL TABLE)
-- No row here = user cannot see the case. Period.
CREATE TABLE case_participants (
    id             UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id        UUID        NOT NULL REFERENCES cases(id) ON DELETE CASCADE,
    participant_id UUID        NOT NULL REFERENCES users(id),
    access_level   VARCHAR(30) NOT NULL DEFAULT 'READ'
                       CHECK (access_level IN ('READ','READ_WRITE','APPROVE','VERIFY','FULL')),
    added_by       UUID        NOT NULL REFERENCES users(id),
    added_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    removed_at     TIMESTAMPTZ DEFAULT NULL,
    removal_reason TEXT,
    UNIQUE (case_id, participant_id)
);

-- TABLE 8: edit_requests
CREATE TABLE edit_requests (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id           UUID         NOT NULL REFERENCES documents(id),
    requester_id          UUID         NOT NULL REFERENCES users(id),
    source_version_id     UUID         NOT NULL REFERENCES document_versions(id),
    proposed_version_id   UUID         REFERENCES document_versions(id),
    quorum_policy_id      UUID         NOT NULL REFERENCES quorum_policies(id),
    reason                TEXT         NOT NULL,
    amendment_reason_code VARCHAR(50)
                              CHECK (amendment_reason_code IN (
                                  'FACTUAL_ERROR','NEW_EVIDENCE',
                                  'COURT_ORDER','CLERICAL','LEGAL_UPDATE'
                              )),
    status                VARCHAR(30)  NOT NULL DEFAULT 'PENDING_QUORUM'
                              CHECK (status IN (
                                  'PENDING_QUORUM','APPROVED',
                                  'REJECTED','WITHDRAWN','EXPIRED'
                              )),
    requested_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    completed_at          TIMESTAMPTZ,
    expires_at            TIMESTAMPTZ
);

-- TABLE 9: approval_assignments
CREATE TABLE approval_assignments (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    edit_request_id      UUID        NOT NULL REFERENCES edit_requests(id),
    approver_id          UUID        NOT NULL REFERENCES users(id),
    anonymous_token      UUID        NOT NULL UNIQUE DEFAULT gen_random_uuid(),
    assigned_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at           TIMESTAMPTZ,
    status               VARCHAR(30) NOT NULL DEFAULT 'PENDING'
                             CHECK (status IN ('PENDING','VOTED','EXPIRED','RECUSED')),
    identity_revealed_at TIMESTAMPTZ DEFAULT NULL,
    UNIQUE (edit_request_id, approver_id)
);

-- TABLE 10: approvals
CREATE TABLE approvals (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID        NOT NULL UNIQUE REFERENCES approval_assignments(id),
    decision      VARCHAR(20) NOT NULL CHECK (decision IN ('APPROVED','REJECTED')),
    remarks       TEXT,
    dsc_signature TEXT,
    approved_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 11: audit_logs (WORM - protected by RULES below)
CREATE TABLE audit_logs (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type    VARCHAR(50) NOT NULL
                      CHECK (event_type IN (
                          'LOGIN','LOGOUT','LOGIN_FAILED',
                          'CASE_CREATED','PARTICIPANT_ADDED','PARTICIPANT_REMOVED',
                          'UPLOAD','DOCUMENT_VIEWED','DOCUMENT_DOWNLOADED','DOCUMENT_PRINTED',
                          'EDIT_REQUESTED','AMENDMENT_APPROVED','AMENDMENT_REJECTED',
                          'APPROVAL_VOTED','QUORUM_REACHED',
                          'CHAIN_VERIFIED','TAMPER_ALERT','HASH_MISMATCH',
                          'KEY_ROTATED','DSC_VERIFIED','DSC_EXPIRED',
                          'MERKLE_CHECKPOINT','COURT_REGISTERED','CERT_GENERATED',
                          'EMERGENCY_OVERRIDE'
                      )),
    severity      VARCHAR(20) NOT NULL DEFAULT 'INFO'
                      CHECK (severity IN ('INFO','WARNING','HIGH','CRITICAL')),
    actor_id      UUID        REFERENCES users(id),
    case_id       UUID        REFERENCES cases(id),
    document_id   UUID        REFERENCES documents(id),
    version_id    UUID        REFERENCES document_versions(id),
    metadata      JSONB       DEFAULT '{}',
    previous_hash CHAR(64),
    event_hash    CHAR(64)    NOT NULL,
    log_hash      CHAR(64)    NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 12: merkle_checkpoints
CREATE TABLE merkle_checkpoints (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    merkle_root      CHAR(64)    NOT NULL,
    cases_included   INTEGER     NOT NULL CHECK (cases_included > 0),
    case_chain_heads JSONB       NOT NULL,
    created_by       UUID        REFERENCES users(id),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 13: dsc_verifications
CREATE TABLE dsc_verifications (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID         NOT NULL REFERENCES users(id),
    document_version_id UUID         REFERENCES document_versions(id),
    dsc_thumbprint      VARCHAR(128) NOT NULL,
    dsc_issuer          VARCHAR(255),
    dsc_valid_from      TIMESTAMPTZ,
    dsc_valid_to        TIMESTAMPTZ,
    verification_result VARCHAR(20)  NOT NULL
                            CHECK (verification_result IN ('VALID','EXPIRED','REVOKED','FAILED')),
    failure_reason      TEXT,
    verified_at         TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- TABLE 14: notifications
CREATE TABLE notifications (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    recipient_id      UUID         NOT NULL REFERENCES users(id),
    sender_id         UUID         REFERENCES users(id),
    notification_type VARCHAR(60)  NOT NULL
                          CHECK (notification_type IN (
                              'CASE_ASSIGNED','FIR_UPLOADED','EVIDENCE_UPLOADED',
                              'FORENSIC_REPORT_UPLOADED','AMENDMENT_REQUESTED',
                              'APPROVAL_REQUIRED','QUORUM_REACHED',
                              'AMENDMENT_APPROVED','AMENDMENT_REJECTED',
                              'TAMPER_ALERT','DSC_EXPIRING','CERT_READY',
                              'COURT_REGISTERED','EMERGENCY_OVERRIDE'
                          )),
    case_id           UUID         REFERENCES cases(id),
    document_id       UUID         REFERENCES documents(id),
    title             VARCHAR(255) NOT NULL,
    message           TEXT,
    severity          VARCHAR(20)  NOT NULL DEFAULT 'INFO'
                          CHECK (severity IN ('INFO','WARNING','HIGH','CRITICAL')),
    is_read           BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    read_at           TIMESTAMPTZ
);

-- TABLE 15: document_diffs
CREATE TABLE document_diffs (
    id                UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    edit_request_id   UUID        NOT NULL UNIQUE REFERENCES edit_requests(id),
    source_version_id UUID        NOT NULL REFERENCES document_versions(id),
    target_version_id UUID        NOT NULL REFERENCES document_versions(id),
    diff_summary      TEXT,
    diff_payload      JSONB,
    changed_sections  TEXT[]      DEFAULT '{}',
    lines_added       INTEGER     NOT NULL DEFAULT 0,
    lines_removed     INTEGER     NOT NULL DEFAULT 0,
    lines_modified    INTEGER     NOT NULL DEFAULT 0,
    diff_hash         CHAR(64),
    computed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 16: document_access_logs
CREATE TABLE document_access_logs (
    id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id              UUID        NOT NULL REFERENCES users(id),
    document_id          UUID        NOT NULL REFERENCES documents(id),
    version_id           UUID        REFERENCES document_versions(id),
    access_type          VARCHAR(30) NOT NULL
                             CHECK (access_type IN (
                                 'VIEW','COMPARE','DOWNLOAD','PRINT','VERIFY_HASH','CERT_REQUEST'
                             )),
    chain_hash_at_access CHAR(64),
    ip_address           INET,
    user_agent           TEXT,
    accessed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 17: case_court_registrations
CREATE TABLE case_court_registrations (
    id                UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id           UUID         NOT NULL REFERENCES cases(id),
    court_name        VARCHAR(255) NOT NULL,
    court_case_number VARCHAR(100) UNIQUE,
    registered_by     UUID         NOT NULL REFERENCES users(id),
    presiding_judge_id UUID        REFERENCES users(id),
    prosecutor_id     UUID         REFERENCES users(id),
    registration_date TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    status            VARCHAR(30)  NOT NULL DEFAULT 'ACTIVE'
                          CHECK (status IN ('ACTIVE','DISPOSED','APPEALED','STAYED','TRANSFERRED'))
);

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- TRIGGER 1: No self-approval
CREATE OR REPLACE FUNCTION fn_no_self_approval()
RETURNS TRIGGER LANGUAGE plpgsql AS 
DECLARE v_requester UUID;
BEGIN
    SELECT requester_id INTO v_requester FROM edit_requests WHERE id = NEW.edit_request_id;
    IF NEW.approver_id = v_requester THEN
        RAISE EXCEPTION 'SELF_APPROVAL_BLOCKED: Cannot approve own edit request.';
    END IF;
    RETURN NEW;
END; ;
CREATE TRIGGER trg_no_self_approval
    BEFORE INSERT ON approval_assignments
    FOR EACH ROW EXECUTE FUNCTION fn_no_self_approval();

-- TRIGGER 2: Protect locked versions
CREATE OR REPLACE FUNCTION fn_protect_locked()
RETURNS TRIGGER LANGUAGE plpgsql AS 
BEGIN
    IF OLD.status IN ('LOCKED','APPROVED','REJECTED') THEN
        RAISE EXCEPTION 'IMMUTABILITY_VIOLATION: Version % is % and cannot be modified.', OLD.id, OLD.status;
    END IF;
    RETURN NEW;
END; ;
CREATE TRIGGER trg_protect_locked
    BEFORE UPDATE ON document_versions
    FOR EACH ROW EXECUTE FUNCTION fn_protect_locked();

-- TRIGGER 3 & 4: WORM Audit Log (RULES, not triggers - fire before everything)
CREATE RULE rule_audit_no_update AS ON UPDATE TO audit_logs DO INSTEAD NOTHING;
CREATE RULE rule_audit_no_delete AS ON DELETE TO audit_logs DO INSTEAD NOTHING;

-- TRIGGER 5: Reveal approver identities after quorum decision
CREATE OR REPLACE FUNCTION fn_reveal_identities()
RETURNS TRIGGER LANGUAGE plpgsql AS 
BEGIN
    IF NEW.status IN ('APPROVED','REJECTED') AND OLD.status NOT IN ('APPROVED','REJECTED') THEN
        UPDATE approval_assignments
        SET identity_revealed_at = NOW()
        WHERE edit_request_id = NEW.id AND identity_revealed_at IS NULL;
    END IF;
    RETURN NEW;
END; ;
CREATE TRIGGER trg_reveal_identities
    AFTER UPDATE OF status ON edit_requests
    FOR EACH ROW EXECUTE FUNCTION fn_reveal_identities();

-- TRIGGER 6: Auto-notify all participants when document uploaded
CREATE OR REPLACE FUNCTION fn_notify_upload()
RETURNS TRIGGER LANGUAGE plpgsql AS 
DECLARE rec RECORD; v_type VARCHAR(60); v_sev VARCHAR(20);
BEGIN
    v_type := CASE NEW.document_type
        WHEN 'FIR' THEN 'FIR_UPLOADED'
        WHEN 'FORENSIC_REPORT' THEN 'FORENSIC_REPORT_UPLOADED'
        ELSE 'EVIDENCE_UPLOADED' END;
    v_sev := CASE WHEN NEW.sensitivity_level = 'CRITICAL' THEN 'HIGH'
                  WHEN NEW.sensitivity_level = 'HIGH' THEN 'WARNING'
                  ELSE 'INFO' END;
    FOR rec IN SELECT participant_id FROM case_participants
               WHERE case_id = NEW.case_id AND participant_id != NEW.created_by AND removed_at IS NULL
    LOOP
        INSERT INTO notifications(recipient_id, notification_type, case_id, document_id, title, message, severity)
        VALUES(rec.participant_id, v_type, NEW.case_id, NEW.id,
               v_type, 'New ' || NEW.document_type || ': ' || NEW.title, v_sev);
    END LOOP;
    RETURN NEW;
END; ;
CREATE TRIGGER trg_notify_upload
    AFTER INSERT ON documents
    FOR EACH ROW EXECUTE FUNCTION fn_notify_upload();

-- TRIGGER 7: Auto-notify on quorum completion
CREATE OR REPLACE FUNCTION fn_notify_quorum()
RETURNS TRIGGER LANGUAGE plpgsql AS 
DECLARE v_case UUID; v_title VARCHAR(255); rec RECORD; v_ntype VARCHAR(60);
BEGIN
    IF NEW.status IN ('APPROVED','REJECTED') AND OLD.status = 'PENDING_QUORUM' THEN
        SELECT d.case_id, d.title INTO v_case, v_title FROM documents d WHERE d.id = NEW.document_id;
        v_ntype := CASE NEW.status WHEN 'APPROVED' THEN 'AMENDMENT_APPROVED' ELSE 'AMENDMENT_REJECTED' END;
        INSERT INTO notifications(recipient_id, notification_type, case_id, document_id, title, message, severity)
        VALUES(NEW.requester_id, v_ntype, v_case, NEW.document_id,
               'Amendment ' || NEW.status || ': ' || v_title,
               'Your amendment was ' || NEW.status || '.',
               CASE NEW.status WHEN 'APPROVED' THEN 'INFO' ELSE 'WARNING' END);
        FOR rec IN SELECT participant_id FROM case_participants
                   WHERE case_id = v_case AND participant_id != NEW.requester_id AND removed_at IS NULL
        LOOP
            INSERT INTO notifications(recipient_id, notification_type, case_id, document_id, title, message, severity)
            VALUES(rec.participant_id, v_ntype, v_case, NEW.document_id,
                   'Amendment ' || NEW.status || ': ' || v_title, 'An amendment was ' || NEW.status || '.', 'INFO');
        END LOOP;
    END IF;
    RETURN NEW;
END; ;
CREATE TRIGGER trg_notify_quorum
    AFTER UPDATE OF status ON edit_requests
    FOR EACH ROW EXECUTE FUNCTION fn_notify_quorum();

-- TRIGGER 8: Auto update_at timestamps
CREATE OR REPLACE FUNCTION fn_update_ts() RETURNS TRIGGER LANGUAGE plpgsql AS 
BEGIN NEW.updated_at = NOW(); RETURN NEW; END; ;
CREATE TRIGGER trg_ts_cases     BEFORE UPDATE ON cases     FOR EACH ROW EXECUTE FUNCTION fn_update_ts();
CREATE TRIGGER trg_ts_documents BEFORE UPDATE ON documents FOR EACH ROW EXECUTE FUNCTION fn_update_ts();
CREATE TRIGGER trg_ts_users     BEFORE UPDATE ON users     FOR EACH ROW EXECUTE FUNCTION fn_update_ts();

-- =============================================================================
-- INDEXES (22 total)
-- =============================================================================
CREATE UNIQUE INDEX idx_users_emp          ON users(employee_id);
CREATE        INDEX idx_users_role         ON users(role_id);
CREATE        INDEX idx_users_active       ON users(is_active) WHERE is_active = TRUE;
CREATE UNIQUE INDEX idx_cases_num          ON cases(case_number);
CREATE        INDEX idx_cases_status       ON cases(status);
CREATE        INDEX idx_cp_participant     ON case_participants(participant_id) WHERE removed_at IS NULL;
CREATE        INDEX idx_cp_case            ON case_participants(case_id)        WHERE removed_at IS NULL;
CREATE        INDEX idx_docs_case          ON documents(case_id);
CREATE        INDEX idx_docs_sensitivity   ON documents(sensitivity_level);
CREATE        INDEX idx_docs_type          ON documents(document_type);
CREATE UNIQUE INDEX idx_dv_doc_ver         ON document_versions(document_id, version_number);
CREATE UNIQUE INDEX idx_dv_chain           ON document_versions(chain_hash);
CREATE        INDEX idx_dv_key             ON document_versions(key_id);
CREATE        INDEX idx_er_doc_status      ON edit_requests(document_id, status);
CREATE        INDEX idx_aa_req_status      ON approval_assignments(edit_request_id, status);
CREATE        INDEX idx_aa_approver        ON approval_assignments(approver_id);
CREATE        INDEX idx_aa_revealed        ON approval_assignments(identity_revealed_at) WHERE identity_revealed_at IS NOT NULL;
CREATE        INDEX idx_audit_doc_time     ON audit_logs(document_id, created_at DESC);
CREATE        INDEX idx_audit_case_time    ON audit_logs(case_id,     created_at DESC);
CREATE        INDEX idx_audit_severity     ON audit_logs(severity) WHERE severity IN ('HIGH','CRITICAL');
CREATE        INDEX idx_notif_unread       ON notifications(recipient_id, is_read) WHERE is_read = FALSE;
CREATE        INDEX idx_access_doc_time    ON document_access_logs(document_id, accessed_at DESC);

-- =============================================================================
-- SEED DATA
-- =============================================================================
INSERT INTO roles (name, pillar, description) VALUES
    ('INVESTIGATING_OFFICER','POLICE','IO: Upload FIRs and evidence. Cannot approve own edits.'),
    ('STATION_HOUSE_OFFICER','POLICE','SHO: Create cases, assign IOs, approve LOW sensitivity edits.'),
    ('SENIOR_POLICE_OFFICER','POLICE','SP/DCP: Approve MEDIUM and HIGH sensitivity edits.'),
    ('FORENSIC_EXPERT','FORENSIC','FSL analyst: Upload forensic reports, view assigned cases.'),
    ('FORENSIC_LAB_HEAD','FORENSIC','FSL director: Approve forensic edits, manage FSL accounts.'),
    ('FORENSIC_AUDITOR','FORENSIC','FSL auditor: Read-only audit logs and chain reports.'),
    ('MAGISTRATE','JUDICIARY','Magistrate: Court verification and tamper-proof certificates.'),
    ('JUDGE','JUDICIARY','Judge: Full read access, chain verification, Merkle reports.'),
    ('COURT_REGISTRAR','JUDICIARY','Registrar: Register cases for trial, manage court access log.'),
    ('PUBLIC_PROSECUTOR','JUDICIARY','PP: View prosecution documents, trigger integrity checks.'),
    ('SYSTEM_ADMIN','ADMIN','IT Admin: Manage accounts and rotate KEK keys. Cannot read case docs.'),
    ('AUDITOR','ADMIN','Auditor: Read-only audit logs, WORM records, chain verification.'),
    ('SUPER_ADMIN','ADMIN','DGP/Ministry: Emergency override (quorum-gated). Full access.');

INSERT INTO quorum_policies (sensitivity_level, required_approvals, pool_size, eligible_roles) VALUES
    ('LOW',      1, 1, ARRAY['STATION_HOUSE_OFFICER','SENIOR_POLICE_OFFICER']),
    ('MEDIUM',   2, 3, ARRAY['SENIOR_POLICE_OFFICER','FORENSIC_LAB_HEAD']),
    ('HIGH',     3, 5, ARRAY['SENIOR_POLICE_OFFICER','FORENSIC_LAB_HEAD','MAGISTRATE']),
    ('CRITICAL', 4, 7, ARRAY['JUDGE','MAGISTRATE','FORENSIC_LAB_HEAD','SUPER_ADMIN']);

COMMIT;

-- VERIFICATION (uncomment to run after migration):
-- SELECT COUNT(*) AS table_count FROM pg_tables WHERE schemaname='public';  -- expect 17
-- SELECT name, pillar FROM roles ORDER BY pillar, name;                      -- expect 13 rows
-- SELECT sensitivity_level, required_approvals, pool_size FROM quorum_policies; -- expect 4 rows
-- SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_schema='public';
-- SELECT rulename, tablename FROM pg_rules WHERE schemaname='public';        -- expect 2 WORM rules
