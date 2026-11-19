"""
i20 AI Garage - CSS Styles & Variable Generation

Generates CSS custom properties (variables) from design tokens and provides
the global stylesheet for the application. Eliminates inline CSS duplication
across modules.
"""

from typing import Final
from dataclasses import dataclass
from functools import lru_cache

# Import design tokens
from .tokens import get_all_tokens, validate_tokens
from .theme import theme


# =============================================================================
# CSS VARIABLE GENERATION
# =============================================================================

# Prefix for all CSS custom properties
CSS_VAR_PREFIX: Final[str] = "--i20"


def _token_to_css_var(token_name: str) -> str:
    """Convert a token name to a CSS custom property name."""
    # Replace dots with hyphens, ensure prefix
    return f"{CSS_VAR_PREFIX}-{token_name.replace('.', '-')}"


def _generate_color_variables() -> dict[str, str]:
    """Generate CSS variables for all color tokens."""
    from .tokens import ALL_COLOR_TOKENS
    return {_token_to_css_var(k): v for k, v in ALL_COLOR_TOKENS.items()}


def _generate_spacing_variables() -> dict[str, str]:
    """Generate CSS variables for all spacing tokens."""
    from .tokens import SPACING_TOKENS, SEMANTIC_SPACING
    vars_dict = {}
    for k, v in SPACING_TOKENS.items():
        vars_dict[_token_to_css_var(k)] = v
    for k, v in SEMANTIC_SPACING.items():
        vars_dict[_token_to_css_var(k)] = v
    return vars_dict


def _generate_radius_variables() -> dict[str, str]:
    """Generate CSS variables for all border radius tokens."""
    from .tokens import RADIUS_TOKENS
    return {_token_to_css_var(k): v for k, v in RADIUS_TOKENS.items()}


def _generate_shadow_variables() -> dict[str, str]:
    """Generate CSS variables for all shadow tokens."""
    from .tokens import SHADOW_TOKENS
    return {_token_to_css_var(k): v for k, v in SHADOW_TOKENS.items()}


def _generate_typography_variables() -> dict[str, str]:
    """Generate CSS variables for typography tokens."""
    from .tokens import (
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
    )
    return {
        f"{CSS_VAR_PREFIX}-font-family-base": FONT_FAMILY_BASE,
        f"{CSS_VAR_PREFIX}-font-family-mono": FONT_FAMILY_MONO,
        f"{CSS_VAR_PREFIX}-font-family-numeric": FONT_FAMILY_NUMERIC,
        f"{CSS_VAR_PREFIX}-font-size-display": FONT_SIZE_DISPLAY,
        f"{CSS_VAR_PREFIX}-font-size-h1": FONT_SIZE_H1,
        f"{CSS_VAR_PREFIX}-font-size-h2": FONT_SIZE_H2,
        f"{CSS_VAR_PREFIX}-font-size-h3": FONT_SIZE_H3,
        f"{CSS_VAR_PREFIX}-font-size-h4": FONT_SIZE_H4,
        f"{CSS_VAR_PREFIX}-font-size-body-lg": FONT_SIZE_BODY_LG,
        f"{CSS_VAR_PREFIX}-font-size-body": FONT_SIZE_BODY,
        f"{CSS_VAR_PREFIX}-font-size-body-sm": FONT_SIZE_BODY_SM,
        f"{CSS_VAR_PREFIX}-font-size-label": FONT_SIZE_LABEL,
        f"{CSS_VAR_PREFIX}-font-size-caption": FONT_SIZE_CAPTION,
        f"{CSS_VAR_PREFIX}-font-size-numeric-xl": FONT_SIZE_NUMERIC_XL,
        f"{CSS_VAR_PREFIX}-font-size-numeric-lg": FONT_SIZE_NUMERIC_LG,
        f"{CSS_VAR_PREFIX}-font-size-numeric-md": FONT_SIZE_NUMERIC_MD,
        f"{CSS_VAR_PREFIX}-font-size-numeric-sm": FONT_SIZE_NUMERIC_SM,
        f"{CSS_VAR_PREFIX}-font-size-code": FONT_SIZE_CODE,
        f"{CSS_VAR_PREFIX}-font-size-code-sm": FONT_SIZE_CODE_SM,
        f"{CSS_VAR_PREFIX}-font-weight-display": str(FONT_WEIGHT_DISPLAY),
        f"{CSS_VAR_PREFIX}-font-weight-h1": str(FONT_WEIGHT_H1),
        f"{CSS_VAR_PREFIX}-font-weight-h2": str(FONT_WEIGHT_H2),
        f"{CSS_VAR_PREFIX}-font-weight-h3": str(FONT_WEIGHT_H3),
        f"{CSS_VAR_PREFIX}-font-weight-h4": str(FONT_WEIGHT_H4),
        f"{CSS_VAR_PREFIX}-font-weight-body": str(FONT_WEIGHT_BODY),
        f"{CSS_VAR_PREFIX}-font-weight-label": str(FONT_WEIGHT_LABEL),
        f"{CSS_VAR_PREFIX}-font-weight-numeric": str(FONT_WEIGHT_NUMERIC),
        f"{CSS_VAR_PREFIX}-line-height-display": str(LINE_HEIGHT_DISPLAY),
        f"{CSS_VAR_PREFIX}-line-height-h1": str(LINE_HEIGHT_H1),
        f"{CSS_VAR_PREFIX}-line-height-h2": str(LINE_HEIGHT_H2),
        f"{CSS_VAR_PREFIX}-line-height-h3": str(LINE_HEIGHT_H3),
        f"{CSS_VAR_PREFIX}-line-height-h4": str(LINE_HEIGHT_H4),
        f"{CSS_VAR_PREFIX}-line-height-body": str(LINE_HEIGHT_BODY),
        f"{CSS_VAR_PREFIX}-line-height-label": str(LINE_HEIGHT_LABEL),
        f"{CSS_VAR_PREFIX}-line-height-numeric": str(LINE_HEIGHT_NUMERIC),
        f"{CSS_VAR_PREFIX}-letter-spacing-display": LETTER_SPACING_DISPLAY,
        f"{CSS_VAR_PREFIX}-letter-spacing-h1": LETTER_SPACING_H1,
        f"{CSS_VAR_PREFIX}-letter-spacing-label": LETTER_SPACING_LABEL,
        f"{CSS_VAR_PREFIX}-letter-spacing-caption": LETTER_SPACING_CAPTION,
    }


def _generate_breakpoint_variables() -> dict[str, str]:
    """Generate CSS variables for breakpoints and container widths."""
    from .tokens import BREAKPOINTS, CONTAINER_MAX_WIDTHS, TOUCH_TARGET_MIN, TOUCH_TARGET_COMFORTABLE
    vars_dict = {_token_to_css_var(k): v for k, v in BREAKPOINTS.items()}
    vars_dict.update({_token_to_css_var(f"container-max-width-{k}"): v for k, v in CONTAINER_MAX_WIDTHS.items()})
    vars_dict[f"{CSS_VAR_PREFIX}-touch-target-min"] = TOUCH_TARGET_MIN
    vars_dict[f"{CSS_VAR_PREFIX}-touch-target-comfortable"] = TOUCH_TARGET_COMFORTABLE
    return vars_dict


def _generate_responsive_spacing_variables() -> dict[str, str]:
    """Generate CSS variables for responsive spacing per breakpoint."""
    from .tokens import RESPONSIVE_SPACING
    vars_dict = {}
    for breakpoint, spacing in RESPONSIVE_SPACING.items():
        for key, value in spacing.items():
            css_key = f"space-{breakpoint}-{key.replace('.', '-')}"
            vars_dict[_token_to_css_var(css_key)] = value
    return vars_dict


def _generate_z_index_variables() -> dict[str, str]:
    """Generate CSS variables for z-index tokens."""
    from .tokens import Z_INDEX_TOKENS
    return {_token_to_css_var(k): str(v) for k, v in Z_INDEX_TOKENS.items()}


def _generate_transition_variables() -> dict[str, str]:
    """Generate CSS variables for transition tokens."""
    from .tokens import TRANSITION_TOKENS
    return {_token_to_css_var(k): v for k, v in TRANSITION_TOKENS.items()}


