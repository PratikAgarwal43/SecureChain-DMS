"""
routes/cases.py — Case creation and listing endpoints.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from database import db_cursor
from auth.rbac import get_current_user, require_roles, require_case_access

router = APIRouter(prefix="/cases", tags=["Cases"])

CASE_UPLOAD_ROLES = ("INVESTIGATING_OFFICER", "STATION_HOUSE_OFFICER",
                     "SENIOR_POLICE_OFFICER", "SYSTEM_ADMIN", "SUPER_ADMIN")


class CreateCaseRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    jurisdiction: Optional[str] = ""
    case_type: Optional[str] = "FIR"


@router.post("", status_code=status.HTTP_201_CREATED)
def create_case(
    body: CreateCaseRequest,
    current_user: dict = Depends(require_roles(*CASE_UPLOAD_ROLES))
):
    case_id = str(uuid.uuid4())
    try:
        with db_cursor() as cur:
            # Generate a simple case number like FIR-2026-XXX
            case_number = f"FIR-2026-{str(uuid.uuid4())[:8].upper()}"
            cur.execute("""
                INSERT INTO cases (id, case_number, title, jurisdiction, case_type, created_by, status)
                VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
            """, (case_id, case_number, body.title, body.jurisdiction, body.case_type, current_user["sub"]))

            # Auto-add the creator as a participant
            cur.execute("""
                INSERT INTO case_participants (case_id, participant_id, access_level, added_by)
                VALUES (%s, %s, 'READ_WRITE', %s)
            """, (case_id, current_user["sub"], current_user["sub"]))
    except Exception as e:
        print("DB ERROR IN create_case:", e)
        import traceback; traceback.print_exc()
        raise e

    return {"case_id": case_id, "title": body.title, "status": "ACTIVE"}


@router.get("")
def list_cases(current_user: dict = Depends(get_current_user)):
    """Return all cases the current user is a participant in."""
    with db_cursor() as cur:
        cur.execute("""
            SELECT c.id, c.title, c.status, c.jurisdiction, c.case_type, c.created_at
            FROM cases c
            JOIN case_participants cp ON cp.case_id = c.id
            WHERE cp.participant_id = %s AND cp.removed_at IS NULL
            ORDER BY c.created_at DESC
        """, (current_user["sub"],))
        cases = cur.fetchall()
    return {"cases": [dict(r) for r in cases]}


@router.get("/{case_id}")
def get_case(case_id: str, current_user: dict = Depends(get_current_user)):
    require_case_access(case_id, current_user)
    with db_cursor() as cur:
        cur.execute("SELECT * FROM cases WHERE id = %s", (case_id,))
        case = cur.fetchone()
        cur.execute("""
            SELECT u.name, u.employee_id, r.name AS role, cp.access_level, cp.added_at
            FROM case_participants cp
            JOIN users u ON u.id = cp.participant_id
            JOIN roles r ON r.id = u.role_id
            WHERE cp.case_id = %s AND cp.removed_at IS NULL
        """, (case_id,))
        participants = cur.fetchall()
    return {"case": dict(case), "participants": [dict(p) for p in participants]}


@router.post("/{case_id}/participants")
def add_participant(
    case_id: str,
    body: dict,
    current_user: dict = Depends(require_roles("STATION_HOUSE_OFFICER", "SENIOR_POLICE_OFFICER", "SYSTEM_ADMIN", "SUPER_ADMIN"))
):
    require_case_access(case_id, current_user)
    with db_cursor() as cur:
        cur.execute("""
            INSERT INTO case_participants (case_id, participant_id, access_level, added_by)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (case_id, participant_id) DO NOTHING
        """, (case_id, body["participant_id"], body.get("access_level", "READ"), current_user["sub"]))
    return {"message": "Participant added successfully"}
