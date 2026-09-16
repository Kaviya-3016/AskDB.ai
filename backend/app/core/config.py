import os
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = (BACKEND_DIR / "nlp_sql.db").as_posix()
DEFAULT_DEMO_DB_PATH = (BACKEND_DIR / "demo_ecommerce.db").as_posix()


class Settings(BaseSettings):
    # App Information
    APP_NAME: str = "Enterprise NLP-to-SQL Generator"
    APP_VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security & Authentication
    SECRET_KEY: str = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Google OAuth (Optional for Open Source / Production)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "*",
    ]

    # Database
    # Anchored to the backend directory so it connects consistently regardless of working directory
    DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DB_PATH}"
    DEMO_DATABASE_URL: str = f"sqlite+aiosqlite:///{DEFAULT_DEMO_DB_PATH}"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # Redis Cache
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_ENABLED: bool = False  # Set to true if Redis service is active, gracefully falls back to memory cache

    # Rate Limiting
    RATE_LIMIT_PER_HOUR: int = 100

    # ML Model Configuration
    ML_MODEL_NAME: str = "t5-base-text2sql"
    ML_MODEL_PATH: str = "models/t5_sql_model"
    USE_MOCK_FALLBACK: bool = True
    INFERENCE_TIMEOUT_SECONDS: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow",
    )


settings = Settings()