def _generate_component_variables() -> dict[str, str]:
    """Generate CSS variables for component-specific constants."""
    from .tokens import (
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
    )
    return {
        f"{CSS_VAR_PREFIX}-button-min-height": BUTTON_MIN_HEIGHT,
        f"{CSS_VAR_PREFIX}-button-padding-v": BUTTON_PADDING_VERTICAL,
        f"{CSS_VAR_PREFIX}-button-padding-h": BUTTON_PADDING_HORIZONTAL,
        f"{CSS_VAR_PREFIX}-button-icon-gap": BUTTON_ICON_GAP,
        f"{CSS_VAR_PREFIX}-button-radius": BUTTON_RADIUS,
        f"{CSS_VAR_PREFIX}-button-font-size": BUTTON_FONT_SIZE,
        f"{CSS_VAR_PREFIX}-button-font-weight": str(BUTTON_FONT_WEIGHT),
        f"{CSS_VAR_PREFIX}-badge-padding-v": BADGE_PADDING_VERTICAL,
        f"{CSS_VAR_PREFIX}-badge-padding-h": BADGE_PADDING_HORIZONTAL,
        f"{CSS_VAR_PREFIX}-badge-radius": BADGE_RADIUS,
        f"{CSS_VAR_PREFIX}-badge-font-size": BADGE_FONT_SIZE,
        f"{CSS_VAR_PREFIX}-badge-font-weight": str(BADGE_FONT_WEIGHT),
        f"{CSS_VAR_PREFIX}-card-radius": CARD_RADIUS,
        f"{CSS_VAR_PREFIX}-card-padding": CARD_PADDING,
        f"{CSS_VAR_PREFIX}-card-border": CARD_BORDER,
        f"{CSS_VAR_PREFIX}-input-height": INPUT_HEIGHT,
        f"{CSS_VAR_PREFIX}-input-padding-v": INPUT_PADDING_VERTICAL,
        f"{CSS_VAR_PREFIX}-input-padding-h": INPUT_PADDING_HORIZONTAL,
        f"{CSS_VAR_PREFIX}-input-radius": INPUT_RADIUS,
        f"{CSS_VAR_PREFIX}-input-font-size": INPUT_FONT_SIZE,
        f"{CSS_VAR_PREFIX}-table-header-bg": TABLE_HEADER_BG,
        f"{CSS_VAR_PREFIX}-table-header-font-size": TABLE_HEADER_FONT_SIZE,
        f"{CSS_VAR_PREFIX}-table-header-font-color": TABLE_HEADER_FONT_COLOR,
        f"{CSS_VAR_PREFIX}-table-row-font-size": TABLE_ROW_FONT_SIZE,
        f"{CSS_VAR_PREFIX}-table-row-font-color": TABLE_ROW_FONT_COLOR,
        f"{CSS_VAR_PREFIX}-table-border": TABLE_BORDER,
        f"{CSS_VAR_PREFIX}-table-hover-bg": TABLE_HOVER_BG,
        f"{CSS_VAR_PREFIX}-table-selected-bg": TABLE_SELECTED_BG,
        f"{CSS_VAR_PREFIX}-empty-state-padding": EMPTY_STATE_PADDING,
        f"{CSS_VAR_PREFIX}-empty-state-icon-size": EMPTY_STATE_ICON_SIZE,
        f"{CSS_VAR_PREFIX}-skeleton-pulse-duration": SKELETON_PULSE_DURATION,
        f"{CSS_VAR_PREFIX}-spinner-size-sm": SPINNER_SIZE_SM,
        f"{CSS_VAR_PREFIX}-spinner-size-md": SPINNER_SIZE_MD,
        f"{CSS_VAR_PREFIX}-spinner-size-lg": SPINNER_SIZE_LG,
        f"{CSS_VAR_PREFIX}-wizard-card-radius": WIZARD_CARD_RADIUS,
        f"{CSS_VAR_PREFIX}-wizard-card-shadow": WIZARD_CARD_SHADOW,
        f"{CSS_VAR_PREFIX}-wizard-card-padding": WIZARD_CARD_PADDING,
        f"{CSS_VAR_PREFIX}-sidebar-width-expanded": SIDEBAR_WIDTH_EXPANDED,
        f"{CSS_VAR_PREFIX}-sidebar-width-collapsed": SIDEBAR_WIDTH_COLLAPSED,
        f"{CSS_VAR_PREFIX}-sidebar-transition": SIDEBAR_TRANSITION,
        f"{CSS_VAR_PREFIX}-top-bar-height": TOP_BAR_HEIGHT,
        f"{CSS_VAR_PREFIX}-top-bar-bg": TOP_BAR_BG,
        f"{CSS_VAR_PREFIX}-top-bar-border": TOP_BAR_BORDER,
    }


def generate_all_css_variables() -> dict[str, str]:
    """Generate all CSS custom properties from design tokens."""
    all_vars = {}
    all_vars.update(_generate_color_variables())
    all_vars.update(_generate_spacing_variables())
    all_vars.update(_generate_responsive_spacing_variables())
    all_vars.update(_generate_radius_variables())
    all_vars.update(_generate_shadow_variables())
    all_vars.update(_generate_typography_variables())
    all_vars.update(_generate_breakpoint_variables())
    all_vars.update(_generate_z_index_variables())
    all_vars.update(_generate_transition_variables())
    all_vars.update(_generate_component_variables())
    return all_vars


# =============================================================================
# CSS VARIABLE STYLESHEET
# =============================================================================

def generate_css_variables_stylesheet() -> str:
    """Generate the :root CSS variable block."""
    vars_dict = generate_all_css_variables()
    lines = [":root {"]
    for name, value in sorted(vars_dict.items()):
        lines.append(f"  {name}: {value};")
    lines.append("}")
    return "\n".join(lines)


# =============================================================================
# GLOBAL STYLESHEET
# =============================================================================

