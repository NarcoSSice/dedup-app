from pydantic import BaseModel

from core.enums.image import RequestStatus
from schemas.image import RejectedFileSchema


class DuplicateSchema(BaseModel):
    image_id: str
    filename: str
    score: float
    source_request_id: str


class DuplicateGroupSchema(BaseModel):
    image_id: str
    filename: str
    duplicates: list[DuplicateSchema]


class FailedImageSchema(BaseModel):
    """Accepted at upload, but the worker could not decode it."""

    filename: str
    reason: str | None


class DuplicatesResponseSchema(BaseModel):
    request_id: str
    status: RequestStatus
    # upload outcome, so a request opened later by id shows the same summary
    accepted: int
    rejected: list[RejectedFileSchema] = []
    groups: list[DuplicateGroupSchema] = []
    failed: list[FailedImageSchema] = []
    message: str | None = None
