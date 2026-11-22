"""Interactive Plotly figures for the Eco Impact view.

Only verified figures are used:
* ID=7 (database): roughly 85% of the excess heat from global warming is absorbed
  by the oceans. The remaining 15% is the derived complement.
* Chart 1 projections come from ``src/projection.py`` (sourced inputs, simple maths,
  clearly labelled as a projection and not a climate-model forecast).
* Paris Agreement participation (UNFCCC, November 2026): 198 UNFCCC Parties, of
  which 194 (193 countries + the European Union) are in the Paris Agreement.
  These counts are NOT in the Excel file; they are global UN context supplied by
  the EcoNova team, so re-check them before publishing.

No Kipling Institute survey results are ever generated here (ID=3: the survey is
still in its collection and validation phase).
"""
from __future__ import annotations

import plotly.graph_objects as go

from .projection import (
    BASE_YEAR, MAX_YEAR, MIN_YEAR, OCEAN_SHARE_PCT, OTHER_SHARE_PCT, SCENARIOS, project, series,
)

FOREST = "#1B4332"
LEAF = "#2D6A4F"
MINT = "#D8F3DC"
OFFWHITE = "#F8FAF9"
CHARCOAL = "#1E293B"
OCEAN_BLUE = "#2B7A9B"
WARM = "#E9A23B"
MUTED = "#94A3B8"

PARIS_PARTIES = 194            # 193 countries + the European Union
PARIS_SIGNED_NOT_RATIFIED = 3  # Iran, Libya, Yemen
PARIS_WITHDRAWN = 1            # United States (effective 27 January 2026)
UNFCCC_PARTIES = 198
PARIS_SOURCE_NOTE = (
    "UNFCCC Paris Agreement status, November 2026. Global UN context supplied by the "
    "EcoNova team (not part of the Excel database)."
)

# Interactive behaviour for every chart: drag to zoom, pan, reset on double-click.
PLOTLY_CONFIG = {
    "displaylogo": False,
    "displayModeBar": True,
    "scrollZoom": False,
    "doubleClick": "reset",
    "modeBarButtonsToAdd": ["zoom2d", "pan2d", "select2d", "lasso2d", "resetScale2d"],
}


def apply_interactive_layout(fig: go.Figure, title: str) -> go.Figure:
    """Shared EcoNova styling plus full mouse interactivity (box zoom by default)."""
    fig.update_layout(
        title={"text": title, "x": 0.01, "font": {"size": 18, "color": FOREST}},
        dragmode="zoom",
        hovermode="closest",
        paper_bgcolor=OFFWHITE,
        plot_bgcolor="white",
        font={"color": CHARCOAL, "family": "Source Sans 3, Segoe UI, Arial, sans-serif"},
        margin={"l": 50, "r": 30, "t": 70, "b": 50},
    )
    return fig


def heat_split(total_units: float) -> tuple[float, float]:
    """Split ``total_units`` into (ocean, other) with the exact 85/15 baseline."""
    ocean = total_units * OCEAN_SHARE_PCT / 100
    return ocean, total_units - ocean


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{alpha})"


