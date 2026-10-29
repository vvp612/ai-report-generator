import pytest
from core.llm import MockLLM
from core.modes import MODES, ModeError, generate, parse

NOTES = "Shipped checkout retry fix. Queue migration had a 30-minute incident on Thursday. Search load test planned for Friday."


@pytest.mark.parametrize("mode", list(MODES))
def test_every_mode_round_trips_through_mock_llm(mode):
    digest = generate(MockLLM(), mode, NOTES)
    assert digest["mode"] == mode
    assert digest["title"]
    assert digest["sections"], "digest must have sections"
    assert all(s["bullets"] for s in digest["sections"])


def test_mock_reproduces_mode_in_content():
    digest = generate(MockLLM(), "risk_flags", NOTES)
    assert "risk_flags" in digest["sections"][0]["bullets"][0]


def test_short_notes_rejected():
    with pytest.raises(ModeError):
        generate(MockLLM(), "weekly_summary", "too short")


def test_parse_tolerates_markdown_fences():
    raw = '```json\n{"title": "T", "period": "p", "sections": [{"heading": "H", "bullets": ["b"]}]}\n```'
    assert parse(raw)["sections"][0]["heading"] == "H"


def test_parse_rejects_non_json():
    with pytest.raises(ModeError):
        parse("Sorry, here is your summary in prose…")


def test_parse_rejects_sections_without_bullets():
    with pytest.raises(ModeError):
        parse('{"title": "T", "sections": [{"heading": "H"}]}')
