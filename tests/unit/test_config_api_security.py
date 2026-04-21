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
