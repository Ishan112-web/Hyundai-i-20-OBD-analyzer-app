"""
i20 AI Garage - Chart Components

Reusable chart components including gauge charts, line charts for telemetry,
and multi-series charts. All components use THEME from config.py for consistent
styling and follow dataviz best practices.
"""

from typing import Optional, List, Dict, Any, Tuple, Union
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from config import THEME, GAUGE_THRESHOLDS


# Chart color palette from THEME
CHART_COLORS = {
    "bg_primary": THEME["bg_primary"],
    "bg_secondary": THEME["bg_secondary"],
    "bg_card": THEME["bg_card"],
    "border": THEME["border"],
    "text_primary": THEME["text_primary"],
    "text_secondary": THEME["text_secondary"],
    "accent_blue": THEME["accent_blue"],      # Primary series
    "accent_green": THEME["accent_green"],    # Good/healthy
    "accent_amber": THEME["accent_amber"],    # Warning
    "accent_red": THEME["accent_red"],        # Critical/error
    "accent_purple": THEME["accent_purple"],  # AI/Assistant
}

# Categorical series colors (following dataviz fixed order for CVD safety)
SERIES_COLORS = [
    THEME["accent_blue"],      # Slot 1: blue - primary telemetry
    THEME["accent_amber"],     # Slot 2: orange/amber - secondary
    THEME["accent_green"],     # Slot 3: green - tertiary
    THEME["accent_purple"],    # Slot 4: purple - AI/derived
    THEME["accent_red"],       # Slot 5: red - alerts
]

# Status colors (distinct from series per dataviz rules)
STATUS_COLORS = {
    "good": THEME["accent_green"],
    "warning": THEME["accent_amber"],
    "serious": "#ec835a",      # Distinct orange-red
    "critical": THEME["accent_red"],
}


