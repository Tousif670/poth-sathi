from fastapi import APIRouter, Depends, Query, status

from app.core.auth import require_auth
from app.models.review import PaginatedReviewsResponse, ReviewCreateRequest, ReviewDoc
from app.models.user import UserContext
from app.services.review_service import ReviewService

router = APIRouter()


def get_review_service() -> ReviewService:
    return ReviewService()


@router.get("/hotels/{hotel_id}/reviews", response_model=PaginatedReviewsResponse)
async def list_hotel_reviews(
    hotel_id: str,
    limit: int = Query(default=10, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
    service: ReviewService = Depends(get_review_service),
) -> PaginatedReviewsResponse:
    """List reviews for a specific hotel."""
    return service.list_reviews(hotel_id=hotel_id, limit=limit, offset=offset)


@router.post(
    "/hotels/{hotel_id}/reviews",
    response_model=ReviewDoc,
    status_code=status.HTTP_201_CREATED,
)
async def create_hotel_review(
    hotel_id: str,
    payload: ReviewCreateRequest,
    user: UserContext = Depends(require_auth),
    service: ReviewService = Depends(get_review_service),
) -> ReviewDoc:
    """Submit a hotel review with automatic lexicon sentiment analysis."""
    return service.create_review(hotel_id=hotel_id, uid=user.uid, payload=payload)
