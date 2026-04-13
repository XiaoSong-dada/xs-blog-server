import os
import json


def parse_allowed_origins(raw: str | None) -> list[str]:
    """Parse ALLOWED_ORIGINS from JSON array or comma-separated string."""
    default_origins = ["http://localhost:5173"]
    if not raw:
        return default_origins

    text = raw.strip()
    if not text:
        return default_origins

    # Priority: JSON array string, e.g. '["https://xsmach.cn"]'
    if text.startswith("[") and text.endswith("]"):
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                origins = [str(item).strip().strip('"\'') for item in parsed if str(item).strip()]
                return origins or default_origins
        except Exception:
            pass

    # Fallback: comma-separated string
    origins = [item.strip().strip('"\'') for item in text.split(",") if item.strip()]
    return origins or default_origins


class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    REDIS_URL = os.getenv("REDIS_URL")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_DB = os.getenv("REDIS_DB")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_PREFIX = os.getenv("REDIS_PREFIX")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT"))
    POSTGRES_USER: str = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB")
    ALLOWED_ORIGINS: list[str] = parse_allowed_origins(os.getenv("ALLOWED_ORIGINS"))
    FILE_STORAGE_PATH: str | None = os.getenv("FILE_STORAGE_PATH")

    EMAIL_HOST: str = os.getenv("EMAIL_HOST")
    EMAIL_PORT: int = int(os.getenv("EMAIL_PORT", "0"))
    EMAIL_CODE: str = os.getenv("EMAIL_CODE")
    EMAIL_SENDER: str = os.getenv("EMAIL_SENDER")
    EMAIL_FROM_NAME: str = os.getenv("EMAIL_FROM_NAME")

    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    DB_POOL_PRE_PING: bool = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"
    # In production, disable schema/docs endpoints to reduce API surface exposure.
    IS_PRODUCTION: bool = os.getenv("ENV", "development").lower() == "production"

settings = Settings()
