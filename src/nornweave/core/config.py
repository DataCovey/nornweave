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

    # Storage (Urdr)  # noqa: ERA001
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

    # -------------------------------------------------------------------------
    # Attachment Storage Configuration
    # -------------------------------------------------------------------------
    # Backend selection: "local", "s3", "gcs", "database"
    attachment_storage_backend: Literal["local", "s3", "gcs", "database"] = Field(
        default="local",
        alias="ATTACHMENT_STORAGE_BACKEND",
        description="Storage backend for attachments",
    )

    # Local filesystem settings
    attachment_local_path: str = Field(
        default="./data/attachments",
        alias="ATTACHMENT_LOCAL_PATH",
        description="Base path for local filesystem storage",
    )
    attachment_serve_url_prefix: str = Field(
        default="/v1/attachments",
        alias="ATTACHMENT_SERVE_URL_PREFIX",
        description="URL prefix for attachment downloads",
    )

    # S3 settings
    attachment_s3_bucket: str | None = Field(
        default=None,
        alias="ATTACHMENT_S3_BUCKET",
        description="S3 bucket for attachment storage",
    )
    attachment_s3_prefix: str = Field(
        default="attachments",
        alias="ATTACHMENT_S3_PREFIX",
        description="S3 key prefix for attachments",
    )
    attachment_s3_region: str = Field(
        default="us-east-1",
        alias="ATTACHMENT_S3_REGION",
        description="AWS region for S3 bucket",
    )
    attachment_s3_access_key: str | None = Field(
        default=None,
        alias="ATTACHMENT_S3_ACCESS_KEY",
        description="AWS access key (uses IAM role if not set)",
    )
    attachment_s3_secret_key: str | None = Field(
        default=None,
        alias="ATTACHMENT_S3_SECRET_KEY",
        description="AWS secret key (uses IAM role if not set)",
    )

    # GCS settings
    attachment_gcs_bucket: str | None = Field(
        default=None,
        alias="ATTACHMENT_GCS_BUCKET",
        description="GCS bucket for attachment storage",
    )
    attachment_gcs_prefix: str = Field(
        default="attachments",
        alias="ATTACHMENT_GCS_PREFIX",
        description="GCS blob prefix for attachments",
    )
    attachment_gcs_credentials_path: str | None = Field(
        default=None,
        alias="ATTACHMENT_GCS_CREDENTIALS_PATH",
        description="Path to GCS service account JSON (uses ADC if not set)",
    )

    # Download URL settings
    attachment_url_expiry_seconds: int = Field(
        default=3600,
        alias="ATTACHMENT_URL_EXPIRY_SECONDS",
        description="Default expiry time for download URLs in seconds",
    )

    # Size limits
    attachment_max_size_mb: int = Field(
        default=25,
        alias="ATTACHMENT_MAX_SIZE_MB",
        description="Maximum size for single attachment in MB",
    )
    attachment_max_total_size_mb: int = Field(
        default=35,
        alias="ATTACHMENT_MAX_TOTAL_SIZE_MB",
        description="Maximum total size for all attachments in MB",
    )
    attachment_max_count: int = Field(
        default=20,
        alias="ATTACHMENT_MAX_COUNT",
        description="Maximum number of attachments per message",
    )

    # -------------------------------------------------------------------------
    # Content Extraction Configuration (Talon)
    # -------------------------------------------------------------------------
    talon_use_ml_signature: bool = Field(
        default=True,
        alias="TALON_USE_ML_SIGNATURE",
        description="Use ML-based signature extraction (more accurate)",
    )
    message_preview_max_length: int = Field(
        default=100,
        alias="MESSAGE_PREVIEW_MAX_LENGTH",
        description="Maximum length for message preview text",
    )
    extraction_fallback_to_original: bool = Field(
        default=True,
        alias="EXTRACTION_FALLBACK_TO_ORIGINAL",
        description="Return original content if extraction fails",
    )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
