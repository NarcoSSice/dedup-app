"""Embedding worker. Scale horizontally: docker compose up --scale worker=N"""

import asyncio

from core.logger import logger
from core.settings import settings
from db.repositories.container import get_repositories
from services.embedding import EmbeddingService


async def run() -> None:
    service = EmbeddingService()
    await service.setup()
    logger.info("worker ready")
    while True:
        try:
            processed = await service.process_batch(get_repositories())
        except Exception:
            logger.exception("batch failed, images return to the queue after the lease")
            processed = 0
            await asyncio.sleep(2)
        if not processed:
            # polling; Mongo change streams (replica set) could replace it
            await asyncio.sleep(settings.worker.IDLE_SLEEP)


if __name__ == "__main__":
    asyncio.run(run())
