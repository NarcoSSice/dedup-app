from qdrant_client import AsyncQdrantClient

from core.settings import settings


def create_client() -> AsyncQdrantClient:
    if settings.qdrant.URL == ":memory:":
        return AsyncQdrantClient(location=":memory:")
    return AsyncQdrantClient(url=settings.qdrant.URL, prefer_grpc=True)


qdrant_client = create_client()
