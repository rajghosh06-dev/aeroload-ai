"""Plotly figures for aircraft weight-and-balance results in light theme."""

from __future__ import annotations

import plotly.graph_objects as go

PLOT_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {
        "color": "#5E6761",
        "family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    },
    "margin": {"l": 34, "r": 24, "t": 42, "b": 36},
}


def cg_envelope_figure(
    *,
    cg_min_m: float,
    cg_max_m: float,
    target_m: float,
    initial_m: float | None,
    final_m: float | None,
) -> go.Figure:
    """Show allowable CG range plus target, initial, and final positions."""
    span = cg_max_m - cg_min_m
    padding = max(span * 0.18, 0.2)
    figure = go.Figure()

    # Allowable CG range band
    figure.add_shape(
        type="rect",
        x0=cg_min_m,
        x1=cg_max_m,
        y0=-0.16,
        y1=0.16,
        fillcolor="rgba(49, 92, 75, 0.10)",
        line={"color": "#315C4B", "width": 1},
    )

    # Target line (Signal copper)
    figure.add_vline(
        x=target_m,
        line={"color": "#AD633E", "width": 2, "dash": "dash"},
        annotation_text="Target",
        annotation_position="top",
        annotation_font={"color": "#AD633E", "size": 11},
    )

    points: list[tuple[str, float, str, str]] = []
    if initial_m is not None:
        points.append(("Initial", initial_m, "#808982", "diamond"))
    if final_m is not None:
        points.append(("Final", final_m, "#3E7957", "circle"))

    for label, value, color, symbol in points:
        figure.add_trace(
            go.Scatter(
                x=[value],
                y=[0],
                mode="markers+text",
                name=label,
                text=[f"{label} {value:+.3f} m"],
                textposition="bottom center" if label == "Initial" else "top center",
                textfont={"color": color, "size": 11},
                marker={"size": 12, "color": color, "symbol": symbol},
                hovertemplate=f"{label}: %{{x:+.3f}} m<extra></extra>",
            )
        )

    figure.update_layout(
        **PLOT_LAYOUT,
        title={"text": "Longitudinal CG Envelope", "font": {"size": 13, "color": "#202522"}},
        height=220,
        showlegend=False,
        xaxis={
            "title": "Longitudinal arm (m)",
            "range": [cg_min_m - padding, cg_max_m + padding],
            "gridcolor": "#E2E6E2",
            "zeroline": False,
        },
        yaxis={"visible": False, "range": [-0.45, 0.45]},
    )
    return figure


def lateral_balance_figure(
    *, left_kg: float, right_kg: float, limit_kg: float
) -> go.Figure:
    """Compare left/right payload and report absolute imbalance."""
    imbalance = abs(left_kg - right_kg)
    safe = imbalance <= limit_kg
    figure = go.Figure(
        go.Bar(
            x=[left_kg, right_kg],
            y=["Left", "Right"],
            orientation="h",
            marker_color=["#7D8681", "#315C4B"],
            text=[f"{left_kg:,.0f} kg", f"{right_kg:,.0f} kg"],
            textposition="auto",
            textfont={"color": "#FFFFFF", "size": 11},
            hovertemplate="%{y}: %{x:,.0f} kg<extra></extra>",
        )
    )
    figure.update_layout(
        **PLOT_LAYOUT,
        title={
            "text": f"Lateral Balance · {imbalance:,.0f} kg Imbalance ({'Within limit' if safe else 'Limit exceeded'})",
            "font": {"size": 13, "color": "#3E7957" if safe else "#B34E48"},
        },
        height=220,
        showlegend=False,
        xaxis={"title": "Assigned payload (kg)", "gridcolor": "#E2E6E2"},
        yaxis={"autorange": "reversed"},
    )
    return figure
