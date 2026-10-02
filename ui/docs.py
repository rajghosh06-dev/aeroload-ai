"""In-app documentation browser with modular technical reading layout and presentation viewer."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import streamlit as st

from ui.presentation import render_presentation_viewer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs"

DOCUMENTATION_TOPICS: list[tuple[str, str, str]] = [
    ("getting-started.md", "Getting Started", "What AeroLoad-AI does & the 4-step workflow"),
    ("aircraft-concepts.md", "Aircraft Concepts", "Weight, arm, moment, CG & balance formulas"),
    ("ai-concepts.md", "AI Concepts", "CSP, AC-3, MRV, LCV & Hill Climbing"),
    ("planning-modes.md", "Planning Modes", "Auto Solve, Manual & AI-Assisted guidance"),
    ("knowledge-base.md", "Knowledge Base", "Simplified hazard rules & frozenset reasoning"),
    ("architecture.md", "Architecture", "System data flow & module map"),
    ("testing.md", "Testing", "Verification methodology & coverage"),
    ("limitations.md", "Limitations", "Academic scope & modeling simplifications"),
    ("presentation", "Presentation", "Academic slide deck & project overview"),
]


def render_docs_page(on_close: Callable[[], None]) -> None:
    """Render a clean, full-width technical reference documentation view with topic selector and pagination."""
    topic_titles = [title for _, title, _ in DOCUMENTATION_TOPICS]

    # Synchronize topic index and selectbox in session_state
    selected_idx = st.session_state.get("selected_doc_topic_idx", 0)
    if not isinstance(selected_idx, int) or not (0 <= selected_idx < len(topic_titles)):
        selected_idx = 0
        st.session_state["selected_doc_topic_idx"] = 0

    if st.session_state.get("doc_topic_select") != topic_titles[selected_idx]:
        st.session_state["doc_topic_select"] = topic_titles[selected_idx]

    def _on_topic_change() -> None:
        val = st.session_state.get("doc_topic_select")
        if val in topic_titles:
            st.session_state["selected_doc_topic_idx"] = topic_titles.index(val)

    # Header Bar: Title on left, compact Topic Selectbox and Back button on right
    with st.container(key="docs_header_bar"):
        header_col, select_col, back_col = st.columns([2.2, 1.8, 1.1], vertical_alignment="bottom")
        with header_col:
            st.markdown("## Help & Documentation")
            st.caption("Reference material for AeroLoad-AI concepts, operation and project implementation.")
        with select_col:
            st.selectbox(
                "Topic",
                topic_titles,
                key="doc_topic_select",
                on_change=_on_topic_change,
            )
        with back_col:
            if st.button("← Back to dashboard", width="stretch", key="docs_back_btn"):
                on_close()
                st.rerun()

    # Re-read current index after possible selectbox change
    selected_idx = st.session_state.get("selected_doc_topic_idx", 0)
    filename, title, subtitle = DOCUMENTATION_TOPICS[selected_idx]

    # Full-width centered technical reading pane (900-1050px)
    with st.container(key="docs_reading_pane"):
        if filename == "presentation":
            render_presentation_viewer()
        else:
            file_path = DOCS_ROOT / filename
            if file_path.is_file():
                raw_text = file_path.read_text(encoding="utf-8")
                # Deduplicate first H1 title from Markdown to maintain clean hierarchy
                lines = raw_text.splitlines()
                if lines and lines[0].strip().startswith("# "):
                    content_body = "\n".join(lines[1:]).lstrip()
                else:
                    content_body = raw_text

                st.markdown(
                    f"<div class='docs-topic-header'>"
                    f"<h2 class='docs-topic-title'>{title}</h2>"
                    f"<p class='docs-topic-subtitle'>{subtitle}</p>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(content_body)
            else:
                st.markdown(
                    f"<div class='info-banner'>Documentation file <code>{filename}</code> is not available.</div>",
                    unsafe_allow_html=True,
                )

        # Pagination row below topic: [ ← Previous topic ] [ x of 9 · Title ] [ Next topic → ]
        st.markdown("<div class='docs-pagination-divider'></div>", unsafe_allow_html=True)
        prev_col, indicator_col, next_col = st.columns([1.2, 2.0, 1.2], vertical_alignment="center")

        with prev_col:
            prev_disabled = selected_idx <= 0
            if st.button("← Previous topic", disabled=prev_disabled, width="stretch", key="docs_prev_btn"):
                new_idx = max(0, selected_idx - 1)
                st.session_state["selected_doc_topic_idx"] = new_idx
                st.rerun()

        with indicator_col:
            st.markdown(
                f"<div class='docs-pagination-indicator'>{selected_idx + 1} of {len(topic_titles)} &nbsp;·&nbsp; {title}</div>",
                unsafe_allow_html=True,
            )

        with next_col:
            next_disabled = selected_idx >= len(topic_titles) - 1
            if st.button("Next topic →", disabled=next_disabled, width="stretch", key="docs_next_btn"):
                new_idx = min(len(topic_titles) - 1, selected_idx + 1)
                st.session_state["selected_doc_topic_idx"] = new_idx
                st.rerun()
