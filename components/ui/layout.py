"""
i20 AI Garage - Layout Helpers

Reusable layout components and utilities for consistent page structure,
responsive grids, and component arrangements.
"""

from typing import Final, Literal, Optional
from dataclasses import dataclass
from functools import lru_cache

import streamlit as st

from .tokens import (
    BREAKPOINT_MOBILE, BREAKPOINT_TABLET, BREAKPOINT_LAPTOP, BREAKPOINT_DESKTOP,
    GAP_CARD_GRID, GAP_SECTION, GAP_PAGE, GAP_FIELD, PADDING_PAGE,
    SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED,
    TOP_BAR_HEIGHT,
    CONTAINER_MAX_WIDTHS,
)
from .styles import inject_global_css


# =============================================================================
# LAYOUT CONSTANTS
# =============================================================================

# Grid column configurations
GRID_COLUMNS = {
    "mobile": 1,
    "tablet": 2,
    "laptop": 3,
    "desktop": 4,
}

# Gauge cluster specific (6 gauges max)
GAUGE_GRID_COLUMNS = {
    "mobile": 1,
    "tablet": 2,
    "laptop": 3,
    "desktop": 3,  # 3x2 grid for 6 gauges
}

# Metric card grid
METRIC_GRID_COLUMNS = {
    "mobile": 1,
    "tablet": 2,
    "laptop": 3,
    "desktop": 4,
}

# Chart grid (typically 2-3 charts)
CHART_GRID_COLUMNS = {
    "mobile": 1,
    "tablet": 2,
    "laptop": 2,
    "desktop": 3,
}

# Form field grid
FORM_GRID_COLUMNS = {
    "mobile": 1,
    "tablet": 2,
    "laptop": 2,
    "desktop": 3,
}


# =============================================================================
# RESPONSIVE GRID HELPERS
# =============================================================================

def responsive_grid_css(
    columns: dict[str, int],
    gap: str = GAP_CARD_GRID,
    min_column_width: str = "280px"
) -> str:
    """
    Generate CSS for a responsive CSS Grid layout using fluid auto-fit approach.

    Args:
        columns: Dict mapping breakpoint names to column counts (used for reference)
        gap: Gap between grid items
        min_column_width: Minimum width before wrapping

    Returns:
        CSS string for the grid container
    """
    # Use fluid auto-fit approach - no media queries needed
    # The grid will automatically adjust based on min_column_width
    return f"""
.i20-grid-responsive {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax({min_column_width}, 1fr));
  gap: {gap};
}}"""


def auto_fit_grid_css(
    min_width: str = "280px",
    max_width: str = "1fr",
    gap: str = GAP_CARD_GRID
) -> str:
    """
    Generate CSS for an auto-fit grid (items wrap based on available space).

    Args:
        min_width: Minimum column width before wrapping
        max_width: Maximum column width (usually 1fr)
        gap: Gap between grid items

    Returns:
        CSS string for the grid container
    """
    return f"""
.i20-grid-auto-fit {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax({min_width}, {max_width}));
  gap: {gap};
}}"""


def fixed_grid_css(columns: int, gap: str = GAP_CARD_GRID) -> str:
    """
    Generate CSS for a fixed column grid.

    Args:
        columns: Number of columns
        gap: Gap between grid items

    Returns:
        CSS string for the grid container
    """
    return f"""
.i20-grid-fixed-{columns} {{
  display: grid;
  grid-template-columns: repeat({columns}, 1fr);
  gap: {gap};
}}"""


# Pre-defined grid CSS classes (fluid auto-fit approach)
GAUGE_GRID_CSS: Final[str] = auto_fit_grid_css("280px", "1fr", GAP_CARD_GRID)
METRIC_GRID_CSS: Final[str] = auto_fit_grid_css("200px", "1fr", GAP_CARD_GRID)
CHART_GRID_CSS: Final[str] = auto_fit_grid_css("500px", "1fr", GAP_SECTION)
FORM_GRID_CSS: Final[str] = auto_fit_grid_css("280px", "1fr", GAP_FIELD)
AUTO_FIT_CARD_CSS: Final[str] = auto_fit_grid_css("320px", "1fr", GAP_CARD_GRID)
AUTO_FIT_METRIC_CSS: Final[str] = auto_fit_grid_css("200px", "1fr", GAP_CARD_GRID)


# =============================================================================
# STREAMLIT LAYOUT HELPERS
# =============================================================================

