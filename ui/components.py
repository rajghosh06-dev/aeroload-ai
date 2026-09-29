"""Presentation components for AeroLoad-AI light engineering interface."""

from __future__ import annotations

from html import escape

import streamlit as st

PLANE_SVG = """<svg class='brand-plane' viewBox='0 0 64 64' aria-hidden='true'><path d='M56 31 38 27 29 10h-6l4 17-15 3-5-5H3l4 8-4 8h4l5-5 15 3-4 17h6l9-17 18-4c3-1 3-4 0-5Z'/></svg>"""


def render_brand() -> None:
    """Render clean, unadorned header brand in dark graphite."""
    st.html(
        "<div class='top-brand'>"
        f"{PLANE_SVG}<div>"
        "<h1>AeroLoad-AI</h1>"
        "<p>Aircraft cargo weight & balance planning</p>"
        "</div></div>"
    )


def render_brand_and_aircraft(name: str, aircraft_id: str, bays: int) -> None:
    """Render brand and aircraft identity together in a single clean toolbar row."""
    st.html(
        "<div class='header-left-bar'>"
        "<div class='top-brand'>"
        f"{PLANE_SVG}<div>"
        "<h1>AeroLoad-AI</h1>"
        "<p>Aircraft cargo weight & balance planning</p>"
        "</div></div>"
        "<div class='header-pipe'></div>"
        "<div class='header-aircraft'>"
        "<span class='header-aircraft-label'>Aircraft</span>"
        f"<span class='header-aircraft-value'><strong>{escape(name)}</strong> · {escape(aircraft_id)} · {bays} bays</span>"
        "</div>"
        "</div>"
    )


def render_aircraft_status(name: str, aircraft_id: str, bays: int) -> None:
    """Render compact, structured aircraft identity."""
    st.html(
        "<div class='header-aircraft'>"
        "<span class='header-aircraft-label'>Aircraft</span>"
        f"<span class='header-aircraft-value'><strong>{escape(name)}</strong> · {escape(aircraft_id)} · {bays} bays</span>"
        "</div>"
    )


def render_kpi_strip(
    *,
    item_count: int,
    bay_count: int,
    payload_kg: float,
    max_payload_kg: float,
    target_cg_m: float,
    cg_min_m: float,
    cg_max_m: float,
    analysis_current: bool,
    has_violations: bool = False,
    status_note: str | None = None,
) -> None:
    """Render ONE horizontal summary strip without individual cards."""
    free_bays = max(0, bay_count - item_count)
    remaining = max_payload_kg - payload_kg
    utilization = (payload_kg / max_payload_kg * 100) if max_payload_kg else 0

    if status_note:
        note_text = escape(status_note)
        dot_class = "dot-danger" if has_violations else ("dot-safe" if analysis_current else "dot-warning")
    elif not analysis_current:
        dot_class = "dot-warning"
        note_text = "Inputs changed — generate a plan to update results" if item_count > 0 else "No cargo items loaded"
    elif has_violations:
        dot_class = "dot-danger"
        note_text = "Plan has violations · see details below"
    else:
        dot_class = "dot-safe"
        note_text = "Plan valid · CG within limits"

    remaining_note = "Within limit" if remaining >= 0 else "Limit exceeded"

    st.html(
        "<section class='summary-strip' aria-label='Operational summary metrics'>"
        f"<div class='summary-col'><span class='summary-label'>Cargo</span>"
        f"<span class='summary-value'>{item_count} items</span>"
        f"<span class='summary-sub'>{free_bays} bays available</span></div>"
        f"<div class='summary-col'><span class='summary-label'>Payload</span>"
        f"<span class='summary-value'>{payload_kg:,.0f} / {max_payload_kg:,.0f} kg</span>"
        f"<span class='summary-sub'>{utilization:.0f}% capacity</span></div>"
        f"<div class='summary-col'><span class='summary-label'>Remaining</span>"
        f"<span class='summary-value'>{remaining:,.0f} kg</span>"
        f"<span class='summary-sub'>{remaining_note}</span></div>"
        f"<div class='summary-col'><span class='summary-label'>Target CG</span>"
        f"<span class='summary-value'>{target_cg_m:+.2f} m</span>"
        f"<span class='summary-sub'>{cg_min_m:+.1f} to {cg_max_m:+.1f} m envelope</span></div>"
        "</section>"
        f"<div class='summary-status-line'><span class='status-dot {dot_class}'></span>"
        f"<span>{note_text}</span></div>"
    )


def render_workflow_indicator(current_step: int) -> None:
    """Render plain breadcrumb-like workflow progress without boxes."""
    steps = [
        (1, "Scenario"),
        (2, "Planning mode"),
        (3, "Build plan"),
        (4, "Results"),
    ]
    step_items = []
    for step_num, label in steps:
        if step_num < current_step:
            step_class = "is-completed"
        elif step_num == current_step:
            step_class = "is-active"
        else:
            step_class = "is-future"
        step_items.append(f"<span class='workflow-step-text {step_class}'>{escape(label)}</span>")

    separator = "<span class='workflow-sep'>&gt;</span>"
    bar_html = separator.join(step_items)
    st.html(f"<nav class='workflow-progress' aria-label='Workflow progress'>{bar_html}</nav>")


def render_status_pill(label: str, status: str) -> None:
    """Render a subtle status indicator."""
    status_lower = status.lower()
    tone = "safe" if status_lower in {"safe", "pass", "optimized", "solved", "ready", "ok"} else (
        "warning" if status_lower in {"warning", "tradeoff", "unchanged", "draft", "incomplete"} else "danger"
    )
    st.html(
        f"<span class='status-pill status-{tone}'><span>{escape(label)}</span>"
        f"<b>{escape(status).upper()}</b></span>"
    )


def render_info_banner(message: str) -> None:
    """Render a neutral workflow notification replacing bright blue alerts."""
    st.html(f"<div class='info-banner'>{escape(message)}</div>")
