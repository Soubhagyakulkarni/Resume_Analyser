"""Compatibility imports for application error types."""

from app.utils.errors import (
    ApplicationError,
    CatalogUnavailableError,
    InvalidModelResponseError,
    InvalidResumeError,
    JobSourceConfigurationError,
    JobSourceUnavailableError,
    ProviderConfigurationError,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderUnavailableError,
    ReportGenerationError,
)

__all__ = [
    "ApplicationError",
    "CatalogUnavailableError",
    "InvalidModelResponseError",
    "InvalidResumeError",
    "JobSourceConfigurationError",
    "JobSourceUnavailableError",
    "ProviderConfigurationError",
    "ProviderRateLimitError",
    "ProviderRequestError",
    "ProviderUnavailableError",
    "ReportGenerationError",
]
