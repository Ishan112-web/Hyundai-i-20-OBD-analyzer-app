"""
i20 AI Garage - Design Tokens

Centralized design token definitions derived from the Stage 2 design specification.
All values are sourced from config.py:THEME and components/charts.py, normalized
for contrast and semantic clarity.

This module is the single source of truth for all design tokens.
"""

from typing import Final, Literal
from dataclasses import dataclass
from functools import lru_cache


# =============================================================================
# COLOR TOKENS
# =============================================================================

# --- Surface & Background Tokens ---
SURFACE_APP: Final[str] = "#1a1d21"      # Application/page background
SURFACE_PAGE: Final[str] = "#1a1d21"     # Page content background
SURFACE_PRIMARY: Final[str] = "#2a2e36"  # Primary card/panel surface
SURFACE_SECONDARY: Final[str] = "#23272e"  # Secondary surface (sidebar, inputs)
SURFACE_ELEVATED: Final[str] = "#2f333c"  # Dropdowns, popovers, modals
SURFACE_INTERACTIVE: Final[str] = "#323741"  # Hover/active states on cards

# --- Text Tokens ---
TEXT_PRIMARY: Final[str] = "#e8eaed"     # Main content, headings
TEXT_SECONDARY: Final[str] = "#9aa3ad"   # Descriptions, metadata, captions
TEXT_MUTED: Final[str] = "#6b7280"       # Disabled, placeholder, subtle labels
TEXT_INVERSE: Final[str] = "#1a1d21"     # On primary accent backgrounds
TEXT_LINK: Final[str] = "#00b4d8"        # Links, actionable text
TEXT_ON_ACCENT: Final[str] = "#ffffff"   # On accent-colored surfaces

# --- Border Tokens ---
BORDER_DEFAULT: Final[str] = "#3a3f4a"   # Standard card/container borders
BORDER_SUBTLE: Final[str] = "#2d3139"    # Hairline separators, table grid
BORDER_STRONG: Final[str] = "#4a4f5c"    # Focus rings, selected states
BORDER_FOCUS: Final[str] = "#00b4d8"     # Keyboard focus indicator
BORDER_SEPARATOR: Final[str] = "#2d3139" # Section dividers

# --- Accent & Brand Tokens ---
ACCENT_PRIMARY: Final[str] = "#00b4d8"       # Primary actions, links, key metrics
ACCENT_PRIMARY_HOVER: Final[str] = "#009db8" # Hover state for primary
ACCENT_PRIMARY_ACTIVE: Final[str] = "#00869e" # Active/pressed state
ACCENT_SECONDARY: Final[str] = "#9b59b6"     # AI/assistant features, secondary actions
ACCENT_SELECTED: Final[str] = "#00b4d820"    # Selected row, active nav (10% opacity fill)

# --- Semantic Status Tokens (Application-Level) ---
STATUS_SUCCESS: Final[str] = "#2ecc71"   # Success, connected, healthy
STATUS_WARNING: Final[str] = "#f39c12"   # Warning, simulation mode, pending
STATUS_CRITICAL: Final[str] = "#e74c3c"  # Error, disconnected, critical
STATUS_INFO: Final[str] = "#00b4d8"      # Information, real data mode
STATUS_NEUTRAL: Final[str] = "#9aa3ad"   # Disabled, unknown, secondary

# --- Diagnostic Severity Tokens (Preserved from DTC_SEVERITY) ---
DIAG_CRITICAL: Final[str] = "#e74c3c"    # Critical - Immediate safety risk
DIAG_MAJOR: Final[str] = "#f39c12"       # Major - Significant issue
DIAG_MINOR: Final[str] = "#3498db"       # Minor - Monitor & schedule
DIAG_INFO: Final[str] = "#9b59b6"        # Information - No action needed

# --- Data Source Tokens ---
DATASOURCE_REAL: Final[str] = "#2ecc71"       # Live Data - Green = real vehicle connection
DATASOURCE_SIMULATION: Final[str] = "#f39c12" # Simulation - Amber = demo/simulated data
DATASOURCE_AI: Final[str] = "#9b59b6"         # AI Analysis - Purple = AI-generated content

# --- Chart Series Tokens (CVD-Safe Categorical Order) ---
SERIES_1: Final[str] = "#00b4d8"  # Primary telemetry (RPM, speed)
SERIES_2: Final[str] = "#f39c12"  # Secondary telemetry (coolant, throttle)
SERIES_3: Final[str] = "#2ecc71"  # Tertiary telemetry (load, voltage)
SERIES_4: Final[str] = "#9b59b6"  # AI/derived metrics
SERIES_5: Final[str] = "#e74c3c"  # Alerts, critical overlays

# --- Chart Status Tokens (Distinct from Series) ---
CHART_GOOD: Final[str] = "#2ecc71"    # Within healthy range
CHART_WARNING: Final[str] = "#f39c12" # Approaching threshold
CHART_SERIOUS: Final[str] = "#ec835a" # Distinct orange-red for serious
CHART_CRITICAL: Final[str] = "#e74c3c" # Beyond critical threshold


# =============================================================================
# COLOR TOKEN REGISTRY (for programmatic access)
# =============================================================================

# Surface tokens
SURFACE_TOKENS: Final[dict[str, str]] = {
    "surface.app": SURFACE_APP,
    "surface.page": SURFACE_PAGE,
    "surface.primary": SURFACE_PRIMARY,
    "surface.secondary": SURFACE_SECONDARY,
    "surface.elevated": SURFACE_ELEVATED,
    "surface.interactive": SURFACE_INTERACTIVE,
}

# Text tokens
TEXT_TOKENS: Final[dict[str, str]] = {
    "text.primary": TEXT_PRIMARY,
    "text.secondary": TEXT_SECONDARY,
    "text.muted": TEXT_MUTED,
    "text.inverse": TEXT_INVERSE,
    "text.link": TEXT_LINK,
    "text.on-accent": TEXT_ON_ACCENT,
}

