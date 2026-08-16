import os
import logging
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache

logger = logging.getLogger(__name__)

INSECURE_SECRETS = {
    "change-this-to-a-random-string",
    "generate_a_real_secret_with_the_command_above",
    "",
}


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:changeme@localhost:5432/jobmatch"

    # Adzuna
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""

    # Reed.co.uk
    reed_api_key: str = ""

    # Groq provider
    groq_api_key: str = ""
    groq_api_base: str = "https://api.groq.com/openai/v1"
    groq_model: str = "llama-3.3-70b-versatile"

    # JWT Auth
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    app_base_url: str = "http://localhost:5000"
    password_reset_expiry_minutes: int = 15

    # Email
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    smtp_timeout_seconds: int = 10

    # Dedicated notification scheduler process
    scheduler_enabled: bool = False
    scheduler_timezone: str = "UTC"
    scheduler_instant_interval_minutes: int = 5
    scheduler_daily_time: str = "09:00"
    scheduler_weekly_day: str = "mon"
    scheduler_weekly_time: str = "09:00"
    notification_max_retries: int = 3
    notification_digest_limit: int = 5
    recommended_search_threshold: float = 0.35

    # Embedding model - BGE is optimized for retrieval/search tasks
    embedding_model: str = "BAAI/bge-base-en-v1.5"
    embedding_dim: int = 768

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v in INSECURE_SECRETS:
            if os.getenv("ENV") == "production":
                raise ValueError(
                    "SECRET_KEY must be a strong random string in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
            logger.warning(
                "SECURITY: SECRET_KEY is not set or is insecure. "
                "Generate a real secret for production use."
            )
        return v

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
