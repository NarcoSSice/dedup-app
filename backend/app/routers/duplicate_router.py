from fastapi import APIRouter, Depends, Query

from core.settings import settings
from schemas.duplicate import DuplicatesResponseSchema
from services.duplicate import DuplicateService

router = APIRouter(prefix="/duplicates", tags=["Duplicates"])


@router.get("/{request_id}", response_model=DuplicatesResponseSchema)
async def get_duplicates(
    request_id: str,
    threshold: float = Query(settings.api.DUPLICATE_THRESHOLD, ge=0.0, le=1.0),
    duplicate_service: DuplicateService = Depends(),
):
    return await duplicate_service.get_duplicates(request_id, threshold)