GLOBAL_STYLESHEET: Final[str] = f"""
{generate_css_variables_stylesheet()}

/* ============================================================================
   GLOBAL RESET & BASE
   ============================================================================ */

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

html {{
  font-size: 16px;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}}

body {{
  font-family: var(--i20-font-family-base);
  font-size: var(--i20-font-size-body);
  font-weight: var(--i20-font-weight-body);
  line-height: var(--i20-line-height-body);
  color: var(--i20-color-text-primary);
  background-color: var(--i20-color-surface-app);
  letter-spacing: 0;
}}

/* ============================================================================
   TYPOGRAPHY UTILITIES
   ============================================================================ */

.i20-display {{
  font-size: var(--i20-font-size-display);
  font-weight: var(--i20-font-weight-display);
  line-height: var(--i20-line-height-display);
  letter-spacing: var(--i20-letter-spacing-display);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-primary);
}}

.i20-h1 {{
  font-size: var(--i20-font-size-h1);
  font-weight: var(--i20-font-weight-h1);
  line-height: var(--i20-line-height-h1);
  letter-spacing: var(--i20-letter-spacing-h1);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-primary);
}}

.i20-h2 {{
  font-size: var(--i20-font-size-h2);
  font-weight: var(--i20-font-weight-h2);
  line-height: var(--i20-line-height-h2);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-primary);
}}

.i20-h3 {{
  font-size: var(--i20-font-size-h3);
  font-weight: var(--i20-font-weight-h3);
  line-height: var(--i20-line-height-h3);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-primary);
}}

.i20-h4 {{
  font-size: var(--i20-font-size-h4);
  font-weight: var(--i20-font-weight-h4);
  line-height: var(--i20-line-height-h4);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-primary);
}}

.i20-body-lg {{
  font-size: var(--i20-font-size-body-lg);
  font-weight: var(--i20-font-weight-body);
  line-height: var(--i20-line-height-body);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-primary);
}}

.i20-body {{
  font-size: var(--i20-font-size-body);
  font-weight: var(--i20-font-weight-body);
  line-height: var(--i20-line-height-body);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-primary);
}}

.i20-body-sm {{
  font-size: var(--i20-font-size-body-sm);
  font-weight: var(--i20-font-weight-body);
  line-height: var(--i20-line-height-body);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-secondary);
}}

.i20-label {{
  font-size: var(--i20-font-size-label);
  font-weight: var(--i20-font-weight-label);
  line-height: var(--i20-line-height-label);
  letter-spacing: var(--i20-letter-spacing-label);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-secondary);
  text-transform: uppercase;
}}

.i20-caption {{
  font-size: var(--i20-font-size-caption);
  font-weight: var(--i20-font-weight-body);
  line-height: var(--i20-line-height-body);
  letter-spacing: var(--i20-letter-spacing-caption);
  font-family: var(--i20-font-family-base);
  color: var(--i20-color-text-muted);
}}

/* Numeric variants (tabular-nums) */
.i20-numeric-xl {{
  font-size: var(--i20-font-size-numeric-xl);
  font-weight: var(--i20-font-weight-numeric);
  line-height: var(--i20-line-height-numeric);
  font-family: var(--i20-font-family-numeric);
  font-variant-numeric: tabular-nums;
  color: var(--i20-color-text-primary);
}}

.i20-numeric-lg {{
  font-size: var(--i20-font-size-numeric-lg);
  font-weight: var(--i20-font-weight-numeric);
  line-height: var(--i20-line-height-numeric);
  font-family: var(--i20-font-family-numeric);
  font-variant-numeric: tabular-nums;
  color: var(--i20-color-text-primary);
}}

.i20-numeric-md {{
  font-size: var(--i20-font-size-numeric-md);
  font-weight: var(--i20-font-weight-numeric);
  line-height: var(--i20-line-height-numeric);
  font-family: var(--i20-font-family-numeric);
  font-variant-numeric: tabular-nums;
  color: var(--i20-color-text-primary);
}}

.i20-numeric-sm {{
  font-size: var(--i20-font-size-numeric-sm);
  font-weight: var(--i20-font-weight-numeric);
  line-height: var(--i20-line-height-numeric);
  font-family: var(--i20-font-family-numeric);
  font-variant-numeric: tabular-nums;
  color: var(--i20-color-text-primary);
}}

/* Code/Monospace */
.i20-code {{
  font-size: var(--i20-font-size-code);
  font-weight: var(--i20-font-weight-body);
  line-height: var(--i20-line-height-body);
  font-family: var(--i20-font-family-mono);
  color: var(--i20-color-text-primary);
  background: var(--i20-color-surface-secondary);
  padding: 2px 6px;
  border-radius: var(--i20-radius-sm);
}}

.i20-code-sm {{
  font-size: var(--i20-font-size-code-sm);
  font-weight: var(--i20-font-weight-body);
  line-height: var(--i20-line-height-body);
  font-family: var(--i20-font-family-mono);
  color: var(--i20-color-text-secondary);
  background: var(--i20-color-surface-secondary);
  padding: 1px 4px;
  border-radius: var(--i20-radius-sm);
}}

/* Links */
.i20-link {{
  color: var(--i20-color-text-link);
  text-decoration: none;
  transition: color var(--i20-transition-fast);
}}

.i20-link:hover {{
  color: var(--i20-color-accent-primary-hover);
  text-decoration: underline;
}}

.i20-link:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-radius-sm);
}}

/* ============================================================================
   SPACING UTILITIES
   ============================================================================ */

.i20-gap-inline {{ gap: var(--i20-gap-inline); }}
.i20-gap-field {{ gap: var(--i20-gap-field); }}
.i20-gap-card {{ gap: var(--i20-gap-card); }}
.i20-gap-card-grid {{ gap: var(--i20-gap-card-grid); }}
.i20-gap-section {{ gap: var(--i20-gap-section); }}
.i20-gap-page {{ gap: var(--i20-gap-page); }}
.i20-gap-sidebar {{ gap: var(--i20-gap-sidebar); }}

.i20-padding-page {{ padding: var(--i20-padding-page); }}
.i20-padding-card {{ padding: var(--i20-padding-card); }}
.i20-padding-card-lg {{ padding: var(--i20-padding-card-lg); }}

/* ============================================================================
   FOCUS VISIBLE (WCAG 2.1 AA)
   ============================================================================ */

:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-radius-sm);
}}

/* Custom button focus-visible */
.i20-btn:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-button-radius);
}}

/* Custom input focus-visible */
.i20-field-input:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-input-radius);
  border-color: var(--i20-color-border-focus);
}}

/* Custom select focus-visible */
.i20-field-input[aria-invalid="true"]:focus-visible {{
  box-shadow: var(--i20-shadow-focus), 0 0 0 2px var(--i20-color-status-critical);
}}

/* Link focus-visible */
.i20-link:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-radius-sm);
}}

/* Wizard step focus-visible */
.i20-wizard-step button:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-radius-sm);
}}

/* Card focus-visible (for clickable cards) */
.i20-card:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-card-radius);
}}

/* Table row focus-visible (for keyboard navigation) */
.i20-table tbody tr:focus-visible {{
  outline: none;
  box-shadow: inset 0 0 0 2px var(--i20-color-accent-primary);
}}

/* Tab focus-visible */
.stTabs [data-baseweb="tab"]:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-radius-sm) var(--i20-radius-sm) 0 0;
}}

/* Sidebar navigation focus-visible */
.i20-sidebar nav a:focus-visible,
.i20-sidebar nav button:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-radius-sm);
}}

/* Top bar focus-visible */
.i20-top-bar button:focus-visible,
.i20-top-bar a:focus-visible {{
  outline: none;
  box-shadow: var(--i20-shadow-focus);
  border-radius: var(--i20-radius-sm);
}}

/* Ensure focus-visible is not applied to mouse/touch interactions */
:focus:not(:focus-visible) {{
  outline: none;
  box-shadow: none;
}}

/* ============================================================================
   SKIP LINK (Accessibility)
   ============================================================================ */

.i20-skip-link {{
  position: absolute;
  top: -100%;
  left: var(--i20-space-4);
  padding: var(--i20-space-2) var(--i20-space-4);
  background: var(--i20-color-accent-primary);
  color: var(--i20-color-text-on-accent);
  font-size: var(--i20-font-size-body);
  font-weight: var(--i20-font-weight-label);
  border-radius: var(--i20-radius-sm);
  z-index: var(--i20-z-tooltip);
  transition: top var(--i20-transition-fast);
}}

.i20-skip-link:focus {{
  top: var(--i20-space-4);
}}

/* ============================================================================
   REDUCED MOTION (Accessibility)
   ============================================================================ */

@media (prefers-reduced-motion: reduce) {{
  *,
  *::before,
  *::after {{
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }}
}}

/* ============================================================================
   HIGH CONTRAST MODE (Accessibility)
   ============================================================================ */

@media (prefers-contrast: high) {{
  :root {{
    --i20-color-border-default: var(--i20-color-border-strong);
    --i20-color-border-subtle: var(--i20-color-border-default);
    --i20-color-text-secondary: var(--i20-color-text-primary);
    --i20-color-text-muted: var(--i20-color-text-secondary);
  }}
}}

/* ============================================================================
   PRINT STYLES (B1.18)
   ============================================================================ */

@media print {{
  .i20-no-print {{
    display: none !important;
  }}

  body {{
    background: white !important;
    color: black !important;
    font-size: 12pt !important;
    line-height: 1.5 !important;
  }}

  /* Page margins and size */
  @page {{
    margin: 2cm;
    size: A4;
  }}

  /* Hide Streamlit UI elements */
  header,
  footer,
  #MainMenu,
  .stAppHeader,
  section[data-testid="stSidebar"],
  .stTabs [data-baseweb="tab-list"],
  .stButton > button,
  .stDownloadButton > button,
  .stFormSubmitButton > button,
  .stSelectbox,
  .stNumberInput,
  .stTextInput,
  .stTextArea,
  .stRadio,
  .stCheckbox,
  .stSlider,
  .stProgress,
  .stFileUploader,
  .stExpander,
  .stSpinner,
  .stAlert,
  .stMarkdown[style*="margin-top"]:has(> div[style*="display: flex"][style*="gap"]),
  .i20-top-bar,
  .i20-skip-link,
  .i20-live-region {{
    display: none !important;
  }}

  /* Main content fills page */
  .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
    width: 100% !important;
  }}

  .main .block-container {{
    padding: 0 !important;
  }}

  /* Cards - print without shadows, with borders */
  .i20-card {{
    border: 1px solid #ccc !important;
    box-shadow: none !important;
    break-inside: avoid;
    page-break-inside: avoid;
    background: white !important;
    color: black !important;
    margin-bottom: 1em !important;
  }}

  .i20-card-lg {{
    border: 1px solid #ccc !important;
    box-shadow: none !important;
    break-inside: avoid;
    page-break-inside: avoid;
    background: white !important;
    color: black !important;
    margin-bottom: 1em !important;
  }}

  /* Buttons - hide in print or show as plain text */
  .i20-btn {{
    display: none !important;
  }}

  .stButton > button,
  .stDownloadButton > button,
  .stFormSubmitButton > button {{
    display: none !important;
  }}

  /* Tables - ensure they break properly */
  .i20-table,
  .stDataFrame,
  table {{
    page-break-inside: auto !important;
    border-collapse: collapse !important;
    width: 100% !important;
    font-size: 10pt !important;
  }}

  .i20-table thead,
  .stDataFrame thead {{
    display: table-header-group !important;
  }}

  .i20-table tbody,
  .stDataFrame tbody {{
    display: table-row-group !important;
  }}

  .i20-table tr,
  .stDataFrame tr {{
    page-break-inside: avoid !important;
    page-break-after: auto !important;
  }}

  .i20-table th,
  .i20-table td,
  .stDataFrame th,
  .stDataFrame td {{
    border: 1px solid #ccc !important;
    padding: 4px 8px !important;
    background: white !important;
    color: black !important;
  }}

  .i20-table th,
  .stDataFrame th {{
    background: #f0f0f0 !important;
    font-weight: bold !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  /* Charts - hide interactive Plotly charts, show data tables instead */
  .js-plotly-plot,
  .i20-chart-visual,
  iframe {{
    display: none !important;
  }}

  .i20-chart-data-table {{
    display: table !important;
    width: 100% !important;
    page-break-inside: auto !important;
  }}

  .i20-chart-container {{
    page-break-inside: avoid !important;
  }}

  /* Badges - print with borders instead of background colors */
  .i20-badge {{
    border: 1px solid #666 !important;
    background: white !important;
    color: black !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  .i20-badge-success {{
    border-color: #2ecc71 !important;
  }}

  .i20-badge-warning {{
    border-color: #f39c12 !important;
  }}

  .i20-badge-critical {{
    border-color: #e74c3c !important;
  }}

  .i20-badge-info {{
    border-color: #3498db !important;
  }}

  .i20-badge-neutral {{
    border-color: #95a5a6 !important;
  }}

  /* Headings */
  h1, h2, h3, h4, h5, h6,
  .i20-display, .i20-h1, .i20-h2, .i20-h3, .i20-h4 {{
    color: black !important;
    page-break-after: avoid !important;
    page-break-inside: avoid !important;
  }}

  h1, .i20-display, .i20-h1 {{
    font-size: 24pt !important;
    border-bottom: 2px solid #333 !important;
    padding-bottom: 0.25em !important;
    margin-bottom: 0.5em !important;
  }}

  h2, .i20-h2 {{
    font-size: 18pt !important;
    margin-top: 1.5em !important;
    margin-bottom: 0.5em !important;
  }}

  h3, .i20-h3 {{
    font-size: 14pt !important;
    margin-top: 1em !important;
    margin-bottom: 0.5em !important;
  }}

  h4, .i20-h4 {{
    font-size: 12pt !important;
    font-weight: bold !important;
    margin-top: 1em !important;
  }}

  /* Links - show URL after link text */
  a[href]::after {{
    content: " (" attr(href) ")" !important;
    font-size: 9pt !important;
    color: #666 !important;
  }}

  a[href^="#"]::after {{
    content: "" !important;
  }}

  /* Code blocks */
  .i20-code,
  .i20-code-sm,
  pre,
  code {{
    background: #f5f5f5 !important;
    border: 1px solid #ddd !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  /* Report-specific: page breaks between report sections */
  .i20-report-section {{
    page-break-before: always;
  }}

  .i20-report-section:first-child {{
    page-break-before: avoid;
  }}

  /* Hide iframe previews */
  .i20-report-iframe {{
    display: none !important;
  }}

  /* Download links - hide */
  a[download] {{
    display: none !important;
  }}

  /* Status indicators - use text instead of color */
  .i20-status-indicator::before {{
    content: attr(aria-label) ": " !important;
  }}

  .i20-status-dot {{
    display: none !important;
  }}

  /* Grid layouts - stack vertically */
  .i20-grid-auto-fit-card,
  .i20-grid-auto-fit-metric,
  .i20-card-grid,
  .i20-metric-grid {{
    display: block !important;
  }}

  .i20-grid-auto-fit-card > *,
  .i20-grid-auto-fit-metric > *,
  .i20-card-grid > *,
  .i20-metric-grid > * {{
    display: block !important;
    width: 100% !important;
    margin-bottom: 1em !important;
  }}

  /* Empty states */
  .i20-empty-state {{
    border: 1px dashed #ccc !important;
    padding: 2em !important;
    page-break-inside: avoid !important;
  }}

  /* Alerts */
  .i20-alert,
  .stAlert {{
    border: 1px solid #ccc !important;
    background: white !important;
    page-break-inside: avoid !important;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
  }}

  .i20-alert-success,
  .stAlert[data-baseweb="notification"][kind="success"] {{
    border-left: 4px solid #2ecc71 !important;
  }}

  .i20-alert-warning,
  .stAlert[data-baseweb="notification"][kind="warning"] {{
    border-left: 4px solid #f39c12 !important;
  }}

  .i20-alert-critical,
  .stAlert[data-baseweb="notification"][kind="error"] {{
    border-left: 4px solid #e74c3c !important;
  }}

  .i20-alert-info,
  .stAlert[data-baseweb="notification"][kind="info"] {{
    border-left: 4px solid #3498db !important;
  }}

  /* Spinners and skeletons */
  .i20-spinner,
  .i20-skeleton,
  .i20-btn-spinner {{
    display: none !important;
  }}

  /* Table wrapper */
  .i20-table-wrapper {{
    overflow: visible !important;
    max-width: 100% !important;
  }}

  /* Ensure text is readable */
  * {{
    text-shadow: none !important;
    filter: none !important;
  }}

  /* Prevent orphans and widows */
  p, li, td, th {{
    orphans: 3;
    widows: 3;
  }}
}}

/* ============================================================================
   SCROLLABLE REGION FOCUS FIX (B1.17 Accessibility)
   ============================================================================ */

 /*
  * Safari/axe-core requires scrollable regions to be keyboard-focusable.
  * Streamlit generates <pre> elements (class .st-emotion-cache-kg09s) for code blocks
  * that become horizontally scrollable on mobile viewports.
  * This CSS ensures they can receive keyboard focus and show visible focus indicators.
  */

/* Target Streamlit's generated pre/code blocks that are scrollable */
.st-emotion-cache-kg09s,
.st-emotion-cache-kg09s[style*="overflow"],
.st-emotion-cache-kg09s[style*="scroll"],
.pre-scrollable,
.code-scrollable,
pre[style*="overflow-x: auto"],
pre[style*="overflow: auto"],
.stMarkdown pre,
.stCodeBlock pre {{
  /* Make scrollable regions focusable via CSS tabindex equivalent */
  /* Note: tabindex must be added via HTML/JS, but we ensure focus styles work */
}}

/* Visible focus indicator for scrollable code/pre blocks */
.st-emotion-cache-kg09s:focus-visible,
.st-emotion-cache-kg09s:focus,
.pre-scrollable:focus-visible,
.pre-scrollable:focus,
.stMarkdown pre:focus-visible,
.stMarkdown pre:focus,
.stCodeBlock pre:focus-visible,
.stCodeBlock pre:focus {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-sm) !important;
  z-index: 10 !important;
}}

/* Ensure scrollable regions have proper touch scrolling on mobile */
.st-emotion-cache-kg09s,
.stMarkdown pre,
.stCodeBlock pre {{
  -webkit-overflow-scrolling: touch;
  overscroll-behavior: contain;
}}

/* ============================================================================
   STREAMLIT-SPECIFIC OVERRIDES
   ============================================================================ */

/* Hide Streamlit default chrome */
#MainMenu {{ visibility: hidden; }}
header {{ visibility: hidden; }}
footer {{ visibility: hidden; }}

/* Fix Streamlit container padding */
.block-container {{
  padding-top: var(--i20-space-4) !important;
  padding-bottom: var(--i20-space-6) !important;
  padding-left: var(--i20-padding-page) !important;
  padding-right: var(--i20-padding-page) !important;
  max-width: 100% !important;
}}

/* Sidebar styling */
section[data-testid="stSidebar"] {{
  background-color: var(--i20-color-surface-secondary) !important;
  border-right: 1px solid var(--i20-color-border-default) !important;
  width: var(--i20-sidebar-width-expanded) !important;
  transition: width var(--i20-sidebar-transition) !important;
}}

section[data-testid="stSidebar"][aria-expanded="false"] {{
  width: var(--i20-sidebar-width-collapsed) !important;
}}

/* Sidebar content */
section[data-testid="stSidebar"] .stMarkdown {{
  color: var(--i20-color-text-primary) !important;
}}

/* Button overrides */
.stButton > button {{
  font-family: var(--i20-font-family-base) !important;
  font-size: var(--i20-font-size-label) !important;
  font-weight: var(--i20-font-weight-label) !important;
  height: var(--i20-button-min-height) !important;
  padding: var(--i20-button-padding-v) var(--i20-button-padding-h) !important;
  border-radius: var(--i20-button-radius) !important;
  border: 1px solid transparent !important;
  transition: all var(--i20-transition-fast) !important;
  white-space: nowrap !important;
}}

/* Primary button */
.stButton > button[kind="primary"] {{
  background-color: var(--i20-color-accent-primary) !important;
  color: var(--i20-color-text-on-accent) !important;
}}

.stButton > button[kind="primary"]:hover {{
  background-color: var(--i20-color-accent-primary-hover) !important;
}}

.stButton > button[kind="primary"]:active {{
  background-color: var(--i20-color-accent-primary-active) !important;
}}

/* Secondary button */
.stButton > button[kind="secondary"] {{
  background-color: var(--i20-color-surface-primary) !important;
  color: var(--i20-color-text-primary) !important;
  border-color: var(--i20-color-border-default) !important;
}}

.stButton > button[kind="secondary"]:hover {{
  background-color: var(--i20-color-surface-interactive) !important;
  border-color: var(--i20-color-border-strong) !important;
}}

/* Form inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div > div,
.stTextArea > div > div > textarea {{
  font-family: var(--i20-font-family-base) !important;
  font-size: var(--i20-input-font-size) !important;
  height: var(--i20-input-height) !important;
  padding: var(--i20-input-padding-v) var(--i20-input-padding-h) !important;
  border-radius: var(--i20-input-radius) !important;
  border: 1px solid var(--i20-color-border-default) !important;
  background-color: var(--i20-color-surface-secondary) !important;
  color: var(--i20-color-text-primary) !important;
  transition: all var(--i20-transition-fast) !important;
}}

.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stSelectbox > div > div > div > div:focus-within,
.stTextArea > div > div > textarea:focus {{
  border-color: var(--i20-color-border-focus) !important;
  box-shadow: var(--i20-shadow-focus) !important;
  outline: none !important;
}}

/* Labels */
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stTextArea label,
.stCheckbox label,
.stRadio label {{
  font-family: var(--i20-font-family-base) !important;
  font-size: var(--i20-font-size-label) !important;
  font-weight: var(--i20-font-weight-label) !important;
  color: var(--i20-color-text-secondary) !important;
  letter-spacing: var(--i20-letter-spacing-label) !important;
  text-transform: uppercase !important;
}}

/* Dataframe/Table */
.stDataFrame {{
  border: 1px solid var(--i20-color-border-subtle) !important;
  border-radius: var(--i20-radius-md) !important;
  overflow: hidden !important;
}}

.stDataFrame thead th {{
  background-color: var(--i20-table-header-bg) !important;
  font-size: var(--i20-table-header-font-size) !important;
  font-weight: var(--i20-font-weight-label) !important;
  color: var(--i20-table-header-font-color) !important;
  text-transform: uppercase !important;
  letter-spacing: var(--i20-letter-spacing-label) !important;
  border-bottom: 1px solid var(--i20-color-border-subtle) !important;
  padding: var(--i20-space-3) var(--i20-space-4) !important;
}}

.stDataFrame tbody td {{
  font-size: var(--i20-table-row-font-size) !important;
  color: var(--i20-table-row-font-color) !important;
  border-bottom: 1px solid var(--i20-color-border-subtle) !important;
  padding: var(--i20-space-3) var(--i20-space-4) !important;
}}

.stDataFrame tbody tr:hover td {{
  background-color: var(--i20-table-hover-bg) !important;
}}

/* Expander */
.streamlit-expanderHeader {{
  font-family: var(--i20-font-family-base) !important;
  font-size: var(--i20-font-size-h4) !important;
  font-weight: var(--i20-font-weight-h4) !important;
  color: var(--i20-color-text-primary) !important;
  background-color: var(--i20-color-surface-primary) !important;
  border: 1px solid var(--i20-color-border-default) !important;
  border-radius: var(--i20-radius-md) !important;
}}

.streamlit-expanderContent {{
  border: 1px solid var(--i20-color-border-default) !important;
  border-top: none !important;
  border-radius: 0 0 var(--i20-radius-md) var(--i20-radius-md) !important;
  background-color: var(--i20-color-surface-primary) !important;
  padding: var(--i20-padding-card) !important;
}}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{
  gap: var(--i20-space-1) !important;
  border-bottom: 1px solid var(--i20-color-border-subtle) !important;
}}

.stTabs [data-baseweb="tab"] {{
  font-family: var(--i20-font-family-base) !important;
  font-size: var(--i20-font-size-label) !important;
  font-weight: var(--i20-font-weight-label) !important;
  color: var(--i20-color-text-secondary) !important;
  padding: var(--i20-space-2) var(--i20-space-4) !important;
  border-radius: var(--i20-radius-sm) var(--i20-radius-sm) 0 0 !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  border-bottom: none !important;
  transition: all var(--i20-transition-fast) !important;
}}

.stTabs [data-baseweb="tab"]:hover {{
  color: var(--i20-color-text-primary) !important;
  background-color: var(--i20-color-surface-secondary) !important;
}}

.stTabs [aria-selected="true"] {{
  color: var(--i20-color-accent-primary) !important;
  background-color: var(--i20-color-surface-primary) !important;
  border-color: var(--i20-color-border-default) !important;
  border-bottom-color: var(--i20-color-surface-primary) !important;
}}

/* Metric */
[data-testid="metric-container"] {{
  background-color: var(--i20-color-surface-primary) !important;
  border: 1px solid var(--i20-color-border-default) !important;
  border-radius: var(--i20-radius-md) !important;
  padding: var(--i20-padding-card) !important;
}}

[data-testid="metric-container"] > div:first-child {{
  font-size: var(--i20-font-size-label) !important;
  font-weight: var(--i20-font-weight-label) !important;
  color: var(--i20-color-text-secondary) !important;
  text-transform: uppercase !important;
  letter-spacing: var(--i20-letter-spacing-label) !important;
}}

[data-testid="metric-container"] > div:nth-child(2) {{
  font-size: var(--i20-font-size-numeric-lg) !important;
  font-weight: var(--i20-font-weight-numeric) !important;
  font-variant-numeric: tabular-nums !important;
  font-family: var(--i20-font-family-numeric) !important;
  color: var(--i20-color-text-primary) !important;
}}

/* Progress bar */
.stProgress > div > div > div {{
  background-color: var(--i20-color-accent-primary) !important;
  border-radius: var(--i20-radius-pill) !important;
}}

.stProgress > div > div {{
  background-color: var(--i20-color-surface-secondary) !important;
  border-radius: var(--i20-radius-pill) !important;
  height: 8px !important;
}}

/* Alert/Info/Success/Error */
.stAlert {{
  border-radius: var(--i20-radius-md) !important;
  border: 1px solid var(--i20-color-border-default) !important;
}}

.stAlert[data-baseweb="notification"][kind="info"] {{
  background-color: var(--i20-color-surface-primary) !important;
  border-left: 4px solid var(--i20-color-status-info) !important;
}}

.stAlert[data-baseweb="notification"][kind="success"] {{
  background-color: var(--i20-color-surface-primary) !important;
  border-left: 4px solid var(--i20-color-status-success) !important;
}}

.stAlert[data-baseweb="notification"][kind="warning"] {{
  background-color: var(--i20-color-surface-primary) !important;
  border-left: 4px solid var(--i20-color-status-warning) !important;
}}

.stAlert[data-baseweb="notification"][kind="error"] {{
  background-color: var(--i20-color-surface-primary) !important;
  border-left: 4px solid var(--i20-color-status-critical) !important;
}}

/* File uploader */
.stFileUploader {{
  border: 2px dashed var(--i20-color-border-default) !important;
  border-radius: var(--i20-radius-md) !important;
  background-color: var(--i20-color-surface-secondary) !important;
  transition: all var(--i20-transition-fast) !important;
}}

.stFileUploader:hover {{
  border-color: var(--i20-color-accent-primary) !important;
  background-color: var(--i20-color-surface-interactive) !important;
}}

/* Selectbox dropdown */
[data-baseweb="popover"] {{
  background-color: var(--i20-color-surface-elevated) !important;
  border: 1px solid var(--i20-color-border-default) !important;
  border-radius: var(--i20-radius-md) !important;
  box-shadow: var(--i20-shadow-lg) !important;
}}

[data-baseweb="menu"] {{
  background-color: var(--i20-color-surface-elevated) !important;
}}

[data-baseweb="menu"] li {{
  font-family: var(--i20-font-family-base) !important;
  font-size: var(--i20-font-size-body) !important;
  color: var(--i20-color-text-primary) !important;
  padding: var(--i20-space-2) var(--i20-space-3) !important;
}}

[data-baseweb="menu"] li:hover {{
  background-color: var(--i20-color-surface-interactive) !important;
}}

[data-baseweb="menu"] li[aria-selected="true"] {{
  background-color: var(--i20-color-accent-selected) !important;
  color: var(--i20-color-accent-primary) !important;
}}

/* Tooltip */
[data-baseweb="tooltip"] {{
  font-family: var(--i20-font-family-base) !important;
  font-size: var(--i20-font-size-caption) !important;
  background-color: var(--i20-color-surface-elevated) !important;
  border: 1px solid var(--i20-color-border-default) !important;
  border-radius: var(--i20-radius-sm) !important;
  box-shadow: var(--i20-shadow-md) !important;
  color: var(--i20-color-text-primary) !important;
  padding: var(--i20-space-2) var(--i20-space-3) !important;
}}

/* ============================================================================
   FOCUS VISIBLE FOR STREAMLIT NATIVE WIDGETS (B1.7)
   ============================================================================ */

/* Streamlit Button focus-visible */
.stButton > button:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-button-radius) !important;
}}

/* Streamlit TextInput focus-visible */
.stTextInput > div > div > input:focus-visible,
.stNumberInput > div > div > input:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-input-radius) !important;
  border-color: var(--i20-color-border-focus) !important;
}}

/* Streamlit Selectbox focus-visible */
.stSelectbox > div > div > div > div:focus-visible,
.stSelectbox [data-baseweb="select"] > div:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-input-radius) !important;
  border-color: var(--i20-color-border-focus) !important;
}}

/* Streamlit TextArea focus-visible */
.stTextArea > div > div > textarea:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-input-radius) !important;
  border-color: var(--i20-color-border-focus) !important;
}}

/* Streamlit Checkbox focus-visible */
.stCheckbox input:focus-visible,
.stCheckbox > div:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-sm) !important;
}}

/* Streamlit Radio focus-visible */
.stRadio > div > label:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-sm) !important;
}}

/* Streamlit Tabs focus-visible (supplements existing rule) */
.stTabs [data-baseweb="tab"]:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-sm) var(--i20-radius-sm) 0 0 !important;
}}

/* Streamlit Slider focus-visible */
.stSlider > div > div > div[role="slider"]:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: 50% !important;
}}

/* Streamlit FileUploader focus-visible */
.stFileUploader > div:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-md) !important;
  border-color: var(--i20-color-border-focus) !important;
}}

/* Streamlit DataFrame focus-visible */
.stDataFrame:focus-visible,
.stDataFrame [data-testid="stDataFrameResizable"]:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-md) !important;
}}

/* Streamlit Expander focus-visible */
.streamlit-expanderHeader:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-md) !important;
}}

/* Streamlit Metric focus-visible */
[data-testid="metric-container"]:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-md) !important;
}}

/* Streamlit Alert focus-visible */
.stAlert:focus-visible {{
  outline: none !important;
  box-shadow: var(--i20-shadow-focus) !important;
  border-radius: var(--i20-radius-md) !important;
}}

/* ============================================================================
   UTILITY CLASSES FOR CUSTOM COMPONENTS
   ============================================================================ */

/* Card */
.i20-card {{
  background-color: var(--i20-color-surface-primary);
  border: 1px solid var(--i20-color-border-default);
  border-radius: var(--i20-radius-md);
  padding: var(--i20-padding-card);
  transition: all var(--i20-transition-normal);
}}

.i20-card:hover {{
  border-color: var(--i20-color-border-strong);
  box-shadow: var(--i20-shadow-sm);
}}

.i20-card-lg {{
  background-color: var(--i20-color-surface-primary);
  border: 1px solid var(--i20-color-border-default);
  border-radius: var(--i20-radius-lg);
  padding: var(--i20-padding-card-lg);
  box-shadow: var(--i20-shadow-md);
}}

/* Badge */
.i20-badge {{
  display: inline-flex;
  align-items: center;
  padding: var(--i20-badge-padding-v) var(--i20-badge-padding-h);
  font-size: var(--i20-badge-font-size);
  font-weight: var(--i20-badge-font-weight);
  border-radius: var(--i20-badge-radius);
  line-height: 1;
  white-space: nowrap;
}}

.i20-badge-success {{
  background-color: var(--i20-color-status-success);
  color: var(--i20-color-text-on-accent);
}}

.i20-badge-warning {{
  background-color: var(--i20-color-status-warning);
  color: var(--i20-color-text-on-accent);
}}

.i20-badge-critical {{
  background-color: var(--i20-color-status-critical);
  color: var(--i20-color-text-on-accent);
}}

.i20-badge-info {{
  background-color: var(--i20-color-status-info);
  color: var(--i20-color-text-on-accent);
}}

.i20-badge-neutral {{
  background-color: var(--i20-color-status-neutral);
  color: var(--i20-color-text-on-accent);
}}

.i20-badge-primary {{
  background-color: var(--i20-color-accent-primary);
  color: var(--i20-color-text-on-accent);
}}

.i20-badge-secondary {{
  background-color: var(--i20-color-accent-secondary);
  color: var(--i20-color-text-on-accent);
}}

/* Button (custom HTML) */
.i20-btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--i20-button-icon-gap);
  font-family: var(--i20-font-family-base);
  font-size: var(--i20-button-font-size);
  font-weight: var(--i20-button-font-weight);
  height: var(--i20-button-min-height);
  padding: var(--i20-button-padding-v) var(--i20-button-padding-h);
  border-radius: var(--i20-button-radius);
  border: 1px solid transparent;
  cursor: pointer;
  transition: all var(--i20-transition-fast);
  text-decoration: none;
  white-space: nowrap;
  line-height: 1;
}}

.i20-btn:disabled {{
  opacity: 0.5;
  cursor: not-allowed;
}}

.i20-btn-primary {{
  background-color: var(--i20-color-accent-primary);
  color: var(--i20-color-text-on-accent);
}}

.i20-btn-primary:hover:not(:disabled) {{
  background-color: var(--i20-color-accent-primary-hover);
}}

.i20-btn-primary:active:not(:disabled) {{
  background-color: var(--i20-color-accent-primary-active);
}}

.i20-btn-secondary {{
  background-color: var(--i20-color-surface-primary);
  color: var(--i20-color-text-primary);
  border-color: var(--i20-color-border-default);
}}

.i20-btn-secondary:hover:not(:disabled) {{
  background-color: var(--i20-color-surface-interactive);
  border-color: var(--i20-color-border-strong);
}}

.i20-btn-ghost {{
  background-color: transparent;
  color: var(--i20-color-text-primary);
  border-color: transparent;
}}

.i20-btn-ghost:hover:not(:disabled) {{
  background-color: var(--i20-color-surface-interactive);
}}

.i20-btn-danger {{
  background-color: var(--i20-color-status-critical);
  color: var(--i20-color-text-on-accent);
}}

.i20-btn-danger:hover:not(:disabled) {{
  background-color: #c0392b;
}}

.i20-btn-sm {{
  height: 32px;
  padding: 4px var(--i20-space-3);
  font-size: var(--i20-font-size-caption);
}}

.i20-btn-lg {{
  height: 48px;
  padding: var(--i20-space-3) var(--i20-space-6);
  font-size: var(--i20-font-size-body);
}}

/* Alert Banner */
.i20-alert {{
  display: flex;
  align-items: flex-start;
  gap: var(--i20-space-3);
  padding: var(--i20-space-4);
  border-radius: var(--i20-radius-md);
  border: 1px solid var(--i20-color-border-default);
}}

.i20-alert-icon {{
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  margin-top: 2px;
}}

.i20-alert-content {{
  flex: 1;
  min-width: 0;
}}

.i20-alert-title {{
  font-size: var(--i20-font-size-body);
  font-weight: var(--i20-font-weight-label);
  color: var(--i20-color-text-primary);
  margin-bottom: var(--i20-space-1);
}}

.i20-alert-message {{
  font-size: var(--i20-font-size-body-sm);
  color: var(--i20-color-text-secondary);
  line-height: var(--i20-line-height-body);
}}

.i20-alert-success {{
  background-color: rgba(46, 204, 113, 0.1);
  border-color: var(--i20-color-status-success);
}}

.i20-alert-success .i20-alert-icon {{
  color: var(--i20-color-status-success);
}}

.i20-alert-warning {{
  background-color: rgba(243, 156, 18, 0.1);
  border-color: var(--i20-color-status-warning);
}}

.i20-alert-warning .i20-alert-icon {{
  color: var(--i20-color-status-warning);
}}

.i20-alert-critical {{
  background-color: rgba(231, 76, 60, 0.1);
  border-color: var(--i20-color-status-critical);
}}

.i20-alert-critical .i20-alert-icon {{
  color: var(--i20-color-status-critical);
}}

.i20-alert-info {{
  background-color: rgba(0, 180, 216, 0.1);
  border-color: var(--i20-color-status-info);
}}

.i20-alert-info .i20-alert-icon {{
  color: var(--i20-color-status-info);
}}

/* Form Field */
.i20-field {{
  display: flex;
  flex-direction: column;
  gap: var(--i20-gap-field);
}}

.i20-field-label {{
  font-size: var(--i20-font-size-label);
  font-weight: var(--i20-font-weight-label);
  color: var(--i20-color-text-secondary);
  letter-spacing: var(--i20-letter-spacing-label);
  text-transform: uppercase;
}}

.i20-field-input {{
  font-family: var(--i20-font-family-base);
  font-size: var(--i20-input-font-size);
  height: var(--i20-input-height);
  padding: var(--i20-input-padding-v) var(--i20-input-padding-h);
  border-radius: var(--i20-input-radius);
  border: 1px solid var(--i20-color-border-default);
  background-color: var(--i20-color-surface-secondary);
  color: var(--i20-color-text-primary);
  transition: all var(--i20-transition-fast);
  width: 100%;
}}

.i20-field-input:focus {{
  border-color: var(--i20-color-border-focus);
  box-shadow: var(--i20-shadow-focus);
  outline: none;
}}

.i20-field-input:disabled {{
  opacity: 0.5;
  cursor: not-allowed;
}}

.i20-field-input::placeholder {{
  color: var(--i20-color-text-muted);
}}

.i20-field-help {{
  font-size: var(--i20-font-size-caption);
  color: var(--i20-color-text-muted);
}}

.i20-field-error {{
  font-size: var(--i20-font-size-caption);
  color: var(--i20-color-status-critical);
}}

/* Table */
.i20-table {{
  width: 100%;
  border-collapse: collapse;
  font-size: var(--i20-table-row-font-size);
  color: var(--i20-table-row-font-color);
}}

.i20-table th {{
  text-align: left;
  font-size: var(--i20-table-header-font-size);
  font-weight: var(--i20-font-weight-label);
  color: var(--i20-table-header-font-color);
  text-transform: uppercase;
  letter-spacing: var(--i20-letter-spacing-label);
  background-color: var(--i20-table-header-bg);
  border-bottom: 1px solid var(--i20-table-border);
  padding: var(--i20-space-3) var(--i20-space-4);
}}

.i20-table td {{
  border-bottom: 1px solid var(--i20-table-border);
  padding: var(--i20-space-3) var(--i20-space-4);
}}

.i20-table tbody tr:hover td {{
  background-color: var(--i20-table-hover-bg);
}}

.i20-table tbody tr.i20-selected td {{
  background-color: var(--i20-table-selected-bg);
}}

/* Empty State */
.i20-empty-state {{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--i20-empty-state-padding);
  text-align: center;
  color: var(--i20-color-text-secondary);
}}

.i20-empty-state-icon {{
  width: var(--i20-empty-state-icon-size);
  height: var(--i20-empty-state-icon-size);
  margin-bottom: var(--i20-space-4);
  color: var(--i20-color-text-muted);
}}

.i20-empty-state-title {{
  font-size: var(--i20-font-size-h3);
  font-weight: var(--i20-font-weight-h3);
  color: var(--i20-color-text-primary);
  margin-bottom: var(--i20-space-2);
}}

.i20-empty-state-message {{
  font-size: var(--i20-font-size-body);
  max-width: 400px;
  line-height: var(--i20-line-height-body);
}}

/* Loading States */
.i20-skeleton {{
  background: linear-gradient(
    90deg,
    var(--i20-color-surface-secondary) 25%,
    var(--i20-color-surface-interactive) 50%,
    var(--i20-color-surface-secondary) 75%
  );
  background-size: 200% 100%;
  animation: i20-skeleton-pulse var(--i20-skeleton-pulse-duration) ease-in-out infinite;
  border-radius: var(--i20-radius-sm);
}}

@keyframes i20-skeleton-pulse {{
  0% {{ background-position: 200% 0; }}
  100% {{ background-position: -200% 0; }}
}}

.i20-spinner {{
  display: inline-block;
  border: 2px solid var(--i20-color-border-default);
  border-top-color: var(--i20-color-accent-primary);
  border-radius: var(--i20-radius-circle);
  animation: i20-spin 1s linear infinite;
}}

.i20-spinner-sm {{ width: var(--i20-spinner-size-sm); height: var(--i20-spinner-size-sm); }}
.i20-spinner-md {{ width: var(--i20-spinner-size-md); height: var(--i20-spinner-size-md); }}
.i20-spinner-lg {{ width: var(--i20-spinner-size-lg); height: var(--i20-spinner-size-lg); }}

@keyframes i20-spin {{
  to {{ transform: rotate(360deg); }}
}}

/* Wizard Stepper */
.i20-wizard {{
  background-color: var(--i20-color-surface-primary);
  border: 1px solid var(--i20-color-border-default);
  border-radius: var(--i20-wizard-card-radius);
  box-shadow: var(--i20-wizard-card-shadow);
  padding: var(--i20-wizard-card-padding);
}}

.i20-wizard-steps {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--i20-space-6);
  position: relative;
}}

.i20-wizard-steps::before {{
  content: '';
  position: absolute;
  top: 50%;
  left: 0;
  right: 0;
  height: 2px;
  background-color: var(--i20-color-border-default);
  transform: translateY(-50%);
  z-index: 0;
}}

.i20-wizard-step {{
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--i20-space-2);
  position: relative;
  z-index: 1;
  flex: 1;
  text-align: center;
}}

.i20-wizard-step-circle {{
  width: 32px;
  height: 32px;
  border-radius: var(--i20-radius-circle);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--i20-font-size-label);
  font-weight: var(--i20-font-weight-label);
  background-color: var(--i20-color-surface-secondary);
  border: 2px solid var(--i20-color-border-default);
  color: var(--i20-color-text-muted);
  transition: all var(--i20-transition-normal);
}}

.i20-wizard-step.completed .i20-wizard-step-circle {{
  background-color: var(--i20-color-status-success);
  border-color: var(--i20-color-status-success);
  color: var(--i20-color-text-on-accent);
}}

.i20-wizard-step.active .i20-wizard-step-circle {{
  background-color: var(--i20-color-accent-primary);
  border-color: var(--i20-color-accent-primary);
  color: var(--i20-color-text-on-accent);
  box-shadow: var(--i20-shadow-focus);
}}

.i20-wizard-step.error .i20-wizard-step-circle {{
  background-color: var(--i20-color-status-critical);
  border-color: var(--i20-color-status-critical);
  color: var(--i20-color-text-on-accent);
}}

.i20-wizard-step-label {{
  font-size: var(--i20-font-size-caption);
  font-weight: var(--i20-font-weight-label);
  color: var(--i20-color-text-muted);
  text-transform: uppercase;
  letter-spacing: var(--i20-letter-spacing-caption);
  white-space: nowrap;
}}

.i20-wizard-step.active .i20-wizard-step-label {{
  color: var(--i20-color-accent-primary);
}}

.i20-wizard-step.completed .i20-wizard-step-label {{
  color: var(--i20-color-text-secondary);
}}

/* ============================================================================
   RESPONSIVE BREAKPOINTS (Canonical 4 Breakpoints)
   ============================================================================ */

   /* Mobile Portrait: < 768px */
   @media (max-width: 767px) {{
     /* Responsive spacing variables for mobile */
     :root {{
       --i20-gap-inline: var(--i20-space-mobile-gap-inline);
       --i20-gap-field: var(--i20-space-mobile-gap-field);
       --i20-gap-card: var(--i20-space-mobile-gap-card);
       --i20-gap-card-grid: var(--i20-space-mobile-gap-card-grid);
       --i20-gap-section: var(--i20-space-mobile-gap-section);
       --i20-gap-page: var(--i20-space-mobile-gap-page);
       --i20-gap-sidebar: var(--i20-space-mobile-gap-sidebar);
       --i20-padding-page: var(--i20-space-mobile-padding-page);
       --i20-padding-card: var(--i20-space-mobile-padding-card);
       --i20-padding-card-lg: var(--i20-space-mobile-padding-card-lg);
     }}

     .block-container {{
       padding-left: var(--i20-space-4) !important;
       padding-right: var(--i20-space-4) !important;
     }}

     .i20-padding-page {{ padding: var(--i20-space-4); }}

     .i20-numeric-xl {{ font-size: 2.5rem; }}
     .i20-numeric-lg {{ font-size: 1.75rem; }}
     .i20-numeric-md {{ font-size: 1.125rem; }}

     .i20-wizard-steps {{
       overflow-x: auto;
       justify-content: flex-start;
       gap: var(--i20-space-4);
       padding-bottom: var(--i20-space-2);
     }}

     .i20-wizard-steps::before {{
       display: none;
     }}

     .i20-wizard-step {{
       flex: 0 0 auto;
       min-width: 80px;
     }}

     /* Touch target enforcement */
     .stButton > button,
     .i20-btn,
     .stSelectbox > div > div > div > div,
     .stTextInput > div > div > input,
     .stNumberInput > div > div > input {{
       min-height: var(--i20-touch-target-min);
     }}

     /* Sidebar drawer support */
     section[data-testid="stSidebar"] {{
       transform: translateX(-100%);
       transition: transform var(--i20-sidebar-transition) !important;
       z-index: var(--i20-z-modal);
     }}

     section[data-testid="stSidebar"][aria-expanded="true"] {{
       transform: translateX(0);
     }}

     /* Top bar compact */
     .i20-top-bar {{
       padding: var(--i20-space-2) var(--i20-space-3);
     }}

     .i20-top-bar__breadcrumb {{
       display: none;
     }}

     .i20-top-bar__status {{
       gap: var(--i20-space-2);
     }}

     /* Table horizontal scroll */
     .i20-table-wrapper {{
       overflow-x: auto;
       -webkit-overflow-scrolling: touch;
     }}

     /* Card grid adjustments */
     .i20-card-grid {{
       grid-template-columns: 1fr !important;
     }}

     /* Metric card grid */
     .i20-metric-grid {{
       grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)) !important;
     }}

     /* Card responsive padding */
     .i20-card {{ padding: var(--i20-padding-card); }}
     .i20-card-lg {{ padding: var(--i20-padding-card-lg); }}
   }}

   /* Mobile Landscape: < 568px (extra small) */
   @media (max-width: 567px) {{
     /* Responsive spacing variables for mobile landscape */
     :root {{
       --i20-gap-inline: var(--i20-space-mobile-landscape-gap-inline);
       --i20-gap-field: var(--i20-space-mobile-landscape-gap-field);
       --i20-gap-card: var(--i20-space-mobile-landscape-gap-card);
       --i20-gap-card-grid: var(--i20-space-mobile-landscape-gap-card-grid);
       --i20-gap-section: var(--i20-space-mobile-landscape-gap-section);
       --i20-gap-page: var(--i20-space-mobile-landscape-gap-page);
       --i20-gap-sidebar: var(--i20-space-mobile-landscape-gap-sidebar);
       --i20-padding-page: var(--i20-space-mobile-landscape-padding-page);
       --i20-padding-card: var(--i20-space-mobile-landscape-padding-card);
       --i20-padding-card-lg: var(--i20-space-mobile-landscape-padding-card-lg);
     }}

     .i20-padding-page {{ padding: var(--i20-space-3); }}

     .i20-numeric-xl {{ font-size: 2rem; }}
     .i20-numeric-lg {{ font-size: 1.5rem; }}

     .i20-h1 {{ font-size: 1.5rem; }}
     .i20-h2 {{ font-size: 1.25rem; }}
     .i20-h3 {{ font-size: 1.125rem; }}

     .i20-btn-lg {{ height: 44px; }}
     .i20-btn-sm {{ height: 36px; }}

     .i20-metric-grid {{
       grid-template-columns: 1fr !important;
     }}

     /* Status pills stack */
     .i20-top-bar__status {{
       flex-wrap: wrap;
     }}

     .i20-card {{ padding: var(--i20-padding-card); }}
     .i20-card-lg {{ padding: var(--i20-padding-card-lg); }}
   }}

   /* Tablet Portrait: 768px - 1023px */
   @media (min-width: 768px) and (max-width: 1023px) {{
     /* Responsive spacing variables for tablet */
     :root {{
       --i20-gap-inline: var(--i20-space-tablet-gap-inline);
       --i20-gap-field: var(--i20-space-tablet-gap-field);
       --i20-gap-card: var(--i20-space-tablet-gap-card);
       --i20-gap-card-grid: var(--i20-space-tablet-gap-card-grid);
       --i20-gap-section: var(--i20-space-tablet-gap-section);
       --i20-gap-page: var(--i20-space-tablet-gap-page);
       --i20-gap-sidebar: var(--i20-space-tablet-gap-sidebar);
       --i20-padding-page: var(--i20-space-tablet-padding-page);
       --i20-padding-card: var(--i20-space-tablet-padding-card);
       --i20-padding-card-lg: var(--i20-space-tablet-padding-card-lg);
     }}

     .block-container {{
       padding-left: var(--i20-space-5) !important;
       padding-right: var(--i20-space-5) !important;
     }}

     .i20-padding-page {{ padding: var(--i20-space-5); }}

     .i20-numeric-xl {{ font-size: 3rem; }}
     .i20-numeric-lg {{ font-size: 2rem; }}

     .i20-card-grid {{
       grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)) !important;
     }}

     .i20-metric-grid {{
       grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)) !important;
     }}

     /* Sidebar visible */
     section[data-testid="stSidebar"] {{
       transform: translateX(0) !important;
     }}

     /* Top bar shows breadcrumbs */
     .i20-top-bar__breadcrumb {{
       display: flex;
     }}

     .i20-card {{ padding: var(--i20-padding-card); }}
     .i20-card-lg {{ padding: var(--i20-padding-card-lg); }}
   }}

   /* Tablet Landscape / Laptop: 1024px - 1279px */
   @media (min-width: 1024px) and (max-width: 1279px) {{
     /* Responsive spacing variables for laptop */
     :root {{
       --i20-gap-inline: var(--i20-space-laptop-gap-inline);
       --i20-gap-field: var(--i20-space-laptop-gap-field);
       --i20-gap-card: var(--i20-space-laptop-gap-card);
       --i20-gap-card-grid: var(--i20-space-laptop-gap-card-grid);
       --i20-gap-section: var(--i20-space-laptop-gap-section);
       --i20-gap-page: var(--i20-space-laptop-gap-page);
       --i20-gap-sidebar: var(--i20-space-laptop-gap-sidebar);
       --i20-padding-page: var(--i20-space-laptop-padding-page);
       --i20-padding-card: var(--i20-space-laptop-padding-card);
       --i20-padding-card-lg: var(--i20-space-laptop-padding-card-lg);
     }}

     .block-container {{
       padding-left: var(--i20-space-6) !important;
       padding-right: var(--i20-space-6) !important;
       max-width: var(--i20-container-max-width-laptop) !important;
     }}

     .i20-padding-page {{ padding: var(--i20-space-6); }}

     .i20-card-grid {{
       grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)) !important;
     }}

     .i20-metric-grid {{
       grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)) !important;
     }}

     .i20-card {{ padding: var(--i20-padding-card); }}
     .i20-card-lg {{ padding: var(--i20-padding-card-lg); }}
   }}

   /* Desktop: >= 1280px */
   @media (min-width: 1280px) {{
     /* Responsive spacing variables for desktop */
     :root {{
       --i20-gap-inline: var(--i20-space-desktop-gap-inline);
       --i20-gap-field: var(--i20-space-desktop-gap-field);
       --i20-gap-card: var(--i20-space-desktop-gap-card);
       --i20-gap-card-grid: var(--i20-space-desktop-gap-card-grid);
       --i20-gap-section: var(--i20-space-desktop-gap-section);
       --i20-gap-page: var(--i20-space-desktop-gap-page);
       --i20-gap-sidebar: var(--i20-space-desktop-gap-sidebar);
       --i20-padding-page: var(--i20-space-desktop-padding-page);
       --i20-padding-card: var(--i20-space-desktop-padding-card);
       --i20-padding-card-lg: var(--i20-space-desktop-padding-card-lg);
     }}

     .block-container {{
       padding-left: var(--i20-space-8) !important;
       padding-right: var(--i20-space-8) !important;
       max-width: var(--i20-container-max-width-desktop) !important;
     }}

     .i20-padding-page {{ padding: var(--i20-space-8); }}

     .i20-card-grid {{
       grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)) !important;
     }}

     .i20-metric-grid {{
       grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)) !important;
     }}

     .i20-card {{ padding: var(--i20-padding-card); }}
     .i20-card-lg {{ padding: var(--i20-padding-card-lg); }}
   }}
"""


