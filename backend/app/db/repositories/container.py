from pymongo.asynchronous.database import AsyncDatabase

from db.mongo import get_database
from db.repositories.image import ImageRepository
from db.repositories.request import RequestRepository


class RepositoryContainer:
    """All Mongo repositories over one database, injected into services.

    Not a unit of work: Mongo transactions need a replica set, so instead the
    services order their writes so that a partial failure leaves nothing broken."""

    def __init__(self, db: AsyncDatabase):
        self.requests = RequestRepository(db)
        self.images = ImageRepository(db)


def get_repositories() -> RepositoryContainer:
    return RepositoryContainer(get_database())
