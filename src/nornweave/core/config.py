"""Application configuration (Pydantic settings)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """NornWeave configuration from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Storage (Urdr)
    db_driver: Literal["postgres", "sqlite"] = Field(default="postgres", alias="DB_DRIVER")
    database_url: str = Field(default="", alias="DATABASE_URL")

    # Email provider
    email_provider: Literal["mailgun", "ses", "sendgrid", "resend"] = Field(
        default="mailgun", alias="EMAIL_PROVIDER"
    )
    email_domain: str = Field(default="", alias="EMAIL_DOMAIN")

    # Provider-specific (filled per provider)
    mailgun_api_key: str = Field(default="", alias="MAILGUN_API_KEY")
    mailgun_domain: str = Field(default="", alias="MAILGUN_DOMAIN")
    sendgrid_api_key: str = Field(default="", alias="SENDGRID_API_KEY")
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")

    # API security
    api_key: str = Field(default="", alias="API_KEY")
    cors_origins: str = Field(default="*", alias="CORS_ORIGINS")

    # Server
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    environment: Literal["development", "staging", "production"] = Field(
        default="development", alias="ENVIRONMENT"
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", alias="LOG_LEVEL"
    )

    # Phase 3
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    webhook_secret: str = Field(default="", alias="WEBHOOK_SECRET")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
