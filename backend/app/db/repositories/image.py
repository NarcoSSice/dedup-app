import uuid
from datetime import timedelta

from pymongo import UpdateOne

from core.enums.image import ImageStatus
from db.repositories.base import BaseRepository
from models import ImageDocument
from models.base import utcnow


class ImageRepository(BaseRepository[ImageDocument]):
    collection_name = "images"
    model = ImageDocument

    async def get_request_images(self, request_id: str) -> list[ImageDocument]:
        return await self.find({"request_id": request_id}, sort="position")

    async def get_done_ids_by_hash(self, hashes: set[str]) -> dict[str, str]:
        """sha256 -> id of an already embedded image with the same bytes."""
        if not hashes:
            return {}
        cursor = await self.collection.aggregate(
            [
                {
                    "$match": {
                        "sha256": {"$in": list(hashes)},
                        "status": ImageStatus.done,
                    }
                },
                {"$group": {"_id": "$sha256", "image_id": {"$first": "$_id"}}},
            ]
        )
        return {doc["_id"]: doc["image_id"] async for doc in cursor}

    async def claim_batch(
        self, limit: int, lease_seconds: int
    ) -> tuple[str, list[ImageDocument]]:
        """Atomically take up to `limit` queued images for one worker.

        Each image is flipped to `processing` by a conditional update, so even if
        several workers pick the same candidates, every image ends up with exactly
        one of them. A batch not finished within the lease (worker crashed) becomes
        claimable again."""
        now = utcnow()
        claimable = {
            "$or": [
                {"status": ImageStatus.pending},
                {
                    "status": ImageStatus.processing,
                    "claimed_at": {"$lt": now - timedelta(seconds=lease_seconds)},
                },
            ]
        }
        candidates = (
            await self.collection.find(claimable, {"_id": 1})
            .sort("created_at")  # FIFO
            .limit(limit)
            .to_list()
        )
        if not candidates:
            return "", []

        claim = uuid.uuid4().hex
        await self.collection.update_many(
            {"_id": {"$in": [doc["_id"] for doc in candidates]}, **claimable},
            {
                "$set": {
                    "status": ImageStatus.processing,
                    "claim": claim,
                    "claimed_at": now,
                }
            },
        )
        return claim, await self.find({"claim": claim})

    async def finish_batch(self, claim: str, results: list[dict]) -> None:
        """results: [{"id", "status", "error"}]. Matching on the claim token means a
        worker whose lease expired cannot overwrite the new owner's result."""
        await self.collection.bulk_write(
            [
                UpdateOne(
                    {"_id": r["id"], "claim": claim},
                    {
                        "$set": {"status": r["status"], "error": r["error"]},
                        "$unset": {"claim": "", "claimed_at": ""},
                    },
                )
                for r in results
            ],
            ordered=False,
        )