# Border tokens
BORDER_TOKENS: Final[dict[str, str]] = {
    "border.default": BORDER_DEFAULT,
    "border.subtle": BORDER_SUBTLE,
    "border.strong": BORDER_STRONG,
    "border.focus": BORDER_FOCUS,
    "border.separator": BORDER_SEPARATOR,
}

# Accent tokens
ACCENT_TOKENS: Final[dict[str, str]] = {
    "accent.primary": ACCENT_PRIMARY,
    "accent.primary-hover": ACCENT_PRIMARY_HOVER,
    "accent.primary-active": ACCENT_PRIMARY_ACTIVE,
    "accent.secondary": ACCENT_SECONDARY,
    "accent.selected": ACCENT_SELECTED,
}

# Status tokens (application-level)
STATUS_TOKENS: Final[dict[str, str]] = {
    "status.success": STATUS_SUCCESS,
    "status.warning": STATUS_WARNING,
    "status.critical": STATUS_CRITICAL,
    "status.info": STATUS_INFO,
    "status.neutral": STATUS_NEUTRAL,
}

# Diagnostic severity tokens
DIAG_TOKENS: Final[dict[str, str]] = {
    "diag.critical": DIAG_CRITICAL,
    "diag.major": DIAG_MAJOR,
    "diag.minor": DIAG_MINOR,
    "diag.info": DIAG_INFO,
}

# Data source tokens
DATASOURCE_TOKENS: Final[dict[str, str]] = {
    "datasource.real": DATASOURCE_REAL,
    "datasource.simulation": DATASOURCE_SIMULATION,
    "datasource.ai": DATASOURCE_AI,
}

# Chart series tokens (fixed order - CVD safe)
SERIES_TOKENS: Final[dict[str, str]] = {
    "series.1": SERIES_1,
    "series.2": SERIES_2,
    "series.3": SERIES_3,
    "series.4": SERIES_4,
    "series.5": SERIES_5,
}

# Chart status tokens
CHART_STATUS_TOKENS: Final[dict[str, str]] = {
    "chart.good": CHART_GOOD,
    "chart.warning": CHART_WARNING,
    "chart.serious": CHART_SERIOUS,
    "chart.critical": CHART_CRITICAL,
}

# Complete color token registry (all 53 tokens)
ALL_COLOR_TOKENS: Final[dict[str, str]] = {
    **SURFACE_TOKENS,
    **TEXT_TOKENS,
    **BORDER_TOKENS,
    **ACCENT_TOKENS,
    **STATUS_TOKENS,
    **DIAG_TOKENS,
    **DATASOURCE_TOKENS,
    **SERIES_TOKENS,
    **CHART_STATUS_TOKENS,
}

# Semantic color role mapping for quick lookup
SEMANTIC_COLORS: Final[dict[str, str]] = {
    # Surface roles
    "bg": SURFACE_APP,
    "card": SURFACE_PRIMARY,
    "sidebar": SURFACE_SECONDARY,
    "input": SURFACE_SECONDARY,
    "dropdown": SURFACE_ELEVATED,
    "hover": SURFACE_INTERACTIVE,
    # Text roles
    "text": TEXT_PRIMARY,
    "text-muted": TEXT_SECONDARY,
    "text-disabled": TEXT_MUTED,
    "text-inverse": TEXT_INVERSE,
    "link": TEXT_LINK,
    "on-accent": TEXT_ON_ACCENT,
    # Border roles
    "border": BORDER_DEFAULT,
    "border-subtle": BORDER_SUBTLE,
    "border-focus": BORDER_FOCUS,
    # Accent roles
    "primary": ACCENT_PRIMARY,
    "primary-hover": ACCENT_PRIMARY_HOVER,
    "primary-active": ACCENT_PRIMARY_ACTIVE,
    "secondary": ACCENT_SECONDARY,
    "selected": ACCENT_SELECTED,
    # Status roles
    "success": STATUS_SUCCESS,
    "warning": STATUS_WARNING,
    "critical": STATUS_CRITICAL,
    "info": STATUS_INFO,
    "neutral": STATUS_NEUTRAL,
    # Diagnostic roles
    "diag-critical": DIAG_CRITICAL,
    "diag-major": DIAG_MAJOR,
    "diag-minor": DIAG_MINOR,
    "diag-info": DIAG_INFO,
    # Data source roles
    "real": DATASOURCE_REAL,
    "simulation": DATASOURCE_SIMULATION,
    "ai": DATASOURCE_AI,
    # Chart series roles (fixed order)
    "series-1": SERIES_1,
    "series-2": SERIES_2,
    "series-3": SERIES_3,
    "series-4": SERIES_4,
    "series-5": SERIES_5,
    # Chart status roles
    "chart-good": CHART_GOOD,
    "chart-warning": CHART_WARNING,
    "chart-serious": CHART_SERIOUS,
    "chart-critical": CHART_CRITICAL,
}


# =============================================================================
# TYPOGRAPHY TOKENS
# =============================================================================

# Font Families
FONT_FAMILY_BASE: Final[str] = "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
FONT_FAMILY_MONO: Final[str] = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, 'Liberation Mono', monospace"
FONT_FAMILY_NUMERIC: Final[str] = FONT_FAMILY_BASE  # Use font-variant-numeric: tabular-nums

