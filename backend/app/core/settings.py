import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"), extra="ignore"
    )


class MongoConfig(BaseConfig):
    URL: str = Field("mongodb://localhost:27017", alias="MONGO_URL")
    DB: str = Field("dedup", alias="MONGO_DB")


class QdrantConfig(BaseConfig):
    # ":memory:" runs an in-process Qdrant (tests)
    URL: str = Field("http://localhost:6333", alias="QDRANT_URL")
    COLLECTION: str = Field("images", alias="QDRANT_COLLECTION")


class StorageConfig(BaseConfig):
    DIR: str = Field("data/images", alias="STORAGE_DIR")


class ModelConfig(BaseConfig):
    PATH: str = Field("dedup_model/sscd_disc_mixup.torchscript.pt", alias="MODEL_PATH")
    URL: str = Field(
        "https://dl.fbaipublicfiles.com/sscd-copy-detection/sscd_disc_mixup.torchscript.pt",
        alias="MODEL_URL",
    )
    INPUT_SIZE: int = Field(224, alias="MODEL_INPUT_SIZE")
    # 0 = torch default (all cores); set per worker when scaling replicas
    TORCH_THREADS: int = Field(0, alias="TORCH_THREADS")


class DuplicateConfig(BaseConfig):
    # calibrated on UKBench for SSCD, see CALIBRATION.md
    THRESHOLD: float = Field(0.75, alias="DUPLICATE_THRESHOLD", ge=0, le=1)
    MAX_PER_IMAGE: int = Field(50, alias="MAX_DUPLICATES_PER_IMAGE")


class UploadConfig(BaseConfig):
    MAX_FILE_BYTES: int = Field(10 * 1024 * 1024, alias="MAX_FILE_BYTES")
    MAX_FILES: int = Field(50, alias="MAX_FILES_PER_REQUEST")
    THUMB_SIZE: int = Field(256, alias="THUMB_SIZE")

    @property
    def max_request_bytes(self) -> int:
        return self.MAX_FILE_BYTES * self.MAX_FILES + 1024 * 1024


class WorkerConfig(BaseConfig):
    BATCH_SIZE: int = Field(64, alias="WORKER_BATCH_SIZE")
    IDLE_SLEEP: float = Field(0.5, alias="WORKER_IDLE_SLEEP")
    LEASE_SECONDS: int = Field(300, alias="WORKER_LEASE_SECONDS")


class AppSettings(BaseConfig):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    WORKERS: int = 1
    ALLOW_ORIGINS: list[str] = ["*"]
    LOG_LEVEL: str = "INFO"

    mongo: MongoConfig = MongoConfig()
    qdrant: QdrantConfig = QdrantConfig()
    storage: StorageConfig = StorageConfig()
    model: ModelConfig = ModelConfig()
    duplicates: DuplicateConfig = DuplicateConfig()
    upload: UploadConfig = UploadConfig()
    worker: WorkerConfig = WorkerConfig()


settings = AppSettings()
