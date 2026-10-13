import asyncio
import os
import tempfile
from pathlib import Path

from core.settings import settings


class LocalStorage:
    """Image files on a disk shared by api and workers (one Docker volume).

    Content-addressed: the key is the sha256 of the bytes, so identical uploads
    are stored once and a file never changes after it is written (safe to cache
    forever). Files are spread over two levels of subdirectories so no directory
    holds millions of entries. Multi-host setup: swap this class for S3."""

    def __init__(self, root: str):
        self.root = Path(root)

    @staticmethod
    def original_key(sha256: str) -> str:
        return f"orig/{sha256[:2]}/{sha256[2:4]}/{sha256}"

    @staticmethod
    def thumbnail_key(sha256: str) -> str:
        return f"thumb/{sha256[:2]}/{sha256[2:4]}/{sha256}.webp"

    def path(self, key: str) -> Path:
        return self.root / key

    def exists(self, key: str) -> bool:
        return self.path(key).is_file()

    async def put(self, key: str, data: bytes) -> None:
        await asyncio.to_thread(self._write_atomic, self.path(key), data)

    async def get(self, key: str) -> bytes | None:
        path = self.path(key)
        try:
            return await asyncio.to_thread(path.read_bytes)
        except FileNotFoundError:
            return None

    @staticmethod
    def _write_atomic(path: Path, data: bytes) -> None:
        """Write to a temp file and rename: readers never see a half-written
        file, and concurrent writers of the same content cannot corrupt it."""
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
            os.replace(tmp, path)
        except BaseException:
            os.unlink(tmp)
            raise


storage = LocalStorage(settings.storage.DIR)
