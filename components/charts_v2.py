"""
i20 AI Garage - Token-Driven Plotly Chart Factory

Replaces components/charts.py with design token-driven chart creation.
All colors, typography, spacing, and layout derived from design tokens.

Accessibility Features (WCAG 2.1 AA):
- Accessible data tables for all chart types (SC 1.1.1)
- aria-hidden on visual charts with alternative data tables
- Reduced motion support (SC 2.3.3)
- Color-independent information (patterns, labels) (SC 1.4.1)
"""

from typing import Final, Literal, Optional, Any, List, Dict, Tuple
from dataclasses import dataclass, field
from functools import lru_cache

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# Import design tokens
from .ui.tokens import (
    # Colors
    SURFACE_APP, SURFACE_PRIMARY, SURFACE_SECONDARY, SURFACE_ELEVATED,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    BORDER_DEFAULT, BORDER_SUBTLE,
    ACCENT_PRIMARY, ACCENT_SECONDARY,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO,
    SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5,
    CHART_GOOD, CHART_WARNING, CHART_SERIOUS, CHART_CRITICAL,
    DATASOURCE_REAL, DATASOURCE_SIMULATION, DATASOURCE_AI,
    DIAG_CRITICAL, DIAG_MAJOR, DIAG_MINOR, DIAG_INFO,
    # Typography
    FONT_FAMILY_BASE, FONT_FAMILY_MONO,
    FONT_SIZE_DISPLAY, FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_H4,
    FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_LABEL, FONT_SIZE_CAPTION,
    FONT_SIZE_NUMERIC_XL, FONT_SIZE_NUMERIC_LG, FONT_SIZE_NUMERIC_MD, FONT_SIZE_NUMERIC_SM,
    FONT_WEIGHT_DISPLAY, FONT_WEIGHT_H1, FONT_WEIGHT_H2, FONT_WEIGHT_H3, FONT_WEIGHT_H4,
    FONT_WEIGHT_BODY, FONT_WEIGHT_LABEL, FONT_WEIGHT_NUMERIC,
    LINE_HEIGHT_DISPLAY, LINE_HEIGHT_H1, LINE_HEIGHT_H2, LINE_HEIGHT_H3, LINE_HEIGHT_H4,
    LINE_HEIGHT_BODY,
    # Spacing
    SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6, SPACE_8,
    # Radius
    RADIUS_MD, RADIUS_LG,
    # Shadows
    SHADOW_MD,
    # Chart tokens
    GAUGE_THRESHOLD_TOKENS, CHART_LAYOUT_DEFAULTS,
)

# Import accessibility utilities
from .ui.accessibility import (
    render_accessible_chart_container,
    ChartAccessibilityProps,
    render_accessible_table_wrapper,
    render_table_caption,
    render_table_header,
    TableCaptionProps,
    TableHeaderProps,
)


# =============================================================================
# ACCESSIBLE CHART CONFIG
# =============================================================================
# WCAG 2.1 AA: Enable keyboard navigation for all charts
# - displayModeBar: True enables keyboard access to mode bar
# - staticPlot: False allows interaction (zoom, pan, hover)
# - responsive: True makes charts responsive
ACCESSIBLE_CHART_CONFIG: Final[dict] = {
    "displayModeBar": True,
    "staticPlot": False,
    "responsive": True,
}

# =============================================================================
# CHART COLOR REGISTRY
# =============================================================================

# Series colors in fixed CVD-safe order
SERIES_PALETTE: Final[list[str]] = [SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5]

# Fill colors (12% opacity)
SERIES_FILL_PALETTE: Final[list[str]] = [f"{c}20" for c in SERIES_PALETTE]

# Semantic status colors (distinct from series)
STATUS_PALETTE: Final[dict[str, str]] = {
    "good": CHART_GOOD,
    "warning": CHART_WARNING,
    "serious": CHART_SERIOUS,
    "critical": CHART_CRITICAL,
}

# Data source colors
DATASOURCE_PALETTE: Final[dict[str, str]] = {
    "real": DATASOURCE_REAL,
    "simulation": DATASOURCE_SIMULATION,
    "ai": DATASOURCE_AI,
}

# Diagnostic severity colors
DIAG_PALETTE: Final[dict[str, str]] = {
    "critical": DIAG_CRITICAL,
    "major": DIAG_MAJOR,
    "minor": DIAG_MINOR,
    "info": DIAG_INFO,
}


# =============================================================================
# BASE LAYOUT FACTORY
# =============================================================================

def get_base_layout(
    title: str = "",
    height: int = 400,
    width: Optional[int] = None,
    show_legend: bool = True,
    legend_orientation: Literal["h", "v"] = "h",
    legend_position: Literal["top", "bottom", "right"] = "top",
    margin: Optional[dict] = None,
    xaxis_title: str = "",
    yaxis_title: str = "",
    yaxis2_title: str = "",
    reduced_motion: bool = False,
    **kwargs
) -> go.Layout:
    """
    Create a base Plotly layout with design system tokens.

    Args:
        title: Chart title
        height: Chart height in pixels
        width: Chart width in pixels (None for responsive)
        show_legend: Whether to show legend
        legend_orientation: Legend orientation
        legend_position: Legend position
        margin: Custom margins
        xaxis_title: X-axis title
        yaxis_title: Primary Y-axis title
        yaxis2_title: Secondary Y-axis title
        reduced_motion: Whether to disable transitions (respects prefers-reduced-motion)
        **kwargs: Additional layout overrides

    Returns:
        Plotly Layout object
    """
    # Default margins
    default_margin = dict(l=60, r=40, t=70 if title else 40, b=60)
    if margin:
        default_margin.update(margin)

    # Legend configuration
    legend_config = {}
    if show_legend:
        if legend_orientation == "h":
            if legend_position == "top":
                legend_config = dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(0,0,0,0)",
                    bordercolor=BORDER_DEFAULT,
                    borderwidth=1,
                    font=dict(color=TEXT_SECONDARY, size=11),
                )
            else:  # bottom
                legend_config = dict(
                    orientation="h",
                    yanchor="top",
                    y=-0.15,
                    xanchor="center",
                    x=0.5,
                    bgcolor="rgba(0,0,0,0)",
                    bordercolor=BORDER_DEFAULT,
                    borderwidth=1,
                    font=dict(color=TEXT_SECONDARY, size=11),
                )
        else:  # vertical
            if legend_position == "right":
                legend_config = dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.02,
                    bgcolor="rgba(0,0,0,0)",
                    bordercolor=BORDER_DEFAULT,
                    borderwidth=1,
                    font=dict(color=TEXT_SECONDARY, size=11),
                )

    # Transition config based on reduced motion
    transition_duration = 0 if reduced_motion else 200

    layout = go.Layout(
        # Base styling
        paper_bgcolor=SURFACE_APP,
        plot_bgcolor=SURFACE_PRIMARY,
        font=dict(
            family=FONT_FAMILY_BASE,
            color=TEXT_PRIMARY,
            size=12,
        ),
        # Title
        title=dict(
            text=title,
            font=dict(
                family=FONT_FAMILY_BASE,
                size=14,
                color=TEXT_PRIMARY,
                weight=FONT_WEIGHT_H3,
            ),
            x=0.02,
            xanchor="left",
        ) if title else None,
        # Dimensions
        height=height,
        width=width,
        # Margins
        margin=default_margin,
        # Legend
        showlegend=show_legend,
        legend=legend_config if show_legend else None,
        # X-axis
        xaxis=dict(
            title=dict(
                text=xaxis_title,
                font=dict(
                    family=FONT_FAMILY_BASE,
                    size=11,
                    color=TEXT_SECONDARY,
                    weight=FONT_WEIGHT_LABEL,
                ),
            ) if xaxis_title else None,
            gridcolor=BORDER_SUBTLE,
            gridwidth=1,
            linecolor=BORDER_DEFAULT,
            linewidth=1,
            tickfont=dict(
                family=FONT_FAMILY_BASE,
                size=10,
                color=TEXT_SECONDARY,
            ),
            tickcolor=BORDER_DEFAULT,
            ticklen=4,
            zeroline=False,
            showspikes=False,
        ),
        # Y-axis
        yaxis=dict(
            title=dict(
                text=yaxis_title,
                font=dict(
                    family=FONT_FAMILY_BASE,
                    size=11,
                    color=TEXT_SECONDARY,
                    weight=FONT_WEIGHT_LABEL,
                ),
            ) if yaxis_title else None,
            gridcolor=BORDER_SUBTLE,
            gridwidth=1,
            linecolor=BORDER_DEFAULT,
            linewidth=1,
            tickfont=dict(
                family=FONT_FAMILY_BASE,
                size=10,
                color=TEXT_SECONDARY,
            ),
            tickcolor=BORDER_DEFAULT,
            ticklen=4,
            zeroline=False,
            showspikes=False,
        ),
        # Hover
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=SURFACE_SECONDARY,
            bordercolor=BORDER_DEFAULT,
            font=dict(
                family=FONT_FAMILY_BASE,
                size=11,
                color=TEXT_PRIMARY,
            ),
            align="left",
        ),
        # Spikelines
        spikedistance=-1,
        # Transitions - respect reduced motion
        transition=dict(
            duration=transition_duration,
            easing="cubic-in-out",
        ),
        **kwargs
    )

    # Add secondary y-axis if title provided
    if yaxis2_title:
        layout["yaxis2"] = dict(
            title=dict(
                text=yaxis2_title,
                font=dict(
                    family=FONT_FAMILY_BASE,
                    size=11,
                    color=TEXT_SECONDARY,
                    weight=FONT_WEIGHT_LABEL,
                ),
            ),
            gridcolor=BORDER_SUBTLE,
            gridwidth=1,
            linecolor=BORDER_DEFAULT,
            linewidth=1,
            tickfont=dict(
                family=FONT_FAMILY_BASE,
                size=10,
                color=TEXT_SECONDARY,
            ),
            overlaying="y",
            side="right",
            showgrid=False,
        )

    return layout


