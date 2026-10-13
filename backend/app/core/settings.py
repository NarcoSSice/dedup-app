import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"), extra="ignore"
    )


class DataConfig(BaseConfig):
    MONGO_URL: str = "mongodb://localhost:27017"
    MONGO_DB: str = "dedup"
    # ":memory:" runs an in-process Qdrant (tests)
    QDRANT_URL: str = "http://localhost:6333"
    STORAGE_DIR: str = "data/images"


class ApiConfig(BaseConfig):
    # calibrated on UKBench for SSCD, see CALIBRATION.md
    DUPLICATE_THRESHOLD: float = Field(0.80, ge=0, le=1)
    MAX_DUPLICATES_PER_IMAGE: int = 50
    MAX_FILE_BYTES: int = 10 * 1024 * 1024
    MAX_FILES_PER_REQUEST: int = 50

    @property
    def max_request_bytes(self) -> int:
        return self.MAX_FILE_BYTES * self.MAX_FILES_PER_REQUEST + 1024 * 1024


class WorkerConfig(BaseConfig):
    MODEL_PATH: str = "dedup_model/sscd_disc_mixup.torchscript.pt"
    # 0 = torch default (all cores); set per worker when scaling replicas
    TORCH_THREADS: int = 0
    WORKER_BATCH_SIZE: int = 64
    WORKER_IDLE_SLEEP: float = 0.5
    WORKER_LEASE_SECONDS: int = 300


class AppSettings(BaseConfig):
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = False
    WORKERS: int = 1
    ALLOW_ORIGINS: list[str] = ["*"]
    LOG_LEVEL: str = "INFO"

    data: DataConfig = DataConfig()
    api: ApiConfig = ApiConfig()
    worker: WorkerConfig = WorkerConfig()


settings = AppSettings()
