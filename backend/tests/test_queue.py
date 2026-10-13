import asyncio
from datetime import timedelta

from core.enums.image import ImageStatus
from db.repositories.container import get_repositories
from models import ImageDocument
from models.base import utcnow


async def _enqueue(count: int) -> None:
    await get_repositories().images.create_many(
        [
            ImageDocument(
                id=f"id-{i}",
                request_id="r",
                position=i,
                filename=f"{i}.png",
                sha256=str(i),
                content_type="image/png",
            )
            for i in range(1, count + 1)
        ]
    )


async def test_concurrent_workers_never_share_an_image():
    await _enqueue(30)
    images = get_repositories().images

    batches = await asyncio.gather(*(images.claim_batch(10, 300) for _ in range(5)))

    claimed = [img.id for _, batch in batches for img in batch]
    assert len(claimed) == len(set(claimed)) == 30


async def test_expired_lease_returns_image_to_queue():
    await _enqueue(1)
    images = get_repositories().images
    first_claim, _ = await images.claim_batch(10, 300)

    # a live lease blocks other workers
    assert (await images.claim_batch(10, 300))[1] == []

    # the first worker "crashed": its lease ran out
    await images.collection.update_one(
        {"_id": "id-1"}, {"$set": {"claimed_at": utcnow() - timedelta(seconds=301)}}
    )
    second_claim, [image] = await images.claim_batch(10, 300)
    assert image.id == "id-1"

    # the stale worker can no longer overwrite the result
    await images.finish_batch(
        first_claim, [{"id": "id-1", "status": ImageStatus.failed, "error": "stale"}]
    )
    await images.finish_batch(
        second_claim, [{"id": "id-1", "status": ImageStatus.done, "error": None}]
    )
    assert (await images.get_by_id("id-1")).status == ImageStatus.done
