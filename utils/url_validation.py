"""URL checks for job-listing destinations."""

from urllib.parse import urlparse

PLACEHOLDER_HOSTS = {
    "example.com",
    "example.net",
    "example.org",
    "example-tech.com",
    "example.invalid",
    "example.test",
}


def is_placeholder_application_url(application_url: str) -> bool:
    """Identify reserved/example hosts that must not appear as job destinations."""
    if not application_url:
        return False
    hostname = (urlparse(application_url).hostname or "").lower().rstrip(".")
    return (
        hostname in PLACEHOLDER_HOSTS
        or any(hostname.endswith(f".{placeholder}") for placeholder in PLACEHOLDER_HOSTS)
        or hostname.endswith((".example", ".invalid", ".test"))
    )