# Type Scale Tokens (name -> (size_px, size_rem, weight, line_height, letter_spacing, font_family_key, usage))
TYPE_SCALE: Final[dict[str, tuple[int, str, int, float, str, str, str]]] = {
    "display":      (48,  "3rem",    700, 1.1, "-0.02em", "base", "Hero vehicle identity (rare)"),
    "h1":           (32,  "2rem",    700, 1.2, "-0.01em", "base", "Page title"),
    "h2":           (24,  "1.5rem",  600, 1.3, "0",       "base", "Major section heading"),
    "h3":           (20,  "1.25rem", 600, 1.4, "0",       "base", "Subsection heading"),
    "h4":           (16,  "1rem",    600, 1.4, "0",       "base", "Card heading, widget group"),
    "body-lg":      (16,  "1rem",    400, 1.6, "0",       "base", "Important explanatory text"),
    "body":         (14,  "0.875rem",400, 1.5, "0",       "base", "Standard content"),
    "body-sm":      (13,  "0.8125rem",400,1.5, "0",       "base", "Secondary content, table cells"),
    "label":        (12,  "0.75rem", 500, 1.4, "+0.02em", "base", "Form labels, metric labels"),
    "caption":      (11,  "0.6875rem",400,1.4, "+0.03em", "base", "Metadata, timestamps, help"),
    # Numeric variants (tabular-nums)
    "numeric-xl":   (48,  "3rem",    700, 1.0, "0",       "numeric", "Main telemetry reading (gauge center)"),
    "numeric-lg":   (32,  "2rem",    600, 1.1, "0",       "numeric", "Secondary metric (metric card value)"),
    "numeric-md":   (20,  "1.25rem", 600, 1.2, "0",       "numeric", "Tertiary metric, sparkline label"),
    "numeric-sm":   (14,  "0.875rem",500, 1.3, "0",       "numeric", "Table numeric cells"),
    "code":         (13,  "0.8125rem",400,1.5, "0",       "mono", "DTC codes, PIDs, VIN, technical IDs"),
    "code-sm":      (11,  "0.6875rem",400,1.4, "0",       "mono", "Inline code, small technical refs"),
}

# Individual token access
FONT_SIZE_DISPLAY: Final[str] = "3rem"
FONT_SIZE_H1: Final[str] = "2rem"
FONT_SIZE_H2: Final[str] = "1.5rem"
FONT_SIZE_H3: Final[str] = "1.25rem"
FONT_SIZE_H4: Final[str] = "1rem"
FONT_SIZE_BODY_LG: Final[str] = "1rem"
FONT_SIZE_BODY: Final[str] = "0.875rem"
FONT_SIZE_BODY_SM: Final[str] = "0.8125rem"
FONT_SIZE_LABEL: Final[str] = "0.75rem"
FONT_SIZE_CAPTION: Final[str] = "0.6875rem"
FONT_SIZE_NUMERIC_XL: Final[str] = "3rem"
FONT_SIZE_NUMERIC_LG: Final[str] = "2rem"
FONT_SIZE_NUMERIC_MD: Final[str] = "1.25rem"
FONT_SIZE_NUMERIC_SM: Final[str] = "0.875rem"
FONT_SIZE_CODE: Final[str] = "0.8125rem"
FONT_SIZE_CODE_SM: Final[str] = "0.6875rem"

FONT_WEIGHT_DISPLAY: Final[int] = 700
FONT_WEIGHT_H1: Final[int] = 700
FONT_WEIGHT_H2: Final[int] = 600
FONT_WEIGHT_H3: Final[int] = 600
FONT_WEIGHT_H4: Final[int] = 600
FONT_WEIGHT_BODY: Final[int] = 400
FONT_WEIGHT_LABEL: Final[int] = 500
FONT_WEIGHT_NUMERIC: Final[int] = 600

LINE_HEIGHT_DISPLAY: Final[float] = 1.1
LINE_HEIGHT_H1: Final[float] = 1.2
LINE_HEIGHT_H2: Final[float] = 1.3
LINE_HEIGHT_H3: Final[float] = 1.4
LINE_HEIGHT_H4: Final[float] = 1.4
LINE_HEIGHT_BODY: Final[float] = 1.5
LINE_HEIGHT_LABEL: Final[float] = 1.4
LINE_HEIGHT_NUMERIC: Final[float] = 1.1

LETTER_SPACING_DISPLAY: Final[str] = "-0.02em"
LETTER_SPACING_H1: Final[str] = "-0.01em"
LETTER_SPACING_LABEL: Final[str] = "+0.02em"
LETTER_SPACING_CAPTION: Final[str] = "+0.03em"


# =============================================================================
# SPACING TOKENS
# =============================================================================

# Base 4px scale
SPACE_0: Final[str] = "0"
SPACE_1: Final[str] = "0.25rem"   # 4px
SPACE_2: Final[str] = "0.5rem"    # 8px
SPACE_3: Final[str] = "0.75rem"   # 12px
SPACE_4: Final[str] = "1rem"      # 16px
SPACE_5: Final[str] = "1.25rem"   # 20px
SPACE_6: Final[str] = "1.5rem"    # 24px
SPACE_8: Final[str] = "2rem"      # 32px
SPACE_10: Final[str] = "2.5rem"   # 40px
SPACE_12: Final[str] = "3rem"     # 48px
SPACE_16: Final[str] = "4rem"     # 64px

# Spacing token registry
SPACING_TOKENS: Final[dict[str, str]] = {
    "space.0": SPACE_0,
    "space.1": SPACE_1,
    "space.2": SPACE_2,
    "space.3": SPACE_3,
    "space.4": SPACE_4,
    "space.5": SPACE_5,
    "space.6": SPACE_6,
    "space.8": SPACE_8,
    "space.10": SPACE_10,
    "space.12": SPACE_12,
    "space.16": SPACE_16,
}

