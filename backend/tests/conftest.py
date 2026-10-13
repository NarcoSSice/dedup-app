import os
import shutil
import tempfile
from pathlib import Path

STORAGE_DIR = tempfile.mkdtemp(prefix="dedup-test-")

# must be set before app modules read settings
os.environ.update(
    MONGO_DB="dedup_test",
    QDRANT_URL=":memory:",
    STORAGE_DIR=STORAGE_DIR,
    MODEL_PATH=str(
        Path(__file__).parents[1] / "dedup_model" / "sscd_disc_mixup.torchscript.pt"
    ),
)

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from core.constants import QDRANT_COLLECTION
from core.settings import settings
from db.mongo import ensure_indexes, get_database, mongo_client
from db.qdrant import qdrant_client
from db.repositories.container import get_repositories
from db.repositories.vector import vector_repository
from main import app
from ml.embedder import embedder
from services.embedding import EmbeddingService


@pytest.fixture(scope="session", autouse=True)
def storage_dir():
    yield
    shutil.rmtree(STORAGE_DIR, ignore_errors=True)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def mongo():
    try:
        await get_database().command("ping")
    except Exception:
        pytest.exit(
            f"MongoDB is not reachable at {settings.data.MONGO_URL}. "
            "Start it with: docker compose up -d mongo"
        )


@pytest_asyncio.fixture(autouse=True)
async def clean_state(mongo):
    """Every test starts with empty files, database and vector collection."""
    shutil.rmtree(STORAGE_DIR, ignore_errors=True)
    await mongo_client.drop_database(settings.data.MONGO_DB)
    await ensure_indexes()
    if await qdrant_client.collection_exists(QDRANT_COLLECTION):
        await qdrant_client.delete_collection(QDRANT_COLLECTION)
    await vector_repository.ensure_collection(embedder.dim)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(scope="session")
def embedding_service():
    return EmbeddingService()


@pytest.fixture
def process_queue(embedding_service):
    """Run the worker synchronously until the queue is empty."""

    async def _process():
        while await embedding_service.process_batch(get_repositories()):
            pass

    return _process
