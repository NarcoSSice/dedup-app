from fastapi import APIRouter

from schemas.index import HealthSchema

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthSchema)
async def health():
    return HealthSchema(status="ok")
