"""Presentation viewer component for AeroLoad-AI academic slides."""

from __future__ import annotations

import re
from pathlib import Path

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SLIDES_DIR = PROJECT_ROOT / "docs" / "slides"

SLIDE_TITLES: dict[int, str] = {
    1: "AeroLoad-AI / Title",
    2: "Introduction & Motivation",
    3: "Objectives & Problem Statement",
    4: "Implementation Overview",
    5: "Code Description — Physics & Balance",
    6: "Code Description — AI Search Engine",
    7: "Application Screenshots — Operations",
    8: "Application Screenshots — Solver & Analysis",
    9: "Technical Challenges & Solutions",
    10: "Real-World Aviation Applications",
    11: "Future Enhancements",
    12: "Conclusion & Key Takeaways",
    13: "Thank You & Q&A",
}


def _extract_slide_number(path: Path) -> int:
    """Extract numeric index from slide filename, e.g. 'slide10.png' -> 10."""
    match = re.search(r"\d+", path.stem)
    return int(match.group()) if match else 999


def discover_slides() -> list[Path]:
    """Discover and return all slide image paths sorted numerically.

    Ensures natural numeric ordering: slide1, slide2, ..., slide9, slide10, slide11, ...
    """
    if not SLIDES_DIR.is_dir():
        return []
    slides = [p for p in SLIDES_DIR.glob("*.png") if p.is_file()]
    slides.sort(key=_extract_slide_number)
    return slides


def render_presentation_viewer() -> None:
    """Render a clean, responsive academic slide viewer."""
    slides = discover_slides()

    if not slides:
        st.markdown(
            "<div class='info-banner'>No presentation slides found in <code>docs/slides/</code>. "
            "Please ensure PNG slide files are placed in the presentation directory.</div>",
            unsafe_allow_html=True,
        )
        return

    total_slides = len(slides)
    if "persisted_presentation_slide_idx" not in st.session_state:
        st.session_state["persisted_presentation_slide_idx"] = 0
    elif not isinstance(st.session_state["persisted_presentation_slide_idx"], int) or not (0 <= st.session_state["persisted_presentation_slide_idx"] < total_slides):
        st.session_state["persisted_presentation_slide_idx"] = 0

    # Restore widget state from persistent store if widget was unmounted
    if "presentation_slide_idx" not in st.session_state:
        st.session_state["presentation_slide_idx"] = st.session_state["persisted_presentation_slide_idx"]

    current_idx = st.session_state["presentation_slide_idx"]
    current_slide_path = slides[current_idx]
    slide_num = _extract_slide_number(current_slide_path)
    slide_title = SLIDE_TITLES.get(slide_num, f"Slide {slide_num}")

    # Slide metadata header
    st.markdown(
        f"<div class='presentation-header'>"
        f"<div class='presentation-counter'>Slide {current_idx + 1} of {total_slides}</div>"
        f"<div class='presentation-title'>{slide_title}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    # Full-width 16:9 slide image using modern non-deprecated API
    st.image(str(current_slide_path), width="stretch")

    # Navigation controls row: [ Previous ] [ Jump to slide dropdown ] [ Next ]
    st.markdown("<div class='presentation-nav-wrapper'>", unsafe_allow_html=True)
    prev_col, select_col, next_col = st.columns([1.2, 2.6, 1.2], vertical_alignment="center")

    def _previous_slide() -> None:
        idx = st.session_state.get("presentation_slide_idx", 0)
        new_idx = max(0, idx - 1)
        st.session_state["presentation_slide_idx"] = new_idx
        st.session_state["persisted_presentation_slide_idx"] = new_idx

    def _next_slide() -> None:
        idx = st.session_state.get("presentation_slide_idx", 0)
        new_idx = min(total_slides - 1, idx + 1)
        st.session_state["presentation_slide_idx"] = new_idx
        st.session_state["persisted_presentation_slide_idx"] = new_idx

    def _on_slide_change() -> None:
        st.session_state["persisted_presentation_slide_idx"] = st.session_state.get("presentation_slide_idx", 0)

    with prev_col:
        st.button(
            "← Previous",
            disabled=(current_idx <= 0),
            width="stretch",
            key="btn_prev_slide",
            on_click=_previous_slide,
        )

    with select_col:
        slide_indices = list(range(total_slides))
        st.selectbox(
            "Jump to slide",
            options=slide_indices,
            format_func=lambda i: f"{i + 1}. {SLIDE_TITLES.get(_extract_slide_number(slides[i]), f'Slide {i + 1}')}",
            key="presentation_slide_idx",
            label_visibility="collapsed",
            on_change=_on_slide_change,
        )

    with next_col:
        st.button(
            "Next →",
            disabled=(current_idx >= total_slides - 1),
            width="stretch",
            key="btn_next_slide",
            on_click=_next_slide,
        )

    st.markdown("</div>", unsafe_allow_html=True)
