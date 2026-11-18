"""
i20 AI Garage - Theme Mapping

Maps the legacy config.py THEME dictionary to the new centralized design tokens.
Provides backward compatibility while enabling the new token system.
"""

from typing import Final
from dataclasses import dataclass
from functools import lru_cache

# Import design tokens
from .tokens import (
    # Color tokens
    SURFACE_APP, SURFACE_PRIMARY, SURFACE_SECONDARY, SURFACE_ELEVATED, SURFACE_INTERACTIVE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_INVERSE, TEXT_LINK, TEXT_ON_ACCENT,
    BORDER_DEFAULT, BORDER_SUBTLE, BORDER_STRONG, BORDER_FOCUS, BORDER_SEPARATOR,
    ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER, ACCENT_PRIMARY_ACTIVE, ACCENT_SECONDARY, ACCENT_SELECTED,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, STATUS_NEUTRAL,
    DIAG_CRITICAL, DIAG_MAJOR, DIAG_MINOR, DIAG_INFO,
    DATASOURCE_REAL, DATASOURCE_SIMULATION, DATASOURCE_AI,
    SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5,
    CHART_GOOD, CHART_WARNING, CHART_SERIOUS, CHART_CRITICAL,
    # Typography
    FONT_FAMILY_BASE, FONT_FAMILY_MONO, FONT_FAMILY_NUMERIC,
    FONT_SIZE_DISPLAY, FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_H4,
    FONT_SIZE_BODY_LG, FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_LABEL, FONT_SIZE_CAPTION,
    FONT_SIZE_NUMERIC_XL, FONT_SIZE_NUMERIC_LG, FONT_SIZE_NUMERIC_MD, FONT_SIZE_NUMERIC_SM,
    FONT_SIZE_CODE, FONT_SIZE_CODE_SM,
    FONT_WEIGHT_DISPLAY, FONT_WEIGHT_H1, FONT_WEIGHT_H2, FONT_WEIGHT_H3, FONT_WEIGHT_H4,
    FONT_WEIGHT_BODY, FONT_WEIGHT_LABEL, FONT_WEIGHT_NUMERIC,
    LINE_HEIGHT_DISPLAY, LINE_HEIGHT_H1, LINE_HEIGHT_H2, LINE_HEIGHT_H3, LINE_HEIGHT_H4,
    LINE_HEIGHT_BODY, LINE_HEIGHT_LABEL, LINE_HEIGHT_NUMERIC,
    LETTER_SPACING_DISPLAY, LETTER_SPACING_H1, LETTER_SPACING_LABEL, LETTER_SPACING_CAPTION,
    # Spacing
    SPACE_0, SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6, SPACE_8, SPACE_10, SPACE_12, SPACE_16,
    GAP_INLINE, GAP_FIELD, GAP_CARD, GAP_CARD_GRID, GAP_SECTION, GAP_PAGE, GAP_SIDEBAR,
    PADDING_PAGE, PADDING_CARD, PADDING_CARD_LG,
    # Radius
    RADIUS_NONE, RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL, RADIUS_PILL, RADIUS_CIRCLE,
    # Shadows
    SHADOW_NONE, SHADOW_HAIRLINE, SHADOW_SM, SHADOW_MD, SHADOW_LG, SHADOW_FOCUS,
    SHADOW_GLOW_SUCCESS, SHADOW_GLOW_WARNING, SHADOW_GLOW_CRITICAL,
    # Breakpoints
    BREAKPOINT_MOBILE, BREAKPOINT_TABLET, BREAKPOINT_LAPTOP, BREAKPOINT_DESKTOP,
    # Z-index
    Z_INDEX_DROPDOWN, Z_INDEX_POPOVER, Z_INDEX_TOAST, Z_INDEX_MODAL, Z_INDEX_TOOLTIP,
    # Transitions
    TRANSITION_FAST, TRANSITION_NORMAL, TRANSITION_SLOW,
    # Chart tokens
    GAUGE_THRESHOLD_TOKENS, CHART_LAYOUT_DEFAULTS,
    # Component constants
    BUTTON_MIN_HEIGHT, BUTTON_PADDING_VERTICAL, BUTTON_PADDING_HORIZONTAL, BUTTON_ICON_GAP,
    BUTTON_RADIUS, BUTTON_FONT_SIZE, BUTTON_FONT_WEIGHT,
    BADGE_PADDING_VERTICAL, BADGE_PADDING_HORIZONTAL, BADGE_RADIUS, BADGE_FONT_SIZE, BADGE_FONT_WEIGHT,
    CARD_RADIUS, CARD_PADDING, CARD_BORDER,
    INPUT_HEIGHT, INPUT_PADDING_VERTICAL, INPUT_PADDING_HORIZONTAL, INPUT_RADIUS, INPUT_FONT_SIZE,
    TABLE_HEADER_BG, TABLE_HEADER_FONT_SIZE, TABLE_HEADER_FONT_COLOR, TABLE_ROW_FONT_SIZE,
    TABLE_ROW_FONT_COLOR, TABLE_BORDER, TABLE_HOVER_BG, TABLE_SELECTED_BG,
    EMPTY_STATE_PADDING, EMPTY_STATE_ICON_SIZE,
    SKELETON_PULSE_DURATION, SPINNER_SIZE_SM, SPINNER_SIZE_MD, SPINNER_SIZE_LG,
    WIZARD_CARD_RADIUS, WIZARD_CARD_SHADOW, WIZARD_CARD_PADDING,
    SIDEBAR_WIDTH_EXPANDED, SIDEBAR_WIDTH_COLLAPSED, SIDEBAR_TRANSITION,
    TOP_BAR_HEIGHT, TOP_BAR_BG, TOP_BAR_BORDER,
    # Helpers
    get_all_tokens, validate_tokens,
)


