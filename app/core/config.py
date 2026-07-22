import os
from pathlib import Path
from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BACKEND_DIR.parent

ENV_FILE_PATHS = [
    str(BACKEND_DIR / ".env"),
    str(ROOT_DIR / ".env"),
    ".env"
]


class Settings(BaseSettings):
    PROJECT_NAME: str = "Surakshak360 Backend API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/v1"
    
    SECRET_KEY: str = "surakshak360_super_secret_jwt_key_2026_dev"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "surakshak360"

    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password"

    REDIS_URL: str = "redis://localhost:6379/0"

    SCAM_INTELLIGENCE_URL: str = "http://localhost:8001"
    VISION_URL: str = "http://localhost:8002"
    INTELLIGENCE_URL: str = "http://localhost:8003"
    FRONTEND_URL: str = "http://localhost:3000"

    CLOUDINARY_URL: str = "cloudinary://api_key:api_secret@cloud_name"

    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://surakshak360.vercel.app"
    ]

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATHS,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
