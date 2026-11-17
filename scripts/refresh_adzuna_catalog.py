"""Refresh the SQLite job catalog from an authorized Adzuna API account."""

import argparse
import logging
import sys

from app.config.settings import Settings
from app.utils.errors import ApplicationError
from config.logging_config import configure_logging
from integrations.adzuna_job_client import AdzunaJobClient
from repositories.sqlite_job_repository import SQLiteJobRepository

logger = logging.getLogger(__name__)


def refresh_catalog(
    client: AdzunaJobClient,
    repository: SQLiteJobRepository,
    what: str,
    where: str,
    pages: int,
) -> int:
    """Replace the catalog only after a successful fetch with usable listings."""
    jobs = client.search(what=what, where=where, pages=pages)
    if not jobs:
        raise ValueError(
            "Adzuna returned no usable listings; the existing job catalog was left unchanged."
        )
    repository.replace_jobs(jobs)
    return len(jobs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--what", default="graduate jobs", help="Search terms for job listings")
    parser.add_argument("--where", default="India", help="Location to search")
    parser.add_argument("--pages", type=int, default=3, help="Pages to fetch (1 to 10)")
    args = parser.parse_args()

    configure_logging()
    try:
        settings = Settings.from_environment()
        client = AdzunaJobClient(
            settings.adzuna_app_id,
            settings.adzuna_app_key,
            country_code=settings.adzuna_country_code,
        )
        count = refresh_catalog(
            client,
            SQLiteJobRepository(settings.sqlite_database_path),
            what=args.what,
            where=args.where,
            pages=args.pages,
        )
    except (ApplicationError, OSError, ValueError) as exc:
        print(f"Job catalog refresh failed: {exc}")
        return 1

    logger.info(
        "Imported %d Adzuna listings for country_code=%s", count, settings.adzuna_country_code
    )
    print(f"Imported {count} Adzuna listings.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
