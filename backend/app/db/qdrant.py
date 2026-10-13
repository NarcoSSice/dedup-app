from qdrant_client import AsyncQdrantClient

from core.settings import settings


def create_client() -> AsyncQdrantClient:
    if settings.data.QDRANT_URL == ":memory:":
        return AsyncQdrantClient(location=":memory:")
    return AsyncQdrantClient(url=settings.data.QDRANT_URL, prefer_grpc=True)


qdrant_client = create_client()
