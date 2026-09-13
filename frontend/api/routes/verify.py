"""
routes/verify.py — Chain integrity verification and audit log endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from database import db_cursor
from auth.rbac import get_current_user, require_case_access
import sys, os
_SECURITY_PATH = r"C:\Users\Shreyash debnath\.gemini\antigravity\scratch\SecureChain-DMS\services\security-and-database"
sys.path.insert(0, _SECURITY_PATH)
from securechain_security.chain_verifier import ChainVerifier
from securechain_security.chain_engine import ChainEngine
from securechain_security.hash_service import HashService

router = APIRouter(tags=["Verification & Audit"])
_hs = HashService()
_ce = ChainEngine(hash_service=_hs)
verifier = ChainVerifier(chain_engine=_ce, hash_service=_hs)


@router.get("/verify/{document_id}")
def verify_document_chain(document_id: str, current_user: dict = Depends(get_current_user)):
    """Walks the full SHA-256 hash chain for a document and returns an integrity certificate."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT version_number, doc_hash, chain_hash, prev_chain_hash,
                   quorum_token, created_by, created_at
            FROM document_versions
            WHERE document_id = %s
            ORDER BY version_number ASC
        """, (document_id,))
        versions = cur.fetchall()

    if not versions:
        raise HTTPException(status_code=404, detail="Document not found")

    chain_records = [dict(v) for v in versions]
    is_intact, report = verifier.verify_chain(chain_records)

    return {
        "document_id": document_id,
        "chain_intact": is_intact,
        "versions_checked": len(chain_records),
        "report": report,
        "verdict": "AUTHENTIC - Chain of custody is intact." if is_intact
                   else "TAMPERED - Chain integrity violation detected. Alert raised."
    }


@router.get("/audit-logs")
def get_audit_logs(
    case_id: str = None,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """Return immutable WORM audit logs. Accessible by Judges and Auditors."""
    allowed = ("JUDGE", "MAGISTRATE", "AUDITOR", "SYSTEM_ADMIN", "SUPER_ADMIN", "PUBLIC_PROSECUTOR")
    if current_user["role"] not in allowed:
        raise HTTPException(status_code=403, detail="Access denied to audit logs")

    with db_cursor() as cur:
        if case_id:
            cur.execute("""
                SELECT al.* FROM audit_logs al
                WHERE al.case_id = %s
                ORDER BY al.created_at DESC LIMIT %s
            """, (case_id, limit))
        else:
            cur.execute("""
                SELECT * FROM audit_logs
                ORDER BY created_at DESC LIMIT %s
            """, (limit,))
        logs = cur.fetchall()

    return {"audit_logs": [dict(l) for l in logs], "count": len(logs)}
