"""Visual aircraft-deck and CG-envelope components."""

from __future__ import annotations

from html import escape

import streamlit as st

from engine.csp import AeroLoadCSP
from ui.planning import BayOption, BayOptionStatus


def _cargo_tone(hazard: str) -> str:
    return {
        "None": "general",
        "Food": "food",
        "Lithium Battery": "lithium",
        "Flammable": "flammable",
        "Toxic": "toxic",
        "Biohazard": "toxic",
        "Oxidizer": "warning",
    }.get(hazard, "general")


def render_aircraft_layout(
    csp: AeroLoadCSP,
    assignment: dict[str, str],
    *,
    mode: str = "AUTO",
    selected_cargo_id: str | None = None,
    bay_options: dict[str, BayOption] | None = None,
) -> None:
    """
    Render a two-sided cargo deck supporting Auto, Manual, and AI-Assisted modes.
    Uses native st.html to prevent Markdown parsing quirks.
    """
    bay_to_cargo = {bay_id: cargo_id for cargo_id, bay_id in assignment.items()}
    side_order = {"Left": 0, "Center": 1, "Right": 2}
    bays = sorted(
        csp.aircraft.bays,
        key=lambda b: (b.row, side_order.get(b.side.value, 9)),
    )
    cards_by_row: dict[int, list[str]] = {}

    for bay in bays:
        cargo_id = bay_to_cargo.get(bay.bay_id)

        # -------------------------------------------------------------
        # Unoccupied Bay
        # -------------------------------------------------------------
        if cargo_id is None:
            if mode == "AI_ASSISTED" and bay_options and bay.bay_id in bay_options:
                opt = bay_options[bay.bay_id]
                if opt.status == BayOptionStatus.LEGAL:
                    card = (
                        f"<article class='deck-bay is-empty bay-legal'>"
                        f"<header><span>{escape(bay.bay_id)}</span><i>{escape(bay.side.value)}</i></header>"
                        f"<strong>Available</strong>"
                        f"<small>{bay.longitudinal_arm_m:+.1f} m arm · {bay.max_weight_kg:.0f} kg capacity</small>"
                        f"<span class='bay-guidance-badge guidance-legal'>✓ LEGAL CHOICE</span>"
                        f"</article>"
                    )
                elif opt.status == BayOptionStatus.ILLEGAL:
                    card = (
                        f"<article class='deck-bay is-empty bay-illegal'>"
                        f"<header><span>{escape(bay.bay_id)}</span><i>{escape(bay.side.value)}</i></header>"
                        f"<strong>Blocked</strong>"
                        f"<small>{escape(opt.reason)}</small>"
                        f"<span class='bay-guidance-badge guidance-illegal'>✕ INCOMPATIBLE</span>"
                        f"</article>"
                    )
                else:
                    card = (
                        f"<article class='deck-bay is-empty bay-occupied'>"
                        f"<header><span>{escape(bay.bay_id)}</span><i>{escape(bay.side.value)}</i></header>"
                        f"<strong>Occupied</strong>"
                        f"<small>{escape(opt.reason)}</small>"
                        f"<span class='bay-guidance-badge guidance-occupied'>OCCUPIED</span>"
                        f"</article>"
                    )
            else:
                card = (
                    f"<article class='deck-bay is-empty'>"
                    f"<header><span>{escape(bay.bay_id)}</span><i>{escape(bay.side.value)}</i></header>"
                    f"<strong>Available</strong>"
                    f"<small>{bay.longitudinal_arm_m:+.1f} m arm · {bay.max_weight_kg:.0f} kg capacity</small>"
                    f"</article>"
                )
            cards_by_row.setdefault(bay.row, []).append(card)
            continue

        # -------------------------------------------------------------
        # Occupied Bay
        # -------------------------------------------------------------
        cargo = csp.get_cargo(cargo_id)
        utilization = cargo.weight_kg / bay.max_weight_kg * 100

        if mode == "AI_ASSISTED" and selected_cargo_id == cargo_id:
            card = (
                f"<article class='deck-bay bay-assigned-current bay-{_cargo_tone(cargo.hazard_class.value)}'>"
                f"<header><span>{escape(bay.bay_id)}</span><i>{escape(bay.side.value)}</i></header>"
                f"<strong>{escape(cargo.cargo_id)}</strong><span>{escape(cargo.name)}</span>"
                f"<small>{cargo.weight_kg:.0f} kg · {utilization:.0f}% bay use</small>"
                f"<span class='bay-guidance-badge guidance-legal'>CURRENT ASSIGNMENT</span>"
                f"<em>{escape(cargo.hazard_class.value)}</em>"
                f"</article>"
            )
        elif mode == "AI_ASSISTED" and selected_cargo_id:
            card = (
                f"<article class='deck-bay bay-occupied bay-{_cargo_tone(cargo.hazard_class.value)}'>"
                f"<header><span>{escape(bay.bay_id)}</span><i>{escape(bay.side.value)}</i></header>"
                f"<strong>{escape(cargo.cargo_id)}</strong><span>{escape(cargo.name)}</span>"
                f"<small>{cargo.weight_kg:.0f} kg · {utilization:.0f}% bay use</small>"
                f"<span class='bay-guidance-badge guidance-occupied'>Occupied by {escape(cargo.cargo_id)}</span>"
                f"<em>{escape(cargo.hazard_class.value)}</em>"
                f"</article>"
            )
        else:
            card = (
                f"<article class='deck-bay bay-{_cargo_tone(cargo.hazard_class.value)}'>"
                f"<header><span>{escape(bay.bay_id)}</span><i>{escape(bay.side.value)}</i></header>"
                f"<strong>{escape(cargo.cargo_id)}</strong><span>{escape(cargo.name)}</span>"
                f"<small>{cargo.weight_kg:.0f} kg · {utilization:.0f}% bay use</small>"
                f"<em>{escape(cargo.hazard_class.value)}</em>"
                f"</article>"
            )
        cards_by_row.setdefault(bay.row, []).append(card)

    deck_rows = "".join(
        f"<section class='deck-row'><div class='deck-row-label'>ROW {row}</div>"
        f"<div class='deck-row-bays'>{''.join(cards_by_row[row])}</div></section>"
        for row in sorted(cards_by_row)
    )

    if mode == "AUTO":
        eyebrow = "Live placement map · Auto Solver Plan"
    elif mode == "MANUAL":
        eyebrow = "Interactive Deck · Manual Placement"
    else:
        if selected_cargo_id:
            eyebrow = f"AI-Assisted Domain Guidance · Candidate Bays for {escape(selected_cargo_id)}"
        else:
            eyebrow = "AI-Assisted Planning · Select Cargo to Inspect CSP Domain"

    legend_html = (
        "<div class='deck-legend'>"
        "<span class='legend-general'></span>General "
        "<span class='legend-warning'></span>Controlled "
        "<span class='legend-danger'></span>Hazardous"
        "</div>"
    )
    if mode == "AI_ASSISTED":
        legend_html = (
            "<div class='deck-legend'>"
            "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#22c55e;margin:0 4px 0 10px;'></span>Legal "
            "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#ef4444;margin:0 4px 0 10px;'></span>Blocked "
            "<span style='display:inline-block;width:8px;height:8px;border-radius:50%;background:#64748b;margin:0 4px 0 10px;'></span>Occupied"
            "</div>"
        )

    st.html(
        "<section class='deck-shell'>"
        f"<div class='deck-heading'><div><div class='eyebrow'>{eyebrow}</div>"
        f"<h3>{escape(csp.aircraft.name)} cargo deck</h3></div>{legend_html}</div>"
        "<div class='direction forward'><svg viewBox='0 0 24 24' aria-hidden='true'><path d='m12 4 6 8h-4v8h-4v-8H6z'/></svg>Forward</div>"
        "<div class='fuselage'><div class='centerline'></div>"
        f"<div class='deck-grid'>{deck_rows}</div></div>"
        "<div class='direction'><svg class='direction-aft' viewBox='0 0 24 24' aria-hidden='true'><path d='m12 4 6 8h-4v8h-4v-8H6z'/></svg>Aft</div>"
        "</section>"
    )


