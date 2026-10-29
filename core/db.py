"""SQLite bootstrap shared by auth + usage (one small file-based DB)."""
from __future__ import annotations

import os
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  pass_salt TEXT NOT NULL,
  pass_hash TEXT NOT NULL,
  is_admin INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS generations (
  id INTEGER PRIMARY KEY,
  ts TEXT NOT NULL,
  username TEXT NOT NULL,
  mode TEXT NOT NULL,
  notes_chars INTEGER NOT NULL,
  deck_bytes INTEGER NOT NULL,
  ms INTEGER NOT NULL
);
"""


def db_path() -> str:
    return os.environ.get("USAGE_DB", "usage.db")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    from .auth import ensure_default_admin  # local import avoids a cycle

    with connect() as conn:
        conn.executescript(SCHEMA)
    ensure_default_admin()
