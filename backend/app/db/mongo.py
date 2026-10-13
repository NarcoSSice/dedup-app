from pymongo import ASCENDING, AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from core.enums.image import ImageStatus
from core.settings import settings

mongo_client: AsyncMongoClient = AsyncMongoClient(
    settings.data.MONGO_URL, tz_aware=True
)


def get_database() -> AsyncDatabase:
    return mongo_client[settings.data.MONGO_DB]


async def ensure_indexes() -> None:
    """Idempotent; called on api and worker startup."""
    images = get_database().images
    await images.create_index([("request_id", ASCENDING), ("position", ASCENDING)])
    await images.create_index("sha256")
    await images.create_index(
        [("status", ASCENDING), ("created_at", ASCENDING)],
        name="queue",
        partialFilterExpression={
            "status": {"$in": [ImageStatus.pending, ImageStatus.processing]}
        },
    )
