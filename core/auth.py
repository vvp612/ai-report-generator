"""Login: scrypt password hashing (stdlib), no auth dependency.

On first run an admin is created from ADMIN_USER/ADMIN_PASSWORD (demo defaults) so
the app is usable out of the box; change them before real use.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets

from .db import connect


def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=1)
    return salt, digest.hex()


def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    _, actual = hash_password(password, salt)
    return hmac.compare_digest(actual, expected_hash)


def create_user(username: str, password: str, is_admin: bool = False) -> int:
    salt, digest = hash_password(password)
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, pass_salt, pass_hash, is_admin, created_at) VALUES (?,?,?,?,datetime('now'))",
            (username, salt, digest, int(is_admin)),
        )
        return cur.lastrowid


def authenticate(username: str, password: str) -> bool:
    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return bool(row) and verify_password(password, row["pass_salt"], row["pass_hash"])


def ensure_default_admin() -> str | None:
    """Create the demo admin on a fresh database; returns the username or None."""
    with connect() as conn:
        exists = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
    if exists:
        return None
    username = os.environ.get("ADMIN_USER", "admin")
    create_user(username, os.environ.get("ADMIN_PASSWORD", "demo1234"), is_admin=True)
    return username