def get_base_layout_with_reduced_motion(
    title: str = "",
    height: int = 400,
    width: Optional[int] = None,
    show_legend: bool = True,
    legend_orientation: Literal["h", "v"] = "h",
    legend_position: Literal["top", "bottom", "right"] = "top",
    margin: Optional[dict] = None,
    xaxis_title: str = "",
    yaxis_title: str = "",
    yaxis2_title: str = "",
    **kwargs
) -> go.Layout:
    """
    Create a base Plotly layout with design system tokens and reduced motion support.
    Automatically detects prefers-reduced-motion via JavaScript injection.

    Returns:
        Plotly Layout object with transition.duration = 0 if reduced motion preferred
    """
    # This will be overridden by JavaScript at runtime
    # The layout is created with transition.duration=0 as default for safety
    return get_base_layout(
        title=title,
        height=height,
        width=width,
        show_legend=show_legend,
        legend_orientation=legend_orientation,
        legend_position=legend_position,
        margin=margin,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        yaxis2_title=yaxis2_title,
        reduced_motion=True,  # Default to no transitions; JS will enable if not reduced
        **kwargs
    )


# =============================================================================
# ACCESSIBLE DATA TABLE GENERATION
# =============================================================================

def generate_chart_data_table(
    chart_id: str,
    title: str,
    headers: List[str],
    rows: List[List[Any]],
    summary: str = "",
    caption: Optional[str] = None,
) -> str:
    """
    Generate an accessible HTML data table for a chart.

    Args:
        chart_id: Unique chart identifier
        title: Chart title
        headers: Column headers
        rows: Data rows
        summary: Summary for screen readers
        caption: Optional caption (defaults to title + " Data Table")

    Returns:
        HTML string for accessible data table
    """
    caption_text = caption or f"{title} - Data Table"

    # Build header row
    header_cells = []
    for i, header in enumerate(headers):
        header_cells.append(render_table_header(TableHeaderProps(
            text=header,
            scope="col",
            id=f"{chart_id}-th-{i}",
        )))

    # Build data rows
    row_html = []
    for row_idx, row in enumerate(rows):
        cells = []
        for col_idx, cell in enumerate(row):
            cells.append(f'<td style="padding: 8px 12px; border-bottom: 1px solid {BORDER_SUBTLE};">{cell}</td>')
        row_html.append(f'<tr style="cursor: default;">{"".join(cells)}</tr>')

    table_html = f"""
<table id="{chart_id}-data-table" class="i20-chart-data-table" role="grid" aria-describedby="{chart_id}-summary">
    {render_table_caption(TableCaptionProps(text=caption_text, id=f"{chart_id}-caption"))}
    <thead>
        <tr>
            {"".join(header_cells)}
        </tr>
    </thead>
    <tbody>
        {"".join(row_html)}
    </tbody>
</table>
"""

    if summary:
        table_html = f'<div id="{chart_id}-summary" class="visually-hidden">{summary}</div>' + table_html

    return render_accessible_table_wrapper(table_html, f"{chart_id}-table-wrapper")


def generate_gauge_data_table(config: 'GaugeConfig', chart_id: str) -> str:
    """Generate data table for gauge chart."""
    thresholds = config.thresholds or GAUGE_THRESHOLD_TOKENS.get(config.metric.lower(), {})

    headers = ["Metric", "Value", "Unit", "Status", "Min", "Max", "Green Zone", "Amber Zone", "Red Zone"]

    # Determine status
    val = config.value
    green_max = thresholds.get("green_max", config.max_val * 0.6)
    amber_max = thresholds.get("amber_max", config.max_val * 0.8)
    red_max = thresholds.get("red_max", config.max_val)
    green_min = thresholds.get("green_min", config.min_val)
    amber_min = thresholds.get("amber_min", config.min_val)
    red_min = thresholds.get("red_min", config.min_val)

    if green_min <= val <= green_max:
        status = "Good (Normal)"
    elif amber_min <= val <= amber_max:
        status = "Warning (Elevated)"
    else:
        status = "Critical (Out of Range)"

    rows = [[
        config.metric.replace("_", " ").title(),
        f"{config.value:.1f}",
        config.unit,
        status,
        str(config.min_val),
        str(config.max_val),
        f"{green_min} - {green_max}",
        f"{amber_min} - {amber_max}",
        f"{red_min} - {red_max}",
    ]]

    summary = f"Gauge chart showing {config.metric} at {config.value:.1f} {config.unit}. Status: {status}."

    return generate_chart_data_table(
        chart_id=chart_id,
        title=config.title or config.metric,
        headers=headers,
        rows=rows,
        summary=summary,
    )