def _get_base_layout(
    title: str = "",
    height: int = 300,
    show_legend: bool = True,
    margin: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """Get base layout configuration for all charts."""
    if margin is None:
        margin = dict(l=50, r=30, t=60, b=50)

    return {
        "title": {
            "text": title,
            "font": {"color": CHART_COLORS["text_primary"], "size": 14, "family": "system-ui, -apple-system, Segoe UI, sans-serif"},
            "x": 0.02,
            "xanchor": "left",
        },
        "font": {"color": CHART_COLORS["text_primary"], "family": "system-ui, -apple-system, Segoe UI, sans-serif"},
        "paper_bgcolor": CHART_COLORS["bg_card"],
        "plot_bgcolor": CHART_COLORS["bg_card"],
        "height": height,
        "margin": margin,
        "showlegend": show_legend,
        "legend": {
            "bgcolor": "rgba(0,0,0,0)",
            "bordercolor": CHART_COLORS["border"],
            "borderwidth": 1,
            "font": {"color": CHART_COLORS["text_secondary"], "size": 11},
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.15,
            "xanchor": "left",
            "x": 0,
        },
        "xaxis": {
            "gridcolor": CHART_COLORS["border"],
            "zerolinecolor": CHART_COLORS["border"],
            "linecolor": CHART_COLORS["border"],
            "tickfont": {"color": CHART_COLORS["text_secondary"], "size": 10},
            "titlefont": {"color": CHART_COLORS["text_secondary"], "size": 11},
        },
        "yaxis": {
            "gridcolor": CHART_COLORS["border"],
            "zerolinecolor": CHART_COLORS["border"],
            "linecolor": CHART_COLORS["border"],
            "tickfont": {"color": CHART_COLORS["text_secondary"], "size": 10},
            "titlefont": {"color": CHART_COLORS["text_secondary"], "size": 11},
        },
        "hovermode": "x unified",
        "hoverlabel": {
            "bgcolor": CHART_COLORS["bg_secondary"],
            "bordercolor": CHART_COLORS["border"],
            "font": {"color": CHART_COLORS["text_primary"], "size": 11, "family": "system-ui, -apple-system, Segoe UI, sans-serif"},
        },
    }


def _apply_threshold_colors(
    value: float,
    thresholds: Dict[str, float],
    reverse: bool = False,
) -> str:
    """Determine color based on threshold configuration."""
    if reverse:
        # Lower is better (e.g., fuel trim close to 0)
        green_max = thresholds.get("green_max", float('inf'))
        amber_max = thresholds.get("amber_max", float('inf'))
        if value <= green_max:
            return CHART_COLORS["accent_green"]
        elif value <= amber_max:
            return CHART_COLORS["accent_amber"]
        else:
            return CHART_COLORS["accent_red"]
    else:
        # Higher is worse (e.g., RPM, temperature)
        green_max = thresholds.get("green_max", float('inf'))
        amber_max = thresholds.get("amber_max", float('inf'))
        red_max = thresholds.get("red_max", float('inf'))
        if value <= green_max:
            return CHART_COLORS["accent_green"]
        elif value <= amber_max:
            return CHART_COLORS["accent_amber"]
        elif value <= red_max:
            return CHART_COLORS["accent_red"]
        else:
            return CHART_COLORS["accent_red"]


def create_gauge_chart(
    value: float,
    title: str,
    unit: str = "",
    gauge_type: str = "rpm",
    min_value: Optional[float] = None,
    max_value: Optional[float] = None,
    height: int = 250,
    show_thresholds: bool = True,
    threshold_config: Optional[Dict[str, float]] = None,
) -> go.Figure:
    """
    Create a gauge chart for real-time telemetry values.

    Args:
        value: Current value to display
        title: Gauge title/label
        unit: Unit of measurement
        gauge_type: Type of gauge (rpm, speed, coolant_temp, throttle, engine_load, fuel_trim, voltage)
        min_value: Minimum value (auto from thresholds if not provided)
        max_value: Maximum value (auto from thresholds if not provided)
        height: Chart height in pixels
        show_thresholds: Whether to show colored threshold zones
        threshold_config: Custom threshold dict (overrides GAUGE_THRESHOLDS)

    Returns:
        Plotly Figure object
    """
    # Get thresholds for this gauge type
    if threshold_config:
        thresholds = threshold_config
    else:
        thresholds = GAUGE_THRESHOLDS.get(gauge_type, {})

    # Determine min/max
    if min_value is None:
        if "green_min" in thresholds:
            min_value = thresholds["green_min"]
        elif "red_min" in thresholds:
            min_value = thresholds["red_min"] * 0.5
        else:
            min_value = 0

    if max_value is None:
        if "red_max" in thresholds:
            max_value = thresholds["red_max"] * 1.1
        elif "amber_max" in thresholds:
            max_value = thresholds["amber_max"] * 1.3
        elif "green_max" in thresholds:
            max_value = thresholds["green_max"] * 1.5
        else:
            max_value = value * 1.5 if value > 0 else 100

    # Determine threshold boundaries for gauge sectors
    green_max = thresholds.get("green_max", max_value * 0.4)
    amber_max = thresholds.get("amber_max", max_value * 0.7)
    red_max = thresholds.get("red_max", max_value)

    # For fuel_trim (diverging - centered at 0)
    if gauge_type == "fuel_trim":
        green_min = thresholds.get("green_min", -10)
        green_max = thresholds.get("green_max", 10)
        amber_min = thresholds.get("amber_min", -20)
        amber_max = thresholds.get("amber_max", 20)
        red_min = thresholds.get("red_min", -30)
        red_max = thresholds.get("red_max", 30)

        min_value = red_min * 1.2
        max_value = red_max * 1.2

        # Create diverging gauge
        fig = go.Figure()

        # Add threshold zones as colored sectors
        if show_thresholds:
            # Red zone (negative)
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis": {"range": [min_value, max_value], "tickcolor": CHART_COLORS["text_secondary"]},
                    "bar": {"color": "rgba(0,0,0,0)"},
                    "bgcolor": CHART_COLORS["bg_card"],
                    "borderwidth": 0,
                    "steps": [
                        {"range": [red_min, amber_min], "color": CHART_COLORS["accent_red"]},
                        {"range": [amber_min, green_min], "color": CHART_COLORS["accent_amber"]},
                        {"range": [green_min, green_max], "color": CHART_COLORS["accent_green"]},
                        {"range": [green_max, amber_max], "color": CHART_COLORS["accent_amber"]},
                        {"range": [amber_max, red_max], "color": CHART_COLORS["accent_red"]},
                    ],
                    "threshold": {
                        "line": {"color": CHART_COLORS["text_primary"], "width": 3},
                        "thickness": 0.8,
                        "value": value,
                    },
                },
                number={
                    "font": {"color": CHART_COLORS["text_primary"], "size": 48, "family": "system-ui, -apple-system, Segoe UI, sans-serif"},
                    "suffix": f" {unit}",
                    "valueformat": ".1f",
                },
                title={"text": title, "font": {"color": CHART_COLORS["text_secondary"], "size": 12}},
            ))
        else:
            # Simple gauge without threshold colors
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis": {"range": [min_value, max_value], "tickcolor": CHART_COLORS["text_secondary"]},
                    "bar": {"color": CHART_COLORS["accent_blue"], "thickness": 0.3},
                    "bgcolor": CHART_COLORS["bg_card"],
                    "borderwidth": 1,
                    "bordercolor": CHART_COLORS["border"],
                },
                number={
                    "font": {"color": CHART_COLORS["text_primary"], "size": 48},
                    "suffix": f" {unit}",
                    "valueformat": ".1f",
                },
                title={"text": title, "font": {"color": CHART_COLORS["text_secondary"], "size": 12}},
            ))
    else:
        # Standard single-direction gauge
        fig = go.Figure()

        # Determine bar color based on current value
        bar_color = _apply_threshold_colors(value, thresholds)

        if show_thresholds:
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis": {
                        "range": [min_value, max_value],
                        "tickcolor": CHART_COLORS["text_secondary"],
                        "tickfont": {"color": CHART_COLORS["text_secondary"], "size": 10},
                    },
                    "bar": {"color": bar_color, "thickness": 0.3},
                    "bgcolor": CHART_COLORS["bg_card"],
                    "borderwidth": 1,
                    "bordercolor": CHART_COLORS["border"],
                    "steps": [
                        {"range": [min_value, green_max], "color": CHART_COLORS["accent_green"] + "40"},
                        {"range": [green_max, amber_max], "color": CHART_COLORS["accent_amber"] + "40"},
                        {"range": [amber_max, red_max], "color": CHART_COLORS["accent_red"] + "40"},
                        {"range": [red_max, max_value], "color": CHART_COLORS["accent_red"] + "60"},
                    ],
                    "threshold": {
                        "line": {"color": CHART_COLORS["text_primary"], "width": 3},
                        "thickness": 0.8,
                        "value": value,
                    },
                },
                number={
                    "font": {"color": CHART_COLORS["text_primary"], "size": 48, "family": "system-ui, -apple-system, Segoe UI, sans-serif"},
                    "suffix": f" {unit}",
                    "valueformat": ".0f" if gauge_type in ["rpm", "speed"] else ".1f",
                },
                title={"text": title, "font": {"color": CHART_COLORS["text_secondary"], "size": 12}},
            ))
        else:
            fig.add_trace(go.Indicator(
                mode="gauge+number",
                value=value,
                domain={"x": [0, 1], "y": [0, 1]},
                gauge={
                    "axis": {"range": [min_value, max_value], "tickcolor": CHART_COLORS["text_secondary"]},
                    "bar": {"color": bar_color, "thickness": 0.3},
                    "bgcolor": CHART_COLORS["bg_card"],
                    "borderwidth": 1,
                    "bordercolor": CHART_COLORS["border"],
                },
                number={
                    "font": {"color": CHART_COLORS["text_primary"], "size": 48},
                    "suffix": f" {unit}",
                    "valueformat": ".0f" if gauge_type in ["rpm", "speed"] else ".1f",
                },
                title={"text": title, "font": {"color": CHART_COLORS["text_secondary"], "size": 12}},
            ))

    fig.update_layout(
        **_get_base_layout("", height=height, show_legend=False, margin=dict(l=20, r=20, t=40, b=20)),
        paper_bgcolor=CHART_COLORS["bg_card"],
        plot_bgcolor=CHART_COLORS["bg_card"],
    )

    return fig


