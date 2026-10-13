from db.repositories.base import BaseRepository
from models import RequestDocument


class RequestRepository(BaseRepository[RequestDocument]):
    collection_name = "requests"
    model = RequestDocument