def generate_line_chart_data_table(config: 'LineChartConfig', chart_id: str) -> str:
    """Generate data table for line chart."""
    if not config.series:
        return generate_chart_data_table(chart_id, config.title, [], [], "No data series available")

    # Build headers: X-axis + each series name
    headers = [config.xaxis_title or "X"]
    for series in config.series:
        headers.append(series.name)

    # Build rows: transpose data
    max_len = max(len(s.x) for s in config.series) if config.series else 0
    rows = []
    for i in range(max_len):
        row = []
        # X value (use first series)
        if config.series and i < len(config.series[0].x):
            row.append(str(config.series[0].x[i]))
        else:
            row.append("")
        # Y values for each series
        for series in config.series:
            if i < len(series.y):
                row.append(f"{series.y[i]:.2f}")
            else:
                row.append("")
        rows.append(row)

    summary = f"Line chart '{config.title}' with {len(config.series)} series over {max_len} data points."

    return generate_chart_data_table(
        chart_id=chart_id,
        title=config.title,
        headers=headers,
        rows=rows,
        summary=summary,
    )


def generate_sparkline_data_table(config: 'SparklineConfig', chart_id: str, label: str = "Value") -> str:
    """Generate data table for sparkline."""
    headers = ["Index", label]
    rows = [[str(i), f"{v:.2f}"] for i, v in enumerate(config.y)]
    summary = f"Sparkline with {len(config.y)} data points. Range: {min(config.y):.2f} to {max(config.y):.2f}."

    return generate_chart_data_table(
        chart_id=chart_id,
        title=f"Sparkline: {label}",
        headers=headers,
        rows=rows,
        summary=summary,
    )


def generate_bar_chart_data_table(config: 'BarChartConfig', chart_id: str) -> str:
    """Generate data table for bar chart."""
    if not config.series:
        return generate_chart_data_table(chart_id, config.title, [], [], "No data series available")

    headers = [config.xaxis_title or "Category"]
    for series in config.series:
        headers.append(series.name)

    max_len = max(len(s.x) for s in config.series) if config.series else 0
    rows = []
    for i in range(max_len):
        row = []
        if config.series and i < len(config.series[0].x):
            row.append(str(config.series[0].x[i]))
        else:
            row.append("")
        for series in config.series:
            if i < len(series.y):
                row.append(f"{series.y[i]:.2f}")
            else:
                row.append("")
        rows.append(row)

    summary = f"Bar chart '{config.title}' with {len(config.series)} series across {max_len} categories."

    return generate_chart_data_table(
        chart_id=chart_id,
        title=config.title,
        headers=headers,
        rows=rows,
        summary=summary,
    )


def generate_pie_chart_data_table(config: 'PieChartConfig', chart_id: str) -> str:
    """Generate data table for pie/donut chart."""
    headers = ["Label", "Value", "Percentage"]
    total = sum(config.values)
    rows = []
    for label, value in zip(config.labels, config.values):
        pct = (value / total * 100) if total > 0 else 0
        rows.append([label, str(value), f"{pct:.1f}%"])

    summary = f"Pie chart '{config.title}' with {len(config.labels)} segments. Total: {total:.1f}."

    return generate_chart_data_table(
        chart_id=chart_id,
        title=config.title,
        headers=headers,
        rows=rows,
        summary=summary,
    )


def generate_scatter_chart_data_table(config: 'ScatterConfig', chart_id: str) -> str:
    """Generate data table for scatter chart."""
    if not config.series:
        return generate_chart_data_table(chart_id, config.title, [], [], "No data series available")

    headers = [config.xaxis_title or "X", config.yaxis_title or "Y", "Series"]
    if config.series and config.series[0].size:
        headers.append("Size")

    rows = []
    for series in config.series:
        for i in range(len(series.x)):
            row = [str(series.x[i]), f"{series.y[i]:.2f}", series.name]
            if series.size and i < len(series.size):
                row.append(f"{series.size[i]:.2f}")
            rows.append(row)

    summary = f"Scatter chart '{config.title}' with {len(config.series)} series and {len(rows)} data points."

    return generate_chart_data_table(
        chart_id=chart_id,
        title=config.title,
        headers=headers,
        rows=rows,
        summary=summary,
    )


def generate_heatmap_data_table(config: 'HeatmapConfig', chart_id: str) -> str:
    """Generate data table for heatmap."""
    headers = [""] + config.x
    rows = []
    for y_idx, y_label in enumerate(config.y):
        row = [y_label]
        for x_idx in range(len(config.x)):
            if y_idx < len(config.z) and x_idx < len(config.z[y_idx]):
                row.append(f"{config.z[y_idx][x_idx]:.2f}")
            else:
                row.append("")
        rows.append(row)

    summary = f"Heatmap '{config.title}' with {len(config.y)} rows and {len(config.x)} columns."

    return generate_chart_data_table(
        chart_id=chart_id,
        title=config.title,
        headers=headers,
        rows=rows,
        summary=summary,
    )


def generate_comparison_chart_data_table(config: 'ComparisonConfig', chart_id: str) -> str:
    """Generate data table for comparison chart."""
    if not config.series:
        return generate_chart_data_table(chart_id, config.title, [], [], "No comparison data available")

    headers = [config.xaxis_title or "X"]
    for series in config.series:
        headers.append(series.name)

    max_len = max(len(s.x) for s in config.series) if config.series else 0
    rows = []
    for i in range(max_len):
        row = []
        if config.series and i < len(config.series[0].x):
            row.append(str(config.series[0].x[i]))
        else:
            row.append("")
        for series in config.series:
            if i < len(series.y):
                row.append(f"{series.y[i]:.2f}")
            else:
                row.append("")
        rows.append(row)

    summary = f"Comparison chart '{config.title}' with {len(config.series)} sessions over {max_len} data points."

    return generate_chart_data_table(
        chart_id=chart_id,
        title=config.title,
        headers=headers,
        rows=rows,
        summary=summary,
    )


# =============================================================================
# GAUGE CHART FACTORY
# =============================================================================

@dataclass
class GaugeConfig:
    """Configuration for gauge chart."""
    metric: str
    value: float
    min_val: float = 0
    max_val: float = 100
    unit: str = ""
    title: str = ""
    thresholds: Optional[dict] = None
    height: int = 280
    show_delta: bool = False
    delta_reference: Optional[float] = None


