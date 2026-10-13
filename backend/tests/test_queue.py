import asyncio
from datetime import timedelta

from core.enums.image import ImageStatus
from db.repositories.image import ImageResult, image_repository
from models import ImageDocument
from models.base import utcnow


async def _enqueue(count: int) -> None:
    await image_repository.create_many(
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

    batches = await asyncio.gather(
        *(image_repository.claim_batch(10, 300) for _ in range(5))
    )

    claimed = [img.id for _, batch in batches for img in batch]
    assert len(claimed) == len(set(claimed)) == 30


async def test_expired_lease_returns_image_to_queue():
    await _enqueue(1)
    first_claim, _ = await image_repository.claim_batch(10, 300)

    # a live lease blocks other workers
    assert (await image_repository.claim_batch(10, 300))[1] == []

    # the first worker "crashed": its lease ran out
    await image_repository.collection.update_one(
        {"_id": "id-1"}, {"$set": {"claimed_at": utcnow() - timedelta(seconds=301)}}
    )
    second_claim, [image] = await image_repository.claim_batch(10, 300)
    assert image.id == "id-1"

    # the stale worker can no longer overwrite the result
    await image_repository.finish_batch(
        first_claim, [ImageResult("id-1", ImageStatus.failed, "stale")]
    )
    await image_repository.finish_batch(
        second_claim, [ImageResult("id-1", ImageStatus.done)]
    )
    assert (await image_repository.get_by_id("id-1")).status == ImageStatus.done