def create_line_chart(
    data: pd.DataFrame,
    x_col: str,
    y_cols: Union[str, List[str]],
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    height: int = 350,
    show_markers: bool = False,
    line_width: int = 2,
    marker_size: int = 6,
    colors: Optional[List[str]] = None,
    y_range: Optional[Tuple[float, float]] = None,
    secondary_y_cols: Optional[List[str]] = None,
    secondary_y_title: str = "",
) -> go.Figure:
    """
    Create a line chart for telemetry time-series data.

    Args:
        data: DataFrame with time-series data
        x_col: Column name for x-axis (typically timestamp)
        y_cols: Column name(s) for y-axis (single or list)
        title: Chart title
        x_title: X-axis label
        y_title: Y-axis label
        height: Chart height in pixels
        show_markers: Whether to show data point markers
        line_width: Line width in pixels
        marker_size: Marker size in pixels
        colors: Custom colors for each series (uses SERIES_COLORS if not provided)
        y_range: Optional (min, max) for y-axis
        secondary_y_cols: Columns for secondary y-axis (avoid per dataviz - use separate chart instead)
        secondary_y_title: Secondary y-axis label

    Returns:
        Plotly Figure object
    """
    if isinstance(y_cols, str):
        y_cols = [y_cols]

    if colors is None:
        colors = SERIES_COLORS[:len(y_cols)]
    elif len(colors) < len(y_cols):
        colors = colors + SERIES_COLORS[len(colors):len(y_cols)]

    fig = go.Figure()

    for i, y_col in enumerate(y_cols):
        color = colors[i % len(colors)]

        fig.add_trace(go.Scatter(
            x=data[x_col],
            y=data[y_col],
            mode="lines+markers" if show_markers else "lines",
            name=y_col.replace("_", " ").title(),
            line=dict(color=color, width=line_width, shape="spline"),
            marker=dict(
                size=marker_size if show_markers else 0,
                color=color,
                line=dict(width=2, color=CHART_COLORS["bg_card"]),
            ),
            hovertemplate=f"<b>%{{y:.1f}} {y_title}</b><br>%{{x}}<extra></extra>",
            connectgaps=True,
        ))

    # Add secondary y-axis traces if provided (not recommended per dataviz)
    if secondary_y_cols:
        for i, y_col in enumerate(secondary_y_cols):
            color_idx = (len(y_cols) + i) % len(SERIES_COLORS)
            color = SERIES_COLORS[color_idx]

            fig.add_trace(go.Scatter(
                x=data[x_col],
                y=data[y_col],
                mode="lines",
                name=y_col.replace("_", " ").title(),
                line=dict(color=color, width=line_width, dash="dot"),
                yaxis="y2",
                hovertemplate=f"<b>%{{y:.1f}} {secondary_y_title}</b><br>%{{x}}<extra></extra>",
            ))

    layout = _get_base_layout(title, height=height, show_legend=len(y_cols) > 1 or bool(secondary_y_cols))
    layout.update({
        "xaxis": {**layout["xaxis"], "title": x_title},
        "yaxis": {**layout["yaxis"], "title": y_title, "rangemode": "tozero"},
    })

    if y_range:
        layout["yaxis"]["range"] = y_range

    if secondary_y_cols:
        layout["yaxis2"] = {
            "title": secondary_y_title,
            "overlaying": "y",
            "side": "right",
            "showgrid": False,
            "gridcolor": CHART_COLORS["border"],
            "zerolinecolor": CHART_COLORS["border"],
            "linecolor": CHART_COLORS["border"],
            "tickfont": {"color": CHART_COLORS["text_secondary"], "size": 10},
            "titlefont": {"color": CHART_COLORS["text_secondary"], "size": 11},
        }

    fig.update_layout(**layout)

    return fig


