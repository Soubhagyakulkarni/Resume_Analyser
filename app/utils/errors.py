"""Typed application errors safe to map to user-facing messages."""


class ApplicationError(Exception):
    """Base class for expected application failures."""

    user_message = "The request could not be completed. Please try again."


class InvalidResumeError(ApplicationError):
    user_message = "The resume could not be read. Check the file and try again."


class ProviderUnavailableError(ApplicationError):
    user_message = (
        "The AI provider is temporarily unavailable. Your resume file was accepted; "
        "please try analyzing it again shortly."
    )


class ProviderRateLimitError(ApplicationError):
    user_message = (
        "The AI provider's request limit or free-tier quota was reached. "
        "Wait for the limit to reset, then retry."
    )


class ProviderConfigurationError(ApplicationError):
    user_message = (
        "The configured AI provider rejected its API key. Check that the key is active, "
        "matches AI_PROVIDER, and is set in the local .env file."
    )


class ProviderRequestError(ApplicationError):
    user_message = "The AI service could not process this request. Check the input and retry."


class InvalidModelResponseError(ApplicationError):
    user_message = "The analysis response could not be validated. Please try again."


class CatalogUnavailableError(ApplicationError):
    user_message = "Job recommendations are temporarily unavailable."


class JobSourceConfigurationError(ApplicationError):
    user_message = "Configure ADZUNA_APP_ID and ADZUNA_APP_KEY in the local .env file."


class JobSourceUnavailableError(ApplicationError):
    user_message = (
        "The Adzuna job feed is temporarily unavailable. The existing catalog was not changed."
    )


class ReportGenerationError(ApplicationError):
    user_message = "The report could not be generated. Please try again."


class AuthenticationError(ApplicationError):
    """Base error for authentication failures."""

    user_message = "Authentication failed. Please check your credentials and try again."


class InvalidCredentialsError(AuthenticationError):
    user_message = "Invalid username/email or password."


class UserAlreadyExistsError(AuthenticationError):
    user_message = "An account with this username or email already exists."


class UserRegistrationError(AuthenticationError):
    user_message = "Registration could not be completed. Please check your inputs and try again."


class UserDatabaseUnavailableError(ApplicationError):
    user_message = "The user database is temporarily unavailable. Please try again shortly."
