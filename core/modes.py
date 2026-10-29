"""Three analysis modes over one strict JSON contract.

Every mode asks the LLM for the same shape (title, period, sections[]), so the deck
builder and the UI never branch on mode. The parser is the trust boundary: it strips
markdown fences Claude sometimes adds, and rejects anything that isn't valid.
"""
from __future__ import annotations

import json
import re


class ModeError(ValueError):
    pass


MODES = {
    "weekly_summary": "Summarise the notes into a neutral weekly digest of what shipped and what is in flight.",
    "risk_flags": "Extract only risks, incidents and blockers, each phrased as a watch-out with impact.",
    "next_week": "Turn the notes into a forward-looking plan of concrete next-week priorities.",
}

_CONTRACT = (
    "Return ONLY JSON of the form "
    '{"title": str, "period": str, "sections": [{"heading": str, "bullets": [str, ...]}, ...]}. '
    "3-5 sections, 2-5 concise bullets each, no markdown, no commentary."
)


def _system(mode: str) -> str:
    if mode not in MODES:
        raise ModeError(f"unknown mode: {mode}")
    # [mode:<name>] marker lets MockLLM reproduce mode-specific behaviour offline.
    return f"You build slide digests. [mode:{mode}] {MODES[mode]} {_CONTRACT}"


def generate(llm, mode: str, notes: str, period: str = "this week") -> dict:
    notes = notes.strip()
    if len(notes) < 20:
        raise ModeError("notes are too short to summarise")
    raw = llm.complete(_system(mode), f"Period: {period}\n\nNotes:\n{notes}")
    digest = parse(raw)
    digest["mode"] = mode
    return digest


def parse(raw: str) -> dict:
    """Validate the model output into the digest shape (tolerating code fences)."""
    text = re.sub(r"^```(?:json)?|```$", "", raw.strip(), flags=re.MULTILINE).strip()
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ModeError(f"model did not return JSON: {exc}") from exc

    if not isinstance(data, dict) or not isinstance(data.get("sections"), list) or not data["sections"]:
        raise ModeError("output missing a non-empty 'sections' list")
    for section in data["sections"]:
        if not isinstance(section, dict) or not section.get("heading") or not isinstance(section.get("bullets"), list):
            raise ModeError("every section needs a heading and a bullets list")
    data["title"] = str(data.get("title") or "Untitled digest")
    data["period"] = str(data.get("period") or "this week")
    return data