def create_gauge(config: GaugeConfig) -> go.Figure:
    """
    Create a gauge/indicator chart with threshold zones.

    Args:
        config: Gauge configuration

    Returns:
        Plotly Figure with gauge chart
    """
    metric = config.metric.lower()
    thresholds = config.thresholds or GAUGE_THRESHOLD_TOKENS.get(metric, {})

    # Default thresholds if not found
    green_max = thresholds.get("green_max", config.max_val * 0.6)
    amber_max = thresholds.get("amber_max", config.max_val * 0.8)
    red_max = thresholds.get("red_max", config.max_val)

    # For metrics with min/max ranges (fuel_trim, voltage)
    green_min = thresholds.get("green_min", config.min_val)
    amber_min = thresholds.get("amber_min", config.min_val)
    red_min = thresholds.get("red_min", config.min_val)

    # Determine gauge color based on value
    val = config.value
    if green_min <= val <= green_max:
        gauge_color = CHART_GOOD
    elif amber_min <= val <= amber_max:
        gauge_color = CHART_WARNING
    else:
        gauge_color = CHART_CRITICAL

    # Build gauge steps (threshold zones)
    steps = []
    if metric in ("fuel_trim", "voltage"):
        # Bidirectional thresholds
        steps = [
            dict(range=[config.min_val, red_min], color=f"{CHART_CRITICAL}30"),
            dict(range=[red_min, amber_min], color=f"{CHART_SERIOUS}30"),
            dict(range=[amber_min, green_min], color=f"{CHART_WARNING}30"),
            dict(range=[green_min, green_max], color=f"{CHART_GOOD}30"),
            dict(range=[green_max, amber_max], color=f"{CHART_WARNING}30"),
            dict(range=[amber_max, red_max], color=f"{CHART_SERIOUS}30"),
            dict(range=[red_max, config.max_val], color=f"{CHART_CRITICAL}30"),
        ]
    else:
        # Unidirectional thresholds
        steps = [
            dict(range=[config.min_val, green_max], color=f"{CHART_GOOD}30"),
            dict(range=[green_max, amber_max], color=f"{CHART_WARNING}30"),
            dict(range=[amber_max, red_max], color=f"{CHART_SERIOUS}30"),
            dict(range=[red_max, config.max_val], color=f"{CHART_CRITICAL}30"),
        ]

    # Create figure
    fig = go.Figure()

    # Add indicator
    fig.add_trace(go.Indicator(
        mode="gauge+number" + ("+delta" if config.show_delta and config.delta_reference is not None else ""),
        value=config.value,
        domain=dict(x=[0, 1], y=[0, 1]),
        title=dict(
            text=config.title or config.metric.replace("_", " ").title(),
            font=dict(
                family=FONT_FAMILY_BASE,
                size=14,
                color=TEXT_PRIMARY,
                weight=FONT_WEIGHT_H3,
            ),
        ),
        number=dict(
            font=dict(
                family=FONT_FAMILY_MONO,
                size=48,
                color=TEXT_PRIMARY,
                weight=FONT_WEIGHT_NUMERIC,
            ),
            suffix=f" {config.unit}" if config.unit else "",
            valueformat=".1f" if isinstance(config.value, float) else ".0f",
        ),
        delta=dict(
            reference=config.delta_reference,
            relative=False,
            font=dict(
                family=FONT_FAMILY_MONO,
                size=16,
                color=TEXT_SECONDARY,
            ),
            valueformat=".1f",
        ) if config.show_delta and config.delta_reference is not None else None,
        gauge=dict(
            axis=dict(
                range=[config.min_val, config.max_val],
                tickfont=dict(
                    family=FONT_FAMILY_BASE,
                    size=10,
                    color=TEXT_SECONDARY,
                ),
                tickcolor=BORDER_DEFAULT,
                ticklen=6,
                tickwidth=1,
            ),
            bar=dict(
                color=gauge_color,
                thickness=0.3,
            ),
            bgcolor=SURFACE_PRIMARY,
            borderwidth=1,
            bordercolor=BORDER_DEFAULT,
            steps=steps,
            threshold=dict(
                line=dict(color=gauge_color, width=4),
                thickness=0.75,
                value=config.value,
            ),
        ),
    ))

    fig.update_layout(
        get_base_layout_with_reduced_motion(
            title="",
            height=config.height,
            margin=dict(l=20, r=20, t=10, b=20),
        ),
        paper_bgcolor=SURFACE_APP,
        plot_bgcolor=SURFACE_PRIMARY,
    )

    return fig


def create_gauge_with_accessibility(config: GaugeConfig, chart_id: str = "") -> Tuple[go.Figure, str]:
    """
    Create a gauge chart with accessible data table.

    Args:
        config: Gauge configuration
        chart_id: Unique chart ID (auto-generated if not provided)

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"gauge-{config.metric}-{str(uuid.uuid4())[:8]}"

    fig = create_gauge(config)
    data_table = generate_gauge_data_table(config, chart_id)
    summary = f"Gauge showing {config.metric} at {config.value:.1f} {config.unit}."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=config.title or config.metric,
        summary=summary,
        data_table=data_table,
        chart_type="gauge",
    ))

    return fig, accessible_html


def create_gauge_cluster(
    metrics: list[dict],
    cols: int = 3,
    height_per_gauge: int = 260
) -> list[go.Figure]:
    """
    Create multiple gauges for cluster display.

    Args:
        metrics: List of metric configs (dict with GaugeConfig fields)
        cols: Number of columns (for reference, actual layout handled by Streamlit)
        height_per_gauge: Height of each gauge

    Returns:
        List of Plotly Figures
    """
    gauges = []
    for metric in metrics:
        config = GaugeConfig(
            metric=metric.get("metric", ""),
            value=metric.get("value", 0),
            min_val=metric.get("min_val", 0),
            max_val=metric.get("max_val", 100),
            unit=metric.get("unit", ""),
            title=metric.get("title", ""),
            thresholds=metric.get("thresholds"),
            height=height_per_gauge,
            show_delta=metric.get("show_delta", False),
            delta_reference=metric.get("delta_reference"),
        )
        gauges.append(create_gauge(config))
    return gauges


# =============================================================================
# LINE CHART FACTORY
# =============================================================================

@dataclass
class LineSeries:
    """Single line series configuration."""
    x: list
    y: list
    name: str
    color: Optional[str] = None
    dash: Optional[str] = None  # "solid", "dash", "dot", "dashdot"
    width: float = 2
    fill: Optional[str] = None  # "tozeroy", "tonexty"
    opacity: float = 1.0
    show_markers: bool = False
    marker_size: int = 6
    yaxis: str = "y"


@dataclass
class LineChartConfig:
    """Line chart configuration."""
    series: list[LineSeries]
    title: str = ""
    xaxis_title: str = ""
    yaxis_title: str = ""
    yaxis2_title: str = ""
    height: int = 400
    show_legend: bool = True
    legend_position: Literal["top", "bottom", "right"] = "top"
    xaxis_type: Literal["linear", "date", "category"] = "linear"
    range_x: Optional[list] = None
    range_y: Optional[list] = None
    annotations: list = field(default_factory=list)
    show_grid: bool = True


def create_line_chart(config: LineChartConfig) -> go.Figure:
    """
    Create a multi-series line chart.

    Args:
        config: Line chart configuration

    Returns:
        Plotly Figure with line chart
    """
    fig = go.Figure()

    # Add each series
    for i, series in enumerate(config.series):
        color = series.color or SERIES_PALETTE[i % len(SERIES_PALETTE)]
        fill_color = f"{color}20" if series.fill else None

        fig.add_trace(go.Scatter(
            x=series.x,
            y=series.y,
            name=series.name,
            mode="lines" + ("+markers" if series.show_markers else ""),
            line=dict(
                color=color,
                width=series.width,
                dash=series.dash or "solid",
            ),
            fill=series.fill,
            fillcolor=fill_color,
            opacity=series.opacity,
            marker=dict(
                size=series.marker_size,
                color=color,
                line=dict(width=0),
            ) if series.show_markers else None,
            yaxis=series.yaxis,
            hovertemplate="%{y:.1f}<extra>%{fullData.name}</extra>",
            connectgaps=False,
        ))

    # Build layout with reduced motion support
    layout = get_base_layout_with_reduced_motion(
        title=config.title,
        height=config.height,
        show_legend=config.show_legend,
        legend_position=config.legend_position,
        xaxis_title=config.xaxis_title,
        yaxis_title=config.yaxis_title,
        yaxis2_title=config.yaxis2_title,
    )

    # Update xaxis type
    if config.xaxis_type == "date":
        layout["xaxis"]["type"] = "date"
    elif config.xaxis_type == "category":
        layout["xaxis"]["type"] = "category"

    # Set ranges if provided
    if config.range_x:
        layout["xaxis"]["range"] = config.range_x
    if config.range_y:
        layout["yaxis"]["range"] = config.range_y

    # Add annotations
    if config.annotations:
        layout["annotations"] = config.annotations

    # Grid visibility
    if not config.show_grid:
        layout["xaxis"]["showgrid"] = False
        layout["yaxis"]["showgrid"] = False
        if "yaxis2" in layout:
            layout["yaxis2"]["showgrid"] = False

    fig.update_layout(layout)

    return fig


def create_line_chart_with_accessibility(config: LineChartConfig, chart_id: str = "") -> Tuple[go.Figure, str]:
    """
    Create a line chart with accessible data table.

    Args:
        config: Line chart configuration
        chart_id: Unique chart ID (auto-generated if not provided)

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"line-{str(uuid.uuid4())[:8]}"

    fig = create_line_chart(config)
    data_table = generate_line_chart_data_table(config, chart_id)
    summary = f"Line chart '{config.title}' with {len(config.series)} series."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=config.title,
        summary=summary,
        data_table=data_table,
        chart_type="line",
        series_names=[s.name for s in config.series],
    ))

    return fig, accessible_html


