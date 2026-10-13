from pydantic import Field

from models.base import BaseDocument, TimestampMixin


class RequestDocument(BaseDocument, TimestampMixin):
    id: str = Field(alias="_id")
    accepted: int
    rejected: list[dict] = []
