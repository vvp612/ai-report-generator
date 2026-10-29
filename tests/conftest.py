import pytest


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Every test gets its own SQLite file (USAGE_DB is read lazily).
    Only the schema is created here — `init_db()` (schema + default admin)
    stays under test in test_auth."""
    monkeypatch.setenv("USAGE_DB", str(tmp_path / "usage.db"))
    from core.db import SCHEMA, connect

    with connect() as conn:
        conn.executescript(SCHEMA)