# Semantic spacing aliases
GAP_INLINE: Final[str] = SPACE_2       # Icon + text, button content (8px)
GAP_FIELD: Final[str] = SPACE_4        # Form field vertical, input + help text (16px)
GAP_CARD: Final[str] = SPACE_4         # Internal card padding (all sides) (16px)
GAP_CARD_GRID: Final[str] = SPACE_5    # Gap between cards in CSS grid (20px)
GAP_SECTION: Final[str] = SPACE_6      # Between major page sections (24px)
GAP_PAGE: Final[str] = SPACE_8         # Page header to content (32px)
GAP_SIDEBAR: Final[str] = SPACE_4      # Sidebar internal section gap (16px)
PADDING_PAGE: Final[str] = SPACE_6     # Main content horizontal padding (24px)
PADDING_CARD: Final[str] = SPACE_4     # Card internal padding (16px)
PADDING_CARD_LG: Final[str] = SPACE_5  # Large card (wizard, modal) padding (20px)

# Responsive spacing scale per breakpoint
# Mobile: smaller spacing for compact layouts
# Tablet: base spacing
# Laptop: slightly larger spacing
# Desktop: full spacing
RESPONSIVE_SPACING: Final[dict[str, dict[str, str]]] = {
    "mobile": {
        "gap.inline": SPACE_1,       # 4px
        "gap.field": SPACE_3,        # 12px
        "gap.card": SPACE_3,         # 12px
        "gap.card-grid": SPACE_4,    # 16px
        "gap.section": SPACE_5,      # 20px
        "gap.page": SPACE_6,         # 24px
        "gap.sidebar": SPACE_3,      # 12px
        "padding.page": SPACE_4,     # 16px
        "padding.card": SPACE_3,     # 12px
        "padding.card-lg": SPACE_4,  # 16px
    },
    "mobile-landscape": {
        "gap.inline": SPACE_2,       # 8px
        "gap.field": SPACE_3,        # 12px
        "gap.card": SPACE_3,         # 12px
        "gap.card-grid": SPACE_4,    # 16px
        "gap.section": SPACE_5,      # 20px
        "gap.page": SPACE_6,         # 24px
        "gap.sidebar": SPACE_3,      # 12px
        "padding.page": SPACE_4,     # 16px
        "padding.card": SPACE_3,     # 12px
        "padding.card-lg": SPACE_4,  # 16px,
    },
    "tablet": {
        "gap.inline": SPACE_2,       # 8px
        "gap.field": SPACE_4,        # 16px
        "gap.card": SPACE_4,         # 16px
        "gap.card-grid": SPACE_5,    # 20px
        "gap.section": SPACE_6,      # 24px
        "gap.page": SPACE_8,         # 32px
        "gap.sidebar": SPACE_4,      # 16px
        "padding.page": SPACE_5,     # 20px
        "padding.card": SPACE_4,     # 16px
        "padding.card-lg": SPACE_5,  # 20px,
    },
    "laptop": {
        "gap.inline": SPACE_2,       # 8px
        "gap.field": SPACE_4,        # 16px
        "gap.card": SPACE_4,         # 16px
        "gap.card-grid": SPACE_5,    # 20px
        "gap.section": SPACE_6,      # 24px
        "gap.page": SPACE_8,         # 32px
        "gap.sidebar": SPACE_4,      # 16px
        "padding.page": SPACE_6,     # 24px
        "padding.card": SPACE_4,     # 16px
        "padding.card-lg": SPACE_5,  # 20px,
    },
    "desktop": {
        "gap.inline": SPACE_2,       # 8px
        "gap.field": SPACE_4,        # 16px
        "gap.card": SPACE_4,         # 16px
        "gap.card-grid": SPACE_5,    # 20px
        "gap.section": SPACE_6,      # 24px
        "gap.page": SPACE_8,         # 32px
        "gap.sidebar": SPACE_4,      # 16px
        "padding.page": SPACE_8,     # 32px
        "padding.card": SPACE_4,     # 16px
        "padding.card-lg": SPACE_5,  # 20px,
    },
}

SEMANTIC_SPACING: Final[dict[str, str]] = {
    "gap.inline": GAP_INLINE,
    "gap.field": GAP_FIELD,
    "gap.card": GAP_CARD,
    "gap.card-grid": GAP_CARD_GRID,
    "gap.section": GAP_SECTION,
    "gap.page": GAP_PAGE,
    "gap.sidebar": GAP_SIDEBAR,
    "padding.page": PADDING_PAGE,
    "padding.card": PADDING_CARD,
    "padding.card-lg": PADDING_CARD_LG,
}


# =============================================================================
# BORDER RADIUS TOKENS
# =============================================================================

RADIUS_NONE: Final[str] = "0"
RADIUS_SM: Final[str] = "4px"       # Inputs, selects, buttons, badges, pills
RADIUS_MD: Final[str] = "8px"       # Standard card, metric card, panel, modal content
RADIUS_LG: Final[str] = "12px"      # Large cards (wizard, report preview), dropdown menus
RADIUS_XL: Final[str] = "16px"      # Page-level containers, modal wrapper
RADIUS_PILL: Final[str] = "9999px"  # Status badges, pills, avatar, progress bars
RADIUS_CIRCLE: Final[str] = "50%"   # Indicator dots, avatars, gauge center

RADIUS_TOKENS: Final[dict[str, str]] = {
    "radius.none": RADIUS_NONE,
    "radius.sm": RADIUS_SM,
    "radius.md": RADIUS_MD,
    "radius.lg": RADIUS_LG,
    "radius.xl": RADIUS_XL,
    "radius.pill": RADIUS_PILL,
    "radius.circle": RADIUS_CIRCLE,
}


# =============================================================================
# ELEVATION & SHADOW TOKENS
# =============================================================================

