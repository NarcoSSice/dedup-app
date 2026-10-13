from fastapi import APIRouter, Depends, Query

from core.constants import DUPLICATES_ROUTE
from core.settings import settings
from db.repositories.container import RepositoryContainer, get_repositories
from schemas.duplicate import DuplicatesResponseSchema
from services.duplicate import DuplicateService

router = APIRouter(prefix=DUPLICATES_ROUTE, tags=["Duplicates"])


@router.get("/{request_id}", response_model=DuplicatesResponseSchema)
async def get_duplicates(
    request_id: str,
    threshold: float = Query(settings.duplicates.THRESHOLD, ge=0.0, le=1.0),
    repos: RepositoryContainer = Depends(get_repositories),
    duplicate_service: DuplicateService = Depends(),
):
    return await duplicate_service.get_duplicates(repos, request_id, threshold)
