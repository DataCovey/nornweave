"""Application configuration (Pydantic settings)."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
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
    email_provider: Literal["mailgun", "ses", "sendgrid", "resend", "imap-smtp"] = Field(
        default="mailgun", alias="EMAIL_PROVIDER"
    )
    email_domain: str = Field(default="", alias="EMAIL_DOMAIN")

    # Provider-specific (filled per provider)
    mailgun_api_key: str = Field(default="", alias="MAILGUN_API_KEY")
    mailgun_domain: str = Field(default="", alias="MAILGUN_DOMAIN")
    sendgrid_api_key: str = Field(default="", alias="SENDGRID_API_KEY")
    resend_api_key: str = Field(default="", alias="RESEND_API_KEY")
    resend_webhook_secret: str = Field(default="", alias="RESEND_WEBHOOK_SECRET")
    aws_access_key_id: str = Field(default="", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field(default="", alias="AWS_SECRET_ACCESS_KEY")
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")

    # SMTP/IMAP provider settings
    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: str = Field(default="", alias="SMTP_USERNAME")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    smtp_use_tls: bool = Field(default=True, alias="SMTP_USE_TLS")
    imap_host: str = Field(default="", alias="IMAP_HOST")
    imap_port: int = Field(default=993, alias="IMAP_PORT")
    imap_username: str = Field(default="", alias="IMAP_USERNAME")
    imap_password: str = Field(default="", alias="IMAP_PASSWORD")
    imap_use_ssl: bool = Field(default=True, alias="IMAP_USE_SSL")
    imap_poll_interval: int = Field(default=60, alias="IMAP_POLL_INTERVAL")
    imap_mailbox: str = Field(default="INBOX", alias="IMAP_MAILBOX")
    imap_mark_as_read: bool = Field(default=True, alias="IMAP_MARK_AS_READ")
    imap_delete_after_fetch: bool = Field(default=False, alias="IMAP_DELETE_AFTER_FETCH")

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
    # LLM Thread Summarization Configuration
    # -------------------------------------------------------------------------
    llm_provider: Literal["openai", "anthropic", "gemini"] | None = Field(
        default=None,
        alias="LLM_PROVIDER",
        description="LLM provider for thread summarization. None = feature disabled.",
    )
    llm_api_key: str = Field(
        default="",
        alias="LLM_API_KEY",
        description="API key for the selected LLM provider",
    )
    llm_model: str = Field(
        default="",
        alias="LLM_MODEL",
        description="Model override (auto-selected per provider if empty)",
    )
    llm_summary_prompt: str = Field(
        default=(
            "You are an email thread summarizer. Given a chronological email conversation, "
            "produce a concise summary that captures:\n"
            "- Key topics discussed\n"
            "- Decisions made or actions agreed upon\n"
            "- Open questions or pending items\n"
            "- Current status of the conversation\n\n"
            "Keep the summary under 300 words. Use bullet points for clarity.\n"
            "Do not include greetings, sign-offs, or meta-commentary."
        ),
        alias="LLM_SUMMARY_PROMPT",
        description="System prompt for thread summarization",
    )
    llm_daily_token_limit: int = Field(
        default=1_000_000,
        alias="LLM_DAILY_TOKEN_LIMIT",
        description="Max tokens per day for summarization (0 = unlimited)",
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

    @model_validator(mode="after")
    def validate_imap_config(self) -> Settings:
        """Validate IMAP configuration: delete requires mark-as-read for safety."""
        if self.imap_delete_after_fetch and not self.imap_mark_as_read:
            msg = (
                "IMAP_DELETE_AFTER_FETCH=true requires IMAP_MARK_AS_READ=true. "
                "Deleting emails without marking them as read first is not safe."
            )
            raise ValueError(msg)
        return self

    @model_validator(mode="after")
    def validate_llm_config(self) -> Settings:
        """Validate LLM configuration: API key is required when provider is set."""
        if self.llm_provider is not None and not self.llm_api_key:
            msg = (
                f"LLM_API_KEY is required when LLM_PROVIDER is set to '{self.llm_provider}'. "
                "Set LLM_API_KEY in your environment or .env file."
            )
            raise ValueError(msg)
        return self


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