SHADOW_NONE: Final[str] = "none"
SHADOW_HAIRLINE: Final[str] = f"0 1px 0 {BORDER_SUBTLE}"
SHADOW_SM: Final[str] = "0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08)"
SHADOW_MD: Final[str] = "0 4px 12px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.1)"
SHADOW_LG: Final[str] = "0 12px 28px rgba(0,0,0,0.2), 0 4px 8px rgba(0,0,0,0.15)"
SHADOW_FOCUS: Final[str] = f"0 0 0 3px {ACCENT_PRIMARY}"
SHADOW_GLOW_SUCCESS: Final[str] = f"0 0 8px {STATUS_SUCCESS}"
SHADOW_GLOW_WARNING: Final[str] = f"0 0 8px {STATUS_WARNING}"
SHADOW_GLOW_CRITICAL: Final[str] = f"0 0 8px {STATUS_CRITICAL}"

SHADOW_TOKENS: Final[dict[str, str]] = {
    "shadow.none": SHADOW_NONE,
    "shadow.hairline": SHADOW_HAIRLINE,
    "shadow.sm": SHADOW_SM,
    "shadow.md": SHADOW_MD,
    "shadow.lg": SHADOW_LG,
    "shadow.focus": SHADOW_FOCUS,
    "shadow.glow.success": SHADOW_GLOW_SUCCESS,
    "shadow.glow.warning": SHADOW_GLOW_WARNING,
    "shadow.glow.critical": SHADOW_GLOW_CRITICAL,
}


# =============================================================================
# BREAKPOINT TOKENS
# =============================================================================

# Canonical 4 breakpoints per design spec:
# Mobile: <768px
# Tablet: 768px - 1023px
# Laptop: 1024px - 1279px
# Desktop: >=1280px

BREAKPOINT_MOBILE: Final[str] = "768px"       # Mobile portrait max-width
BREAKPOINT_MOBILE_LANDSCAPE: Final[str] = "568px"  # Mobile landscape max-width
BREAKPOINT_TABLET: Final[str] = "768px"       # Tablet portrait min-width
BREAKPOINT_TABLET_LANDSCAPE: Final[str] = "1024px" # Tablet landscape min-width
BREAKPOINT_LAPTOP: Final[str] = "1024px"      # Laptop min-width
BREAKPOINT_DESKTOP: Final[str] = "1280px"     # Desktop min-width

# Primary breakpoints for media queries (max-width approach)
BREAKPOINTS: Final[dict[str, str]] = {
    "mobile": BREAKPOINT_MOBILE,              # max-width: 768px
    "mobile-landscape": BREAKPOINT_MOBILE_LANDSCAPE,  # max-width: 568px
    "tablet": BREAKPOINT_TABLET,              # min-width: 768px
    "tablet-landscape": BREAKPOINT_TABLET_LANDSCAPE,  # min-width: 1024px
    "laptop": BREAKPOINT_LAPTOP,              # min-width: 1024px
    "desktop": BREAKPOINT_DESKTOP,            # min-width: 1280px
}

# Container max-widths per breakpoint
CONTAINER_MAX_WIDTHS: Final[dict[str, str]] = {
    "mobile": "100%",
    "tablet": "720px",
    "laptop": "960px",
    "desktop": "1200px",
}

# Touch target minimums
TOUCH_TARGET_MIN: Final[str] = "44px"
TOUCH_TARGET_COMFORTABLE: Final[str] = "48px"


# =============================================================================
# Z-INDEX TOKENS
# =============================================================================

Z_INDEX_DROPDOWN: Final[int] = 100
Z_INDEX_POPOVER: Final[int] = 200
Z_INDEX_TOAST: Final[int] = 300
Z_INDEX_MODAL: Final[int] = 400
Z_INDEX_TOOLTIP: Final[int] = 500

Z_INDEX_TOKENS: Final[dict[str, int]] = {
    "z.dropdown": Z_INDEX_DROPDOWN,
    "z.popover": Z_INDEX_POPOVER,
    "z.toast": Z_INDEX_TOAST,
    "z.modal": Z_INDEX_MODAL,
    "z.tooltip": Z_INDEX_TOOLTIP,
}


# =============================================================================
# TRANSITION TOKENS
# =============================================================================

TRANSITION_FAST: Final[str] = "0.15s ease"
TRANSITION_NORMAL: Final[str] = "0.2s ease"
TRANSITION_SLOW: Final[str] = "0.3s ease"

TRANSITION_TOKENS: Final[dict[str, str]] = {
    "transition.fast": TRANSITION_FAST,
    "transition.normal": TRANSITION_NORMAL,
    "transition.slow": TRANSITION_SLOW,
}


# =============================================================================
# CHART SPECIFIC TOKENS
# =============================================================================

# Gauge chart thresholds (derived from config.py:GAUGE_THRESHOLDS)
GAUGE_THRESHOLD_TOKENS: Final[dict[str, dict[str, float]]] = {
    "rpm": {"green_max": 3000, "amber_max": 5000, "red_max": 6500},
    "speed": {"green_max": 60, "amber_max": 100, "red_max": 140},
    "coolant_temp": {"green_max": 95, "amber_max": 105, "red_max": 115},
    "throttle": {"green_max": 40, "amber_max": 70, "red_max": 100},
    "engine_load": {"green_max": 50, "amber_max": 80, "red_max": 100},
    "fuel_trim": {"green_min": -10, "green_max": 10, "amber_min": -20, "amber_max": 20, "red_min": -30, "red_max": 30},
    "voltage": {"green_min": 13.5, "green_max": 14.5, "amber_min": 12.5, "amber_max": 15.5, "red_min": 11.5, "red_max": 16.0},
}

