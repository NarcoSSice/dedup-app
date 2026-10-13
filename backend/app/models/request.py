from models.base import BaseDocument
from schemas.image import RejectedFileSchema


class RequestDocument(BaseDocument):
    accepted: int
    rejected: list[RejectedFileSchema] = []
