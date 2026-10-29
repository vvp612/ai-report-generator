"""LLM layer: one tiny interface, two providers.

`MockLLM` keeps the whole app testable and demoable without an API key —
`get_llm()` falls back to it when `ANTHROPIC_API_KEY` is unset.
"""
from __future__ import annotations

import json
import os


class LLMError(RuntimeError):
    pass


class MockLLM:
    """Deterministic offline stand-in. Modes are detected from the system prompt
    marker (`[mode:<name>]`) so mode logic can be exercised without the network."""

    def complete(self, system: str, prompt: str) -> str:
        mode = "weekly_summary"
        for token in system.split():
            if token.startswith("[mode:") and token.endswith("]"):
                mode = token[6:-1]
        words = len(prompt.split())
        bullets = [
            f"[{mode}] shipped {min(words, 3)} key initiatives from the notes",
            f"[{mode}] reviewed {max(words // 2, 1)} reported items",
            "[mock] deterministic output — set ANTHROPIC_API_KEY for live Claude",
        ]
        return json.dumps({
            "title": f"{mode.replace('_', ' ').title()} (mock)",
            "period": "this week",
            "sections": [
                {"heading": "Highlights", "bullets": bullets[:2]},
                {"heading": "Watch-outs", "bullets": bullets[2:]},
            ],
        })


class AnthropicLLM:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        from anthropic import Anthropic  # imported lazily so mock mode needs no dep

        self.client = Anthropic(api_key=api_key)
        self.model = model or os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5")

    def complete(self, system: str, prompt: str) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system,
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:  # surface provider errors as ours
            raise LLMError(f"Anthropic call failed: {exc}") from exc
        return "".join(block.text for block in response.content if block.type == "text")


def get_llm(prefer: str | None = None):
    """Provider selection: explicit `prefer` ('mock'|'anthropic'), else
    REPORT_LLM env, else anthropic when a key exists, else mock."""
    choice = prefer or os.environ.get("REPORT_LLM", "")
    if choice == "mock":
        return MockLLM()
    if choice == "anthropic" or os.environ.get("ANTHROPIC_API_KEY"):
        return AnthropicLLM()
    return MockLLM()
