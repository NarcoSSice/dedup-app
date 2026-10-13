from qdrant_client.models import ScoredPoint

from core.constants import NO_DUPLICATES_MESSAGE
from core.enums.image import ImageStatus, RequestStatus
from core.exceptions.request import RequestNotFoundException
from core.settings import settings
from db.repositories.container import RepositoryContainer
from db.repositories.vector import vector_repository
from models import ImageDocument
from schemas.duplicate import (
    DuplicateGroupSchema,
    DuplicateSchema,
    DuplicatesResponseSchema,
    FailedImageSchema,
)
from utils.image_utils import to_public_id

UNFINISHED = (ImageStatus.pending, ImageStatus.processing)


class DuplicateService:
    @staticmethod
    def _build_groups(
        images: list[ImageDocument], hits: list[list[ScoredPoint]]
    ) -> list[DuplicateGroupSchema]:
        """One group per request image that has matches. If two images of the
        same request match each other, the pair is reported once, under the
        first of them."""
        request_ids = {img.id for img in images}
        already_shown: set[int] = set()
        groups = []
        for image, points in zip(images, hits, strict=True):
            if image.id in already_shown:
                continue
            matches = [p for p in points if p.id != image.id]
            matches = matches[: settings.duplicates.MAX_PER_IMAGE]
            if not matches:
                continue
            groups.append(
                DuplicateGroupSchema(
                    image_id=to_public_id(image.id),
                    filename=image.filename,
                    duplicates=[
                        DuplicateSchema(
                            image_id=to_public_id(p.id),
                            filename=p.payload["filename"],
                            score=round(min(p.score, 1.0), 3),
                            source_request_id=p.payload["request_id"],
                        )
                        for p in matches
                    ],
                )
            )
            already_shown |= {p.id for p in matches if p.id in request_ids}
        return groups

    async def get_duplicates(
        self, repos: RepositoryContainer, request_id: str, threshold: float
    ) -> DuplicatesResponseSchema:
        request = await repos.requests.get_by_id(request_id)
        if request is None:
            raise RequestNotFoundException
        images = await repos.images.get_request_images(request_id)

        response = DuplicatesResponseSchema(
            request_id=request_id,
            status=RequestStatus.done,
            failed=[
                FailedImageSchema(filename=img.filename, reason=img.error)
                for img in images
                if img.status == ImageStatus.failed
            ],
        )
        if any(img.status in UNFINISHED for img in images):
            response.status = RequestStatus.processing
            return response

        done = [img for img in images if img.status == ImageStatus.done]
        if done:
            # searched at read time, so ?threshold needs no reprocessing
            vectors = await vector_repository.get_vectors([img.id for img in done])
            done = [img for img in done if img.id in vectors]
            hits = await vector_repository.search_many(
                [vectors[img.id] for img in done],
                threshold=threshold,
                # ignore images uploaded after this request
                uploaded_before=request.created_at.timestamp(),
                limit=settings.duplicates.MAX_PER_IMAGE,
            )
            response.groups = self._build_groups(done, hits)

        if not response.groups:
            response.message = NO_DUPLICATES_MESSAGE
        return response