def create_multi_series_chart(
    data: pd.DataFrame,
    x_col: str,
    series_config: List[Dict[str, Any]],
    title: str = "",
    x_title: str = "",
    height: int = 400,
    shared_xaxes: bool = True,
    vertical_spacing: float = 0.08,
) -> go.Figure:
    """
    Create a multi-series chart with multiple subplots (small multiples).
    Following dataviz principle: avoid dual-axis, use small multiples instead.

    Args:
        data: DataFrame with time-series data
        x_col: Column name for x-axis
        series_config: List of dicts, each with:
            - "y_col": column name
            - "title": subplot title
            - "y_title": y-axis label
            - "color": optional color (uses SERIES_COLORS)
            - "type": "line" or "area" or "bar"
            - "show_markers": bool
            - "y_range": optional (min, max)
        title: Overall chart title
        x_title: X-axis label (shared)
        height: Total chart height
        shared_xaxes: Whether subplots share x-axis
        vertical_spacing: Spacing between subplots

    Returns:
        Plotly Figure object with subplots
    """
    n_rows = len(series_config)
    subplot_titles = [cfg.get("title", "") for cfg in series_config]

    fig = make_subplots(
        rows=n_rows,
        cols=1,
        shared_xaxes=shared_xaxes,
        vertical_spacing=vertical_spacing,
        subplot_titles=subplot_titles,
    )

    for i, cfg in enumerate(series_config):
        row = i + 1
        y_col = cfg["y_col"]
        color = cfg.get("color", SERIES_COLORS[i % len(SERIES_COLORS)])
        chart_type = cfg.get("type", "line")
        show_markers = cfg.get("show_markers", False)
        y_range = cfg.get("y_range")
        y_title = cfg.get("y_title", "")

        if chart_type == "area":
            trace = go.Scatter(
                x=data[x_col],
                y=data[y_col],
                mode="lines",
                name=y_col.replace("_", " ").title(),
                line=dict(color=color, width=1.5),
                fill="tozeroy",
                fillcolor=color + "30",
                hovertemplate=f"<b>%{{y:.1f}} {y_title}</b><br>%{{x}}<extra></extra>",
            )
        elif chart_type == "bar":
            trace = go.Bar(
                x=data[x_col],
                y=data[y_col],
                name=y_col.replace("_", " ").title(),
                marker_color=color,
                hovertemplate=f"<b>%{{y:.1f}} {y_title}</b><br>%{{x}}<extra></extra>",
            )
        else:  # line
            trace = go.Scatter(
                x=data[x_col],
                y=data[y_col],
                mode="lines+markers" if show_markers else "lines",
                name=y_col.replace("_", " ").title(),
                line=dict(color=color, width=2, shape="spline"),
                marker=dict(
                    size=5 if show_markers else 0,
                    color=color,
                    line=dict(width=1.5, color=CHART_COLORS["bg_card"]),
                ),
                hovertemplate=f"<b>%{{y:.1f}} {y_title}</b><br>%{{x}}<extra></extra>",
                connectgaps=True,
            )

        fig.add_trace(trace, row=row, col=1)

        # Update y-axis for this subplot
        fig.update_yaxes(
            title_text=y_title,
            row=row, col=1,
            gridcolor=CHART_COLORS["border"],
            zerolinecolor=CHART_COLORS["border"],
            linecolor=CHART_COLORS["border"],
            tickfont={"color": CHART_COLORS["text_secondary"], "size": 9},
            titlefont={"color": CHART_COLORS["text_secondary"], "size": 10},
            rangemode="tozero" if chart_type != "bar" else None,
        )

        if y_range:
            fig.update_yaxes(range=y_range, row=row, col=1)

    # Update x-axis (only bottom one shows labels if shared)
    fig.update_xaxes(
        title_text=x_title,
        row=n_rows, col=1,
        gridcolor=CHART_COLORS["border"],
        zerolinecolor=CHART_COLORS["border"],
        linecolor=CHART_COLORS["border"],
        tickfont={"color": CHART_COLORS["text_secondary"], "size": 9},
        titlefont={"color": CHART_COLORS["text_secondary"], "size": 10},
    )

    if shared_xaxes:
        for row in range(1, n_rows):
            fig.update_xaxes(showticklabels=False, row=row, col=1)

    fig.update_layout(
        **_get_base_layout(title, height=height, show_legend=False),
        paper_bgcolor=CHART_COLORS["bg_card"],
        plot_bgcolor=CHART_COLORS["bg_card"],
    )

    # Update subplot title styling
    for annotation in fig.layout.annotations:
        annotation.update(
            font={"color": CHART_COLORS["text_primary"], "size": 11, "family": "system-ui, -apple-system, Segoe UI, sans-serif"},
            x=0.02,
            xanchor="left",
        )

    return fig