def create_multi_series_chart(
    data: dict[str, list],
    x: list,
    title: str = "",
    xaxis_title: str = "Time",
    yaxis_title: str = "",
    height: int = 350,
    series_names: Optional[dict[str, str]] = None,
    series_units: Optional[dict[str, str]] = None,
) -> go.Figure:
    """
    Create a multi-series chart from a data dictionary (legacy compatibility).

    Args:
        data: Dict mapping series keys to y-values
        x: X-axis values
        title: Chart title
        xaxis_title: X-axis title
        yaxis_title: Y-axis title
        height: Chart height
        series_names: Optional display names for series
        series_units: Optional units for series

    Returns:
        Plotly Figure
    """
    series_list = []
    for i, (key, y_values) in enumerate(data.items()):
        name = series_names.get(key, key.replace("_", " ").title()) if series_names else key.replace("_", " ").title()
        unit = series_units.get(key, "") if series_units else ""
        display_name = f"{name} ({unit})" if unit else name

        series_list.append(LineSeries(
            x=x,
            y=y_values,
            name=display_name,
            color=SERIES_PALETTE[i % len(SERIES_PALETTE)],
            fill="tozeroy" if i == 0 else None,
            opacity=0.8 if i == 0 else 1.0,
        ))

    config = LineChartConfig(
        series=series_list,
        title=title,
        xaxis_title=xaxis_title,
        yaxis_title=yaxis_title,
        height=height,
        show_legend=True,
        legend_position="top",
    )

    return create_line_chart(config)


def create_multi_series_chart_with_accessibility(
    data: dict[str, list],
    x: list,
    title: str = "",
    xaxis_title: str = "Time",
    yaxis_title: str = "",
    height: int = 350,
    series_names: Optional[dict[str, str]] = None,
    series_units: Optional[dict[str, str]] = None,
    chart_id: str = "",
) -> Tuple[go.Figure, str]:
    """
    Create a multi-series chart with accessible data table.

    Args:
        data: Dict mapping series keys to y-values
        x: X-axis values
        title: Chart title
        xaxis_title: X-axis title
        yaxis_title: Y-axis title
        height: Chart height
        series_names: Optional display names for series
        series_units: Optional units for series
        chart_id: Unique chart ID

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"multiseries-{str(uuid.uuid4())[:8]}"

    fig = create_multi_series_chart(data, x, title, xaxis_title, yaxis_title, height, series_names, series_units)
    data_table = generate_line_chart_data_table(
        LineChartConfig(
            series=[
                LineSeries(
                    x=x,
                    y=y_values,
                    name=series_names.get(key, key.replace("_", " ").title()) if series_names else key.replace("_", " ").title(),
                    color=SERIES_PALETTE[i % len(SERIES_PALETTE)],
                )
                for i, (key, y_values) in enumerate(data.items())
            ],
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            height=height,
        ),
        chart_id,
    )
    summary = f"Multi-series chart '{title}' with {len(data)} series."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=title,
        summary=summary,
        data_table=data_table,
        chart_type="line",
        series_names=[series_names.get(k, k) if series_names else k for k in data.keys()],
    ))

    return fig, accessible_html


# =============================================================================
# SPARKLINE FACTORY
# =============================================================================

@dataclass
class SparklineConfig:
    """Sparkline configuration."""
    y: list
    color: str = SERIES_1
    fill: bool = True
    height: int = 60
    width: int = 200
    line_width: float = 1.5
    show_min_max: bool = False
    min_max_labels: bool = False


def create_sparkline(config: SparklineConfig) -> go.Figure:
    """
    Create a minimal sparkline chart.

    Args:
        config: Sparkline configuration

    Returns:
        Plotly Figure with sparkline
    """
    x = list(range(len(config.y)))

    fig = go.Figure()

    fill_color = f"{config.color}20" if config.fill else None

    fig.add_trace(go.Scatter(
        x=x,
        y=config.y,
        mode="lines",
        line=dict(color=config.color, width=config.line_width),
        fill="tozeroy" if config.fill else None,
        fillcolor=fill_color,
        hoverinfo="skip",
        showlegend=False,
    ))

    # Add min/max markers if requested
    if config.show_min_max and config.y:
        min_idx = np.argmin(config.y)
        max_idx = np.argmax(config.y)
        min_val = config.y[min_idx]
        max_val = config.y[max_idx]

        fig.add_trace(go.Scatter(
            x=[min_idx, max_idx],
            y=[min_val, max_val],
            mode="markers",
            marker=dict(
                size=6,
                color=[CHART_CRITICAL, CHART_GOOD],
                symbol=["triangle-down", "triangle-up"],
            ),
            hoverinfo="skip",
            showlegend=False,
        ))

    fig.update_layout(
        get_base_layout_with_reduced_motion(
            title="",
            height=config.height,
            width=config.width,
            show_legend=False,
            margin=dict(l=0, r=0, t=0, b=0),
        ),
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return fig


def create_sparkline_with_accessibility(config: SparklineConfig, chart_id: str = "", label: str = "Value") -> Tuple[go.Figure, str]:
    """
    Create a sparkline with accessible data table.

    Args:
        config: Sparkline configuration
        chart_id: Unique chart ID (auto-generated if not provided)
        label: Label for the data series

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"sparkline-{str(uuid.uuid4())[:8]}"

    fig = create_sparkline(config)
    data_table = generate_sparkline_data_table(config, chart_id, label)
    summary = f"Sparkline with {len(config.y)} data points. Range: {min(config.y):.2f} to {max(config.y):.2f}."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=f"Sparkline: {label}",
        summary=summary,
        data_table=data_table,
        chart_type="line",
    ))

    return fig, accessible_html


# =============================================================================
# COMPARISON CHART FACTORY
# =============================================================================

@dataclass
class ComparisonSeries:
    """Comparison chart series."""
    x: list
    y: list
    name: str
    session_id: Any
    color: Optional[str] = None


@dataclass
class ComparisonConfig:
    """Comparison chart configuration."""
    series: list[ComparisonSeries]
    title: str = ""
    xaxis_title: str = ""
    yaxis_title: str = ""
    height: int = 400
    normalize: bool = False