def render_cg_envelope(
    cg_m: float,
    cg_min_m: float,
    cg_max_m: float,
    target_m: float,
) -> None:
    """Render CG position within its operating envelope."""
    span = max(cg_max_m - cg_min_m, 0.001)
    marker = min(100, max(0, (cg_m - cg_min_m) / span * 100))
    target = min(100, max(0, (target_m - cg_min_m) / span * 100))
    status = "Within envelope" if cg_min_m <= cg_m <= cg_max_m else "Outside envelope"
    tone = "safe" if status == "Within envelope" else "danger"
    st.html(
        "<section class='cg-card'><div class='cg-heading'><div><div class='eyebrow'>Longitudinal stability</div><h3>CG envelope</h3></div>"
        f"<div class='cg-reading cg-{tone}'>{cg_m:+.3f} m <span>{status}</span></div></div><div class='cg-scale'><div class='cg-safe-band'></div>"
        f"<div class='cg-target' style='left:{target:.2f}%'><i></i><span>Target</span></div><div class='cg-marker cg-{tone}' style='left:{marker:.2f}%'><i></i><span>Current</span></div></div>"
        f"<div class='cg-labels'><span>{cg_min_m:+.1f} m limit</span><span>{target_m:+.1f} m target</span><span>{cg_max_m:+.1f} m limit</span></div></section>"
    )