def create_telemetry_dashboard(
    data: pd.DataFrame,
    x_col: str = "timestamp",
    metrics: Optional[List[Dict[str, Any]]] = None,
    height: int = 600,
) -> go.Figure:
    """
    Create a comprehensive telemetry dashboard with multiple gauges and charts.

    Args:
        data: DataFrame with telemetry data
        x_col: Timestamp column
        metrics: List of metric configurations
        height: Total height

    Returns:
        Plotly Figure with subplots
    """
    if metrics is None:
        # Default telemetry metrics for i20
        metrics = [
            {"y_col": "rpm", "title": "Engine RPM", "y_title": "RPM", "type": "line", "gauge_type": "rpm"},
            {"y_col": "speed", "title": "Vehicle Speed", "y_title": "km/h", "type": "line", "gauge_type": "speed"},
            {"y_col": "coolant_temp", "title": "Coolant Temperature", "y_title": "°C", "type": "line", "gauge_type": "coolant_temp"},
            {"y_col": "throttle_pos", "title": "Throttle Position", "y_title": "%", "type": "line", "gauge_type": "throttle"},
            {"y_col": "engine_load", "title": "Engine Load", "y_title": "%", "type": "line", "gauge_type": "engine_load"},
            {"y_col": "fuel_trim_st", "title": "Short Term Fuel Trim", "y_title": "%", "type": "line", "gauge_type": "fuel_trim"},
        ]

    return create_multi_series_chart(
        data=data,
        x_col=x_col,
        series_config=metrics,
        title="Real-Time Telemetry",
        x_title="Time",
        height=height,
    )


