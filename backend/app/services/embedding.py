import asyncio

from PIL import Image

from core.constants import MODEL_INPUT_SIZE, THUMB_SIZE
from core.enums.image import ImageStatus
from core.logger import logger
from core.settings import settings
from db.mongo import ensure_indexes
from db.repositories.image import ImageResult, image_repository
from db.repositories.vector import vector_repository
from ml.embedder import embedder
from utils.image_utils import decode_image, make_thumbnail
from utils.storage import storage


class EmbeddingService:
    """Turns queued images into vectors. Run by workers, never by the API."""

    async def setup(self) -> None:
        await ensure_indexes()
        # also loads the model before the first batch
        await vector_repository.ensure_collection(embedder.dim)

    async def _load(self, sha256: str) -> Image.Image:
        """Fetch original, decode at model resolution, store the thumbnail."""
        data = await storage.get(storage.original_key(sha256))
        if data is None:
            raise ValueError("original_missing")
        min_side = max(MODEL_INPUT_SIZE, THUMB_SIZE)
        img = await asyncio.to_thread(decode_image, data, min_side)
        thumbnail = await asyncio.to_thread(make_thumbnail, img, THUMB_SIZE)
        await storage.put(storage.thumbnail_key(sha256), thumbnail)
        return img

    async def _embed_new(
        self, hashes: list[str]
    ) -> tuple[dict[str, list[float]], dict[str, str]]:
        """-> (vectors by sha256, errors by sha256).
        One bad file never fails the batch."""
        results = await asyncio.gather(
            *(self._load(sha) for sha in hashes), return_exceptions=True
        )
        errors, loaded = {}, []
        for sha, result in zip(hashes, results, strict=True):
            if isinstance(result, Exception):
                logger.warning("decode failed for %s: %s", sha, result)
                errors[sha] = (str(result) or type(result).__name__)[:255]
            else:
                loaded.append((sha, result))
        if not loaded:
            return {}, errors

        vectors = await asyncio.to_thread(embedder.embed, [img for _, img in loaded])
        embedded = {
            sha: v.tolist() for (sha, _), v in zip(loaded, vectors, strict=True)
        }
        return embedded, errors

    async def process_batch(self) -> int:
        """Embed one batch of queued images. Returns how many were claimed."""
        claim, images = await image_repository.claim_batch(
            settings.worker.WORKER_BATCH_SIZE, settings.worker.WORKER_LEASE_SECONDS
        )
        if not images:
            return 0

        # exact byte copies reuse the stored vector instead of running the model
        hashes = {img.sha256 for img in images}
        known_ids = await image_repository.get_done_ids_by_hash(hashes)
        stored = await vector_repository.get_vectors(list(known_ids.values()))
        vectors = {sha: stored[pk] for sha, pk in known_ids.items() if pk in stored}

        new_vectors, errors = await self._embed_new(sorted(hashes - vectors.keys()))
        vectors |= new_vectors

        embedded = [img for img in images if img.sha256 in vectors]
        if embedded:
            await vector_repository.upsert(
                ids=[img.id for img in embedded],
                vectors=[vectors[img.sha256] for img in embedded],
                payloads=[
                    {
                        "request_id": img.request_id,
                        "filename": img.filename,
                    }
                    for img in embedded
                ],
            )
        await image_repository.finish_batch(
            claim,
            [
                ImageResult(
                    img.id,
                    ImageStatus.done if img.sha256 in vectors else ImageStatus.failed,
                    errors.get(img.sha256),
                )
                for img in images
            ],
        )
        logger.info(
            "batch: %d images, %d through the model, %d failed",
            len(images),
            len(new_vectors),
            len(images) - len(embedded),
        )
        return len(images)