# =============================================================================
# LEGACY THEME MAPPING
# =============================================================================

# This mapping preserves the exact config.py THEME values for backward compatibility
# The design tokens are derived from these but normalized for semantic clarity

LEGACY_THEME: Final[dict[str, str]] = {
    "bg_primary": "#1a1d21",
    "bg_secondary": "#23272e",
    "bg_card": "#2a2e36",
    "border": "#3a3f4a",
    "text_primary": "#e8eaed",
    "text_secondary": "#9aa3ad",
    "accent_blue": "#00b4d8",
    "accent_green": "#2ecc71",
    "accent_amber": "#f39c12",
    "accent_red": "#e74c3c",
    "accent_purple": "#9b59b6",
}

# Mapping from legacy theme keys to design token roles
LEGACY_TO_TOKEN_MAP: Final[dict[str, str]] = {
    "bg_primary": "surface.app",
    "bg_secondary": "surface.secondary",
    "bg_card": "surface.primary",
    "border": "border.default",
    "text_primary": "text.primary",
    "text_secondary": "text.secondary",
    "accent_blue": "accent.primary",
    "accent_green": "status.success",
    "accent_amber": "status.warning",
    "accent_red": "status.critical",
    "accent_purple": "accent.secondary",
}

# Reverse mapping for reference
TOKEN_TO_LEGACY_MAP: Final[dict[str, str]] = {v: k for k, v in LEGACY_TO_TOKEN_MAP.items()}


# =============================================================================
# THEME OBJECT (Compatible with config.py THEME)
# =============================================================================

@dataclass(frozen=True)
class Theme:
    """
    Immutable theme object providing both legacy and token-based access.

    Usage:
        theme = Theme()
        theme.bg_primary           # Legacy access (config.py compatible)
        theme.surface.primary      # Token access (design system)
        theme.get("surface.primary")  # Dynamic access
    """

    # Legacy properties (config.py compatible)
    bg_primary: str = LEGACY_THEME["bg_primary"]
    bg_secondary: str = LEGACY_THEME["bg_secondary"]
    bg_card: str = LEGACY_THEME["bg_card"]
    border: str = LEGACY_THEME["border"]
    text_primary: str = LEGACY_THEME["text_primary"]
    text_secondary: str = LEGACY_THEME["text_secondary"]
    accent_blue: str = LEGACY_THEME["accent_blue"]
    accent_green: str = LEGACY_THEME["accent_green"]
    accent_amber: str = LEGACY_THEME["accent_amber"]
    accent_red: str = LEGACY_THEME["accent_red"]
    accent_purple: str = LEGACY_THEME["accent_purple"]

    # Token-based access (design system)
    surface_app: str = SURFACE_APP
    surface_primary: str = SURFACE_PRIMARY
    surface_secondary: str = SURFACE_SECONDARY
    surface_elevated: str = SURFACE_ELEVATED
    surface_interactive: str = SURFACE_INTERACTIVE

    text_primary_token: str = TEXT_PRIMARY
    text_secondary_token: str = TEXT_SECONDARY
    text_muted: str = TEXT_MUTED
    text_inverse: str = TEXT_INVERSE
    text_link: str = TEXT_LINK
    text_on_accent: str = TEXT_ON_ACCENT

    border_default: str = BORDER_DEFAULT
    border_subtle: str = BORDER_SUBTLE
    border_strong: str = BORDER_STRONG
    border_focus: str = BORDER_FOCUS
    border_separator: str = BORDER_SEPARATOR

    accent_primary: str = ACCENT_PRIMARY
    accent_primary_hover: str = ACCENT_PRIMARY_HOVER
    accent_primary_active: str = ACCENT_PRIMARY_ACTIVE
    accent_secondary: str = ACCENT_SECONDARY
    accent_selected: str = ACCENT_SELECTED

    status_success: str = STATUS_SUCCESS
    status_warning: str = STATUS_WARNING
    status_critical: str = STATUS_CRITICAL
    status_info: str = STATUS_INFO
    status_neutral: str = STATUS_NEUTRAL

    diag_critical: str = DIAG_CRITICAL
    diag_major: str = DIAG_MAJOR
    diag_minor: str = DIAG_MINOR
    diag_info: str = DIAG_INFO

    datasource_real: str = DATASOURCE_REAL
    datasource_simulation: str = DATASOURCE_SIMULATION
    datasource_ai: str = DATASOURCE_AI

    series_1: str = SERIES_1
    series_2: str = SERIES_2
    series_3: str = SERIES_3
    series_4: str = SERIES_4
    series_5: str = SERIES_5

    chart_good: str = CHART_GOOD
    chart_warning: str = CHART_WARNING
    chart_serious: str = CHART_SERIOUS
    chart_critical: str = CHART_CRITICAL

    def get(self, token_name: str, default: str = "") -> str:
        """Get any token by name (supports both legacy and token names)."""
        # Try legacy mapping first
        if token_name in LEGACY_THEME:
            return LEGACY_THEME[token_name]

        # Try token mapping
        from .tokens import get_color_token
        token_value = get_color_token(token_name)
        if token_value:
            return token_value

        # Try semantic colors
        from .tokens import get_semantic_color
        semantic_value = get_semantic_color(token_name)
        if semantic_value:
            return semantic_value

        return default

    def get_legacy(self, key: str, default: str = "") -> str:
        """Get a legacy theme value by key."""
        return LEGACY_THEME.get(key, default)

    def get_token(self, token_name: str, default: str = "") -> str:
        """Get a design token by name."""
        from .tokens import get_color_token
        return get_color_token(token_name, default)

    def get_semantic(self, role: str, default: str = "") -> str:
        """Get a color by semantic role."""
        from .tokens import get_semantic_color
        return get_semantic_color(role, default)

    def as_legacy_dict(self) -> dict[str, str]:
        """Return the theme as a legacy-compatible dictionary."""
        return dict(LEGACY_THEME)

    def as_token_dict(self) -> dict[str, str]:
        """Return all design tokens as a flat dictionary."""
        return get_all_tokens()

    def validate(self) -> dict[str, bool]:
        """Validate all required tokens are present."""
        return validate_tokens()


