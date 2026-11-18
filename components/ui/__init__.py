"""
i20 AI Garage - UI Design System Package

Centralized design system with tokens, theme, styles, layout, and components.
"""

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
    # Token registries
    ALL_COLOR_TOKENS, SEMANTIC_COLORS,
    SURFACE_TOKENS, TEXT_TOKENS, BORDER_TOKENS, ACCENT_TOKENS,
    STATUS_TOKENS, DIAG_TOKENS, DATASOURCE_TOKENS, SERIES_TOKENS, CHART_STATUS_TOKENS,
    # Typography
    FONT_FAMILY_BASE, FONT_FAMILY_MONO, FONT_FAMILY_NUMERIC,
    TYPE_SCALE,
    FONT_SIZE_DISPLAY, FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_H4,
    FONT_SIZE_BODY_LG, FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_LABEL, FONT_SIZE_CAPTION,
    FONT_SIZE_NUMERIC_XL, FONT_SIZE_NUMERIC_LG, FONT_SIZE_NUMERIC_MD, FONT_SIZE_NUMERIC_SM,
    FONT_SIZE_CODE, FONT_SIZE_CODE_SM,
    # Spacing
    SPACE_0, SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6, SPACE_8, SPACE_10, SPACE_12, SPACE_16,
    SPACING_TOKENS, SEMANTIC_SPACING,
    GAP_INLINE, GAP_FIELD, GAP_CARD, GAP_CARD_GRID, GAP_SECTION, GAP_PAGE, GAP_SIDEBAR,
    PADDING_PAGE, PADDING_CARD, PADDING_CARD_LG,
    # Radius
    RADIUS_NONE, RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_XL, RADIUS_PILL, RADIUS_CIRCLE,
    RADIUS_TOKENS,
    # Shadows
    SHADOW_NONE, SHADOW_HAIRLINE, SHADOW_SM, SHADOW_MD, SHADOW_LG, SHADOW_FOCUS,
    SHADOW_GLOW_SUCCESS, SHADOW_GLOW_WARNING, SHADOW_GLOW_CRITICAL,
    SHADOW_TOKENS,
    # Breakpoints
    BREAKPOINT_MOBILE, BREAKPOINT_TABLET, BREAKPOINT_LAPTOP, BREAKPOINT_DESKTOP,
    BREAKPOINTS,
    # Z-index
    Z_INDEX_DROPDOWN, Z_INDEX_POPOVER, Z_INDEX_TOAST, Z_INDEX_MODAL, Z_INDEX_TOOLTIP,
    Z_INDEX_TOKENS,
    # Transitions
    TRANSITION_FAST, TRANSITION_NORMAL, TRANSITION_SLOW,
    TRANSITION_TOKENS,
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
    get_color_token, get_semantic_color, get_spacing_token, get_radius_token,
    get_shadow_token, get_typography_token, get_all_tokens, validate_tokens,
)

from .theme import (
    LEGACY_THEME,
    LEGACY_TO_TOKEN_MAP,
    TOKEN_TO_LEGACY_MAP,
    LEGACY_CHART_COLORS,
    LEGACY_SERIES_COLORS,
    LEGACY_STATUS_COLORS,
    LEGACY_GAUGE_THRESHOLDS,
    Theme,
    get_theme,
    theme,
)

from .styles import (
    CSS_VAR_PREFIX,
    generate_all_css_variables,
    generate_css_variables_stylesheet,
    GLOBAL_STYLESHEET,
    inject_global_css,
    get_css_variables,
    get_global_stylesheet,
    validate_css_variables,
)

from .layout import (
    responsive_grid_css,
    auto_fit_grid_css,
    fixed_grid_css,
    GAUGE_GRID_CSS,
    METRIC_GRID_CSS,
    CHART_GRID_CSS,
    FORM_GRID_CSS,
    AUTO_FIT_CARD_CSS,
    AUTO_FIT_METRIC_CSS,
    ColumnSpec,
    create_columns,
    gauge_cluster_columns,
    metric_row_columns,
    chart_columns,
    form_field_columns,
    page_header,
    section_header,
    card_container,
    grid_container,
    sidebar_section,
    sidebar_nav_item,
    top_bar,
    status_indicator,
    responsive_container,
    visually_hidden,
    LAYOUT_CSS,
    inject_layout_css,
    initialize_layout,
)