def create_comparison_chart(
    data: pd.DataFrame,
    x_col: str,
    y_col: str,
    group_col: str,
    title: str = "",
    x_title: str = "",
    y_title: str = "",
    height: int = 350,
    chart_type: str = "line",
) -> go.Figure:
    """
    Create a comparison chart showing multiple groups/series.
    Uses categorical colors in fixed order (dataviz principle).

    Args:
        data: DataFrame with data
        x_col: X-axis column
        y_col: Y-axis column
        group_col: Column to group by (creates separate series)
        title: Chart title
        x_title: X-axis label
        y_title: Y-axis label
        height: Chart height
        chart_type: "line" or "bar"

    Returns:
        Plotly Figure object
    """
    groups = data[group_col].unique()

    fig = go.Figure()

    for i, group in enumerate(groups):
        group_data = data[data[group_col] == group].sort_values(x_col)
        color = SERIES_COLORS[i % len(SERIES_COLORS)]

        if chart_type == "bar":
            trace = go.Bar(
                x=group_data[x_col],
                y=group_data[y_col],
                name=str(group),
                marker_color=color,
                hovertemplate=f"<b>{group}</b><br>%{{y:.1f}} {y_title}<br>%{{x}}<extra></extra>",
            )
        else:
            trace = go.Scatter(
                x=group_data[x_col],
                y=group_data[y_col],
                mode="lines+markers",
                name=str(group),
                line=dict(color=color, width=2, shape="spline"),
                marker=dict(size=6, color=color, line=dict(width=2, color=CHART_COLORS["bg_card"])),
                hovertemplate=f"<b>{group}</b><br>%{{y:.1f}} {y_title}<br>%{{x}}<extra></extra>",
                connectgaps=True,
            )

        fig.add_trace(trace)

    fig.update_layout(
        **_get_base_layout(title, height=height, show_legend=True),
        xaxis_title=x_title,
        yaxis_title=y_title,
    )

    return fig