@dataclass
class ColumnSpec:
    """Specification for a Streamlit column."""
    ratio: int = 1
    gap: str = "medium"  # "small", "medium", "large"
    vertical_alignment: str = "top"  # "top", "center", "bottom"


def create_columns(
    specs: list[ColumnSpec],
    gap: Optional[str] = None
) -> list:
    """
    Create Streamlit columns with consistent configuration.

    Args:
        specs: List of ColumnSpec objects
        gap: Override gap for all columns

    Returns:
        List of Streamlit column objects
    """
    ratios = [spec.ratio for spec in specs]
    return st.columns(ratios, gap=gap or "medium")


def gauge_cluster_columns(count: int = 6) -> list:
    """
    Create columns optimized for gauge cluster display.

    Args:
        count: Number of gauges (typically 6)

    Returns:
        List of Streamlit column objects
    """
    # For 6 gauges: 3 columns on desktop, 2 on tablet, 1 on mobile
    # Streamlit doesn't have responsive columns, so we use 3 as base
    if count <= 3:
        return st.columns(count, gap="medium")
    elif count <= 6:
        return st.columns(3, gap="medium")
    else:
        # For more gauges, use 4 columns
        return st.columns(4, gap="medium")


def metric_row_columns(count: int = 4) -> list:
    """
    Create columns for metric card row.

    Args:
        count: Number of metric cards

    Returns:
        List of Streamlit column objects
    """
    if count <= 4:
        return st.columns(count, gap="medium")
    else:
        return st.columns(4, gap="medium")


def chart_columns(count: int = 2) -> list:
    """
    Create columns for chart display.

    Args:
        count: Number of charts side by side

    Returns:
        List of Streamlit column objects
    """
    return st.columns(count, gap="large")


def form_field_columns(fields_per_row: int = 2) -> list:
    """
    Create columns for form fields.

    Args:
        fields_per_row: Number of fields per row (1-3)

    Returns:
        List of Streamlit column objects
    """
    return st.columns(fields_per_row, gap="medium")


# =============================================================================
# PAGE STRUCTURE HELPERS
# =============================================================================

def page_header(title: str, subtitle: str = "", icon: str = "") -> None:
    """
    Render a consistent page header.

    Args:
        title: Page title
        subtitle: Optional subtitle/description
        icon: Optional icon emoji or HTML
    """
    st.markdown(f"""
<div class="i20-page-header" style="margin-bottom: var(--i20-gap-page);">
  <div style="display: flex; align-items: baseline; gap: var(--i20-gap-inline); margin-bottom: var(--i20-space-2);">
    {f'<span style="font-size: var(--i20-font-size-h1);">{icon}</span>' if icon else ''}
    <h1 class="i20-h1" style="margin: 0;">{title}</h1>
  </div>
  {f'<p class="i20-body-sm" style="margin: 0; color: var(--i20-color-text-secondary);">{subtitle}</p>' if subtitle else ''}
</div>
""", unsafe_allow_html=True)


def section_header(title: str, description: str = "", action: str = "", level: int = 2) -> None:
    """
    Render a section header within a page.

    Args:
        title: Section title
        description: Optional description
        action: Optional action button HTML
        level: Heading level (2, 3, or 4). Defaults to 2 for h2.
    """
    level = max(2, min(4, level))  # Clamp to valid heading levels
    heading_class = f"i20-h{level}"
    heading_tag = f"h{level}"
    st.markdown(f"""
<div class="i20-section-header" style="margin-bottom: var(--i20-gap-section); display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: var(--i20-gap-field);">
  <div>
    <{heading_tag} class="{heading_class}" style="margin: 0;">{title}</{heading_tag}>
    {f'<p class="i20-caption" style="margin: var(--i20-space-1) 0 0 0;">{description}</p>' if description else ''}
  </div>
  {f'<div>{action}</div>' if action else ''}
</div>
""", unsafe_allow_html=True)


def card_container(content: str, class_name: str = "i20-card", extra_style: str = "") -> str:
    """
    Wrap content in a card container.

    Args:
        content: HTML content to wrap
        class_name: CSS class for the card
        extra_style: Additional inline styles

    Returns:
        HTML string with card wrapper
    """
    return f'<div class="{class_name}" style="{extra_style}">{content}</div>'


