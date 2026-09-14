from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.quorum_client import quorum_client

router = APIRouter()

@router.get("/")
async def get_all_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch all WORM audit logs from the Quorum Approval Engine."""
    return await quorum_client.get_audit_logs()
