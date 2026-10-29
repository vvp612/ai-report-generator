"""Usage logging: every generation is recorded, CSV-exportable.

Internal tools earn trust by being traceable — this is core, not an afterthought.
"""
from __future__ import annotations

import csv
import io

from .db import connect


def log_generation(username: str, mode: str, notes_chars: int, deck_bytes: int, ms: int) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO generations (ts, username, mode, notes_chars, deck_bytes, ms) "
            "VALUES (datetime('now'),?,?,?,?,?)",
            (username, mode, notes_chars, deck_bytes, ms),
        )


def generations() -> list[dict]:
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT ts, username, mode, notes_chars, deck_bytes, ms FROM generations ORDER BY id DESC")]


def csv_report() -> str:
    rows = generations()
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=["ts", "username", "mode", "notes_chars", "deck_bytes", "ms"])
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()
