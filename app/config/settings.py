"""Application settings using Pydantic"""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/scaledux"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # API Settings
    API_V1_PREFIX: str = "/api/v1"
    DEBUG: bool = True
    ENVIRONMENT: str = "development"

    # Security
    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Scoring Engine
    DEFAULT_FRAMEWORK_VERSION: str = "1.0.0"
    FRAMEWORK_VERSION: str = "1.0.0"
    ENABLE_DRAFT_SCORES: bool = True
    SNAPSHOT_DAYS: str = "1,15"

    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "png", "jpg", "jpeg", "doc", "docx", "xls", "xlsx"]
    UPLOAD_STORAGE_PATH: str = "/var/uploads/scaledux"

    # Time Decay
    DEFAULT_DECAY_LAMBDA: float = 0.005
    HIGH_VOLATILITY_LAMBDA: float = 0.1
    LOW_VOLATILITY_LAMBDA: float = 0.001

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    @property
    def snapshot_days_list(self) -> List[int]:
        """Parse SNAPSHOT_DAYS string into list of integers"""
        return [int(day.strip()) for day in self.SNAPSHOT_DAYS.split(",")]


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()
