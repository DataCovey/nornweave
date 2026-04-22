"""Tests for API security configuration validation."""

import pytest
from pydantic import ValidationError

from nornweave.core.config import Settings


@pytest.mark.unit
class TestApiSecurityConfigValidation:
    """Validate API key requirements based on environment."""

    def test_production_requires_api_key(self) -> None:
        with pytest.raises(ValidationError, match="API_KEY is required"):
            Settings(
                _env_file=None,
                ENVIRONMENT="production",
                API_KEY="",
                DB_DRIVER="sqlite",
            )

    def test_staging_requires_api_key(self) -> None:
        with pytest.raises(ValidationError, match="API_KEY is required"):
            Settings(
                _env_file=None,
                ENVIRONMENT="staging",
                API_KEY="",
                DB_DRIVER="sqlite",
            )

    def test_development_allows_empty_api_key(self) -> None:
        settings = Settings(
            _env_file=None,
            ENVIRONMENT="development",
            API_KEY="",
            DB_DRIVER="sqlite",
        )
        assert settings.api_key == ""

    def test_production_accepts_api_key(self) -> None:
        settings = Settings(
            _env_file=None,
            ENVIRONMENT="production",
            API_KEY="test-secret",
            DB_DRIVER="sqlite",
        )
        assert settings.api_key == "test-secret"


@pytest.mark.unit
class TestCorsSecurityConfigValidation:
    """Validate CORS requirements based on environment."""

    def test_production_rejects_wildcard_cors(self) -> None:
        with pytest.raises(ValidationError, match="CORS_ORIGINS cannot include wildcard"):
            Settings(
                _env_file=None,
                ENVIRONMENT="production",
                API_KEY="test-secret",
                CORS_ORIGINS="*",
                DB_DRIVER="sqlite",
            )

    def test_staging_requires_explicit_cors_origins(self) -> None:
        with pytest.raises(
            ValidationError, match="CORS_ORIGINS must include at least one explicit origin"
        ):
            Settings(
                _env_file=None,
                ENVIRONMENT="staging",
                API_KEY="test-secret",
                CORS_ORIGINS="",
                DB_DRIVER="sqlite",
            )

    def test_rejects_mixing_wildcard_and_explicit_origins(self) -> None:
        with pytest.raises(ValidationError, match="cannot mix wildcard"):
            Settings(
                _env_file=None,
                ENVIRONMENT="development",
                API_KEY="",
                CORS_ORIGINS="*,http://localhost:3000",
                DB_DRIVER="sqlite",
            )

    def test_rejects_invalid_origin_format(self) -> None:
        with pytest.raises(ValidationError, match="Invalid CORS origin"):
            Settings(
                _env_file=None,
                ENVIRONMENT="development",
                API_KEY="",
                CORS_ORIGINS="localhost:3000",
                DB_DRIVER="sqlite",
            )

    def test_development_allows_wildcard_cors(self) -> None:
        settings = Settings(
            _env_file=None,
            ENVIRONMENT="development",
            API_KEY="",
            CORS_ORIGINS="*",
            DB_DRIVER="sqlite",
        )
        assert settings.cors_origin_list == ["*"]
