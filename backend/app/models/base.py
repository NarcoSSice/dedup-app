from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field


def utcnow() -> datetime:
    return datetime.now(UTC)


class BaseDocument(BaseModel):
    """A MongoDB document. `id` is stored as `_id`."""

    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=utcnow)

    def to_mongo(self) -> dict:
        return self.model_dump(by_alias=True, exclude_none=True)
