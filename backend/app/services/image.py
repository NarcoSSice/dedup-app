import asyncio
import hashlib
import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from core.constants import THUMBNAIL_CONTENT_TYPE
from core.exceptions.image import (
    ImageNotFoundException,
    InvalidImageError,
    TooManyFilesException,
)
from core.settings import settings
from db.repositories.container import RepositoryContainer
from models import ImageDocument, RequestDocument
from models.base import utcnow
from schemas.image import RejectedFileSchema, UploadResponseSchema
from utils.image_utils import parse_public_id, validate_image
from utils.storage import storage


@dataclass
class _AcceptedFile:
    filename: str
    sha256: str
    content_type: str


class ImageService:
    @staticmethod
    async def _store_file(file: UploadFile) -> _AcceptedFile:
        """Validate and store one file right away, so a request holds at most
        one file in memory instead of all of them."""
        # read at most limit+1 bytes: enough to tell "too large" without loading it all
        data = await file.read(settings.api.MAX_FILE_BYTES + 1)
        content_type = await asyncio.to_thread(
            validate_image, data, settings.api.MAX_FILE_BYTES
        )
        sha256 = hashlib.sha256(data).hexdigest()
        # content-addressed: put skips bytes stored by an earlier upload
        await storage.put(storage.original_key(sha256), data)
        return _AcceptedFile(
            filename=(file.filename or "unnamed")[:255],
            sha256=sha256,
            content_type=content_type,
        )

    async def upload_images(
        self, repos: RepositoryContainer, files: list[UploadFile]
    ) -> UploadResponseSchema:
        if len(files) > settings.api.MAX_FILES_PER_REQUEST:
            raise TooManyFilesException(settings.api.MAX_FILES_PER_REQUEST)

        accepted: list[_AcceptedFile] = []
        rejected: list[RejectedFileSchema] = []
        for file in files:
            try:
                accepted.append(await self._store_file(file))
            except InvalidImageError as e:
                rejected.append(
                    RejectedFileSchema(
                        filename=file.filename or "unnamed", reason=e.reason
                    )
                )

        request_id = str(uuid.uuid4())
        # one timestamp for the request and all its images: orders uploads in time
        uploaded_at = utcnow()
        # images first, request last: GET /duplicates only sees complete requests
        await repos.images.create_many(
            [
                ImageDocument(
                    id=str(uuid.uuid4()),
                    request_id=request_id,
                    position=position,
                    created_at=uploaded_at,
                    filename=f.filename,
                    sha256=f.sha256,
                    content_type=f.content_type,
                )
                for position, f in enumerate(accepted)
            ]
        )
        await repos.requests.create(
            RequestDocument(
                id=request_id,
                accepted=len(accepted),
                rejected=[r.model_dump(mode="json") for r in rejected],
                created_at=uploaded_at,
            )
        )

        return UploadResponseSchema(
            request_id=request_id, accepted=len(accepted), rejected=rejected
        )

    async def get_image(
        self, repos: RepositoryContainer, image_id: str, thumbnail: bool
    ) -> tuple[Path, str]:
        """-> (file path, content type)"""
        internal_id = parse_public_id(image_id)
        if internal_id is None:
            raise ImageNotFoundException
        image = await repos.images.get_by_id(internal_id)
        if image is None:
            raise ImageNotFoundException

        # thumbnail exists once a worker processed the image; fall back to original
        thumbnail_key = storage.thumbnail_key(image.sha256)
        if thumbnail and await storage.exists(thumbnail_key):
            return storage.path(thumbnail_key), THUMBNAIL_CONTENT_TYPE
        original_key = storage.original_key(image.sha256)
        if not await storage.exists(original_key):
            raise ImageNotFoundException
        return storage.path(original_key), image.content_type
