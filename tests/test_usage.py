import csv
import io

from core.usage import csv_report, generations, log_generation


def test_generations_are_logged_newest_first():
    log_generation("admin", "weekly_summary", 500, 30000, 1200)
    log_generation("admin", "risk_flags", 800, 32000, 1500)
    rows = generations()
    assert [r["mode"] for r in rows] == ["risk_flags", "weekly_summary"]
    assert rows[0]["notes_chars"] == 800


def test_csv_report_parses_with_expected_columns():
    log_generation("admin", "next_week", 42, 28000, 900)
    rows = list(csv.DictReader(io.StringIO(csv_report())))
    assert {"ts", "username", "mode", "notes_chars", "deck_bytes", "ms"} == set(rows[0].keys())
    assert rows[0]["mode"] == "next_week"
