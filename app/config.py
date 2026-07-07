from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "motodi-go-backend-ai"
    environment: Literal["local", "test", "staging", "production"] = "local"
    log_level: str = "INFO"
    backend_core_base_url: str = "http://localhost:8081"
    request_timeout_seconds: float = Field(default=3.0, gt=0)
    max_recommendations: int = Field(default=5, ge=1, le=50)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