# =============================================================================
# STREAMLIT INJECTION HELPERS
# =============================================================================

def inject_global_css() -> None:
    """
    Inject the global stylesheet into Streamlit.
    Call once at app startup (e.g., in app.py).
    """
    import streamlit as st
    st.markdown(f"<style>{GLOBAL_STYLESHEET}</style>", unsafe_allow_html=True)


def get_css_variables() -> str:
    """Get just the CSS variable definitions as a string."""
    return generate_css_variables_stylesheet()


def get_global_stylesheet() -> str:
    """Get the complete global stylesheet as a string."""
    return GLOBAL_STYLESHEET


# =============================================================================
# VALIDATION
# =============================================================================

def validate_css_variables() -> dict[str, bool]:
    """Validate all CSS variables can be generated."""
    try:
        vars_dict = generate_all_css_variables()
        results = {k: bool(v) for k, v in vars_dict.items()}
        results["_all_valid"] = all(results.values())
        return results
    except Exception as e:
        return {"_error": str(e), "_all_valid": False}


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "CSS_VAR_PREFIX",
    "generate_all_css_variables",
    "generate_css_variables_stylesheet",
    "GLOBAL_STYLESHEET",
    "inject_global_css",
    "get_css_variables",
    "get_global_stylesheet",
    "validate_css_variables",
]