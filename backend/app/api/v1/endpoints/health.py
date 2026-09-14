from fastapi import APIRouter
from app.core.config import settings
from app.schemas.health import HealthResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Check backend service operational health status.",
)
def get_health() -> HealthResponse:
    """
    Returns operational health status of the SecureChain DMS Backend service.
    """
    return HealthResponse(
        status="ok",
        service=settings.PROJECT_NAME,
    )
