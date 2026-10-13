from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import FileResponse

from core.constants import IMAGES_ROUTE, IMMUTABLE_CACHE_HEADER
from db.repositories.container import RepositoryContainer, get_repositories
from schemas.image import UploadResponseSchema
from services.image import ImageService

router = APIRouter(prefix=IMAGES_ROUTE, tags=["Images"])


@router.post("", response_model=UploadResponseSchema)
async def upload_images(
    # format=binary makes Swagger UI render file pickers instead of text inputs
    files: list[UploadFile] = File(
        ..., json_schema_extra={"items": {"type": "string", "format": "binary"}}
    ),
    repos: RepositoryContainer = Depends(get_repositories),
    image_service: ImageService = Depends(),
):
    return await image_service.upload_images(repos, files)


@router.get(
    "/{image_id}",
    response_class=FileResponse,
    responses={200: {"content": {"image/jpeg": {}, "image/png": {}, "image/webp": {}}}},
)
async def get_image(
    image_id: str,
    thumb: bool = False,
    repos: RepositoryContainer = Depends(get_repositories),
    image_service: ImageService = Depends(),
):
    path, content_type = await image_service.get_image(repos, image_id, thumb)
    return FileResponse(
        path, media_type=content_type, headers={"Cache-Control": IMMUTABLE_CACHE_HEADER}
    )