def grid_container(items: list[str], grid_type: Literal["gauge", "metric", "chart", "form", "auto-fit", "auto-fit-metric"] = "auto-fit") -> str:
    """
    Create a responsive grid container with items.

    Args:
        items: List of HTML strings for grid items
        grid_type: Type of grid layout

    Returns:
        HTML string with grid container and items
    """
    grid_class_map = {
        "gauge": "i20-grid-responsive i20-grid-gauge",
        "metric": "i20-grid-responsive i20-grid-metric",
        "chart": "i20-grid-responsive i20-grid-chart",
        "form": "i20-grid-responsive i20-grid-form",
        "auto-fit": "i20-grid-auto-fit",
        "auto-fit-metric": "i20-grid-auto-fit-metric",
    }
    grid_class = grid_class_map.get(grid_type, "i20-grid-auto-fit")
    items_html = "".join(f'<div class="i20-grid-item">{item}</div>' for item in items)
    return f'<div class="{grid_class}">{items_html}</div>'


# =============================================================================
# SIDEBAR LAYOUT
# =============================================================================

def sidebar_section(title: str, content: str, expanded: bool = True) -> str:
    """
    Create a collapsible sidebar section.

    Args:
        title: Section title
        content: Section content HTML
        expanded: Whether section is expanded by default

    Returns:
        HTML string for sidebar section
    """
    return f"""
<div class="i20-sidebar-section" style="margin-bottom: var(--i20-gap-sidebar);">
  <button class="i20-sidebar-section-toggle"
          style="width: 100%; display: flex; align-items: center; justify-content: space-between;
                 background: none; border: none; color: var(--i20-color-text-secondary);
                 font-size: var(--i20-font-size-label); font-weight: var(--i20-font-weight-label);
                 text-transform: uppercase; letter-spacing: var(--i20-letter-spacing-label);
                 padding: var(--i20-space-2) 0; cursor: pointer;"
          aria-expanded="{str(expanded).lower()}"
          onclick="this.nextElementSibling.style.display = this.getAttribute('aria-expanded') === 'true' ? 'none' : 'block';
                   this.setAttribute('aria-expanded', this.getAttribute('aria-expanded') === 'true' ? 'false' : 'true');
                   this.querySelector('.i20-chevron').style.transform = this.getAttribute('aria-expanded') === 'true' ? 'rotate(0deg)' : 'rotate(-90deg)';">
    <span>{title}</span>
    <span class="i20-chevron" style="transition: transform var(--i20-transition-fast);
           transform: {'rotate(0deg)' if expanded else 'rotate(-90deg)'};">
      ▼
    </span>
  </button>
  <div class="i20-sidebar-section-content" style="display: {'block' if expanded else 'none'};">
    {content}
  </div>
</div>
"""


def sidebar_nav_item(
    label: str,
    icon: str,
    active: bool = False,
    badge: str = "",
    href: str = "",
    onclick: str = ""
) -> str:
    """
    Create a sidebar navigation item.

    Args:
        label: Navigation label
        icon: Icon emoji or HTML
        active: Whether this item is active
        badge: Optional badge text
        href: Optional link href (for anchor tags)
        onclick: Optional click handler

    Returns:
        HTML string for nav item
    """
    active_class = "i20-nav-item-active" if active else ""
    badge_html = f'<span class="i20-badge i20-badge-primary" style="margin-left: auto; font-size: 0.6rem;">{badge}</span>' if badge else ""

    if href:
        return f"""
<a href="{href}"
   class="i20-nav-item {active_class}"
   style="display: flex; align-items: center; gap: var(--i20-gap-inline);
          padding: var(--i20-space-2) var(--i20-space-3);
          border-radius: var(--i20-radius-sm);
          color: var(--i20-color-text-primary);
          text-decoration: none;
          transition: all var(--i20-transition-fast);
          {'background: var(--i20-color-accent-selected); color: var(--i20-color-accent-primary);' if active else 'background: transparent;'}">
  <span style="font-size: 1.25rem;">{icon}</span>
  <span style="flex: 1; font-size: var(--i20-font-size-body); font-weight: var(--i20-font-weight-body);">{label}</span>
  {badge_html}
</a>
"""
    else:
        return f"""
<button class="i20-nav-item {active_class}"
        style="display: flex; align-items: center; gap: var(--i20-gap-inline);
               width: 100%; padding: var(--i20-space-2) var(--i20-space-3);
               border-radius: var(--i20-radius-sm);
               color: var(--i20-color-text-primary);
               background: {'var(--i20-color-accent-selected)' if active else 'transparent'};
               border: none; cursor: pointer; text-align: left;
               transition: all var(--i20-transition-fast);"
        onclick="{onclick}"
        aria-current="{'page' if active else 'false'}">
  <span style="font-size: 1.25rem;">{icon}</span>
  <span style="flex: 1; font-size: var(--i20-font-size-body); font-weight: var(--i20-font-weight-body);">{label}</span>
  {badge_html}
</button>
"""


