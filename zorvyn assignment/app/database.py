from __future__ import annotations

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.security import hash_password

DEFAULT_DB_PATH = Path(__file__).resolve().parent.parent / "finance.db"


def get_db_path() -> str:
    configured_path = os.getenv("FINANCE_DB_PATH")
    if configured_path:
        return configured_path
    return str(DEFAULT_DB_PATH)


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(get_db_path())
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON;")
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('viewer', 'analyst', 'admin')),
                is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS financial_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL CHECK(amount > 0),
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                category TEXT NOT NULL,
                record_date TEXT NOT NULL,
                description TEXT,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE RESTRICT
            );

            CREATE INDEX IF NOT EXISTS idx_records_date ON financial_records(record_date);
            CREATE INDEX IF NOT EXISTS idx_records_type ON financial_records(type);
            CREATE INDEX IF NOT EXISTS idx_records_category ON financial_records(category);
            """
        )

        default_admin = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            ("admin",),
        ).fetchone()

        if default_admin is None:
            connection.execute(
                """
                INSERT INTO users (username, full_name, password_hash, role, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                ("admin", "System Administrator", hash_password("admin123"), "admin", 1),
            )
