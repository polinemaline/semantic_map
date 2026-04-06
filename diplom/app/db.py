import sqlite3
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


def init_db() -> None:
    db = get_db()

    db.executescript(
        """
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

        CREATE INDEX IF NOT EXISTS idx_terms_normalized_name
            ON terms(normalized_name);

        CREATE INDEX IF NOT EXISTS idx_definitions_normalized_text
            ON definitions(normalized_text);

        CREATE INDEX IF NOT EXISTS idx_occurrences_document_id
            ON term_occurrences(document_id);

        CREATE INDEX IF NOT EXISTS idx_occurrences_term_id
            ON term_occurrences(term_id);
        """
    )

    db.commit()