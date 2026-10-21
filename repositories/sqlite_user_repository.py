"""SQLite repository for persistent user authentication and profiles."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from app.utils.errors import UserAlreadyExistsError, UserDatabaseUnavailableError
from models.user import User

logger = logging.getLogger(__name__)
MIGRATION = Path(__file__).with_name("migrations") / "002_create_users_table.sql"


class SQLiteUserRepository:
    """Manages persistent SQLite storage for user accounts."""

    def __init__(self, database_path: Path) -> None:
        self._database_path = database_path
        self._database_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with self._connect() as connection:
                connection.executescript(MIGRATION.read_text(encoding="utf-8"))
        except (OSError, sqlite3.Error) as exc:
            logger.exception("Could not initialize SQLite users database")
            raise UserDatabaseUnavailableError() from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._database_path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    def create_user(self, user: User) -> None:
        """Insert a new user account or raise UserAlreadyExistsError on duplicate."""
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO users (
                        id, username, email, full_name, password_hash, salt, created_at, last_login_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        user.id,
                        user.username.strip(),
                        user.email.strip().lower(),
                        user.full_name.strip(),
                        user.password_hash,
                        user.salt,
                        user.created_at,
                        user.last_login_at,
                    ),
                )
        except sqlite3.IntegrityError as exc:
            logger.info("Attempted registration with existing username or email: %s", exc)
            raise UserAlreadyExistsError() from exc
        except sqlite3.Error as exc:
            logger.exception("Failed to insert user account")
            raise UserDatabaseUnavailableError() from exc

    def get_by_id(self, user_id: str) -> User | None:
        """Fetch a user by exact unique ID."""
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT id, username, email, full_name, password_hash, salt, created_at, last_login_at
                    FROM users
                    WHERE id = ?
                    """,
                    (user_id,),
                ).fetchone()
                return self._row_to_user(row) if row else None
        except sqlite3.Error as exc:
            logger.exception("Failed to query user by ID")
            raise UserDatabaseUnavailableError() from exc

    def get_by_username(self, username: str) -> User | None:
        """Fetch a user by username (case-insensitive)."""
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT id, username, email, full_name, password_hash, salt, created_at, last_login_at
                    FROM users
                    WHERE username = ? COLLATE NOCASE
                    """,
                    (username.strip(),),
                ).fetchone()
                return self._row_to_user(row) if row else None
        except sqlite3.Error as exc:
            logger.exception("Failed to query user by username")
            raise UserDatabaseUnavailableError() from exc

    def get_by_email(self, email: str) -> User | None:
        """Fetch a user by email (case-insensitive)."""
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT id, username, email, full_name, password_hash, salt, created_at, last_login_at
                    FROM users
                    WHERE email = ? COLLATE NOCASE
                    """,
                    (email.strip().lower(),),
                ).fetchone()
                return self._row_to_user(row) if row else None
        except sqlite3.Error as exc:
            logger.exception("Failed to query user by email")
            raise UserDatabaseUnavailableError() from exc

    def get_by_identifier(self, identifier: str) -> User | None:
        """Fetch a user by either username or email (case-insensitive)."""
        clean_identifier = identifier.strip()
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT id, username, email, full_name, password_hash, salt, created_at, last_login_at
                    FROM users
                    WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE
                    """,
                    (clean_identifier, clean_identifier.lower()),
                ).fetchone()
                return self._row_to_user(row) if row else None
        except sqlite3.Error as exc:
            logger.exception("Failed to query user by identifier")
            raise UserDatabaseUnavailableError() from exc

    def update_last_login(self, user_id: str, last_login_at: str) -> None:
        """Update last login timestamp for an authenticated user."""
        try:
            with self._connect() as connection:
                connection.execute(
                    "UPDATE users SET last_login_at = ? WHERE id = ?",
                    (last_login_at, user_id),
                )
        except sqlite3.Error as exc:
            logger.exception("Failed to update last login timestamp")
            raise UserDatabaseUnavailableError() from exc

    def count_users(self) -> int:
        """Return total number of registered users."""
        try:
            with self._connect() as connection:
                row = connection.execute("SELECT COUNT(*) FROM users").fetchone()
                return int(row[0]) if row else 0
        except sqlite3.Error as exc:
            logger.exception("Failed to count users")
            raise UserDatabaseUnavailableError() from exc

    @staticmethod
    def _row_to_user(row: sqlite3.Row) -> User:
        return User(
            id=row["id"],
            username=row["username"],
            email=row["email"],
            full_name=row["full_name"],
            password_hash=row["password_hash"],
            salt=row["salt"],
            created_at=row["created_at"],
            last_login_at=row["last_login_at"],
        )
