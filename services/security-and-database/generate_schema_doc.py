from docx import Document
from docx.shared import Pt, RGBColor, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ── Page margins ──────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin   = Cm(2.5)
    section.right_margin  = Cm(2.5)

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY   = RGBColor(0x1A, 0x35, 0x6E)   # headings
TEAL   = RGBColor(0x00, 0x70, 0x96)   # sub-headings
GREEN  = RGBColor(0x1E, 0x7E, 0x34)   # PASS
RED    = RGBColor(0xC8, 0x20, 0x2C)   # FAIL
AMBER  = RGBColor(0xD4, 0x7F, 0x00)   # WARNING
WHITE  = RGBColor(0xFF, 0xFF, 0xFF)
LGREY  = RGBColor(0xF2, 0xF2, 0xF2)   # table row alt
HEADER = RGBColor(0x1A, 0x35, 0x6E)   # table header bg

# ── Helper functions ──────────────────────────────────────────────────────────
def set_cell_bg(cell, rgb: RGBColor):
    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  '{:02X}{:02X}{:02X}'.format(rgb[0], rgb[1], rgb[2]))
    tcPr.append(shd)

def set_cell_borders(tbl):
    """Thin borders on every cell of the table."""
    for row in tbl.rows:
        for cell in row.cells:
            tc   = cell._tc
            tcPr = tc.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for side in ('top','left','bottom','right'):
                el = OxmlElement(f'w:{side}')
                el.set(qn('w:val'),  'single')
                el.set(qn('w:sz'),   '4')
                el.set(qn('w:space'),'0')
                el.set(qn('w:color'),'AAAAAA')
                tcBorders.append(el)
            tcPr.append(tcBorders)

