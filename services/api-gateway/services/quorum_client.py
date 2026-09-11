"""
services/quorum_client.py — HTTP client for calling the Quorum Approval Engine (Port 3000).
"""
import httpx
import logging
from typing import List
from database import db_cursor
from config import settings

logger = logging.getLogger(__name__)


def _get_quorum_pool(case_id: str, sensitivity: str) -> List[str]:
    """
    Fetch the list of eligible approver user IDs for a given case and sensitivity.
    Looks up quorum_policies, then finds users with the eligible roles in the same jurisdiction.
    """
    with db_cursor() as cur:
        # Get policy M and N for the sensitivity level
        cur.execute("""
            SELECT required_approvals, pool_size, eligible_roles
            FROM quorum_policies
            WHERE sensitivity_level = %s
            ORDER BY created_at DESC LIMIT 1
        """, (sensitivity,))
        policy = cur.fetchone()

        if not policy:
            return []

        eligible_roles = policy["eligible_roles"]  # e.g. ["SHO", "SENIOR_POLICE_OFFICER"]

        # Find users with those roles who are participants in this case
        cur.execute("""
            SELECT u.id FROM users u
            JOIN case_participants cp ON cp.participant_id = u.id
            JOIN roles r ON r.id = u.role_id
            WHERE cp.case_id = %s
              AND r.name = ANY(%s)
              AND cp.removed_at IS NULL
              AND u.is_active = TRUE
            LIMIT %s
        """, (case_id, eligible_roles, policy["pool_size"]))

        rows = cur.fetchall()
        return [str(row["id"]) for row in rows]


async def create_approval_request(
    document_id: str,
    case_id: str,
    requester_id: str,
    sensitivity: str,
    proposed_content: str = ""
) -> dict:
    """
    Create a quorum approval request in the Quorum Engine (Node.js).
    Returns the created request data.
    """
    pool_ids = _get_quorum_pool(case_id, sensitivity)
    if not pool_ids:
        logger.warning(f"No eligible approvers found for case {case_id}, sensitivity {sensitivity}. Skipping quorum.")
        return {"skipped": True, "reason": "No eligible approvers found"}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.quorum_service_url}/api/approval/request",
                json={
                    "documentId": document_id,
                    "requesterId": requester_id,
                    "proposedContent": proposed_content or f"Document upload approved: {document_id}",
                    "sensitivityTier": sensitivity,
                    "poolMemberIds": pool_ids,
                }
            )
            response.raise_for_status()
            return response.json()

    except httpx.ConnectError:
        logger.warning("Quorum Engine is offline. Approval request not created.")
        return {"skipped": True, "reason": "Quorum Engine offline"}
    except Exception as e:
        logger.error(f"Quorum request failed: {e}")
        raise