from .components import (
    # Button
    ButtonVariant,
    ButtonSize,
    ButtonProps,
    button,
    button_primary,
    button_secondary,
    button_ghost,
    button_danger,
    # Badge
    BadgeVariant,
    badge,
    # Alert
    AlertVariant,
    alert,
    # Card
    CardProps,
    card,
    card_simple,
    # Form
    FormFieldProps,
    form_field,
    text_input,
    selectbox,
    # Table
    TableColumn,
    TableProps,
    table,
    # Empty State
    EmptyStateProps,
    empty_state,
    # Loading
    skeleton,
    skeleton_text,
    skeleton_card,
    spinner,
    loading_overlay,
    # Wizard
    WizardStep,
    WizardProps,
    wizard,
    # Sidebar
    SidebarNavItem,
    SidebarProps,
    sidebar,
    # Top Bar
    TopBarProps,
    top_bar,
)

__all__ = [
    # Tokens
    "SURFACE_APP", "SURFACE_PRIMARY", "SURFACE_SECONDARY", "SURFACE_ELEVATED", "SURFACE_INTERACTIVE",
    "TEXT_PRIMARY", "TEXT_SECONDARY", "TEXT_MUTED", "TEXT_INVERSE", "TEXT_LINK", "TEXT_ON_ACCENT",
    "BORDER_DEFAULT", "BORDER_SUBTLE", "BORDER_STRONG", "BORDER_FOCUS", "BORDER_SEPARATOR",
    "ACCENT_PRIMARY", "ACCENT_PRIMARY_HOVER", "ACCENT_PRIMARY_ACTIVE", "ACCENT_SECONDARY", "ACCENT_SELECTED",
    "STATUS_SUCCESS", "STATUS_WARNING", "STATUS_CRITICAL", "STATUS_INFO", "STATUS_NEUTRAL",
    "DIAG_CRITICAL", "DIAG_MAJOR", "DIAG_MINOR", "DIAG_INFO",
    "DATASOURCE_REAL", "DATASOURCE_SIMULATION", "DATASOURCE_AI",
    "SERIES_1", "SERIES_2", "SERIES_3", "SERIES_4", "SERIES_5",
    "CHART_GOOD", "CHART_WARNING", "CHART_SERIOUS", "CHART_CRITICAL",
    "ALL_COLOR_TOKENS", "SEMANTIC_COLORS",
    "SURFACE_TOKENS", "TEXT_TOKENS", "BORDER_TOKENS", "ACCENT_TOKENS",
    "STATUS_TOKENS", "DIAG_TOKENS", "DATASOURCE_TOKENS", "SERIES_TOKENS", "CHART_STATUS_TOKENS",
    "FONT_FAMILY_BASE", "FONT_FAMILY_MONO", "FONT_FAMILY_NUMERIC",
    "TYPE_SCALE",
    "FONT_SIZE_DISPLAY", "FONT_SIZE_H1", "FONT_SIZE_H2", "FONT_SIZE_H3", "FONT_SIZE_H4",
    "FONT_SIZE_BODY_LG", "FONT_SIZE_BODY", "FONT_SIZE_BODY_SM", "FONT_SIZE_LABEL", "FONT_SIZE_CAPTION",
    "FONT_SIZE_NUMERIC_XL", "FONT_SIZE_NUMERIC_LG", "FONT_SIZE_NUMERIC_MD", "FONT_SIZE_NUMERIC_SM",
    "FONT_SIZE_CODE", "FONT_SIZE_CODE_SM",
    "SPACE_0", "SPACE_1", "SPACE_2", "SPACE_3", "SPACE_4", "SPACE_5", "SPACE_6", "SPACE_8", "SPACE_10", "SPACE_12", "SPACE_16",
    "SPACING_TOKENS", "SEMANTIC_SPACING",
    "GAP_INLINE", "GAP_FIELD", "GAP_CARD", "GAP_CARD_GRID", "GAP_SECTION", "GAP_PAGE", "GAP_SIDEBAR",
    "PADDING_PAGE", "PADDING_CARD", "PADDING_CARD_LG",
    "RADIUS_NONE", "RADIUS_SM", "RADIUS_MD", "RADIUS_LG", "RADIUS_XL", "RADIUS_PILL", "RADIUS_CIRCLE",
    "RADIUS_TOKENS",
    "SHADOW_NONE", "SHADOW_HAIRLINE", "SHADOW_SM", "SHADOW_MD", "SHADOW_LG", "SHADOW_FOCUS",
    "SHADOW_GLOW_SUCCESS", "SHADOW_GLOW_WARNING", "SHADOW_GLOW_CRITICAL",
    "SHADOW_TOKENS",
    "BREAKPOINT_MOBILE", "BREAKPOINT_TABLET", "BREAKPOINT_LAPTOP", "BREAKPOINT_DESKTOP",
    "BREAKPOINTS",
    "Z_INDEX_DROPDOWN", "Z_INDEX_POPOVER", "Z_INDEX_TOAST", "Z_INDEX_MODAL", "Z_INDEX_TOOLTIP",
    "Z_INDEX_TOKENS",
    "TRANSITION_FAST", "TRANSITION_NORMAL", "TRANSITION_SLOW",
    "TRANSITION_TOKENS",
    "GAUGE_THRESHOLD_TOKENS", "CHART_LAYOUT_DEFAULTS",
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
    "get_color_token", "get_semantic_color", "get_spacing_token", "get_radius_token",
    "get_shadow_token", "get_typography_token", "get_all_tokens", "validate_tokens",
    # Theme
    "LEGACY_THEME", "LEGACY_TO_TOKEN_MAP", "TOKEN_TO_LEGACY_MAP",
    "LEGACY_CHART_COLORS", "LEGACY_SERIES_COLORS", "LEGACY_STATUS_COLORS", "LEGACY_GAUGE_THRESHOLDS",
    "Theme", "get_theme", "theme",
    # Styles
    "CSS_VAR_PREFIX", "generate_all_css_variables", "generate_css_variables_stylesheet",
    "GLOBAL_STYLESHEET", "inject_global_css", "get_css_variables", "get_global_stylesheet", "validate_css_variables",
    # Layout
    "responsive_grid_css", "auto_fit_grid_css", "fixed_grid_css",
    "GAUGE_GRID_CSS", "METRIC_GRID_CSS", "CHART_GRID_CSS", "FORM_GRID_CSS",
    "AUTO_FIT_CARD_CSS", "AUTO_FIT_METRIC_CSS",
    "ColumnSpec", "create_columns", "gauge_cluster_columns", "metric_row_columns", "chart_columns", "form_field_columns",
    "page_header", "section_header", "card_container", "grid_container",
    "sidebar_section", "sidebar_nav_item", "top_bar", "status_indicator",
    "responsive_container", "visually_hidden",
    "LAYOUT_CSS", "inject_layout_css", "initialize_layout",
    # Components
    "ButtonVariant", "ButtonSize", "ButtonProps", "button", "button_primary", "button_secondary", "button_ghost", "button_danger",
    "BadgeVariant", "badge",
    "AlertVariant", "alert",
    "CardProps", "card", "card_simple",
    "FormFieldProps", "form_field", "text_input", "selectbox",
    "TableColumn", "TableProps", "table",
    "EmptyStateProps", "empty_state",
    "skeleton", "skeleton_text", "skeleton_card", "spinner", "loading_overlay",
    "WizardStep", "WizardProps", "wizard",
    "SidebarNavItem", "SidebarProps", "sidebar",
    "TopBarProps", "top_bar",
]

# Version
__version__ = "1.0.0"