# =============================================================================
# CHART THEME MAPPING
# =============================================================================

# Legacy CHART_COLORS from components/charts.py mapped to tokens
LEGACY_CHART_COLORS: Final[dict[str, str]] = {
    "bg": SURFACE_APP,
    "grid": BORDER_DEFAULT,
    "text": TEXT_PRIMARY,
    "text_muted": TEXT_SECONDARY,
    "line_primary": SERIES_1,
    "line_secondary": SERIES_2,
    "line_tertiary": SERIES_3,
    "fill_primary": f"{SERIES_1}20",    # 12% opacity
    "fill_secondary": f"{SERIES_2}20",  # 12% opacity
    "fill_tertiary": f"{SERIES_3}20",   # 12% opacity
}

# Legacy SERIES_COLORS (CVD-safe order)
LEGACY_SERIES_COLORS: Final[list[str]] = [SERIES_1, SERIES_2, SERIES_3, SERIES_4, SERIES_5]

# Legacy STATUS_COLORS (distinct from series)
LEGACY_STATUS_COLORS: Final[dict[str, str]] = {
    "good": CHART_GOOD,
    "warning": CHART_WARNING,
    "serious": CHART_SERIOUS,
    "critical": CHART_CRITICAL,
}

# Legacy GAUGE_THRESHOLDS (preserved exactly)
LEGACY_GAUGE_THRESHOLDS: Final[dict[str, dict[str, float]]] = {
    "rpm": {"green_max": 3000, "amber_max": 5000, "red_max": 6500},
    "speed": {"green_max": 60, "amber_max": 100, "red_max": 140},
    "coolant_temp": {"green_max": 95, "amber_max": 105, "red_max": 115},
    "throttle": {"green_max": 40, "amber_max": 70, "red_max": 100},
    "engine_load": {"green_max": 50, "amber_max": 80, "red_max": 100},
    "fuel_trim": {"green_min": -10, "green_max": 10, "amber_min": -20, "amber_max": 20, "red_min": -30, "red_max": 30},
    "voltage": {"green_min": 13.5, "green_max": 14.5, "amber_min": 12.5, "amber_max": 15.5, "red_min": 11.5, "red_max": 16.0},
}


# =============================================================================
# SINGLETON THEME INSTANCE
# =============================================================================

@lru_cache(maxsize=1)
def get_theme() -> Theme:
    """Get the singleton theme instance."""
    return Theme()


# Convenience instance
theme = get_theme()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Legacy theme
    "LEGACY_THEME",
    "LEGACY_TO_TOKEN_MAP",
    "TOKEN_TO_LEGACY_MAP",
    # Chart theme
    "LEGACY_CHART_COLORS",
    "LEGACY_SERIES_COLORS",
    "LEGACY_STATUS_COLORS",
    "LEGACY_GAUGE_THRESHOLDS",
    # Theme class and instance
    "Theme",
    "get_theme",
    "theme",
]