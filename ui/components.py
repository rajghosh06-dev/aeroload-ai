"""Small, reusable presentation components for AeroLoad-AI."""

from __future__ import annotations

from html import escape

import streamlit as st

PLANE_SVG = """<svg class='brand-plane' viewBox='0 0 64 64' aria-hidden='true'><path d='M56 31 38 27 29 10h-6l4 17-15 3-5-5H3l4 8-4 8h4l5-5 15 3-4 17h6l9-17 18-4c3-1 3-4 0-5Z'/></svg>"""


def render_brand() -> None:
    """Render the left side of the native top header."""
    st.html(
        "<div class='top-brand'>"
        f"{PLANE_SVG}<div><div class='eyebrow'><span class='signal-dot'></span>AI Cargo Load Simulation</div>"
        "<h1>AeroLoad<span>-AI</span></h1><p>Academic Cargo Weight, Balance & Hazmat Planning</p>"
        "</div></div>"
    )


def render_aircraft_status(name: str, aircraft_id: str, bays: int) -> None:
    """Render compact aircraft identity in the center of the header."""
    st.html(
        "<div class='header-aircraft'><small>SELECTED AIRCRAFT</small>"
        f"<strong>{escape(name)}</strong><span>{escape(aircraft_id)} · {bays} bays</span></div>"
    )


def render_kpi_strip(
    *, item_count: int, bay_count: int, payload_kg: float, max_payload_kg: float,
    target_cg_m: float, cg_min_m: float, cg_max_m: float, analysis_current: bool,
) -> None:
    """Render five equal operational tiles with predictable internal alignment."""
    free_bays = bay_count - item_count
    remaining = max_payload_kg - payload_kg
    utilization = payload_kg / max_payload_kg * 100 if max_payload_kg else 0
    analysis_value = "UP TO DATE" if analysis_current else "INPUTS CHANGED"
    analysis_note = "Results match current inputs" if analysis_current else "Run solver to analyze"
    analysis_tone = "safe" if analysis_current else "warning"
    st.html(
        "<section class='kpi-grid' aria-label='Current scenario summary'>"
        f"<article class='kpi-tile'><span>Manifest</span><strong>{item_count} items</strong>"
        f"<small class='tone-info'>{free_bays} bays available</small></article>"
        f"<article class='kpi-tile'><span>Payload</span><strong>{payload_kg:,.0f} kg</strong>"
        f"<small>{utilization:.0f}% of {max_payload_kg:,.0f} kg limit</small></article>"
        f"<article class='kpi-tile'><span>Remaining</span><strong>{remaining:,.0f} kg</strong>"
        f"<small class='tone-{'safe' if remaining >= 0 else 'danger'}'>{'Within limit' if remaining >= 0 else 'Limit exceeded'}</small></article>"
        f"<article class='kpi-tile'><span>Target CG</span><strong>{target_cg_m:+.2f} m</strong>"
        f"<small>{cg_min_m:+.1f} to {cg_max_m:+.1f} m envelope</small></article>"
        f"<article class='kpi-tile kpi-analysis'><span>Analysis Status</span><strong>{analysis_value}</strong>"
        f"<small class='tone-{analysis_tone}'>{analysis_note}</small></article>"
        "</section>"
    )


def render_status_pill(label: str, status: str) -> None:
    """Render one concise native-HTML status indicator."""
    status_lower = status.lower()
    tone = "safe" if status_lower in {"safe", "pass", "optimized", "solved", "ready"} else (
        "warning" if status_lower in {"warning", "tradeoff", "unchanged", "draft"} else "danger"
    )
    st.html(
        f"<div class='status-pill status-{tone}'><span>{escape(label)}</span>"
        f"<b>{escape(status).upper()}</b></div>"
    )


def render_workflow_indicator(current_step: int) -> None:
    """Render a compact visual 4-step workflow indicator."""
    steps = [
        ("1", "Prepare Scenario"),
        ("2", "Choose Mode"),
        ("3", "Plan Cargo"),
        ("4", "Review Results"),
    ]
    step_html = []
    for num, label in steps:
        step_num = int(num)
        if step_num < current_step:
            status_class = "step-completed"
            icon = "✓"
        elif step_num == current_step:
            status_class = "step-active"
            icon = num
        else:
            status_class = "step-pending"
            icon = num
        step_html.append(
            f"<div class='workflow-step {status_class}'>"
            f"<span class='step-badge'>{icon}</span>"
            f"<span class='step-label'>{escape(label)}</span>"
            f"</div>"
        )
    connector = "<span class='workflow-arrow'>→</span>"
    bar = connector.join(step_html)
    st.html(f"<div class='workflow-bar' aria-label='Workflow steps'>{bar}</div>")
