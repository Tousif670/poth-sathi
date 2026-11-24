from fastapi import APIRouter, Depends, status

from app.core.auth import get_optional_user
from app.models.admin import ReportCreateRequest, ReportSubmissionResponse
from app.models.user import UserContext
from app.services.admin_service import AdminService

router = APIRouter()


def get_admin_service() -> AdminService:
    return AdminService()


@router.post(
    "/reports",
    response_model=ReportSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def submit_data_report(
    payload: ReportCreateRequest,
    user: UserContext | None = Depends(get_optional_user),
    service: AdminService = Depends(get_admin_service),
) -> ReportSubmissionResponse:
    """Report inaccurate or outdated reference data for administrative review (P1)."""
    uid = user.uid if user is not None else None
    return service.submit_report(payload=payload, uid=uid)