# Chart layout defaults
CHART_LAYOUT_DEFAULTS: Final[dict[str, any]] = {
    "paper_bgcolor": SURFACE_APP,
    "plot_bgcolor": SURFACE_PRIMARY,
    "font_family": FONT_FAMILY_BASE,
    "font_color": TEXT_PRIMARY,
    "font_size": 12,
    "grid_color": BORDER_DEFAULT,
    "axis_line_color": BORDER_DEFAULT,
    "tick_font_color": TEXT_SECONDARY,
    "tick_font_size": 10,
    "title_font_color": TEXT_PRIMARY,
    "title_font_size": 14,
    "legend_bgcolor": "rgba(0,0,0,0)",
    "legend_border_color": BORDER_DEFAULT,
    "legend_font_color": TEXT_SECONDARY,
    "legend_font_size": 11,
    "hover_bgcolor": SURFACE_SECONDARY,
    "hover_border_color": BORDER_DEFAULT,
    "hover_font_color": TEXT_PRIMARY,
    "hover_font_size": 11,
    "margin": {"l": 50, "r": 30, "t": 60, "b": 50},
}


# =============================================================================
# COMPONENT-SPECIFIC CONSTANTS
# =============================================================================

# Button
BUTTON_MIN_HEIGHT: Final[str] = "40px"
BUTTON_PADDING_VERTICAL: Final[str] = SPACE_2   # 8px
BUTTON_PADDING_HORIZONTAL: Final[str] = SPACE_4 # 16px
BUTTON_ICON_GAP: Final[str] = GAP_INLINE        # 8px
BUTTON_RADIUS: Final[str] = RADIUS_SM           # 4px
BUTTON_FONT_SIZE: Final[str] = FONT_SIZE_LABEL  # 0.75rem
BUTTON_FONT_WEIGHT: Final[int] = FONT_WEIGHT_LABEL # 500

# Badge
BADGE_PADDING_VERTICAL: Final[str] = "4px"
BADGE_PADDING_HORIZONTAL: Final[str] = "10px"
BADGE_RADIUS: Final[str] = RADIUS_PILL
BADGE_FONT_SIZE: Final[str] = FONT_SIZE_CAPTION # 0.6875rem
BADGE_FONT_WEIGHT: Final[int] = 600

# Card
CARD_RADIUS: Final[str] = RADIUS_MD      # 8px
CARD_PADDING: Final[str] = PADDING_CARD  # 16px
CARD_BORDER: Final[str] = f"1px solid {BORDER_DEFAULT}"

# Input
INPUT_HEIGHT: Final[str] = "40px"
INPUT_PADDING_VERTICAL: Final[str] = SPACE_2  # 8px
INPUT_PADDING_HORIZONTAL: Final[str] = SPACE_3 # 12px
INPUT_RADIUS: Final[str] = RADIUS_SM          # 4px
INPUT_FONT_SIZE: Final[str] = FONT_SIZE_BODY  # 0.875rem

# Table
TABLE_HEADER_BG: Final[str] = SURFACE_SECONDARY
TABLE_HEADER_FONT_SIZE: Final[str] = FONT_SIZE_LABEL
TABLE_HEADER_FONT_COLOR: Final[str] = TEXT_SECONDARY
TABLE_ROW_FONT_SIZE: Final[str] = FONT_SIZE_BODY_SM
TABLE_ROW_FONT_COLOR: Final[str] = TEXT_PRIMARY
TABLE_BORDER: Final[str] = f"1px solid {BORDER_SUBTLE}"
TABLE_HOVER_BG: Final[str] = SURFACE_INTERACTIVE
TABLE_SELECTED_BG: Final[str] = ACCENT_SELECTED

# Empty State
EMPTY_STATE_PADDING: Final[str] = SPACE_12  # 48px
EMPTY_STATE_ICON_SIZE: Final[str] = "64px"

# Loading
SKELETON_PULSE_DURATION: Final[str] = "1.5s"
SPINNER_SIZE_SM: Final[str] = "20px"
SPINNER_SIZE_MD: Final[str] = "32px"
SPINNER_SIZE_LG: Final[str] = "48px"

# Wizard
WIZARD_CARD_RADIUS: Final[str] = RADIUS_LG   # 12px
WIZARD_CARD_SHADOW: Final[str] = SHADOW_LG
WIZARD_CARD_PADDING: Final[str] = PADDING_CARD_LG # 20px

# Sidebar
SIDEBAR_WIDTH_EXPANDED: Final[str] = "280px"
SIDEBAR_WIDTH_COLLAPSED: Final[str] = "72px"
SIDEBAR_TRANSITION: Final[str] = TRANSITION_NORMAL

# Top Bar
TOP_BAR_HEIGHT: Final[str] = "48px"
TOP_BAR_BG: Final[str] = SURFACE_SECONDARY
TOP_BAR_BORDER: Final[str] = f"1px solid {BORDER_DEFAULT}"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_color_token(token_name: str) -> str:
    """Get a color token by name (e.g., 'surface.primary', 'status.success')."""
    return ALL_COLOR_TOKENS.get(token_name, "")


def get_semantic_color(role: str) -> str:
    """Get a color by semantic role (e.g., 'primary', 'success', 'card')."""
    return SEMANTIC_COLORS.get(role, "")


def get_spacing_token(token_name: str) -> str:
    """Get a spacing token by name (e.g., 'space.4', 'gap.card')."""
    return SPACING_TOKENS.get(token_name, SEMANTIC_SPACING.get(token_name, ""))


def get_responsive_spacing_token(breakpoint: str, token_name: str) -> str:
    """Get a responsive spacing token for a specific breakpoint.

    Args:
        breakpoint: One of 'mobile', 'mobile-landscape', 'tablet', 'laptop', 'desktop'
        token_name: Semantic spacing token name (e.g., 'gap.card', 'padding.card')

    Returns:
        Spacing value for the breakpoint, or empty string if not found.
    """
    breakpoint_spacing = RESPONSIVE_SPACING.get(breakpoint, {})
    return breakpoint_spacing.get(token_name, "")


def get_radius_token(token_name: str) -> str:
    """Get a radius token by name (e.g., 'radius.md', 'radius.pill')."""
    return RADIUS_TOKENS.get(token_name, "")