# =============================================================================
# TOP BAR LAYOUT
# =============================================================================

def top_bar(
    page_title: str,
    breadcrumb: list[tuple[str, str]] = None,
    actions: list[str] = None,
    status_indicators: list[str] = None
) -> str:
    """
    Generate the top bar HTML.

    Args:
        page_title: Current page title
        breadcrumb: List of (label, href) tuples for breadcrumb
        actions: List of action button HTML strings
        status_indicators: List of status indicator HTML strings

    Returns:
        HTML string for top bar
    """
    breadcrumb_html = ""
    if breadcrumb:
        crumbs = []
        for i, (label, href) in enumerate(breadcrumb):
            if i == len(breadcrumb) - 1:
                crumbs.append(f'<span class="i20-breadcrumb-current" style="color: var(--i20-color-text-secondary);">{label}</span>')
            else:
                crumbs.append(f'<a href="{href}" class="i20-breadcrumb-item" style="color: var(--i20-color-text-muted); text-decoration: none;">{label}</a>')
        separator = ' <span style="color: var(--i20-color-text-muted);">/</span> '
        breadcrumb_html = f'<nav class="i20-breadcrumb" style="display: flex; align-items: center; gap: var(--i20-space-2); font-size: var(--i20-font-size-caption);">{separator.join(crumbs)}</nav>'

    actions_html = ""
    if actions:
        actions_html = f'<div class="i20-top-bar-actions" style="display: flex; align-items: center; gap: var(--i20-gap-inline);">{"".join(actions)}</div>'

    status_html = ""
    if status_indicators:
        status_html = f'<div class="i20-top-bar-status" style="display: flex; align-items: center; gap: var(--i20-gap-inline);">{"".join(status_indicators)}</div>'

    return f"""
<header class="i20-top-bar" style="height: var(--i20-top-bar-height);
    background: var(--i20-top-bar-bg);
    border-bottom: var(--i20-top-bar-border);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 var(--i20-padding-page); position: sticky; top: 0; z-index: var(--i20-z-dropdown);">
  <div class="i20-top-bar-left" style="display: flex; align-items: center; gap: var(--i20-gap-field);">
    {breadcrumb_html}
    <h1 class="i20-h3" style="margin: 0;">{page_title}</h1>
  </div>
  <div class="i20-top-bar-right" style="display: flex; align-items: center; gap: var(--i20-gap-field);">
    {status_html}
    {actions_html}
  </div>
</header>
"""


def status_indicator(label: str, status: Literal["success", "warning", "critical", "info", "neutral"], dot: bool = True) -> str:
    """
    Generate a status indicator for top bar.

    Args:
        label: Status label
        status: Status type
        dot: Whether to show colored dot

    Returns:
        HTML string for status indicator
    """
    status_colors = {
        "success": "var(--i20-color-status-success)",
        "warning": "var(--i20-color-status-warning)",
        "critical": "var(--i20-color-status-critical)",
        "info": "var(--i20-color-status-info)",
        "neutral": "var(--i20-color-status-neutral)",
    }
    color = status_colors.get(status, "var(--i20-color-status-neutral)")

    dot_html = f'<span style="width: 8px; height: 8px; border-radius: 50%; background: {color};"></span>' if dot else ""

    return f"""
<div class="i20-status-indicator" style="display: flex; align-items: center; gap: var(--i20-space-1); font-size: var(--i20-font-size-caption); color: var(--i20-color-text-secondary);">
  {dot_html}
  <span>{label}</span>
</div>
"""


# =============================================================================
# RESPONSIVE UTILITIES
# =============================================================================

def responsive_container(content: str, max_width: str = "1400px") -> str:
    """
    Wrap content in a responsive container with max-width and padding.

    Args:
        content: HTML content
        max_width: Maximum content width

    Returns:
        HTML string with container
    """
    return f"""
<div class="i20-responsive-container" style="max-width: {max_width}; margin: 0 auto; padding: 0 var(--i20-padding-page);">
  {content}
</div>
"""