def create_comparison_chart(config: ComparisonConfig) -> go.Figure:
    """
    Create a session comparison chart (small multiples or overlaid).

    Args:
        config: Comparison configuration

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    for i, series in enumerate(config.series):
        color = series.color or SERIES_PALETTE[i % len(SERIES_PALETTE)]

        y_data = series.y
        if config.normalize and y_data:
            y_min, y_max = min(y_data), max(y_data)
            if y_max > y_min:
                y_data = [(v - y_min) / (y_max - y_min) * 100 for v in y_data]

        fig.add_trace(go.Scatter(
            x=series.x,
            y=y_data,
            name=series.name,
            mode="lines",
            line=dict(color=color, width=2),
            hovertemplate=f"<b>{series.name}</b><br>%{{x}}<br>%{{y:.1f}}<extra></extra>",
        ))

    fig.update_layout(
        get_base_layout_with_reduced_motion(
            title=config.title,
            height=config.height,
            show_legend=True,
            legend_position="top",
            xaxis_title=config.xaxis_title,
            yaxis_title=config.yaxis_title,
        )
    )

    return fig


def create_comparison_chart_with_accessibility(config: ComparisonConfig, chart_id: str = "") -> Tuple[go.Figure, str]:
    """
    Create a comparison chart with accessible data table.

    Args:
        config: Comparison configuration
        chart_id: Unique chart ID (auto-generated if not provided)

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"comparison-{str(uuid.uuid4())[:8]}"

    fig = create_comparison_chart(config)
    data_table = generate_comparison_chart_data_table(config, chart_id)
    summary = f"Comparison chart '{config.title}' with {len(config.series)} sessions."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=config.title,
        summary=summary,
        data_table=data_table,
        chart_type="line",
        series_names=[s.name for s in config.series],
    ))

    return fig, accessible_html


# =============================================================================
# SUBPLOT / SMALL MULTIPLES FACTORY
# =============================================================================

@dataclass
class SubplotConfig:
    """Subplot configuration."""
    rows: int
    cols: int
    subplot_titles: list[str]
    shared_xaxes: bool = True
    shared_yaxes: bool = False
    vertical_spacing: float = 0.12
    horizontal_spacing: float = 0.08
    height: int = 600


def create_subplot_figure(config: SubplotConfig) -> go.Figure:
    """
    Create a subplot figure for small multiples.

    Args:
        config: Subplot configuration

    Returns:
        Plotly Figure with subplots
    """
    fig = make_subplots(
        rows=config.rows,
        cols=config.cols,
        subplot_titles=config.subplot_titles,
        shared_xaxes=config.shared_xaxes,
        shared_yaxes=config.shared_yaxes,
        vertical_spacing=config.vertical_spacing,
        horizontal_spacing=config.horizontal_spacing,
    )

    # Apply base styling to all subplots
    for i in range(1, config.rows * config.cols + 1):
        fig.update_xaxes(
            gridcolor=BORDER_SUBTLE,
            gridwidth=1,
            linecolor=BORDER_DEFAULT,
            linewidth=1,
            tickfont=dict(family=FONT_FAMILY_BASE, size=9, color=TEXT_SECONDARY),
            row=(i - 1) // config.cols + 1,
            col=(i - 1) % config.cols + 1,
        )
        fig.update_yaxes(
            gridcolor=BORDER_SUBTLE,
            gridwidth=1,
            linecolor=BORDER_DEFAULT,
            linewidth=1,
            tickfont=dict(family=FONT_FAMILY_BASE, size=9, color=TEXT_SECONDARY),
            row=(i - 1) // config.cols + 1,
            col=(i - 1) % config.cols + 1,
        )

    fig.update_layout(
        get_base_layout_with_reduced_motion(
            title="",
            height=config.height,
            show_legend=False,
            margin=dict(l=50, r=20, t=60, b=50),
        ),
        paper_bgcolor=SURFACE_APP,
        plot_bgcolor=SURFACE_PRIMARY,
    )

    # Style subplot titles
    for annotation in fig.layout.annotations:
        annotation.update(
            font=dict(
                family=FONT_FAMILY_BASE,
                size=11,
                color=TEXT_SECONDARY,
                weight=FONT_WEIGHT_LABEL,
            ),
        )

    return fig


def add_trace_to_subplot(
    fig: go.Figure,
    trace: go.Scatter,
    row: int,
    col: int,
    secondary_y: bool = False
) -> go.Figure:
    """Add a trace to a specific subplot."""
    fig.add_trace(trace, row=row, col=col, secondary_y=secondary_y)
    return fig


# =============================================================================
# BAR CHART FACTORY
# =============================================================================

@dataclass
class BarSeries:
    """Bar chart series."""
    x: list
    y: list
    name: str
    color: Optional[str] = None
    text: Optional[list] = None
    text_position: str = "outside"


@dataclass
class BarChartConfig:
    """Bar chart configuration."""
    series: list[BarSeries]
    title: str = ""
    xaxis_title: str = ""
    yaxis_title: str = ""
    height: int = 400
    orientation: Literal["v", "h"] = "v"
    barmode: Literal["group", "stack", "overlay"] = "group"
    show_legend: bool = True


def create_bar_chart(config: BarChartConfig) -> go.Figure:
    """
    Create a bar chart.

    Args:
        config: Bar chart configuration

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    for i, series in enumerate(config.series):
        color = series.color or SERIES_PALETTE[i % len(SERIES_PALETTE)]

        if config.orientation == "v":
            fig.add_trace(go.Bar(
                x=series.x,
                y=series.y,
                name=series.name,
                marker_color=color,
                text=series.text,
                textposition=series.text_position,
                textfont=dict(family=FONT_FAMILY_BASE, size=10, color=TEXT_PRIMARY),
                hovertemplate="%{y}<extra>%{fullData.name}</extra>",
            ))
        else:
            fig.add_trace(go.Bar(
                x=series.y,
                y=series.x,
                name=series.name,
                marker_color=color,
                text=series.text,
                textposition=series.text_position,
                textfont=dict(family=FONT_FAMILY_BASE, size=10, color=TEXT_PRIMARY),
                orientation="h",
                hovertemplate="%{x}<extra>%{fullData.name}</extra>",
            ))

    fig.update_layout(
        get_base_layout_with_reduced_motion(
            title=config.title,
            height=config.height,
            show_legend=config.show_legend,
            legend_position="top",
            xaxis_title=config.xaxis_title,
            yaxis_title=config.yaxis_title,
        ),
        barmode=config.barmode,
        bargap=0.2,
        bargroupgap=0.1,
    )

    return fig


def create_bar_chart_with_accessibility(config: BarChartConfig, chart_id: str = "") -> Tuple[go.Figure, str]:
    """
    Create a bar chart with accessible data table.

    Args:
        config: Bar chart configuration
        chart_id: Unique chart ID (auto-generated if not provided)

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"bar-{str(uuid.uuid4())[:8]}"

    fig = create_bar_chart(config)
    data_table = generate_bar_chart_data_table(config, chart_id)
    summary = f"Bar chart '{config.title}' with {len(config.series)} series."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=config.title,
        summary=summary,
        data_table=data_table,
        chart_type="bar",
        series_names=[s.name for s in config.series],
    ))

    return fig, accessible_html


# =============================================================================
# PIE / DONUT CHART FACTORY
# =============================================================================

@dataclass
class PieChartConfig:
    """Pie/Donut chart configuration."""
    labels: list[str]
    values: list[float]
    title: str = ""
    hole: float = 0.5  # 0 for pie, >0 for donut
    height: int = 400
    colors: Optional[list[str]] = None
    show_legend: bool = True
    text_info: str = "label+percent"
    text_position: str = "inside"


