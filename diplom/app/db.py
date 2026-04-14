import sqlite3
from datetime import datetime
from typing import Optional

from flask import current_app, g


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(str(current_app.config["DATABASE_PATH"]))
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_: Optional[BaseException] = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


def _column_names(db: sqlite3.Connection, table_name: str) -> set[str]:
    rows = db.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def init_db() -> None:
    db = get_db()

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            display_name TEXT,
            email TEXT,
            password_hash TEXT NOT NULL,
            avatar_filename TEXT,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            saved_filename TEXT NOT NULL,
            file_type TEXT NOT NULL,
            full_text TEXT NOT NULL,
            extracted_pairs_count INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS terms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            normalized_name TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS definitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            normalized_text TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS term_occurrences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_id INTEGER NOT NULL,
            term_id INTEGER NOT NULL,
            definition_id INTEGER NOT NULL,
            source_line TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY(document_id) REFERENCES documents(id) ON DELETE CASCADE,
            FOREIGN KEY(term_id) REFERENCES terms(id),
            FOREIGN KEY(definition_id) REFERENCES definitions(id)
        );

        CREATE INDEX IF NOT EXISTS idx_terms_normalized_name ON terms(normalized_name);
        CREATE INDEX IF NOT EXISTS idx_definitions_normalized_text ON definitions(normalized_text);
        CREATE INDEX IF NOT EXISTS idx_occurrences_document_id ON term_occurrences(document_id);
        CREATE INDEX IF NOT EXISTS idx_occurrences_term_id ON term_occurrences(term_id);
        """
    )

    user_columns = _column_names(db, "users")

    if "email" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN email TEXT")

    if "username" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN username TEXT")

    if "display_name" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN display_name TEXT")

    if "avatar_filename" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN avatar_filename TEXT")

    if "created_at" not in user_columns:
        db.execute("ALTER TABLE users ADD COLUMN created_at TEXT")

    db.execute(
        """
        UPDATE users
        SET email = LOWER(username)
        WHERE (email IS NULL OR TRIM(email) = '')
          AND username IS NOT NULL
          AND TRIM(username) != ''
        """
    )

    db.execute(
        """
        UPDATE users
        SET created_at = ?
        WHERE created_at IS NULL OR TRIM(created_at) = ''
        """,
        (datetime.utcnow().isoformat(timespec="seconds"),),
    )

    db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    db.commit()