def create_sparkline(
    data: pd.Series,
    height: int = 60,
    width: int = 200,
    color: Optional[str] = None,
    fill: bool = True,
) -> go.Figure:
    """
    Create a compact sparkline chart for inline display.

    Args:
        data: Series of values
        height: Chart height
        width: Chart width
        color: Line color (uses accent_blue if not provided)
        fill: Whether to fill area under line

    Returns:
        Plotly Figure object
    """
    if color is None:
        color = CHART_COLORS["accent_blue"]

    fig = go.Figure()

    if fill:
        fig.add_trace(go.Scatter(
            x=list(range(len(data))),
            y=data.values,
            mode="lines",
            line=dict(color=color, width=1.5),
            fill="tozeroy",
            fillcolor=color + "20",
            hoverinfo="skip",
            showlegend=False,
        ))
    else:
        fig.add_trace(go.Scatter(
            x=list(range(len(data))),
            y=data.values,
            mode="lines",
            line=dict(color=color, width=2),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.update_layout(
        width=width,
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        showlegend=False,
    )

    return fig


# Convenience functions for specific gauge types
def create_rpm_gauge(value: float, **kwargs) -> go.Figure:
    """Create RPM gauge chart."""
    return create_gauge_chart(value, "Engine RPM", "RPM", "rpm", **kwargs)


def create_speed_gauge(value: float, **kwargs) -> go.Figure:
    """Create speed gauge chart."""
    return create_gauge_chart(value, "Speed", "km/h", "speed", **kwargs)


def create_coolant_temp_gauge(value: float, **kwargs) -> go.Figure:
    """Create coolant temperature gauge chart."""
    return create_gauge_chart(value, "Coolant Temp", "°C", "coolant_temp", **kwargs)


def create_throttle_gauge(value: float, **kwargs) -> go.Figure:
    """Create throttle position gauge chart."""
    return create_gauge_chart(value, "Throttle", "%", "throttle", **kwargs)


def create_engine_load_gauge(value: float, **kwargs) -> go.Figure:
    """Create engine load gauge chart."""
    return create_gauge_chart(value, "Engine Load", "%", "engine_load", **kwargs)


def create_fuel_trim_gauge(value: float, **kwargs) -> go.Figure:
    """Create fuel trim gauge chart (diverging)."""
    return create_gauge_chart(value, "Fuel Trim", "%", "fuel_trim", **kwargs)


def create_voltage_gauge(value: float, **kwargs) -> go.Figure:
    """Create battery voltage gauge chart."""
    return create_gauge_chart(value, "Battery Voltage", "V", "voltage", **kwargs)