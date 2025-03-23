from pydantic_settings import BaseSettings, SettingsConfigDict
import logging

logger = logging.getLogger("api")

class Settings(BaseSettings):
    database_url: str = "sqlite:///./default.db"
    storage_type: str = "in_memory"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    def __init__(self, **data):
        super().__init__(**data)
        logger.info("Loaded settings: %s", self.model_dump_json())

settings = Settings()