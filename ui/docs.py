"""In-app documentation browser for project Markdown files."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def documentation_files() -> list[Path]:
    """Return README first, followed by Markdown files under ``docs``."""
    files: list[Path] = []
    readme = PROJECT_ROOT / "README.md"
    if readme.is_file():
        files.append(readme)
    docs_root = PROJECT_ROOT / "docs"
    if docs_root.is_dir():
        files.extend(sorted(path for path in docs_root.rglob("*.md") if path.is_file()))
    return files


def render_docs_page(on_close: Callable[[], None]) -> None:
    """Render a restrained documentation workspace."""
    title_col, close_col = st.columns([4, 1], vertical_alignment="center")
    title_col.markdown("## Documentation")
    title_col.caption("Project overview, user guidance and academic notes - available without leaving AeroLoad-AI.")
    if close_col.button("Back to dashboard", icon=":material/arrow_back:", use_container_width=True):
        on_close()
        st.rerun()

    files = documentation_files()
    if not files:
        st.info("No Markdown documentation is available yet.")
        return

    labels = [
        "README | Project overview" if path.name.casefold() == "readme.md"
        else path.relative_to(PROJECT_ROOT).as_posix()
        for path in files
    ]
    nav_col, content_col = st.columns([1, 3], gap="large")
    with nav_col:
        st.markdown("#### Browse")
        selected = st.radio("Documentation section", labels, label_visibility="collapsed")
        st.caption(f"{len(files)} section{'s' if len(files) != 1 else ''} available")
    selected_path = files[labels.index(selected)]
    with content_col:
        with st.container(border=True, key="docs_content"):
            st.markdown(selected_path.read_text(encoding="utf-8"))
