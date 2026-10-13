from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.settings import settings
from db.mongo import ensure_indexes
from routers import duplicate_router, image_router, index_router
from routers.middlewares import limit_request_size


@asynccontextmanager
async def lifespan(_: FastAPI):
    await ensure_indexes()
    yield


app = FastAPI(title="Image duplicate finder", lifespan=lifespan)
app.include_router(index_router.router)
app.include_router(image_router.router)
app.include_router(duplicate_router.router)

app.middleware("http")(limit_request_size)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOW_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS,
    )
