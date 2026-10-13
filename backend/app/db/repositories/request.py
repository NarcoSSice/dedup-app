from db.mongo import get_database
from db.repositories.base import BaseRepository
from models import RequestDocument


class RequestRepository(BaseRepository[RequestDocument]):
    collection_name = "requests"
    model = RequestDocument


request_repository = RequestRepository(get_database())