def create_pie_chart(config: PieChartConfig) -> go.Figure:
    """
    Create a pie or donut chart.

    Args:
        config: Pie chart configuration

    Returns:
        Plotly Figure
    """
    colors = config.colors or SERIES_PALETTE

    fig = go.Figure()

    fig.add_trace(go.Pie(
        labels=config.labels,
        values=config.values,
        hole=config.hole,
        marker=dict(
            colors=colors[:len(config.labels)],
            line=dict(color=SURFACE_APP, width=2),
        ),
        textinfo=config.text_info,
        textposition=config.text_position,
        textfont=dict(family=FONT_FAMILY_BASE, size=11, color=TEXT_ON_ACCENT),
        hovertemplate="<b>%{label}</b><br>%{value}<br>%{percent}<extra></extra>",
        showlegend=config.show_legend,
    ))

    fig.update_layout(
        get_base_layout_with_reduced_motion(
            title=config.title,
            height=config.height,
            show_legend=config.show_legend,
            legend_position="right",
            margin=dict(l=20, r=20, t=60, b=20),
        ),
    )

    return fig


def create_pie_chart_with_accessibility(config: PieChartConfig, chart_id: str = "") -> Tuple[go.Figure, str]:
    """
    Create a pie chart with accessible data table.

    Args:
        config: Pie chart configuration
        chart_id: Unique chart ID (auto-generated if not provided)

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"pie-{str(uuid.uuid4())[:8]}"

    fig = create_pie_chart(config)
    data_table = generate_pie_chart_data_table(config, chart_id)
    summary = f"Pie chart '{config.title}' with {len(config.labels)} segments. Total: {sum(config.values):.1f}."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=config.title,
        summary=summary,
        data_table=data_table,
        chart_type="pie",
        series_names=config.labels,
    ))

    return fig, accessible_html


# =============================================================================
# SCATTER CHART FACTORY
# =============================================================================

@dataclass
class ScatterSeries:
    """Scatter plot series."""
    x: list
    y: list
    name: str
    color: Optional[str] = None
    size: Optional[list] = None
    size_max: int = 20
    symbol: str = "circle"
    opacity: float = 0.7


@dataclass
class ScatterConfig:
    """Scatter chart configuration."""
    series: list[ScatterSeries]
    title: str = ""
    xaxis_title: str = ""
    yaxis_title: str = ""
    height: int = 400
    show_legend: bool = True
    trendline: bool = False


def create_scatter_chart(config: ScatterConfig) -> go.Figure:
    """
    Create a scatter plot.

    Args:
        config: Scatter chart configuration

    Returns:
        Plotly Figure
    """
    fig = go.Figure()

    for i, series in enumerate(config.series):
        color = series.color or SERIES_PALETTE[i % len(SERIES_PALETTE)]

        marker = dict(
            color=color,
            size=series.size if series.size else 8,
            sizemode="area" if series.size else "diameter",
            sizeref=2. * max(series.size) / (config.size_max ** 2) if series.size else 1,
            sizemin=4,
            symbol=series.symbol,
            opacity=series.opacity,
            line=dict(width=0),
        )

        fig.add_trace(go.Scatter(
            x=series.x,
            y=series.y,
            name=series.name,
            mode="markers",
            marker=marker,
            hovertemplate="<b>%{fullData.name}</b><br>%{x}<br>%{y}<extra></extra>",
        ))

    fig.update_layout(
        get_base_layout_with_reduced_motion(
            title=config.title,
            height=config.height,
            show_legend=config.show_legend,
            legend_position="top",
            xaxis_title=config.xaxis_title,
            yaxis_title=config.yaxis_title,
        )
    )

    return fig


def create_scatter_chart_with_accessibility(config: ScatterConfig, chart_id: str = "") -> Tuple[go.Figure, str]:
    """
    Create a scatter chart with accessible data table.

    Args:
        config: Scatter chart configuration
        chart_id: Unique chart ID (auto-generated if not provided)

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"scatter-{str(uuid.uuid4())[:8]}"

    fig = create_scatter_chart(config)
    data_table = generate_scatter_chart_data_table(config, chart_id)
    summary = f"Scatter chart '{config.title}' with {len(config.series)} series."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=config.title,
        summary=summary,
        data_table=data_table,
        chart_type="scatter",
        series_names=[s.name for s in config.series],
    ))

    return fig, accessible_html


# =============================================================================
# HEATMAP FACTORY
# =============================================================================

@dataclass
class HeatmapConfig:
    """Heatmap configuration."""
    z: list[list[float]]
    x: list[str]
    y: list[str]
    title: str = ""
    colorscale: str = "RdYlGn"  # Red-Yellow-Green (reversed for our theme)
    height: int = 400
    show_colorbar: bool = True
    colorbar_title: str = ""
    text_template: str = "%{z:.1f}"


def create_heatmap(config: HeatmapConfig) -> go.Figure:
    """
    Create a heatmap.

    Args:
        config: Heatmap configuration

    Returns:
        Plotly Figure
    """
    # Use a CVD-safe colorscale
    custom_colorscale = [
        [0.0, CHART_CRITICAL],
        [0.5, CHART_WARNING],
        [1.0, CHART_GOOD],
    ]

    fig = go.Figure()

    fig.add_trace(go.Heatmap(
        z=config.z,
        x=config.x,
        y=config.y,
        colorscale=custom_colorscale,
        colorbar=dict(
            title=dict(
                text=config.colorbar_title,
                font=dict(family=FONT_FAMILY_BASE, size=11, color=TEXT_SECONDARY),
            ),
            tickfont=dict(family=FONT_FAMILY_BASE, size=10, color=TEXT_SECONDARY),
            len=0.8,
            thickness=12,
            outlinewidth=1,
            outlinecolor=BORDER_DEFAULT,
        ) if config.show_colorbar else None,
        hovertemplate="<b>%{y}</b> / <b>%{x}</b><br>Value: %{z}<extra></extra>",
        showscale=config.show_colorbar,
    ))

    fig.update_layout(
        get_base_layout_with_reduced_motion(
            title=config.title,
            height=config.height,
            show_legend=False,
            margin=dict(l=80, r=60, t=60, b=50),
        ),
        xaxis=dict(
            side="top",
            tickfont=dict(family=FONT_FAMILY_BASE, size=10, color=TEXT_SECONDARY),
        ),
        yaxis=dict(
            tickfont=dict(family=FONT_FAMILY_BASE, size=10, color=TEXT_SECONDARY),
            autorange="reversed",
        ),
    )

    return fig


def create_heatmap_with_accessibility(config: HeatmapConfig, chart_id: str = "") -> Tuple[go.Figure, str]:
    """
    Create a heatmap with accessible data table.

    Args:
        config: Heatmap configuration
        chart_id: Unique chart ID (auto-generated if not provided)

    Returns:
        Tuple of (Plotly Figure, accessible HTML container string)
    """
    if not chart_id:
        import uuid
        chart_id = f"heatmap-{str(uuid.uuid4())[:8]}"

    fig = create_heatmap(config)
    data_table = generate_heatmap_data_table(config, chart_id)
    summary = f"Heatmap '{config.title}' with {len(config.y)} rows and {len(config.x)} columns."

    accessible_html = render_accessible_chart_container(ChartAccessibilityProps(
        chart_id=chart_id,
        title=config.title,
        summary=summary,
        data_table=data_table,
        chart_type="heatmap",
    ))

    return fig, accessible_html


# =============================================================================
# STATUS INDICATOR (for telemetry cards)
# =============================================================================