def get_shadow_token(token_name: str) -> str:
    """Get a shadow token by name (e.g., 'shadow.md', 'shadow.focus')."""
    return SHADOW_TOKENS.get(token_name, "")


def get_typography_token(token_name: str) -> tuple:
    """Get typography token details by name."""
    return TYPE_SCALE.get(token_name, ())


def get_all_tokens() -> dict:
    """Get all tokens as a flat dictionary for CSS variable generation."""
    # Generate responsive spacing CSS variables
    responsive_spacing_vars = {}
    for breakpoint, spacing in RESPONSIVE_SPACING.items():
        for key, value in spacing.items():
            css_key = f"space-{breakpoint}-{key.replace('.', '-')}"
            responsive_spacing_vars[css_key] = value

    return {
        **{f"color-{k}": v for k, v in ALL_COLOR_TOKENS.items()},
        **{f"space-{k.replace('.', '-')}": v for k, v in SPACING_TOKENS.items()},
        **{f"space-{k.replace('.', '-')}": v for k, v in SEMANTIC_SPACING.items()},
        **responsive_spacing_vars,
        **{f"radius-{k.replace('.', '-')}": v for k, v in RADIUS_TOKENS.items()},
        **{f"shadow-{k.replace('.', '-')}": v for k, v in SHADOW_TOKENS.items()},
        **{f"font-{k.replace('.', '-')}": v for k, v in {
            "family.base": FONT_FAMILY_BASE,
            "family.mono": FONT_FAMILY_MONO,
            "size.display": FONT_SIZE_DISPLAY,
            "size.h1": FONT_SIZE_H1,
            "size.h2": FONT_SIZE_H2,
            "size.h3": FONT_SIZE_H3,
            "size.h4": FONT_SIZE_H4,
            "size.body-lg": FONT_SIZE_BODY_LG,
            "size.body": FONT_SIZE_BODY,
            "size.body-sm": FONT_SIZE_BODY_SM,
            "size.label": FONT_SIZE_LABEL,
            "size.caption": FONT_SIZE_CAPTION,
            "size.numeric-xl": FONT_SIZE_NUMERIC_XL,
            "size.numeric-lg": FONT_SIZE_NUMERIC_LG,
            "size.numeric-md": FONT_SIZE_NUMERIC_MD,
            "size.numeric-sm": FONT_SIZE_NUMERIC_SM,
            "size.code": FONT_SIZE_CODE,
            "size.code-sm": FONT_SIZE_CODE_SM,
        }.items()},
        **{f"breakpoint-{k}": v for k, v in BREAKPOINTS.items()},
        **{f"container-max-width-{k}": v for k, v in CONTAINER_MAX_WIDTHS.items()},
        **{"touch-target-min": TOUCH_TARGET_MIN},
        **{"touch-target-comfortable": TOUCH_TARGET_COMFORTABLE},
        **{f"z-{k.replace('.', '-')}": str(v) for k, v in Z_INDEX_TOKENS.items()},
        **{f"transition-{k.replace('.', '-')}": v for k, v in TRANSITION_TOKENS.items()},
    }


