"""Plotly figures for aircraft weight-and-balance telemetry."""

from __future__ import annotations

import plotly.graph_objects as go

PLOT_LAYOUT = {"paper_bgcolor": "rgba(0,0,0,0)", "plot_bgcolor": "rgba(0,0,0,0)",
               "font": {"color": "#cbd5e1"}, "margin": {"l": 34, "r": 24, "t": 42, "b": 36}}


def cg_envelope_figure(*, cg_min_m: float, cg_max_m: float, target_m: float,
                       initial_m: float | None, final_m: float | None) -> go.Figure:
    """Show allowable CG range plus target, initial, and final positions."""
    span = cg_max_m - cg_min_m
    padding = max(span * 0.18, 0.2)
    figure = go.Figure()
    figure.add_shape(type="rect", x0=cg_min_m, x1=cg_max_m, y0=-0.16, y1=0.16,
                     fillcolor="rgba(34,197,94,0.20)",
                     line={"color": "rgba(34,197,94,0.65)", "width": 1})
    figure.add_vline(x=target_m, line={"color": "#f59e0b", "width": 2, "dash": "dot"},
                     annotation_text="Target", annotation_position="top")
    points: list[tuple[str, float, str, str]] = []
    if initial_m is not None:
        points.append(("Initial", initial_m, "#94a3b8", "diamond"))
    if final_m is not None:
        points.append(("Final", final_m, "#38bdf8", "circle"))
    for label, value, color, symbol in points:
        figure.add_trace(go.Scatter(
            x=[value], y=[0], mode="markers+text", name=label,
            text=[f"{label} {value:+.3f} m"],
            textposition="bottom center" if label == "Initial" else "top center",
            marker={"size": 15, "color": color, "symbol": symbol},
            hovertemplate=f"{label}: %{{x:+.3f}} m<extra></extra>",
        ))
    figure.update_layout(
        **PLOT_LAYOUT, title={"text": "Longitudinal CG envelope", "font": {"size": 15}},
        height=245, showlegend=False,
        xaxis={"title": "Longitudinal arm (m)", "range": [cg_min_m - padding, cg_max_m + padding],
               "gridcolor": "rgba(148,163,184,0.12)", "zeroline": False},
        yaxis={"visible": False, "range": [-0.45, 0.45]},
    )
    return figure


def lateral_balance_figure(*, left_kg: float, right_kg: float, limit_kg: float) -> go.Figure:
    """Compare left/right payload and report absolute imbalance."""
    imbalance = abs(left_kg - right_kg)
    safe = imbalance <= limit_kg
    figure = go.Figure(go.Bar(
        x=[left_kg, right_kg], y=["Left", "Right"], orientation="h",
        marker_color=["#38bdf8", "#60a5fa"],
        text=[f"{left_kg:,.0f} kg", f"{right_kg:,.0f} kg"], textposition="auto",
        hovertemplate="%{y}: %{x:,.0f} kg<extra></extra>",
    ))
    figure.update_layout(
        **PLOT_LAYOUT,
        title={"text": f"Lateral balance · {imbalance:,.0f} kg imbalance ({'SAFE' if safe else 'LIMIT EXCEEDED'})",
               "font": {"size": 15, "color": "#86efac" if safe else "#fca5a5"}},
        height=245, showlegend=False,
        xaxis={"title": "Assigned payload (kg)", "gridcolor": "rgba(148,163,184,0.12)"},
        yaxis={"autorange": "reversed"},
    )
    return figure
