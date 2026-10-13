from datetime import datetime

from core.enums.image import ImageStatus
from models.base import BaseDocument


class ImageDocument(BaseDocument):
    """One uploaded image, and at the same time a job in the worker queue.
    id is a UUID shared with the Qdrant point; created_at equals the request's
    created_at, which orders uploads in time."""

    request_id: str
    position: int
    filename: str
    sha256: str
    content_type: str
    status: ImageStatus = ImageStatus.pending
    error: str | None = None
    # set while a worker holds the image (see ImageRepository.claim_batch)
    claim: str | None = None
    claimed_at: datetime | None = None