def visually_hidden(content: str) -> str:
    """
    Wrap content for screen readers only (visually hidden).

    Args:
        content: Content to hide visually

    Returns:
        HTML string with visually hidden wrapper
    """
    return f'<span class="i20-visually-hidden" style="position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0;">{content}</span>'


# =============================================================================
# CSS INJECTION FOR LAYOUT
# =============================================================================

LAYOUT_CSS: Final[str] = f"""
/* ============================================================================
   LAYOUT GRID STYLES
   ============================================================================ */

{GAUGE_GRID_CSS}
{METRIC_GRID_CSS}
{CHART_GRID_CSS}
{FORM_GRID_CSS}
{AUTO_FIT_CARD_CSS}
{AUTO_FIT_METRIC_CSS}

.i20-grid-item {{
  min-width: 0; /* Prevents grid overflow */
}}

/* ============================================================================
   PAGE STRUCTURE
   ============================================================================ */

.i20-page-header {{
  padding-bottom: var(--i20-space-4);
  border-bottom: 1px solid var(--i20-color-border-subtle);
}}

.i20-section-header {{
  padding-bottom: var(--i20-space-3);
  border-bottom: 1px solid var(--i20-color-border-subtle);
}}

.i20-responsive-container {{
  width: 100%;
}}

/* ============================================================================
   SIDEBAR
   ============================================================================ */

.i20-sidebar-section-toggle:hover {{
  color: var(--i20-color-text-primary) !important;
}}

.i20-sidebar-section-content {{
  animation: i20-slide-down 0.2s ease;
}}

@keyframes i20-slide-down {{
  from {{ opacity: 0; transform: translateY(-8px); }}
  to {{ opacity: 1; transform: translateY(0); }}
}}

.i20-nav-item {{
  border-radius: var(--i20-radius-sm);
  margin-bottom: var(--i20-space-1);
}}

.i20-nav-item:hover:not(.i20-nav-item-active) {{
  background: var(--i20-color-surface-interactive) !important;
  color: var(--i20-color-text-primary) !important;
}}

.i20-nav-item-active {{
  background: var(--i20-color-accent-selected) !important;
  color: var(--i20-color-accent-primary) !important;
}}

.i20-nav-item:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
}}

/* ============================================================================
   TOP BAR
   ============================================================================ */

.i20-breadcrumb-item:hover {{
  color: var(--i20-color-accent-primary) !important;
  text-decoration: underline;
}}

.i20-breadcrumb-current {{
  font-weight: var(--i20-font-weight-label);
}}

.i20-top-bar-actions .i20-btn {{
  margin-left: var(--i20-space-2);
}}

.i20-top-bar-status .i20-status-indicator {{
  margin-left: var(--i20-space-3);
  padding-left: var(--i20-space-3);
  border-left: 1px solid var(--i20-color-border-subtle);
}}

.i20-top-bar-status .i20-status-indicator:first-child {{
  margin-left: 0;
  padding-left: 0;
  border-left: none;
}}
"""


def inject_layout_css() -> None:
    """Inject layout CSS into Streamlit."""
    st.markdown(f"<style>{LAYOUT_CSS}</style>", unsafe_allow_html=True)


# =============================================================================
# INITIALIZATION
# =============================================================================

def initialize_layout() -> None:
    """
    Initialize all layout CSS and global styles.
    Call once at app startup.
    """
    inject_global_css()
    inject_layout_css()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Grid helpers
    "responsive_grid_css",
    "auto_fit_grid_css",
    "fixed_grid_css",
    "GAUGE_GRID_CSS",
    "METRIC_GRID_CSS",
    "CHART_GRID_CSS",
    "FORM_GRID_CSS",
    "AUTO_FIT_CARD_CSS",
    "AUTO_FIT_METRIC_CSS",
    # Streamlit column helpers
    "ColumnSpec",
    "create_columns",
    "gauge_cluster_columns",
    "metric_row_columns",
    "chart_columns",
    "form_field_columns",
    # Page structure
    "page_header",
    "section_header",
    "card_container",
    "grid_container",
    # Sidebar
    "sidebar_section",
    "sidebar_nav_item",
    # Top bar
    "top_bar",
    "status_indicator",
    # Responsive
    "responsive_container",
    "visually_hidden",
    # CSS injection
    "LAYOUT_CSS",
    "inject_layout_css",
    "initialize_layout",
]