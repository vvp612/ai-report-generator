"""Digest Studio — notes → LLM analysis → branded .pptx digest (Streamlit UI).

Run:  streamlit run app.py
Logic lives in core/ (fully unit-tested with MockLLM); this file is forms + calls.
"""
from __future__ import annotations

import time

import streamlit as st

from core import deck, modes, usage
from core.auth import authenticate
from core.db import init_db
from core.llm import LLMError, MockLLM, get_llm
from core.modes import ModeError

st.set_page_config(page_title="Digest Studio", page_icon="📊", layout="wide")
init_db()

MODE_LABELS = {
    "weekly_summary": "Weekly summary",
    "risk_flags": "Risk flags",
    "next_week": "Next week",
}
SAMPLE = (
    "Shipped the checkout retry fix; p95 latency down 40ms. Migrated jobs to the new "
    "queue — one backfill incident on Thursday, recovered in 30 minutes. Design review "
    "for mobile onboarding done; API contract for v2 still open. Next: load test the "
    "search cluster before Friday's campaign."
)


def login_view() -> None:
    st.title("📊 Digest Studio")
    st.caption("Turn raw team notes into a slide-ready weekly digest.")
    with st.form("login"):
        username = st.text_input("Username", autocomplete="username")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Sign in", type="primary"):
            if authenticate(username, password):
                st.session_state.user = username
                st.rerun()
            else:
                st.error("Invalid username or password")
    st.caption("First run? The demo admin is `admin / demo1234`.")


def main_view() -> None:
    llm = get_llm()
    with st.sidebar:
        st.markdown(f"Signed in as **{st.session_state.user}**")
        st.caption("Model: `MockLLM` (offline demo)" if isinstance(llm, MockLLM) else "Model: Claude (Anthropic API)")
        if st.button("Sign out"):
            st.session_state.clear()
            st.rerun()

    st.title("📊 Digest Studio")
    mode = st.selectbox("Analysis mode", list(modes.MODES), format_func=MODE_LABELS.get)
    period = st.text_input("Period label", "week of 27 Oct 2026")
    notes = st.text_area("Raw notes (standup, incidents, releases…)", height=240, placeholder=SAMPLE)

    if st.button("Generate digest", type="primary", disabled=not notes.strip()):
        started = time.perf_counter()
        try:
            digest = modes.generate(llm, mode, notes, period)
        except (ModeError, LLMError) as exc:
            st.error(str(exc))
            return
        pptx = deck.build_deck(digest)
        usage.log_generation(st.session_state.user, mode, len(notes), len(pptx), int((time.perf_counter() - started) * 1000))

        st.subheader(digest["title"])
        for section in digest["sections"]:
            st.markdown(f"**{section['heading']}**")
            for bullet in section["bullets"]:
                st.markdown(f"- {bullet}")
        st.download_button(
            f"Download .pptx ({len(pptx) // 1024} KB)",
            pptx,
            file_name=f"digest-{mode}.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            type="primary",
        )

    # Rendered last so the log already includes the generation of this run.
    with st.sidebar:
        st.divider()
        st.subheader("Usage log")
        rows = usage.generations()
        st.dataframe(rows[:8], use_container_width=True, hide_index=True)
        if rows:
            st.download_button("Download CSV", usage.csv_report().encode(), "usage.csv", "text/csv")


if "user" in st.session_state:
    main_view()
else:
    login_view()
