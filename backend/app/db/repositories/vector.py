from qdrant_client import AsyncQdrantClient, models

from core.settings import settings
from db.qdrant import qdrant_client


class VectorRepository:
    """One Qdrant point per image; point id = image UUID (same as in Mongo)."""

    def __init__(self, client: AsyncQdrantClient, collection: str):
        self.client = client
        self.collection = collection

    async def ensure_collection(self, dim: int) -> None:
        """Called by workers only, so the API never loads the model to learn dim."""
        if await self.client.collection_exists(self.collection):
            return
        try:
            await self._create_collection(dim)
        except Exception:
            # several workers start at once; losing the race is fine
            if not await self.client.collection_exists(self.collection):
                raise

    async def _create_collection(self, dim: int) -> None:
        await self.client.create_collection(
            self.collection,
            # full-precision vectors stay on disk, used only to rescore top candidates
            vectors_config=models.VectorParams(
                size=dim, distance=models.Distance.COSINE, on_disk=True
            ),
            # int8 copy in RAM for HNSW search: 4x less memory (10M x 512d: 20GB -> 5GB)
            quantization_config=models.ScalarQuantization(
                scalar=models.ScalarQuantizationConfig(
                    type=models.ScalarType.INT8, quantile=0.99, always_ram=True
                ),
            ),
        )
        # upload time, lets a search ignore images added after the request
        await self.client.create_payload_index(
            self.collection, "uploaded_at", models.PayloadSchemaType.FLOAT
        )

    async def upsert(
        self, ids: list[str], vectors: list[list[float]], payloads: list[dict]
    ) -> None:
        await self.client.upsert(
            self.collection,
            points=models.Batch(ids=ids, vectors=vectors, payloads=payloads),
        )

    async def get_vectors(self, ids: list[str]) -> dict[str, list[float]]:
        if not ids:
            return {}
        points = await self.client.retrieve(
            self.collection, ids=ids, with_vectors=True, with_payload=False
        )
        return {p.id: p.vector for p in points}

    async def search_many(
        self,
        vectors: list[list[float]],
        threshold: float,
        uploaded_before: float,
        limit: int,
    ) -> list[list[models.ScoredPoint]]:
        """Nearest neighbours for all vectors in a single round-trip."""
        time_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="uploaded_at", range=models.Range(lte=uploaded_before)
                )
            ]
        )
        requests = [
            models.QueryRequest(
                query=vector,
                filter=time_filter,
                score_threshold=threshold,
                limit=limit + 1,  # +1 for the image itself
                with_payload=True,
                params=models.SearchParams(
                    quantization=models.QuantizationSearchParams(rescore=True)
                ),
            )
            for vector in vectors
        ]
        responses = await self.client.query_batch_points(
            self.collection, requests=requests
        )
        return [r.points for r in responses]


vector_repository = VectorRepository(qdrant_client, settings.qdrant.COLLECTION)