def validate_tokens() -> dict[str, bool]:
    """Validate all required tokens are present and non-empty."""
    required_colors = [
        "surface.app", "surface.primary", "surface.secondary", "surface.elevated", "surface.interactive",
        "text.primary", "text.secondary", "text.muted", "text.inverse", "text.link", "text.on-accent",
        "border.default", "border.subtle", "border.strong", "border.focus", "border.separator",
        "accent.primary", "accent.primary-hover", "accent.primary-active", "accent.secondary", "accent.selected",
        "status.success", "status.warning", "status.critical", "status.info", "status.neutral",
        "diag.critical", "diag.major", "diag.minor", "diag.info",
        "datasource.real", "datasource.simulation", "datasource.ai",
        "series.1", "series.2", "series.3", "series.4", "series.5",
        "chart.good", "chart.warning", "chart.serious", "chart.critical",
    ]
    required_spacing = ["space.1", "space.2", "space.3", "space.4", "space.5", "space.6", "space.8", "space.10", "space.12", "space.16"]
    required_radius = ["radius.none", "radius.sm", "radius.md", "radius.lg", "radius.xl", "radius.pill", "radius.circle"]
    required_shadows = ["shadow.none", "shadow.sm", "shadow.md", "shadow.lg", "shadow.focus"]

    results = {}
    for token in required_colors:
        results[f"color.{token}"] = bool(ALL_COLOR_TOKENS.get(token))
    for token in required_spacing:
        results[f"spacing.{token}"] = bool(SPACING_TOKENS.get(token))
    for token in required_radius:
        results[f"radius.{token}"] = bool(RADIUS_TOKENS.get(token))
    for token in required_shadows:
        results[f"shadow.{token}"] = bool(SHADOW_TOKENS.get(token))

    return results


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Color tokens (individual)
    "SURFACE_APP", "SURFACE_PAGE", "SURFACE_PRIMARY", "SURFACE_SECONDARY", "SURFACE_ELEVATED", "SURFACE_INTERACTIVE",
    "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED", "TEXT_INVERSE", "TEXT_LINK", "TEXT_ON_ACCENT",
    "BORDER_DEFAULT", "BORDER_SUBTLE", "BORDER_STRONG", "BORDER_FOCUS", "BORDER_SEPARATOR",
    "ACCENT_PRIMARY", "ACCENT_PRIMARY_HOVER", "ACCENT_PRIMARY_ACTIVE", "ACCENT_SECONDARY", "ACCENT_SELECTED",
    "STATUS_SUCCESS", "STATUS_WARNING", "STATUS_CRITICAL", "STATUS_INFO", "STATUS_NEUTRAL",
    "DIAG_CRITICAL", "DIAG_MAJOR", "DIAG_MINOR", "DIAG_INFO",
    "DATASOURCE_REAL", "DATASOURCE_SIMULATION", "DATASOURCE_AI",
    "SERIES_1", "SERIES_2", "SERIES_3", "SERIES_4", "SERIES_5",
    "CHART_GOOD", "CHART_WARNING", "CHART_SERIOUS", "CHART_CRITICAL",
    # Color token registries
    "SURFACE_TOKENS", "TEXT_TOKENS", "BORDER_TOKENS", "ACCENT_TOKENS", "STATUS_TOKENS",
    "DIAG_TOKENS", "DATASOURCE_TOKENS", "SERIES_TOKENS", "CHART_STATUS_TOKENS",
    "ALL_COLOR_TOKENS", "SEMANTIC_COLORS",
    # Typography
    "FONT_FAMILY_BASE", "FONT_FAMILY_MONO", "FONT_FAMILY_NUMERIC",
    "TYPE_SCALE",
    "FONT_SIZE_DISPLAY", "FONT_SIZE_H1", "FONT_SIZE_H2", "FONT_SIZE_H3", "FONT_SIZE_H4",
    "FONT_SIZE_BODY_LG", "FONT_SIZE_BODY", "FONT_SIZE_BODY_SM", "FONT_SIZE_LABEL", "FONT_SIZE_CAPTION",
    "FONT_SIZE_NUMERIC_XL", "FONT_SIZE_NUMERIC_LG", "FONT_SIZE_NUMERIC_MD", "FONT_SIZE_NUMERIC_SM",
    "FONT_SIZE_CODE", "FONT_SIZE_CODE_SM",
    # Spacing
    "SPACE_0", "SPACE_1", "SPACE_2", "SPACE_3", "SPACE_4", "SPACE_5", "SPACE_6", "SPACE_8", "SPACE_10", "SPACE_12", "SPACE_16",
    "SPACING_TOKENS", "SEMANTIC_SPACING", "RESPONSIVE_SPACING",
    "GAP_INLINE", "GAP_FIELD", "GAP_CARD", "GAP_CARD_GRID", "GAP_SECTION", "GAP_PAGE", "GAP_SIDEBAR",
    "PADDING_PAGE", "PADDING_CARD", "PADDING_CARD_LG",
    # Radius
    "RADIUS_NONE", "RADIUS_SM", "RADIUS_MD", "RADIUS_LG", "RADIUS_XL", "RADIUS_PILL", "RADIUS_CIRCLE",
    "RADIUS_TOKENS",
    # Shadows
    "SHADOW_NONE", "SHADOW_HAIRLINE", "SHADOW_SM", "SHADOW_MD", "SHADOW_LG", "SHADOW_FOCUS",
    "SHADOW_GLOW_SUCCESS", "SHADOW_GLOW_WARNING", "SHADOW_GLOW_CRITICAL",
    "SHADOW_TOKENS",
    # Breakpoints
    "BREAKPOINT_MOBILE", "BREAKPOINT_MOBILE_LANDSCAPE", "BREAKPOINT_TABLET", "BREAKPOINT_TABLET_LANDSCAPE",
    "BREAKPOINT_LAPTOP", "BREAKPOINT_DESKTOP",
    "BREAKPOINTS", "CONTAINER_MAX_WIDTHS",
    "TOUCH_TARGET_MIN", "TOUCH_TARGET_COMFORTABLE",
    # Z-index
    "Z_INDEX_DROPDOWN", "Z_INDEX_POPOVER", "Z_INDEX_TOAST", "Z_INDEX_MODAL", "Z_INDEX_TOOLTIP",
    "Z_INDEX_TOKENS",
    # Transitions
    "TRANSITION_FAST", "TRANSITION_NORMAL", "TRANSITION_SLOW", "TRANSITION_TOKENS",
    # Chart tokens
    "GAUGE_THRESHOLD_TOKENS", "CHART_LAYOUT_DEFAULTS",
    # Component constants
    "BUTTON_MIN_HEIGHT", "BUTTON_PADDING_VERTICAL", "BUTTON_PADDING_HORIZONTAL", "BUTTON_ICON_GAP",
    "BUTTON_RADIUS", "BUTTON_FONT_SIZE", "BUTTON_FONT_WEIGHT",
    "BADGE_PADDING_VERTICAL", "BADGE_PADDING_HORIZONTAL", "BADGE_RADIUS", "BADGE_FONT_SIZE", "BADGE_FONT_WEIGHT",
    "CARD_RADIUS", "CARD_PADDING", "CARD_BORDER",
    "INPUT_HEIGHT", "INPUT_PADDING_VERTICAL", "INPUT_PADDING_HORIZONTAL", "INPUT_RADIUS", "INPUT_FONT_SIZE",
    "TABLE_HEADER_BG", "TABLE_HEADER_FONT_SIZE", "TABLE_HEADER_FONT_COLOR", "TABLE_ROW_FONT_SIZE",
    "TABLE_ROW_FONT_COLOR", "TABLE_BORDER", "TABLE_HOVER_BG", "TABLE_SELECTED_BG",
    "EMPTY_STATE_PADDING", "EMPTY_STATE_ICON_SIZE",
    "SKELETON_PULSE_DURATION", "SPINNER_SIZE_SM", "SPINNER_SIZE_MD", "SPINNER_SIZE_LG",
    "WIZARD_CARD_RADIUS", "WIZARD_CARD_SHADOW", "WIZARD_CARD_PADDING",
    "SIDEBAR_WIDTH_EXPANDED", "SIDEBAR_WIDTH_COLLAPSED", "SIDEBAR_TRANSITION",
    "TOP_BAR_HEIGHT", "TOP_BAR_BG", "TOP_BAR_BORDER",
    # Helpers
    "get_color_token", "get_semantic_color", "get_spacing_token", "get_responsive_spacing_token",
    "get_radius_token", "get_shadow_token", "get_typography_token", "get_all_tokens", "validate_tokens",
]