def heading1(text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = NAVY
    run.font.name = 'Calibri'
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after  = Pt(6)
    # underline rule
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bot  = OxmlElement('w:bottom')
    bot.set(qn('w:val'),  'single')
    bot.set(qn('w:sz'),   '6')
    bot.set(qn('w:space'),'1')
    bot.set(qn('w:color'),'{:02X}{:02X}{:02X}'.format(NAVY[0], NAVY[1], NAVY[2]))
    pBdr.append(bot)
    pPr.append(pBdr)
    return p

def heading2(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(13)
    run.font.color.rgb = TEAL
    run.font.name = 'Calibri'
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after  = Pt(4)
    return p

def heading3(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = True
    run.font.size = Pt(11)
    run.font.color.rgb = NAVY
    run.font.name = 'Calibri'
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after  = Pt(2)
    return p

def body(text, indent=0):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.font.name = 'Calibri'
    p.paragraph_format.space_after = Pt(4)
    if indent:
        p.paragraph_format.left_indent = Inches(indent * 0.3)
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style='List Bullet')
    run = p.add_run(text)
    run.font.size = Pt(10.5)
    run.font.name = 'Calibri'
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.left_indent = Inches(0.3 + level*0.3)
    return p

def code_block(text):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = 'Courier New'
    run.font.size = Pt(9)
    run.font.color.rgb = RGBColor(0x1A,0x1A,0x1A)
    p.paragraph_format.left_indent  = Inches(0.4)
    p.paragraph_format.space_after  = Pt(2)
    p.paragraph_format.space_before = Pt(2)
    # light grey background via paragraph shading
    pPr = p._p.get_or_add_pPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'),   'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'),  'F0F0F0')
    pPr.append(shd)
    return p

def make_table(headers, rows, col_widths=None):
    """Creates a styled table with navy header row."""
    tbl = doc.add_table(rows=1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.LEFT
    tbl.style = 'Table Grid'
    # Header row
    hdr = tbl.rows[0]
    for i, h in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_bg(cell, HEADER)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(h)
        run.bold = True
        run.font.color.rgb = WHITE
        run.font.size = Pt(9.5)
        run.font.name = 'Calibri'
    # Data rows
    for ri, row_data in enumerate(rows):
        row = tbl.add_row()
        bg  = LGREY if ri % 2 == 0 else WHITE
        for ci, val in enumerate(row_data):
            cell = row.cells[ci]
            set_cell_bg(cell, bg)
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.size = Pt(9.5)
            run.font.name = 'Calibri'
    set_cell_borders(tbl)
    # column widths
    if col_widths:
        for row in tbl.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Inches(w)
    doc.add_paragraph()   # spacing after table
    return tbl

def pass_fail_table(checks):
    """Green PASS / Red FAIL status table."""
    tbl = doc.add_table(rows=1, cols=3)
    tbl.style = 'Table Grid'
    hdr = tbl.rows[0]
    for i, h in enumerate(['Check', 'Status', 'Detail']):
        set_cell_bg(hdr.cells[i], HEADER)
        p = hdr.cells[i].paragraphs[0]
        run = p.add_run(h)
        run.bold = True; run.font.color.rgb = WHITE
        run.font.size = Pt(9.5); run.font.name = 'Calibri'
    for check, status, detail in checks:
        row  = tbl.add_row()
        col  = GREEN if status == 'PASS' else RED
        row.cells[0].paragraphs[0].add_run(check).font.size = Pt(9.5)
        row.cells[0].paragraphs[0].runs[0].font.name = 'Calibri'
        s_run = row.cells[1].paragraphs[0].add_run(status)
        s_run.bold = True; s_run.font.color.rgb = col
        s_run.font.size = Pt(9.5); s_run.font.name = 'Calibri'
        row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        row.cells[2].paragraphs[0].add_run(detail).font.size = Pt(9.5)
        row.cells[2].paragraphs[0].runs[0].font.name = 'Calibri'
    set_cell_borders(tbl)
    tbl.columns[0].width = Inches(2.8)
    tbl.columns[1].width = Inches(0.7)
    tbl.columns[2].width = Inches(3.5)
    doc.add_paragraph()

# ==============================================================================
# COVER PAGE
# ==============================================================================
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('SECURECHAIN DMS')
run.bold = True; run.font.size = Pt(28); run.font.color.rgb = NAVY; run.font.name = 'Calibri'

p2 = doc.add_paragraph()
p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
run2 = p2.add_run('PostgreSQL Database Schema — Complete Technical Document')
run2.font.size = Pt(14); run2.font.color.rgb = TEAL; run2.font.name = 'Calibri'

p3 = doc.add_paragraph()
p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
run3 = p3.add_run('SIH26190  |  Zero-Trust Legal Evidence Vault  |  Schema v0.3')
run3.font.size = Pt(11); run3.font.name = 'Calibri'

doc.add_paragraph()
make_table(
    ['Item','Value'],
    [
        ['Problem Statement', 'SIH26190 — Secure Digital Document Management'],
        ['Version',           'v0.3 (Production Schema)'],
        ['Total Tables',      '17'],
        ['Triggers',          '8'],
        ['WORM Rules',        '2'],
        ['Indexes',           '22'],
        ['Seed Data',         '13 Roles + 4 Quorum Policies'],
        ['Status',            'APPROVED FOR IMPLEMENTATION'],
    ],
    col_widths=[2.0, 4.5]
)
doc.add_page_break()

# ==============================================================================
# 1. WHAT CHANGED FROM v0.1 → v0.3
# ==============================================================================
heading1('1. What Changed from v0.1 to v0.3')
make_table(
    ['Area', 'v0.1 Status', 'v0.3 Fix'],
    [
        ['Encryption fields in document_versions', 'MISSING — could not decrypt files',
         'Added wrapped_dek, iv, key_id, kek_version, aad'],
        ['Hash-chain columns', 'Ambiguous file_hash / previous_hash',
         'Renamed to doc_hash, chain_hash, prev_chain_hash'],
        ['Quorum proof in chain', 'MISSING — amendments unverifiable',
         'Added quorum_token baked into chain_hash formula'],
        ['Merkle Checkpoint table', 'MISSING',
         'New merkle_checkpoints table for global Merkle anchoring'],
        ['DSC verification table', 'MISSING',
         'New dsc_verifications table for Pillar 5 compliance'],
        ['Case access control', 'BROKEN — Forensic/Judiciary invisible to cases',
         'New case_participants table — the access control gateway'],
        ['Cross-department notifications', 'MISSING',
         'New notifications table + trigger fires on every upload'],
        ['Version comparison for judges', 'MISSING — full re-decryption required',
         'New document_diffs table — instant pre-computed diff'],
        ['Access audit (BSA S63)', 'MISSING',
         'New document_access_logs with chain_hash_at_access snapshot'],
        ['Court handover', 'MISSING',
         'New case_court_registrations table'],
        ['Approver anonymity control', 'No reveal mechanism',
         'identity_revealed_at column + trigger on approval_assignments'],
        ['Audit severity', 'MISSING',
         'Added severity column to audit_logs (INFO/WARNING/HIGH/CRITICAL)'],
        ['Role pillar grouping', 'Generic names only',
         'Added pillar column to roles (POLICE/FORENSIC/JUDICIARY/ADMIN)'],
    ],
    col_widths=[2.0, 1.8, 3.2]
)

# ==============================================================================
# 2. SENSITIVITY COLUMN — DEEP AUDIT
# ==============================================================================
heading1('2. Sensitivity Column — Deep Audit')
body('The sensitivity_level column is the engine that drives the entire approval workflow. '
     'Every document uploaded must carry a sensitivity classification, and that classification '
     'determines exactly how many officers must approve any amendment, and which roles are eligible to vote.')

heading2('2.1  Audit Result — All 9 Checks PASSED')
pass_fail_table([
    ('documents.sensitivity_level column present',       'PASS', 'Line 92 in migration SQL'),
    ('CHECK constraint LOW/MEDIUM/HIGH/CRITICAL',        'PASS', 'Line 93 — invalid values rejected at DB level'),
    ('quorum_policies table present',                    'PASS', 'Table 6 in schema'),
    ('quorum_policies.sensitivity_level UNIQUE',         'PASS', 'One policy per sensitivity level'),
    ('edit_requests.quorum_policy_id FK',                'PASS', 'Policy snapshot stored at request creation'),
    ('quorum_policies.eligible_roles array',             'PASS', 'Controls WHICH roles can vote'),
    ('quorum_policies.required_approvals (M)',           'PASS', 'Minimum votes needed'),
    ('quorum_policies.pool_size (N)',                    'PASS', 'Total approvers assigned'),
    ('Seed data for all 4 sensitivity levels',           'PASS', 'LOW/MEDIUM/HIGH/CRITICAL all seeded'),
])

heading2('2.2  How Sensitivity Drives the Approval Engine')
body('When a document is uploaded, the officer must select its sensitivity level. '
     'This value is stored in documents.sensitivity_level. When any officer later requests an '
     'amendment, the approval engine performs the following chain of lookups:')

steps = [
    ('Step 1', 'Officer uploads document',
     'documents.sensitivity_level = HIGH is saved to database.'),
    ('Step 2', 'Amendment requested',
     'App queries: SELECT * FROM quorum_policies WHERE sensitivity_level = HIGH'),
    ('Step 3', 'Policy snapshot captured',
     'Returns: required_approvals=3, pool_size=5, eligible_roles=[SR_POLICE, FSL_HEAD, MAGISTRATE]'),
    ('Step 4', 'Policy FK stored',
     'edit_requests.quorum_policy_id = <HIGH policy UUID> — snapshot, not a live reference'),
    ('Step 5', 'Approver pool created',
     '5 approval_assignments created. None can be the requester (self-approval trigger blocks it).'),
    ('Step 6', 'Officers vote',
     'Each eligible officer creates one approvals row with APPROVED or REJECTED.'),
    ('Step 7', 'Quorum check',
     'App counts: SELECT COUNT(*) FROM approvals WHERE decision=APPROVED >= 3'),
    ('Step 8', 'Decision finalized',
     'edit_requests.status = APPROVED. Trigger fires. Approver identities revealed to judiciary.'),
]
make_table(['Step','Action','Database Effect'], steps, col_widths=[0.7, 1.8, 4.5])

heading2('2.3  Sensitivity → Quorum Policy Mapping')
make_table(
    ['Sensitivity', 'M (Min Approvals)', 'N (Pool Size)', 'Eligible Roles', 'Use Case'],
    [
        ['LOW',      '1', '1', 'SHO, Senior Police Officer',
         'Internal notes, case diary entries'],
        ['MEDIUM',   '2', '3', 'Senior Police Officer, FSL Lab Head',
         'Witness statements, progress notes'],
        ['HIGH',     '3', '5', 'Senior Police Officer, FSL Lab Head, Magistrate',
         'FIR amendments, chargesheet changes'],
        ['CRITICAL', '4', '7', 'Judge, Magistrate, FSL Lab Head, Super Admin',
         'Major forensic report edits, court-ordered changes'],
    ],
    col_widths=[1.0, 1.1, 1.0, 2.5, 2.0]
)

heading2('2.4  The sensitivity_level Found in 9 Places in Migration SQL')
locs = [
    ('Line 92',  'documents table',          'Column definition: sensitivity_level VARCHAR(20) NOT NULL'),
    ('Line 93',  'documents table',          "CHECK constraint: IN ('LOW','MEDIUM','HIGH','CRITICAL')"),
    ('Line 143', 'quorum_policies table',    'Column definition: sensitivity_level VARCHAR(20) UNIQUE NOT NULL'),
    ('Line 144', 'quorum_policies table',    "CHECK constraint: IN ('LOW','MEDIUM','HIGH','CRITICAL')"),
    ('Line 398', 'fn_notify_upload trigger', 'Drives notification severity: CRITICAL→HIGH, HIGH→WARNING'),
    ('Line 399', 'fn_notify_upload trigger', 'MEDIUM/LOW → INFO severity'),
    ('Line 459', 'Indexes',                  'CREATE INDEX idx_docs_sensitivity ON documents(sensitivity_level)'),
    ('Line 492', 'Seed data',                'INSERT INTO quorum_policies — all 4 levels seeded'),
    ('Line 503', 'Verification comment',     'Post-migration verification query'),
]
make_table(['Location','Table/Function','Purpose'], locs, col_widths=[1.0, 1.8, 4.2])

doc.add_page_break()

# ==============================================================================
# 3. ROLE ARCHITECTURE
# ==============================================================================
heading1('3. Role Architecture — 13 Roles Across 4 Pillars')

heading2('3.1  Police Wing')
make_table(
    ['Role (DB Name)', 'Display Name', 'Who Holds It', 'Key Permissions'],
    [
        ['INVESTIGATING_OFFICER', 'Investigating Officer', 'IO assigned to case',
         'Upload FIR/evidence, request edits on own documents, view own cases'],
        ['STATION_HOUSE_OFFICER', 'Station House Officer', 'SHO of police station',
         'Create cases, assign IOs, add participants, approve LOW edits (1-of-1)'],
        ['SENIOR_POLICE_OFFICER', 'Senior Police Officer / SP', 'District SP or above',
         'Approve MEDIUM and HIGH sensitivity edits, view cross-station cases'],
    ],
    col_widths=[1.7, 1.5, 1.4, 2.4]
)

heading2('3.2  Forensic Wing')
make_table(
    ['Role (DB Name)', 'Display Name', 'Who Holds It', 'Key Permissions'],
    [
        ['FORENSIC_EXPERT', 'Forensic Expert', 'FSL officer/analyst',
         'Upload forensic reports, view assigned cases, cannot approve non-forensic docs'],
        ['FORENSIC_LAB_HEAD', 'Forensic Lab Head', 'FSL director',
         'Approve forensic edits, manage forensic accounts, view FSL case portfolio'],
        ['FORENSIC_AUDITOR', 'Forensic Auditor', 'Internal FSL auditor',
         'Read-only: audit logs, chain integrity reports, Merkle checkpoints'],
    ],
    col_widths=[1.7, 1.5, 1.4, 2.4]
)

heading2('3.3  Judiciary Wing')
make_table(
    ['Role (DB Name)', 'Display Name', 'Who Holds It', 'Key Permissions'],
    [
        ['MAGISTRATE', 'Judicial Magistrate', 'Magistrate court officer',
         'Request court verification, view tamper-proof certificates, view all assigned docs'],
        ['JUDGE', 'Sessions / High Court Judge', 'Sitting judge',
         'Full read access, trigger chain verification, approve CRITICAL edits, Merkle reports'],
        ['COURT_REGISTRAR', 'Court Registrar', 'Court admin staff',
         'Register cases for trial, create case_court_registrations, manage court access log'],
        ['PUBLIC_PROSECUTOR', 'Public Prosecutor', 'Government prosecutor',
         'View all assigned prosecution documents, trigger pre-trial integrity checks'],
    ],
    col_widths=[1.7, 1.5, 1.4, 2.4]
)

heading2('3.4  System / Admin Wing')
make_table(
    ['Role (DB Name)', 'Display Name', 'Who Holds It', 'Key Permissions'],
    [
        ['SYSTEM_ADMIN', 'System Administrator', 'IT admin',
         'Manage user accounts, rotate KEK keys, view system audit logs — CANNOT read case docs'],
        ['AUDITOR', 'Independent Auditor', 'Internal/external auditor',
         'Read-only: audit logs, WORM records, chain verification, Merkle checkpoint reports'],
        ['SUPER_ADMIN', 'Super Administrator', 'DGP/Ministry-level authority',
         'Emergency override (quorum-gated even here), manage all accounts, full access'],
    ],
    col_widths=[1.7, 1.5, 1.4, 2.4]
)

heading2('3.5  Role Permission Matrix')
make_table(
    ['Action', 'IO', 'SHO', 'SR\nPOLICE', 'FSL\nEXPERT', 'FSL\nHEAD', 'FSL\nAUDIT', 'MAGI\nSTRATE', 'JUDGE', 'REGIS\nTRAR', 'PROS\nECUTOR', 'SYS\nADMIN', 'AUDIT\nOR', 'SUPER\nADMIN'],
    [
        ['Create Case',          'Y','Y','Y','—','—','—','—','—','Y','—','—','—','Y'],
        ['Upload Document',      'Y','Y','Y','Y','Y','—','—','—','—','—','—','—','Y'],
        ['Request Edit',         'Y','Y','Y','Y','Y','—','—','—','—','—','—','—','Y'],
        ['Approve Edit (LOW)',   '—','Y','Y','—','—','—','—','—','—','—','—','—','Y'],
        ['Approve Edit (MEDIUM)','—','—','Y','—','Y','—','—','—','—','—','—','—','Y'],
        ['Approve Edit (HIGH)',  '—','—','Y','—','Y','—','Y','—','—','—','—','—','Y'],
        ['Approve Edit (CRITICAL)','—','—','—','—','Y','—','Y','Y','—','—','—','—','Y'],
        ['View Own Case Docs',   'Y','Y','Y','Y','Y','—','Y','Y','Y','Y','—','—','Y'],
        ['View All Cases',       '—','—','Y','—','Y','—','—','Y','Y','Y','—','—','Y'],
        ['Verify Chain',         '—','—','—','—','Y','Y','Y','Y','—','—','—','Y','Y'],
        ['Court Certificate',    '—','—','—','—','—','—','Y','Y','Y','Y','—','—','Y'],
        ['View Audit Logs',      '—','—','Y','—','Y','Y','—','Y','—','—','Y','Y','Y'],
        ['Rotate KEK Keys',      '—','—','—','—','—','—','—','—','—','—','Y','—','Y'],
        ['Manage Accounts',      '—','—','—','—','—','—','—','—','—','—','Y','—','Y'],
        ['Merkle Checkpoint',    '—','—','—','—','—','Y','—','—','—','—','Y','Y','Y'],
        ['Emergency Override',   '—','—','—','—','—','—','—','—','—','—','—','—','Y'],
    ],
    col_widths=[1.7,0.3,0.3,0.4,0.4,0.4,0.4,0.5,0.4,0.4,0.5,0.4,0.5,0.5]
)

doc.add_page_break()

# ==============================================================================
# 4. ALL 17 TABLES
# ==============================================================================
heading1('4. All 17 Tables — Schema Reference')

tables_data = [
    ('Table 1: roles', 'Defines the 13 application roles across 4 pillars.',
     [('id','UUID','PK','Unique role identifier'),
      ('name','VARCHAR(50)','UNIQUE NOT NULL','e.g. INVESTIGATING_OFFICER, MAGISTRATE'),
      ('pillar','VARCHAR(30)','NOT NULL CHECK','POLICE / FORENSIC / JUDICIARY / ADMIN'),
      ('description','TEXT','—','Human-readable role description'),
      ('created_at','TIMESTAMPTZ','DEFAULT NOW()','Creation time')]),

    ('Table 2: users', 'Every government officer, judge, and admin who accesses the system.',
     [('id','UUID','PK','User identifier'),
      ('employee_id','VARCHAR(50)','UNIQUE NOT NULL','Government / employee ID'),
      ('full_name','VARCHAR(150)','NOT NULL','Full name'),
      ('email','VARCHAR(255)','UNIQUE','Work email'),
      ('phone','VARCHAR(20)','—','OTP phone number'),
      ('role_id','UUID','FK -> roles.id','Single role assignment (RBAC)'),
      ('department','VARCHAR(100)','—','Police station / FSL / Court name'),
      ('jurisdiction','VARCHAR(150)','—','District / zone / court jurisdiction'),
      ('dsc_certificate','TEXT','—','PEM X.509 cert from NIC CA'),
      ('dsc_expires_at','TIMESTAMPTZ','—','DSC expiry — system warns/blocks on expiry'),
      ('password_hash','VARCHAR(255)','NOT NULL','Bcrypt hash'),
      ('is_active','BOOLEAN','DEFAULT TRUE','Account active flag'),
      ('failed_logins','SMALLINT','DEFAULT 0','Locked after 5 failures'),
      ('created_at','TIMESTAMPTZ','DEFAULT NOW()','Creation time'),
      ('updated_at','TIMESTAMPTZ','DEFAULT NOW()','Last update — auto via trigger')]),

    ('Table 3: cases', 'Top-level legal container. All documents hang off a case.',
     [('id','UUID','PK','Case identifier'),
      ('case_number','VARCHAR(100)','UNIQUE NOT NULL','Official FIR number'),
      ('title','VARCHAR(255)','NOT NULL','Case title'),
      ('case_type','VARCHAR(100)','—','CRIMINAL / CIVIL / FORENSIC / CYBER'),
      ('department','VARCHAR(100)','—','Originating police station'),
      ('jurisdiction','VARCHAR(150)','—','Police jurisdiction'),
      ('created_by','UUID','FK -> users.id','SHO who created the case'),
      ('status','VARCHAR(30)','CHECK','ACTIVE / UNDER_REVIEW / CLOSED / STAYED'),
      ('created_at','TIMESTAMPTZ','DEFAULT NOW()','Creation time'),
      ('updated_at','TIMESTAMPTZ','DEFAULT NOW()','Auto-updated via trigger')]),

    ('Table 4: documents', 'Logical document record. Groups all immutable versions.',
     [('id','UUID','PK','Document identifier'),
      ('case_id','UUID','FK -> cases.id','Owning case'),
      ('title','VARCHAR(255)','NOT NULL','Document title'),
      ('document_type','VARCHAR(100)','NOT NULL CHECK','FIR / CHARGESHEET / FORENSIC_REPORT / etc.'),
      ('sensitivity_level','VARCHAR(20)','NOT NULL CHECK','LOW / MEDIUM / HIGH / CRITICAL'),
      ('current_version_id','UUID','FK DEFERRABLE','Latest approved version (circular FK)'),
      ('status','VARCHAR(30)','CHECK','DRAFT / LOCKED / PENDING_QUORUM / UNDER_AMENDMENT / ARCHIVED'),
      ('created_by','UUID','FK -> users.id','Uploader'),
      ('created_at','TIMESTAMPTZ','DEFAULT NOW()','Creation time'),
      ('updated_at','TIMESTAMPTZ','DEFAULT NOW()','Auto-updated via trigger')]),

    ('Table 5: document_versions', '[CRITICAL] Immutable snapshots. Contains all Vault 1 key material.',
     [('id','UUID','PK','Version identifier'),
      ('document_id','UUID','FK -> documents.id','Parent document'),
      ('version_number','INTEGER','CHECK >= 1','1=v1.0, 2=v1.1...'),
      ('storage_key','TEXT','NOT NULL UNIQUE','Object-storage path (Vault 2 pointer)'),
      ('doc_hash','CHAR(64)','NOT NULL','SHA-256 of original plaintext file'),
      ('chain_hash','CHAR(64)','NOT NULL UNIQUE','SHA256(doc_hash||prev_chain||timestamp||officer||quorum_token)'),
      ('prev_chain_hash','CHAR(64)','NOT NULL','000...0 for v1. Previous chain_hash for amendments.'),
      ('quorum_token','TEXT','—','NULL for v1.0. Required for v1.1+ amendments.'),
      ('wrapped_dek','TEXT','NOT NULL','AES-256-GCM encrypted Data Encryption Key [VAULT 1]'),
      ('iv','VARCHAR(24)','NOT NULL','96-bit AES-GCM Initialization Vector, hex-encoded'),
      ('key_id','UUID','NOT NULL','UUID of the KEK that wrapped this DEK'),
      ('kek_version','VARCHAR(10)','NOT NULL',"'v1','v2' etc. — supports KEK rotation"),
      ('aad','TEXT','NOT NULL','Additional Authenticated Data: doc_id:case_id:version'),
      ('algorithm','VARCHAR(20)','DEFAULT AES-256-GCM','Encryption algorithm'),
      ('file_size','BIGINT','CHECK > 0','File size in bytes'),
      ('mime_type','VARCHAR(100)','—','MIME type'),
      ('original_filename','VARCHAR(255)','—','Original uploaded filename'),
      ('created_by','UUID','FK -> users.id','Uploader of this version'),
      ('status','VARCHAR(30)','CHECK','DRAFT / LOCKED / APPROVED / REJECTED'),
      ('created_at','TIMESTAMPTZ','DEFAULT NOW()','Creation timestamp')]),

    ('Table 6: quorum_policies', 'M-of-N approval rules. One policy per sensitivity level.',
     [('id','UUID','PK','Policy identifier'),
      ('sensitivity_level','VARCHAR(20)','UNIQUE NOT NULL CHECK','LOW / MEDIUM / HIGH / CRITICAL'),
      ('required_approvals','INTEGER','CHECK > 0','M — minimum votes to approve'),
      ('pool_size','INTEGER','CHECK >= M','N — total approvers assigned'),
      ('eligible_roles','TEXT[]','NOT NULL','Array of role names allowed to vote')]),

    ('Table 7: case_participants [NEW]', 'THE ACCESS CONTROL TABLE. No row here = user cannot see the case.',
     [('id','UUID','PK','Assignment identifier'),
      ('case_id','UUID','FK -> cases.id ON DELETE CASCADE','The case'),
      ('participant_id','UUID','FK -> users.id','The user being granted access'),
      ('access_level','VARCHAR(30)','CHECK','READ / READ_WRITE / APPROVE / VERIFY / FULL'),
      ('added_by','UUID','FK -> users.id','SHO or admin who added this participant'),
      ('added_at','TIMESTAMPTZ','DEFAULT NOW()','When access was granted'),
      ('removed_at','TIMESTAMPTZ','DEFAULT NULL','NULL=active. Set to revoke (soft delete).'),
      ('removal_reason','TEXT','—','Reason for revoking access')]),

    ('Table 8: edit_requests', 'Formal amendment request. Quorum policy snapshot stored at creation.',
     [('id','UUID','PK','Request identifier'),
      ('document_id','UUID','FK -> documents.id','Document being amended'),
      ('requester_id','UUID','FK -> users.id','Officer requesting the change'),
      ('source_version_id','UUID','FK -> document_versions.id','Version being amended (the old doc)'),
      ('proposed_version_id','UUID','FK -> document_versions.id','Draft new version (NULL until uploaded)'),
      ('quorum_policy_id','UUID','FK -> quorum_policies.id','Policy snapshot at request time'),
      ('reason','TEXT','NOT NULL','Human-readable reason for amendment'),
      ('amendment_reason_code','VARCHAR(50)','CHECK','FACTUAL_ERROR / NEW_EVIDENCE / COURT_ORDER / CLERICAL'),
      ('status','VARCHAR(30)','CHECK','PENDING_QUORUM / APPROVED / REJECTED / WITHDRAWN / EXPIRED'),
      ('requested_at','TIMESTAMPTZ','DEFAULT NOW()','Request time'),
      ('completed_at','TIMESTAMPTZ','—','Set when APPROVED/REJECTED'),
      ('expires_at','TIMESTAMPTZ','—','Deadline — cron sets status=EXPIRED after this')]),

    ('Table 9: approval_assignments', 'Approver pool. Blind review via anonymous_token during quorum.',
     [('id','UUID','PK','Assignment identifier'),
      ('edit_request_id','UUID','FK -> edit_requests.id','The request'),
      ('approver_id','UUID','FK -> users.id','Real identity — backend only, never exposed during quorum'),
      ('anonymous_token','UUID','UNIQUE DEFAULT gen_random_uuid()','Opaque token shown on UI'),
      ('assigned_at','TIMESTAMPTZ','DEFAULT NOW()','Assignment time'),
      ('expires_at','TIMESTAMPTZ','—','Optional deadline per approver'),
      ('status','VARCHAR(30)','CHECK','PENDING / VOTED / EXPIRED / RECUSED'),
      ('identity_revealed_at','TIMESTAMPTZ','DEFAULT NULL','NULL=anonymous. Set by trigger after final decision.')]),

    ('Table 10: approvals', 'One vote per assignment. dsc_signature provides non-repudiation.',
     [('id','UUID','PK','Approval identifier'),
      ('assignment_id','UUID','UNIQUE FK','One decision per assignment'),
      ('decision','VARCHAR(20)','CHECK','APPROVED or REJECTED'),
      ('remarks','TEXT','—','Optional legal remarks by approver'),
      ('dsc_signature','TEXT','—','Digital signature of the decision (signed with approver DSC)'),
      ('approved_at','TIMESTAMPTZ','DEFAULT NOW()','Decision timestamp')]),

    ('Table 11: audit_logs', 'WORM append-only event log. UPDATE and DELETE blocked by SQL RULES.',
     [('id','UUID','PK','Audit event identifier'),
      ('event_type','VARCHAR(50)','NOT NULL CHECK','LOGIN / UPLOAD / EDIT_REQUESTED / TAMPER_ALERT / etc.'),
      ('severity','VARCHAR(20)','CHECK','INFO / WARNING / HIGH / CRITICAL'),
      ('actor_id','UUID','FK -> users.id','NULL for system-generated events'),
      ('case_id','UUID','FK -> cases.id','Related case'),
      ('document_id','UUID','FK -> documents.id','Related document'),
      ('version_id','UUID','FK -> document_versions.id','Related version'),
      ('metadata','JSONB','DEFAULT {}','Flexible additional payload'),
      ('previous_hash','CHAR(64)','—','Hash of previous audit event (audit chain link)'),
      ('event_hash','CHAR(64)','NOT NULL','SHA-256 of this event record'),
      ('log_hash','CHAR(64)','NOT NULL','WORM self-verifying hash from TamperAlertSystem'),
      ('created_at','TIMESTAMPTZ','DEFAULT NOW()','Event time')]),

    ('Table 12: merkle_checkpoints [NEW]', 'Global Merkle anchor. Single root covers all cases.',
     [('id','UUID','PK','Checkpoint identifier'),
      ('merkle_root','CHAR(64)','NOT NULL','SHA-256 Merkle root hash'),
      ('cases_included','INTEGER','CHECK > 0','Number of cases anchored in this checkpoint'),
      ('case_chain_heads','JSONB','NOT NULL','Snapshot: {case_id: head_chain_hash}'),
      ('created_by','UUID','FK -> users.id','NULL for automated cron checkpoints'),
      ('created_at','TIMESTAMPTZ','DEFAULT NOW()','Checkpoint creation time')]),

    ('Table 13: dsc_verifications [NEW]', 'Pre-upload DSC certificate check record.',
     [('id','UUID','PK','Verification identifier'),
      ('user_id','UUID','FK -> users.id','Officer whose DSC was checked'),
      ('document_version_id','UUID','FK -> document_versions.id','NULL if DSC failed before version created'),
      ('dsc_thumbprint','VARCHAR(128)','NOT NULL','SHA-256 thumbprint of the certificate'),
      ('dsc_issuer','VARCHAR(255)','—','Certificate authority (e.g. NIC CA)'),
      ('dsc_valid_from','TIMESTAMPTZ','—','Certificate validity start'),
      ('dsc_valid_to','TIMESTAMPTZ','—','Certificate validity end'),
      ('verification_result','VARCHAR(20)','CHECK','VALID / EXPIRED / REVOKED / FAILED'),
      ('failure_reason','TEXT','—','Reason for failure if not VALID'),
      ('verified_at','TIMESTAMPTZ','DEFAULT NOW()','When check was performed')]),

    ('Table 14: notifications [NEW]', 'In-app notifications fired by database triggers.',
     [('id','UUID','PK','Notification identifier'),
      ('recipient_id','UUID','FK -> users.id','Who receives this notification'),
      ('sender_id','UUID','FK -> users.id','NULL for system-generated notifications'),
      ('notification_type','VARCHAR(60)','CHECK','CASE_ASSIGNED / FIR_UPLOADED / FORENSIC_REPORT_UPLOADED / etc.'),
      ('case_id','UUID','FK -> cases.id','Related case'),
      ('document_id','UUID','FK -> documents.id','Related document'),
      ('title','VARCHAR(255)','NOT NULL','Notification title'),
      ('message','TEXT','—','Full notification body'),
      ('severity','VARCHAR(20)','CHECK','INFO / WARNING / HIGH / CRITICAL'),
      ('is_read','BOOLEAN','DEFAULT FALSE','Read flag'),
      ('created_at','TIMESTAMPTZ','DEFAULT NOW()','Creation time'),
      ('read_at','TIMESTAMPTZ','—','When user marked as read')]),

    ('Table 15: document_diffs [NEW]', 'Pre-computed version diff for instant judicial comparison.',
     [('id','UUID','PK','Diff identifier'),
      ('edit_request_id','UUID','UNIQUE FK','One diff per edit request'),
      ('source_version_id','UUID','FK -> document_versions.id','The old version'),
      ('target_version_id','UUID','FK -> document_versions.id','The new version'),
      ('diff_summary','TEXT','—','Human-readable: "3 sections changed, 12 lines added"'),
      ('diff_payload','JSONB','—','Structured: [{line_no, type, old_text, new_text}]'),
      ('changed_sections','TEXT[]','DEFAULT {}','["Section 3 - Accused Details", ...]'),
      ('lines_added','INTEGER','DEFAULT 0','Count of added lines'),
      ('lines_removed','INTEGER','DEFAULT 0','Count of removed lines'),
      ('lines_modified','INTEGER','DEFAULT 0','Count of modified lines'),
      ('diff_hash','CHAR(64)','—','SHA-256 of diff_payload — proves diff was not altered'),
      ('computed_at','TIMESTAMPTZ','DEFAULT NOW()','When diff was computed')]),

    ('Table 16: document_access_logs [NEW]', 'Judicial access log. Required for BSA S63 compliance.',
     [('id','UUID','PK','Access log identifier'),
      ('user_id','UUID','FK -> users.id','Who accessed the document'),
      ('document_id','UUID','FK -> documents.id','Which document was accessed'),
      ('version_id','UUID','FK -> document_versions.id','Which version was accessed'),
      ('access_type','VARCHAR(30)','CHECK','VIEW / COMPARE / DOWNLOAD / PRINT / VERIFY_HASH / CERT_REQUEST'),
      ('chain_hash_at_access','CHAR(64)','—','Snapshot of chain_hash — proves doc was intact when viewed'),
      ('ip_address','INET','—','IP address of accessor'),
      ('user_agent','TEXT','—','Browser/client info'),
      ('accessed_at','TIMESTAMPTZ','DEFAULT NOW()','Access timestamp')]),

    ('Table 17: case_court_registrations [NEW]', 'Formal Police-to-Court handover record.',
     [('id','UUID','PK','Registration identifier'),
      ('case_id','UUID','FK -> cases.id','The case being registered'),
      ('court_name','VARCHAR(255)','NOT NULL','Name of the court'),
      ('court_case_number','VARCHAR(100)','UNIQUE','Court-issued docket number'),
      ('registered_by','UUID','FK -> users.id','Must be COURT_REGISTRAR role'),
      ('presiding_judge_id','UUID','FK -> users.id','Assigned presiding judge'),
      ('prosecutor_id','UUID','FK -> users.id','Assigned public prosecutor'),
      ('registration_date','TIMESTAMPTZ','DEFAULT NOW()','Date of court registration'),
      ('status','VARCHAR(30)','CHECK','ACTIVE / DISPOSED / APPEALED / STAYED / TRANSFERRED')]),
]

for title, desc, cols in tables_data:
    heading2(title)
    body(desc)
    make_table(['Column','Type','Constraint','Meaning'], cols, col_widths=[1.5, 1.1, 1.4, 3.0])

doc.add_page_break()

# ==============================================================================
# 5. TRIGGERS
# ==============================================================================
heading1('5. Database Triggers — 8 Total')
make_table(
    ['#','Trigger Name','Table','When Fires','What It Enforces'],
    [
        ['1','trg_no_self_approval','approval_assignments','BEFORE INSERT',
         'Blocks IO from being added as approver on their own edit request. HTTP 403 at DB level.'],
        ['2','trg_protect_locked','document_versions','BEFORE UPDATE',
         'Raises exception if any column of a LOCKED/APPROVED/REJECTED version is modified. Absolute immutability.'],
        ['3','rule_audit_no_update','audit_logs','ON UPDATE (RULE)',
         'WORM: Silently drops any UPDATE attempt. Cannot be bypassed by triggers.'],
        ['4','rule_audit_no_delete','audit_logs','ON DELETE (RULE)',
         'WORM: Silently drops any DELETE attempt. Cannot be bypassed by triggers.'],
        ['5','trg_reveal_identities','edit_requests','AFTER UPDATE status',
         'When status changes to APPROVED/REJECTED, sets identity_revealed_at=NOW() on all assignments. Judges can now see real approvers.'],
        ['6','trg_notify_upload','documents','AFTER INSERT',
         'Fires notification to ALL case participants when any document is uploaded (FIR, Forensic Report, Evidence).'],
        ['7','trg_notify_quorum','edit_requests','AFTER UPDATE status',
         'Fires notification to requester and all participants when amendment is APPROVED or REJECTED.'],
        ['8','trg_ts_cases/docs/users','cases/documents/users','BEFORE UPDATE',
         'Auto-updates updated_at timestamp on modification.'],
    ],
    col_widths=[0.2, 1.6, 1.4, 1.2, 3.1]
)

doc.add_page_break()

# ==============================================================================
# 6. COMPLETE WORKFLOW
# ==============================================================================
heading1('6. Complete End-to-End Workflow')
heading2('Step-by-Step: FIR Upload → Forensic Analysis → Court Verdict')

workflow = [
    ('DAY 1 — Police Station', [
        ('SHO Ramesh creates Case C-100 (FIR/2026/DL/001)', 'cases table. case_number = FIR/2026/DL/001'),
        ('SHO adds participants: IO Suresh, FSL Dr. Sharma, Prosecutor Mehta, Judge Verma', 'case_participants: 4 rows with appropriate access_levels'),
        ('IO Suresh DSC verified before upload', 'dsc_verifications: verification_result = VALID'),
        ('IO uploads FIR (sensitivity = HIGH)', 'documents (type=FIR, sensitivity_level=HIGH) + document_versions v1 (chain_hash, wrapped_dek, iv...)'),
        ('FIR locked automatically', 'document_versions.status = LOCKED. Trigger blocks any future modification.'),
        ('Notification fires to Dr. Sharma and Prosecutor Mehta', "notifications: FIR_UPLOADED, severity='WARNING' (because HIGH sensitivity)"),
    ]),
    ('DAY 3 — Forensic Science Laboratory', [
        ('Dr. Sharma logs in, sees FIR_UPLOADED notification', 'notifications WHERE recipient_id = Dr.Sharma, is_read=FALSE'),
        ('Dr. Sharma opens Case C-100 — access verified', 'case_participants confirms READ_WRITE access. document_access_logs records VIEW event.'),
        ('Dr. Sharma uploads Forensic Report (sensitivity = HIGH)', 'documents (type=FORENSIC_REPORT) + document_versions v1 with new chain_hash'),
        ('Notification fires to IO Suresh and Prosecutor Mehta', "notifications: FORENSIC_REPORT_UPLOADED"),
    ]),
    ('DAY 10 — Amendment Requested', [
        ('IO Suresh finds typo in FIR (accused name wrong)', '—'),
        ('IO raises edit request on FIR v1', 'edit_requests: source_version_id=FIR_v1, amendment_reason_code=CLERICAL, status=PENDING_QUORUM'),
        ('App looks up: documents.sensitivity_level = HIGH → quorum_policies WHERE sensitivity=HIGH', 'Returns: required=3, pool=5, eligible=[SR_POLICE, FSL_HEAD, MAGISTRATE]'),
        ('quorum_policy_id captured as snapshot in edit_requests', 'Even if policy changes later, this request stays at 3-of-5'),
        ('5 approval_assignments created. IO Suresh excluded (self-approval trigger blocks).', 'trg_no_self_approval fires. Each assignment gets anonymous_token UUID.'),
        ('3 officers vote APPROVED', 'approvals: 3 rows. COUNT(APPROVED) >= 3 = quorum reached.'),
        ('edit_requests.status → APPROVED', 'trg_reveal_identities fires: identity_revealed_at = NOW() on all 5 assignments'),
        ('New FIR v2 created with corrected name', 'document_versions v2: chain_hash built on v1 chain_hash + quorum_token'),
        ('document_diffs computed and stored', "diff_summary: '1 name corrected in Section 2 — Accused Details'"),
    ]),
    ('DAY 15 — Court', [
        ('Court Registrar registers case for trial', 'case_court_registrations: court_case_number=Sessions/2026/001'),
        ('Judge Verma opens Case C-100 dashboard', 'case_participants confirms READ access. All 2 documents visible.'),
        ('Judge clicks Compare FIR v1 vs v2', "document_diffs: instant response — '1 name corrected'. No decryption needed for summary."),
        ('Judge clicks Show Approvers', 'approval_assignments WHERE identity_revealed_at IS NOT NULL → real names, employee IDs, DSC signatures'),
        ('Judge requests Tamper-Proof Certificate', "chain_verifier runs SHA-256 chain walk. Court certificate generated with chain_status=INTACT"),
        ('document_access_logs records: Judge viewed FIR v2', 'chain_hash_at_access snapshot = proves doc was intact at time of judicial review'),
    ]),
]

for phase, steps in workflow:
    heading3(phase)
    step_rows = [(f'{i+1}.', action, db_effect) for i,(action,db_effect) in enumerate(steps)]
    make_table(['#','Action','Database Effect'], step_rows, col_widths=[0.2, 2.8, 4.0])

doc.add_page_break()

# ==============================================================================
# 7. INDEXES
# ==============================================================================
heading1('7. Indexes — 22 Total')
make_table(
    ['Index Name','Table','Columns','Why'],
    [
        ('idx_users_emp',         'users',                'employee_id',                   'Fast login lookup. UNIQUE.'),
        ('idx_users_role',        'users',                'role_id',                       'RBAC permission checks.'),
        ('idx_users_active',      'users',                'is_active WHERE TRUE',          'Filter active accounts only.'),
        ('idx_cases_num',         'cases',                'case_number',                   'Fast case lookup by FIR number. UNIQUE.'),
        ('idx_cases_status',      'cases',                'status',                        'Filter open/closed cases.'),
        ('idx_cp_participant',    'case_participants',    'participant_id WHERE active',    'Hot path: every API call checks this.'),
        ('idx_cp_case',           'case_participants',    'case_id WHERE active',          'List all participants of a case.'),
        ('idx_docs_case',         'documents',            'case_id',                       'List all documents in a case.'),
        ('idx_docs_sensitivity',  'documents',            'sensitivity_level',             'Quorum policy resolution on edit request.'),
        ('idx_docs_type',         'documents',            'document_type',                 'Filter FIR / Forensic Report etc.'),
        ('idx_dv_doc_ver',        'document_versions',    '(document_id, version_number)', 'Uniqueness + version history walk. UNIQUE.'),
        ('idx_dv_chain',          'document_versions',    'chain_hash',                    'Chain integrity walk. UNIQUE.'),
        ('idx_dv_key',            'document_versions',    'key_id',                        'Key rotation — find all versions using old KEK.'),
        ('idx_er_doc_status',     'edit_requests',        '(document_id, status)',          'Show pending requests for a document.'),
        ('idx_aa_req_status',     'approval_assignments', '(edit_request_id, status)',      'Count pending approvers for quorum check.'),
        ('idx_aa_approver',       'approval_assignments', 'approver_id',                   "Find all pending votes for an officer's dashboard."),
        ('idx_aa_revealed',       'approval_assignments', 'identity_revealed_at WHERE SET','Fast judiciary query for revealed identities.'),
        ('idx_audit_doc_time',    'audit_logs',           '(document_id, created_at DESC)','Chronological document audit history.'),
        ('idx_audit_case_time',   'audit_logs',           '(case_id, created_at DESC)',    'Case-level audit history.'),
        ('idx_audit_severity',    'audit_logs',           'severity WHERE HIGH/CRITICAL',  'Fast tamper alert dashboard.'),
        ('idx_notif_unread',      'notifications',        '(recipient_id, is_read=FALSE)', 'Unread notification bell count.'),
        ('idx_access_doc_time',   'document_access_logs', '(document_id, accessed_at DESC)','Who viewed this document and when.'),
    ],
    col_widths=[1.6, 1.5, 1.7, 2.2]
)

doc.add_page_break()

# ==============================================================================
# 8. HOW TO RUN
# ==============================================================================
heading1('8. How to Deploy This Schema')
heading2('Prerequisites')
bullet('PostgreSQL 14 or later')
bullet('psql client installed')
bullet('Database created: CREATE DATABASE securechain_db;')

heading2('Run the Migration')
code_block('psql -U postgres -d securechain_db -f securechain_v03_migration.sql')

heading2('Post-Migration Verification')
code_block('-- Confirm all 17 tables')
code_block("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;")
doc.add_paragraph()
code_block('-- Confirm 13 roles')
code_block("SELECT name, pillar FROM roles ORDER BY pillar, name;")
doc.add_paragraph()
code_block('-- Confirm 4 quorum policies')
code_block('SELECT sensitivity_level, required_approvals, pool_size FROM quorum_policies;')
doc.add_paragraph()
code_block('-- Confirm WORM rules exist')
code_block("SELECT rulename, tablename FROM pg_rules WHERE schemaname='public';")
doc.add_paragraph()
code_block('-- Confirm triggers exist')
code_block("SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_schema='public';")

heading2('Sensitivity Quick Test')
body('After seeding, verify the full approval engine chain with this query:')
code_block("SELECT qp.sensitivity_level, qp.required_approvals, qp.pool_size, qp.eligible_roles")
code_block("FROM   quorum_policies qp")
code_block("ORDER  BY qp.required_approvals;")
body('Expected output: LOW(1of1), MEDIUM(2of3), HIGH(3of5), CRITICAL(4of7)')

# footer
doc.add_paragraph()
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
run = p.add_run('SecureChain DMS  |  SIH26190  |  Database Schema v0.3  |  September 2026')
run.font.size = Pt(9)
run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)
run.font.name = 'Calibri'

# Save
out = r'C:\Users\Shreyash debnath\.gemini\antigravity\scratch\securechain-dms-security\SecureChain_DMS_Database_Schema_v0.3.docx'
doc.save(out)
print(f'Word document saved: {out}')
