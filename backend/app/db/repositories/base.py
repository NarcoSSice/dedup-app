from typing import Any, Generic, TypeVar

from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase

from models import BaseDocument

DocumentType = TypeVar("DocumentType", bound=BaseDocument)


class BaseRepository(Generic[DocumentType]):
    collection_name: str
    model: type[DocumentType]

    def __init__(self, db: AsyncDatabase):
        self.collection: AsyncCollection = db[self.collection_name]

    async def get_by_id(self, obj_id: Any) -> DocumentType | None:
        doc = await self.collection.find_one({"_id": obj_id})
        return self.model.model_validate(doc) if doc else None

    async def find(self, query: dict, sort: str = "_id") -> list[DocumentType]:
        cursor = self.collection.find(query).sort(sort)
        return [self.model.model_validate(doc) async for doc in cursor]

    async def create(self, obj: DocumentType) -> None:
        await self.collection.insert_one(obj.to_mongo())

    async def create_many(self, objs: list[DocumentType]) -> None:
        if objs:
            await self.collection.insert_many([obj.to_mongo() for obj in objs])
