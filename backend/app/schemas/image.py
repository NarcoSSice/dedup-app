from pydantic import BaseModel

from core.enums.image import RejectReason


class RejectedFileSchema(BaseModel):
    filename: str
    reason: RejectReason


class UploadResponseSchema(BaseModel):
    request_id: str
    accepted: int
    rejected: list[RejectedFileSchema]
