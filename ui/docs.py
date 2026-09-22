"""In-app documentation browser with modular topic navigation."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs"

DOCUMENTATION_TOPICS: list[tuple[str, str, str]] = [
    ("getting-started.md", "Getting Started", "What AeroLoad-AI does & the 4-step workflow"),
    ("aircraft-concepts.md", "Aircraft Concepts", "Weight, arm, moment, CG & balance formulas"),
    ("ai-concepts.md", "AI Concepts", "CSP, AC-3, MRV, LCV & Hill Climbing"),
    ("planning-modes.md", "Planning Modes", "Auto Solve, Manual & AI-Assisted guidance"),
    ("knowledge-base.md", "Knowledge Base", "Simplified hazard rules & frozenset reasoning"),
    ("architecture.md", "Architecture", "System data flow & module map"),
    ("testing.md", "Testing", "Pytest suite & verification coverage"),
    ("limitations.md", "Limitations", "Academic scope & modeling simplifications"),
]


def render_docs_page(on_close: Callable[[], None]) -> None:
    """Render a clean, modular documentation browser with topic navigation."""
    header_col, close_col = st.columns([4, 1], vertical_alignment="center")
    with header_col:
        st.markdown("## Documentation & Academic Notes")
        st.caption("Select a topic below to read concise guidance without leaving the application.")
    with close_col:
        if st.button("Back to dashboard", icon=":material/arrow_back:", use_container_width=True, type="primary"):
            on_close()
            st.rerun()

    topic_titles = [title for _, title, _ in DOCUMENTATION_TOPICS]
    selected_idx = st.session_state.get("selected_doc_topic_idx", 0)

    nav_col, content_col = st.columns([1.1, 2.9], gap="large")

    with nav_col:
        st.markdown("#### Topics")
        selected_title = st.radio(
            "Select topic",
            topic_titles,
            index=selected_idx if 0 <= selected_idx < len(topic_titles) else 0,
            label_visibility="collapsed",
            key="doc_topic_radio",
        )
        selected_idx = topic_titles.index(selected_title)
        st.session_state["selected_doc_topic_idx"] = selected_idx

        filename, title, subtitle = DOCUMENTATION_TOPICS[selected_idx]
        st.caption(f"**{title}**: {subtitle}")

    with content_col:
        filename = DOCUMENTATION_TOPICS[selected_idx][0]
        file_path = DOCS_ROOT / filename
        if file_path.is_file():
            with st.container(border=True):
                st.markdown(file_path.read_text(encoding="utf-8"))
        else:
            st.info(f"Documentation file `{filename}` is not available.")
