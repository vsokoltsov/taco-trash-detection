from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from trash_annotation.storage import StorageEnum


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    MASK_RCNN_V1_PATH: str = ""
    YOLO_V8_PATH: str = ""
    YOLO_V11_TOP5_PATH: str = ""
    STORAGE: StorageEnum = StorageEnum.GOOGLE_DRIVE
    USE_GPU: bool = False


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