def build_heat_figure(year: int = 2050, scenario: str = "trend") -> go.Figure:
    """Chart 1: where the excess heat goes (donut) and how it piles up over time (lines).

    Everything moves with the year slider and the scenario choice. The 85/15 split is
    exact; the amounts come from ``src.projection`` (documented, sourced maths).
    """
    now = project(year, scenario)
    other_scenario = "steady" if scenario == "trend" else "trend"
    years = list(range(BASE_YEAR, now.year + 1))
    main = series(now.year, scenario)
    alt = series(now.year, other_scenario)

    fig = go.Figure()
    fig.add_trace(go.Pie(
        labels=["Oceans", "Air, land & ice"], values=[now.ocean_zj, now.other_zj],
        hole=0.58, sort=False, direction="clockwise", showlegend=False,
        domain={"x": [0.0, 0.36], "y": [0.0, 1.0]}, automargin=True,
        marker={"colors": [OCEAN_BLUE, WARM], "line": {"color": "white", "width": 2}},
        textinfo="label+percent", textposition=["inside", "outside"],
        insidetextorientation="horizontal",
        hovertemplate="%{label}: %{value:.0f} ZJ (%{percent})<extra></extra>",
    ))
    # uncertainty band for the selected scenario (upper line, then lower line filled to it)
    fig.add_trace(go.Scatter(x=years, y=[p.total_high_zj for p in main], mode="lines", line={"width": 0},
                             showlegend=False, hoverinfo="skip", xaxis="x", yaxis="y"))
    fig.add_trace(go.Scatter(x=years, y=[p.total_low_zj for p in main], mode="lines", line={"width": 0},
                             fill="tonexty", fillcolor=_rgba(OCEAN_BLUE, 0.18), name="Uncertainty range",
                             hoverinfo="skip", xaxis="x", yaxis="y"))
    fig.add_trace(go.Scatter(x=years, y=[p.total_zj for p in alt], mode="lines", name=SCENARIOS[other_scenario].split(" (")[0],
                             line={"color": MUTED, "width": 2, "dash": "dash"}, xaxis="x", yaxis="y",
                             hovertemplate="%{x}: %{y:.0f} ZJ<extra>" + SCENARIOS[other_scenario].split(" (")[0] + "</extra>"))
    fig.add_trace(go.Scatter(x=years, y=[p.total_zj for p in main], mode="lines", name=SCENARIOS[scenario].split(" (")[0],
                             line={"color": OCEAN_BLUE, "width": 4}, xaxis="x", yaxis="y",
                             hovertemplate="%{x}: %{y:.0f} ZJ<extra>" + SCENARIOS[scenario].split(" (")[0] + "</extra>"))
    fig.add_trace(go.Scatter(x=[now.year], y=[now.total_zj], mode="markers+text", showlegend=False,
                             marker={"size": 13, "color": FOREST, "line": {"color": "white", "width": 2}},
                             text=[f"{now.total_zj:,.0f} ZJ"], textposition="top left", xaxis="x", yaxis="y",
                             hovertemplate=f"{now.year}: {now.total_zj:,.0f} ZJ<extra>Selected year</extra>"))
    fig.update_layout(
        xaxis={"domain": [0.47, 1.0], "title": "Year", "range": [BASE_YEAR, max(now.year, BASE_YEAR + 1)], "dtick": 5 if now.years_ahead > 12 else 1, "tickformat": "d"},
        yaxis={"title": "Heat gained since 2025 (ZJ)", "rangemode": "tozero"},
        legend={"orientation": "h", "x": 0.47, "y": -0.28, "font": {"size": 12}},
        height=520,
    )
    fig.add_annotation(text=f"<b>{now.total_zj:,.0f} ZJ</b><br>by {now.year}", x=0.18, y=0.5, xref="paper", yref="paper",
                       showarrow=False, font={"size": 16, "color": FOREST})
    fig.add_annotation(text="<b>Where the heat goes</b>", x=0.18, y=1.09, xref="paper", yref="paper", showarrow=False,
                       font={"size": 14, "color": FOREST})
    fig.add_annotation(text="<b>How the heat piles up</b>", x=0.735, y=1.09, xref="paper", yref="paper", showarrow=False,
                       font={"size": 14, "color": FOREST})
    apply_interactive_layout(fig, "Where excess global warming heat goes (Gapminder / UN SDG 13)")
    fig.update_layout(margin={"l": 60, "r": 30, "t": 120, "b": 90})
    return fig


def build_paris_figure() -> go.Figure:
    """Chart 2: Paris Agreement participation. One trace per category so the legend filters."""
    categories = [
        ("In the Paris Agreement", "193 countries + the European Union", PARIS_PARTIES, LEAF),
        ("Signed, not ratified", "Iran, Libya, Yemen", PARIS_SIGNED_NOT_RATIFIED, WARM),
        ("Withdrew", "United States, effective 27 Jan 2026", PARIS_WITHDRAWN, MUTED),
    ]
    fig = go.Figure()
    for label, detail, count, color in categories:
        fig.add_trace(
            go.Bar(x=[label], y=[count], name=label, marker_color=color, text=[count], textposition="outside",
                   hovertemplate=f"{label}<br>{detail}<br>%{{y}} of {UNFCCC_PARTIES} UNFCCC Parties<extra></extra>")
        )
    fig.update_yaxes(title_text="UNFCCC Parties", range=[0, 225])
    fig.update_layout(showlegend=True, barmode="group", height=460,
                      legend={"orientation": "h", "x": 0, "y": -0.2, "font": {"size": 12}})
    return apply_interactive_layout(
        fig, f"Global climate cooperation: {PARIS_PARTIES} of {UNFCCC_PARTIES} UNFCCC Parties are in the Paris Agreement"
    )


# Survey areas only describe the *structure* of the dashboard. They hold no data.
SURVEY_PLANNED_AREAS = (
    "Climate awareness",
    "Recycling habits at school",
    "Energy-saving habits",
    "Pollution concerns",
)


def build_survey_placeholder_figure() -> go.Figure:
    """Panel 3: an intentionally empty chart (no traces, no numbers)."""
    fig = go.Figure()
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.add_annotation(
        text="Collection & Validation Phase: no validated survey results yet",
        x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
        font={"size": 15, "color": MUTED},
    )
    return apply_interactive_layout(fig, "Kipling Institute school survey (pending validation)")