def create_status_indicator(
    value: float,
    metric: str,
    unit: str = "",
    thresholds: Optional[dict] = None,
    size: Literal["sm", "md", "lg"] = "md"
) -> dict:
    """
    Create a status indicator configuration for telemetry cards.
    Returns dict with color, label, and icon for custom rendering.

    Args:
        value: Current value
        metric: Metric name
        unit: Unit string
        thresholds: Custom thresholds
        size: Size variant

    Returns:
        Dict with status info
    """
    metric_lower = metric.lower()
    thresh = thresholds or GAUGE_THRESHOLD_TOKENS.get(metric_lower, {})

    green_max = thresh.get("green_max", 100)
    amber_max = thresh.get("amber_max", 100)
    red_max = thresh.get("red_max", 100)
    green_min = thresh.get("green_min", 0)
    amber_min = thresh.get("amber_min", 0)
    red_min = thresh.get("red_min", 0)

    # Determine status
    if green_min <= value <= green_max:
        status = "good"
        color = CHART_GOOD
        icon = "●"
    elif amber_min <= value <= amber_max:
        status = "warning"
        color = CHART_WARNING
        icon = "●"
    else:
        status = "critical"
        color = CHART_CRITICAL
        icon = "●"

    size_map = {"sm": "0.75rem", "md": "1rem", "lg": "1.5rem"}

    return {
        "status": status,
        "color": color,
        "icon": icon,
        "label": f"{value:.1f} {unit}".strip(),
        "size": size_map[size],
    }


# =============================================================================
# CHART THEME EXPORT (for Plotly defaults)
# =============================================================================

def get_plotly_template() -> go.layout.Template:
    """
    Get a Plotly template with design system tokens.
    Can be registered as default template.
    """
    return go.layout.Template(
        layout=dict(
            paper_bgcolor=SURFACE_APP,
            plot_bgcolor=SURFACE_PRIMARY,
            font=dict(
                family=FONT_FAMILY_BASE,
                color=TEXT_PRIMARY,
                size=12,
            ),
            title=dict(
                font=dict(
                    family=FONT_FAMILY_BASE,
                    size=14,
                    color=TEXT_PRIMARY,
                    weight=FONT_WEIGHT_H3,
                ),
                x=0.02,
            ),
            xaxis=dict(
                gridcolor=BORDER_SUBTLE,
                gridwidth=1,
                linecolor=BORDER_DEFAULT,
                linewidth=1,
                tickfont=dict(family=FONT_FAMILY_BASE, size=10, color=TEXT_SECONDARY),
                title=dict(font=dict(family=FONT_FAMILY_BASE, size=11, color=TEXT_SECONDARY, weight=FONT_WEIGHT_LABEL)),
            ),
            yaxis=dict(
                gridcolor=BORDER_SUBTLE,
                gridwidth=1,
                linecolor=BORDER_DEFAULT,
                linewidth=1,
                tickfont=dict(family=FONT_FAMILY_BASE, size=10, color=TEXT_SECONDARY),
                title=dict(font=dict(family=FONT_FAMILY_BASE, size=11, color=TEXT_SECONDARY, weight=FONT_WEIGHT_LABEL)),
            ),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                bordercolor=BORDER_DEFAULT,
                borderwidth=1,
                font=dict(family=FONT_FAMILY_BASE, size=11, color=TEXT_SECONDARY),
            ),
            hoverlabel=dict(
                bgcolor=SURFACE_SECONDARY,
                bordercolor=BORDER_DEFAULT,
                font=dict(family=FONT_FAMILY_BASE, size=11, color=TEXT_PRIMARY),
            ),
            colorway=SERIES_PALETTE,
        )
    )


# Register template globally
I20_TEMPLATE = get_plotly_template()


# =============================================================================
# LEGACY COMPATIBILITY
# =============================================================================

# Legacy function signatures for backward compatibility
def create_gauge_chart(
    metric: str,
    value: float,
    min_val: float = 0,
    max_val: float = 100,
    unit: str = "",
    title: str = "",
    thresholds: Optional[dict] = None,
    height: int = 280,
) -> go.Figure:
    """Legacy gauge chart function."""
    return create_gauge(GaugeConfig(
        metric=metric,
        value=value,
        min_val=min_val,
        max_val=max_val,
        unit=unit,
        title=title,
        thresholds=thresholds,
        height=height,
    ))


def create_multi_series_chart_legacy(
    data: dict,
    x: list,
    title: str = "",
    xaxis_title: str = "Time",
    yaxis_title: str = "",
    height: int = 350,
) -> go.Figure:
    """Legacy multi-series chart function."""
    return create_multi_series_chart(data, x, title, xaxis_title, yaxis_title, height)


def create_comparison_chart_legacy(
    sessions_data: dict,
    metric: str,
    title: str = "",
    height: int = 400,
) -> go.Figure:
    """Legacy comparison chart function."""
    series = []
    for i, (session_id, data) in enumerate(sessions_data.items()):
        series.append(ComparisonSeries(
            x=data.get("timestamps", []),
            y=data.get(metric, []),
            name=f"Session {session_id}",
            session_id=session_id,
            color=SERIES_PALETTE[i % len(SERIES_PALETTE)],
        ))
    return create_comparison_chart(ComparisonConfig(
        series=series,
        title=title,
        xaxis_title="Time",
        yaxis_title=metric.replace("_", " ").title(),
        height=height,
    ))


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Color palettes
    "SERIES_PALETTE",
    "SERIES_FILL_PALETTE",
    "STATUS_PALETTE",
    "DATASOURCE_PALETTE",
    "DIAG_PALETTE",
    # Base layout
    "get_base_layout",
    "get_base_layout_with_reduced_motion",
    "get_plotly_template",
    "I20_TEMPLATE",
    # Gauge
    "GaugeConfig",
    "create_gauge",
    "create_gauge_cluster",
    "create_gauge_with_accessibility",
    # Line
    "LineSeries",
    "LineChartConfig",
    "create_line_chart",
    "create_multi_series_chart",
    "create_line_chart_with_accessibility",
    "create_multi_series_chart_with_accessibility",
    # Sparkline
    "SparklineConfig",
    "create_sparkline",
    "create_sparkline_with_accessibility",
    # Comparison
    "ComparisonSeries",
    "ComparisonConfig",
    "create_comparison_chart",
    "create_comparison_chart_with_accessibility",
    # Subplots
    "SubplotConfig",
    "create_subplot_figure",
    "add_trace_to_subplot",
    # Bar
    "BarSeries",
    "BarChartConfig",
    "create_bar_chart",
    "create_bar_chart_with_accessibility",
    # Pie
    "PieChartConfig",
    "create_pie_chart",
    "create_pie_chart_with_accessibility",
    # Scatter
    "ScatterSeries",
    "ScatterConfig",
    "create_scatter_chart",
    "create_scatter_chart_with_accessibility",
    # Heatmap
    "HeatmapConfig",
    "create_heatmap",
    "create_heatmap_with_accessibility",
    # Status indicator
    "create_status_indicator",
    # Accessibility utilities
    "generate_chart_data_table",
    "generate_gauge_data_table",
    "generate_line_chart_data_table",
    "generate_sparkline_data_table",
    "generate_bar_chart_data_table",
    "generate_pie_chart_data_table",
    "generate_scatter_chart_data_table",
    "generate_heatmap_data_table",
    "generate_comparison_chart_data_table",
    # Legacy compatibility
    "create_gauge_chart",
    "create_multi_series_chart_legacy",
    "create_comparison_chart_legacy",
]