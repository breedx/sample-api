"""
Configuration management for multi-environment testing
"""
import os
from typing import Literal
from pydantic import BaseModel


class Settings(BaseModel):
    """Application settings from environment variables"""

    # Environment
    api_env: Literal["dev", "stage", "prod"] = "dev"

    # Security
    jwt_secret: str = "dev_secret_change_in_production_!!!"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Rate limiting
    rate_limit_per_minute: int = 10

    # Pagination
    default_page_size: int = 20
    max_page_size: int = 100

    # File upload
    max_file_size_mb: int = 10
    allowed_file_types: list[str] = [
        "image/jpeg",
        "image/png",
        "image/gif",
        "application/pdf",
        "text/plain",
        "text/csv",
    ]

    # Database (in-memory for this assessment)
    database_url: str = "memory://"

    class Config:
        env_prefix = ""  # No prefix for env vars


def get_settings() -> Settings:
    """Load settings from environment variables"""
    return Settings(
        api_env=os.getenv("API_ENV", "dev"),
        jwt_secret=os.getenv("JWT_SECRET", "dev_secret_change_in_production_!!!"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
        refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
        rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "10")),
        default_page_size=int(os.getenv("DEFAULT_PAGE_SIZE", "20")),
        max_page_size=int(os.getenv("MAX_PAGE_SIZE", "100")),
        max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "10")),
    )


settings = get_settings()
