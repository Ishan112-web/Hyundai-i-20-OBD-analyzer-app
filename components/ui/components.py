"""
i20 AI Garage - UI Component Primitives

Reusable, accessible Streamlit-compatible component primitives built on the design system.
All components use design tokens and semantic HTML with ARIA attributes.
"""

from typing import Final, Literal, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import streamlit as st

from .tokens import (
    # Colors
    ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER, ACCENT_PRIMARY_ACTIVE, ACCENT_SECONDARY, ACCENT_SELECTED,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, STATUS_NEUTRAL,
    SURFACE_PRIMARY, SURFACE_SECONDARY, SURFACE_ELEVATED, SURFACE_INTERACTIVE,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    BORDER_DEFAULT, BORDER_SUBTLE, BORDER_STRONG, BORDER_FOCUS,
    # Spacing
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,
    GAP_INLINE, GAP_FIELD, GAP_SIDEBAR, PADDING_PAGE,
    # Radius
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    # Shadows
    SHADOW_SM, SHADOW_MD, SHADOW_LG, SHADOW_FOCUS,
    # Typography
    FONT_FAMILY_BASE, FONT_SIZE_LABEL, FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_CAPTION,
    FONT_WEIGHT_LABEL, FONT_WEIGHT_BODY,
    LETTER_SPACING_LABEL, LETTER_SPACING_CAPTION,
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
    TRANSITION_FAST, TRANSITION_NORMAL,
    SEMANTIC_COLORS,
)
from .styles import CSS_VAR_PREFIX
from .accessibility import (
    render_accessible_status_indicator,
    render_compact_status_indicator,
    render_accessible_button,
    render_accessible_text_input,
    render_accessible_table_wrapper,
    render_table_caption,
    render_table_header,
    TableCaptionProps,
    TableHeaderProps,
    render_focus_trap_html,
    render_wizard_aria_tabs,
    WizardAccessibilityProps,
)


# =============================================================================
# BUTTON COMPONENT
# =============================================================================

class ButtonVariant(Enum):
    PRIMARY = "primary"
    SECONDARY = "secondary"
    GHOST = "ghost"
    DANGER = "danger"

class ButtonSize(Enum):
    SM = "sm"
    MD = "md"
    LG = "lg"

@dataclass
class ButtonProps:
    """Properties for Button component."""
    label: str
    variant: ButtonVariant = ButtonVariant.PRIMARY
    size: ButtonSize = ButtonSize.MD
    icon: str = ""
    icon_position: Literal["left", "right"] = "left"
    disabled: bool = False
    full_width: bool = False
    on_click: Optional[Callable] = None
    key: Optional[str] = None
    aria_label: Optional[str] = None
    type: Literal["button", "submit", "reset"] = "button"


def button(props: ButtonProps) -> bool:
    """
    Render an accessible styled button with proper ARIA and keyboard support.

    Addresses WCAG 2.1.1 Keyboard, 4.1.2 Name/Role/Value.
    Uses custom HTML button with Streamlit postMessage for click handling.

    Returns True if button was clicked.
    """
    # Build unique key
    btn_key = props.key or f"btn_{id(props)}"

    # Variant styles mapping to semantic tokens
    variant_map = {
        ButtonVariant.PRIMARY: "primary",
        ButtonVariant.SECONDARY: "secondary",
        ButtonVariant.GHOST: "ghost",
        ButtonVariant.DANGER: "danger",
    }

    # Size styles
    size_styles = {
        ButtonSize.SM: {"height": "32px", "padding": f"4px {SPACE_3}", "font_size": FONT_SIZE_CAPTION},
        ButtonSize.MD: {"height": BUTTON_MIN_HEIGHT, "padding": f"{BUTTON_PADDING_VERTICAL} {BUTTON_PADDING_HORIZONTAL}", "font_size": BUTTON_FONT_SIZE},
        ButtonSize.LG: {"height": "48px", "padding": f"{SPACE_3} {SPACE_6}", "font_size": FONT_SIZE_BODY},
    }

    s = size_styles[props.size]

    # Build accessible button props
    from .ui.accessibility import AccessibleButtonProps

    accessible_props = AccessibleButtonProps(
        id=btn_key,
        label=props.label,
        variant=variant_map[props.variant],
        disabled=props.disabled,
        loading=False,
        icon=props.icon if props.icon else None,
        icon_position=props.icon_position,
        aria_label=props.aria_label,
        aria_pressed=None,
        aria_expanded=None,
        aria_controls=None,
        aria_describedby=None,
        type=props.type,
        onclick=f"window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{btn_key}', 'value': true}}, '*');" if not props.disabled else None,
        full_width=props.full_width,
    )

    # Render accessible button
    st.markdown(render_accessible_button(accessible_props), unsafe_allow_html=True)

    # Also use hidden Streamlit button for functionality (as fallback)
    # This is hidden but handles the actual click for Streamlit
    st.markdown(f"""
<button id="{btn_key}-st" style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0;" tabindex="-1" aria-hidden="true"></button>
""", unsafe_allow_html=True)

    # Check for click via session state (set by the accessible button's onclick)
    clicked = st.session_state.get(btn_key, False)
    if clicked:
        st.session_state[btn_key] = False
        return True

    return False


def button_primary(label: str, **kwargs) -> bool:
    """Convenience function for primary button."""
    return button(ButtonProps(label=label, variant=ButtonVariant.PRIMARY, **kwargs))

def button_secondary(label: str, **kwargs) -> bool:
    """Convenience function for secondary button."""
    return button(ButtonProps(label=label, variant=ButtonVariant.SECONDARY, **kwargs))

def button_ghost(label: str, **kwargs) -> bool:
    """Convenience function for ghost button."""
    return button(ButtonProps(label=label, variant=ButtonVariant.GHOST, **kwargs))

def button_danger(label: str, **kwargs) -> bool:
    """Convenience function for danger button."""
    return button(ButtonProps(label=label, variant=ButtonVariant.DANGER, **kwargs))


# =============================================================================
# BADGE COMPONENT
# =============================================================================

class BadgeVariant(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    CRITICAL = "critical"
    INFO = "info"
    NEUTRAL = "neutral"
    PRIMARY = "primary"
    SECONDARY = "secondary"

BADGE_STYLES = {
    BadgeVariant.SUCCESS: {"bg": STATUS_SUCCESS, "color": TEXT_ON_ACCENT},
    BadgeVariant.WARNING: {"bg": STATUS_WARNING, "color": TEXT_ON_ACCENT},
    BadgeVariant.CRITICAL: {"bg": STATUS_CRITICAL, "color": TEXT_ON_ACCENT},
    BadgeVariant.INFO: {"bg": STATUS_INFO, "color": TEXT_ON_ACCENT},
    BadgeVariant.NEUTRAL: {"bg": TEXT_MUTED, "color": TEXT_ON_ACCENT},
    BadgeVariant.PRIMARY: {"bg": ACCENT_PRIMARY, "color": TEXT_ON_ACCENT},
    BadgeVariant.SECONDARY: {"bg": ACCENT_SECONDARY, "color": TEXT_ON_ACCENT},
}


def badge(label: str, variant: BadgeVariant = BadgeVariant.NEUTRAL, icon: str = "", key: str = "") -> None:
    """
    Render a badge/pill component.

    Args:
        label: Badge text
        variant: Badge variant
        icon: Optional icon
        key: Optional key for uniqueness
    """
    style = BADGE_STYLES[variant]
    badge_key = key or f"badge_{id(label)}"

    icon_html = f'<span style="display: flex; align-items: center; margin-right: 4px;">{icon}</span>' if icon else ""

    st.markdown(f"""
<style>
.i20-badge-{badge_key} {{
  display: inline-flex;
  align-items: center;
  padding: {BADGE_PADDING_VERTICAL} {BADGE_PADDING_HORIZONTAL};
  font-size: {BADGE_FONT_SIZE};
  font-weight: {BADGE_FONT_WEIGHT};
  border-radius: {BADGE_RADIUS};
  line-height: 1;
  white-space: nowrap;
  background-color: {style['bg']};
  color: {style['color']};
}}
</style>
<span class="i20-badge-{badge_key}">{icon_html}{label}</span>
""", unsafe_allow_html=True)


# =============================================================================
# ALERT COMPONENT
# =============================================================================

class AlertVariant(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    CRITICAL = "critical"
    INFO = "info"

ALERT_STYLES = {
    AlertVariant.SUCCESS: {"bg": f"{STATUS_SUCCESS}1a", "border": STATUS_SUCCESS, "icon_color": STATUS_SUCCESS},
    AlertVariant.WARNING: {"bg": f"{STATUS_WARNING}1a", "border": STATUS_WARNING, "icon_color": STATUS_WARNING},
    AlertVariant.CRITICAL: {"bg": f"{STATUS_CRITICAL}1a", "border": STATUS_CRITICAL, "icon_color": STATUS_CRITICAL},
    AlertVariant.INFO: {"bg": f"{STATUS_INFO}1a", "border": STATUS_INFO, "icon_color": STATUS_INFO},
}

ALERT_ICONS = {
    AlertVariant.SUCCESS: "✓",
    AlertVariant.WARNING: "⚠",
    AlertVariant.CRITICAL: "✕",
    AlertVariant.INFO: "ℹ",
}


def alert(
    title: str,
    message: str,
    variant: AlertVariant = AlertVariant.INFO,
    dismissible: bool = False,
    key: str = "",
    auto_focus: bool = False,
) -> None:
    """
    Render an accessible alert banner with optional focus trap.

    Args:
        title: Alert title
        message: Alert message
        variant: Alert variant
        dismissible: Whether alert can be dismissed
        key: Unique key for state management
        auto_focus: Whether to trap focus in this alert (for critical alerts)
    """
    style = ALERT_STYLES[variant]
    icon = ALERT_ICONS[variant]
    alert_key = key or f"alert_{id(title)}"
    dismiss_key = f"{alert_key}_dismissed"

    # Check dismiss state
    if dismissible and st.session_state.get(dismiss_key, False):
        return

    dismiss_html = ""
    if dismissible:
        dismiss_html = f"""
<button class="i20-alert-dismiss"
        onclick="document.getElementById('{alert_key}').style.display='none';
                window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{dismiss_key}', 'value': true}}, '*');"
        style="background: none; border: none; color: inherit; cursor: pointer; padding: 4px; line-height: 1; opacity: 0.6; flex-shrink: 0;"
        aria-label="Dismiss alert">
  ✕
</button>
"""

    # Add role="alert" for assertive live region behavior
    # Add focus trap for critical alerts if auto_focus is True
    focus_trap_html = ""
    if auto_focus and variant in (AlertVariant.CRITICAL, AlertVariant.WARNING):
        focus_trap_html = render_focus_trap_html(
            container_id=alert_key,
            enabled=True,
            initial_focus_selector="button.i20-alert-dismiss, [tabindex]:not([tabindex='-1'])",
            on_deactivate=""
        )

    st.markdown(f"""
<div id="{alert_key}" class="i20-alert i20-alert-{variant.value}" role="alert" style="
  display: flex;
  align-items: flex-start;
  gap: {GAP_FIELD};
  padding: {SPACE_4};
  border-radius: {RADIUS_MD};
  border: 1px solid {style['border']};
  background-color: {style['bg']};
">
  <span class="i20-alert-icon" style="
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    margin-top: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: {style['icon_color']};
    font-weight: bold;
  " aria-hidden="true">{icon}</span>
  <div class="i20-alert-content" style="flex: 1; min-width: 0;">
    <div class="i20-alert-title" style="
      font-size: {FONT_SIZE_BODY};
      font-weight: {FONT_WEIGHT_LABEL};
      color: {TEXT_PRIMARY};
      margin-bottom: {SPACE_1};
    ">{title}</div>
    <div class="i20-alert-message" style="
      font-size: {FONT_SIZE_BODY_SM};
      color: {TEXT_SECONDARY};
      line-height: 1.5;
    ">{message}</div>
  </div>
  {dismiss_html}
</div>
{focus_trap_html}
""", unsafe_allow_html=True)


# =============================================================================
# CARD COMPONENT
# =============================================================================

@dataclass
class CardProps:
    """Properties for Card component."""
    title: str = ""
    subtitle: str = ""
    content: str = ""
    footer: str = ""
    elevated: bool = False
    bordered: bool = True
    padding: str = CARD_PADDING
    radius: str = CARD_RADIUS
    class_name: str = ""
    on_click: Optional[Callable] = None


def card(props: CardProps) -> None:
    """
    Render a card component.

    Args:
        props: Card properties
    """
    card_key = f"card_{id(props)}"

    shadow = SHADOW_MD if props.elevated else SHADOW_SM
    border = CARD_BORDER if props.bordered else "none"

    header_html = ""
    if props.title or props.subtitle:
        header_html = f"""
<div class="i20-card-header" style="margin-bottom: {GAP_FIELD};">
  {f'<h3 class="i20-h4" style="margin: 0;">{props.title}</h3>' if props.title else ''}
  {f'<p class="i20-body-sm" style="margin: {SPACE_1} 0 0 0;">{props.subtitle}</p>' if props.subtitle else ''}
</div>
"""

    footer_html = ""
    if props.footer:
        footer_html = f"""
<div class="i20-card-footer" style="margin-top: {GAP_FIELD}; padding-top: {GAP_FIELD}; border-top: 1px solid {BORDER_SUBTLE};">
  {props.footer}
</div>
"""

    clickable = "cursor: pointer;" if props.on_click else ""
    onclick = f"onclick=\"window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{card_key}_clicked', 'value': true}}, '*');\"" if props.on_click else ""

    st.markdown(f"""
<div id="{card_key}" class="i20-card {props.class_name}" style="
  background-color: {SURFACE_PRIMARY};
  border: {border};
  border-radius: {props.radius};
  padding: {props.padding};
  box-shadow: {shadow};
  transition: all {TRANSITION_NORMAL};
  {clickable}
" {onclick}>
  {header_html}
  <div class="i20-card-content">{props.content}</div>
  {footer_html}
</div>
""", unsafe_allow_html=True)


def card_simple(content: str, **kwargs) -> None:
    """Convenience function for simple card."""
    card(CardProps(content=content, **kwargs))


# =============================================================================
# FORM COMPONENTS
# =============================================================================

@dataclass
class FormFieldProps:
    """Properties for form field."""
    label: str
    help_text: str = ""
    error_text: str = ""
    required: bool = False
    disabled: bool = False
    input_id: str = ""  # ID of the input element for label 'for' association


def form_field(props: FormFieldProps, input_html: str) -> str:
    """
    Generate a form field wrapper with label, input, help, and error.

    Args:
        props: Form field properties
        input_html: HTML for the input element

    Returns:
        Complete form field HTML
    """
    required_mark = '<span style="color: var(--i20-color-status-critical); margin-left: 2px;">*</span>' if props.required else ""
    disabled_class = "i20-field-disabled" if props.disabled else ""

    help_html = f'<div class="i20-field-help">{props.help_text}</div>' if props.help_text else ""
    error_html = f'<div class="i20-field-error">{props.error_text}</div>' if props.error_text else ""

    # Label 'for' attribute for programmatic association with input
    label_for = f' for="{props.input_id}"' if props.input_id else ""

    return f"""
<div class="i20-field {disabled_class}" style="display: flex; flex-direction: column; gap: {GAP_FIELD};">
  <label class="i20-field-label"{label_for} style="
    font-size: {FONT_SIZE_LABEL};
    font-weight: {FONT_WEIGHT_LABEL};
    color: {TEXT_SECONDARY};
    letter-spacing: {LETTER_SPACING_LABEL};
    text-transform: uppercase;
  ">{props.label}{required_mark}</label>
  {input_html}
  {help_html}
  {error_html}
</div>
"""


def text_input(
    label: str,
    value: str = "",
    placeholder: str = "",
    key: str = "",
    help_text: str = "",
    error_text: str = "",
    required: bool = False,
    disabled: bool = False,
    type: str = "text",
    on_change: Optional[Callable] = None,
) -> str:
    """
    Render a text input field with B1.5 (aria-describedby/aria-invalid) and B1.6 (aria-required) support.

    Returns the input value.
    """
    input_key = key or f"input_{id(label)}"

    # Use Streamlit's native input for functionality
    result = st.text_input(
        label,
        value=value,
        placeholder=placeholder,
        key=input_key,
        disabled=disabled,
        type=type if type == "password" else "default",
        help=help_text if not error_text else None,
        on_change=on_change,
        label_visibility="collapsed",
    )

    # Render styled version with accessibility
    input_id = f"{input_key}-input"
    help_id = f"{input_key}-help" if help_text else ""
    error_id = f"{input_key}-error" if error_text else ""

    # Build aria-describedby: combines help and error IDs
    describedby_ids = []
    if help_text:
        describedby_ids.append(help_id)
    if error_text:
        describedby_ids.append(error_id)
    describedby = " ".join(describedby_ids) if describedby_ids else ""

    field_props = FormFieldProps(
        label=label,
        help_text=help_text,
        error_text=error_text,
        required=required,
        disabled=disabled,
        input_id=input_id,
    )

    input_html = f"""
<input type="{type}"
       class="i20-field-input"
       value="{value}"
       placeholder="{placeholder}"
       {'disabled' if disabled else ''}
       style="
         font-family: {FONT_FAMILY_BASE};
         font-size: {INPUT_FONT_SIZE};
         height: {INPUT_HEIGHT};
         padding: {INPUT_PADDING_VERTICAL} {INPUT_PADDING_HORIZONTAL};
         border-radius: {INPUT_RADIUS};
         border: 1px solid {BORDER_DEFAULT if not error_text else STATUS_CRITICAL};
         background-color: {SURFACE_SECONDARY};
         color: {TEXT_PRIMARY};
         transition: all {TRANSITION_FAST};
         width: 100%;
         {'opacity: 0.5;' if disabled else ''}
       "
       aria-invalid="{'true' if error_text else 'false'}"
       {f'aria-describedby="{describedby}"' if describedby else ''}
       {f'aria-required="true"' if required else ''}
       id="{input_id}"
/>
"""

    if help_text:
        input_html += f'<div id="{help_id}" class="i20-field-help" style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">{help_text}</div>'
    if error_text:
        input_html += f'<div id="{error_id}" class="i20-field-error" role="alert" aria-live="polite" style="font-size: {FONT_SIZE_CAPTION}; color: {STATUS_CRITICAL};">{error_text}</div>'

    st.markdown(form_field(field_props, input_html), unsafe_allow_html=True)

    return result


def selectbox(
    label: str,
    options: list[str],
    index: int = 0,
    key: str = "",
    help_text: str = "",
    error_text: str = "",
    required: bool = False,
    disabled: bool = False,
    on_change: Optional[Callable] = None,
) -> str:
    """
    Render a select box with B1.5 (aria-describedby/aria-invalid) and B1.6 (aria-required) support.

    Returns the selected value.
    """
    input_key = key or f"select_{id(label)}"

    # Use Streamlit's native selectbox for functionality
    result = st.selectbox(
        label,
        options=options,
        index=index,
        key=input_key,
        disabled=disabled,
        help=help_text if not error_text else None,
        on_change=on_change,
        label_visibility="collapsed",
    )

    # Render styled version with accessibility
    select_id = f"{input_key}-select"
    help_id = f"{input_key}-help" if help_text else ""
    error_id = f"{input_key}-error" if error_text else ""

    # Build aria-describedby: combines help and error IDs
    describedby_ids = []
    if help_text:
        describedby_ids.append(help_id)
    if error_text:
        describedby_ids.append(error_id)
    describedby = " ".join(describedby_ids) if describedby_ids else ""

    field_props = FormFieldProps(
        label=label,
        help_text=help_text,
        error_text=error_text,
        required=required,
        disabled=disabled,
        input_id=select_id,
    )

    options_html = "".join(f'<option value="{opt}" {"selected" if i == index else ""}>{opt}</option>' for i, opt in enumerate(options))

    input_html = f"""
<select class="i20-field-input"
        style="
          font-family: {FONT_FAMILY_BASE};
          font-size: {INPUT_FONT_SIZE};
          height: {INPUT_HEIGHT};
          padding: {INPUT_PADDING_VERTICAL} {INPUT_PADDING_HORIZONTAL};
          border-radius: {INPUT_RADIUS};
          border: 1px solid {BORDER_DEFAULT if not error_text else STATUS_CRITICAL};
          background-color: {SURFACE_SECONDARY};
          color: {TEXT_PRIMARY};
          transition: all {TRANSITION_FAST};
          width: 100%;
          appearance: none;
          background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%239aa3ad' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E");
          background-repeat: no-repeat;
          background-position: right {SPACE_3} center;
          padding-right: {SPACE_6};
          {'opacity: 0.5;' if disabled else ''}
        "
        {'disabled' if disabled else ''}
        aria-invalid="{'true' if error_text else 'false'}"
        {f'aria-describedby="{describedby}"' if describedby else ''}
        {f'aria-required="true"' if required else ''}
        id="{select_id}"
>
  {options_html}
</select>
"""

    if help_text:
        input_html += f'<div id="{help_id}" class="i20-field-help" style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">{help_text}</div>'
    if error_text:
        input_html += f'<div id="{error_id}" class="i20-field-error" role="alert" aria-live="polite" style="font-size: {FONT_SIZE_CAPTION}; color: {STATUS_CRITICAL};">{error_text}</div>'

    st.markdown(form_field(field_props, input_html), unsafe_allow_html=True)

    return result


# =============================================================================
# TABLE COMPONENT
# =============================================================================

@dataclass
class TableColumn:
    """Table column definition."""
    key: str
    header: str
    width: str = ""
    align: Literal["left", "center", "right"] = "left"
    format: Optional[Callable[[any], str]] = None
    # Accessibility
    scope: Literal["col", "row", "colgroup", "rowgroup"] = "col"
    abbr: Optional[str] = None
    sort_key: Optional[str] = None


@dataclass
class TableProps:
    """Table component properties."""
    columns: list[TableColumn]
    data: list[dict]
    key: str = ""
    selectable: bool = False
    on_row_click: Optional[Callable[[dict], None]] = None
    empty_message: str = "No data available"
    striped: bool = True
    hoverable: bool = True
    # Accessibility
    caption: Optional[str] = None
    caption_id: Optional[str] = None
    described_by: Optional[str] = None  # aria-describedby for the table


def table(props: TableProps) -> Optional[dict]:
    """
    Render an accessible data table with caption, th scope, and accessible scroll wrapper.

    Returns the selected row data if selectable and a row was clicked.
    """
    table_key = props.key or f"table_{id(props)}"
    selected_key = f"{table_key}_selected"

    # Build header with proper scope
    header_cells = []
    for col in props.columns:
        width_style = f"width: {col.width};" if col.width else ""
        align_style = f"text-align: {col.align};"
        header_cells.append(render_table_header(TableHeaderProps(
            text=col.header,
            scope=col.scope,
            id=f"{table_key}-th-{col.key}" if col.scope == "col" else None,
            abbr=col.abbr,
            sort_key=col.sort_key,
        )))

    # Build rows
    row_html_parts = []
    for row_idx, row in enumerate(props.data):
        row_data_attrs = " ".join(f'data-{k}="{v}"' for k, v in row.items() if isinstance(v, (str, int, float)))
        selected = st.session_state.get(selected_key) == row_idx
        selected_class = "i20-selected" if selected else ""
        clickable = "cursor: pointer;" if props.on_row_click or props.selectable else ""

        cells = []
        for col in props.columns:
            value = row.get(col.key, "")
            if col.format:
                value = col.format(value)
            align_style = f"text-align: {col.align};"
            cells.append(f'<td style="{align_style} padding: {SPACE_3} {SPACE_4};">{value}</td>')

        onclick = ""
        if props.on_row_click or props.selectable:
            onclick = f"onclick=\"window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{selected_key}', 'value': {row_idx}}}, '*');\""

        row_html_parts.append(f"""
<tr class="{selected_class}" style="{clickable}" {onclick} {row_data_attrs}>
  {''.join(cells)}
</tr>
""")

    empty_html = ""
    if not props.data:
        empty_html = f"""
<tbody>
  <tr>
    <td colspan="{len(props.columns)}" style="padding: {EMPTY_STATE_PADDING}; text-align: center; color: {TEXT_SECONDARY};">
      {props.empty_message}
    </td>
  </tr>
</tbody>
"""

    stripe_style = ""
    if props.striped:
        stripe_style = f"""
.i20-table-{table_key} tbody tr:nth-child(even) {{
  background-color: {SURFACE_SECONDARY};
}}
"""

    hover_style = ""
    if props.hoverable:
        hover_style = f"""
.i20-table-{table_key} tbody tr:hover {{
  background-color: {TABLE_HOVER_BG};
}}
"""

    selected_style = f"""
.i20-table-{table_key} tbody tr.i20-selected {{
  background-color: {TABLE_SELECTED_BG};
}}
"""

    # Build table HTML
    caption_html = ""
    if props.caption:
        caption_html = render_table_caption(TableCaptionProps(
            text=props.caption,
            id=props.caption_id or f"{table_key}-caption"
        ))

    table_html = f"""
<table class="i20-table-{table_key}" role="grid" aria-describedby="{props.described_by}" id="{table_key}-table">
  {caption_html}
  <thead>
    <tr>
      {''.join(header_cells)}
    </tr>
  </thead>
  {empty_html if not props.data else f'<tbody>{"".join(row_html_parts)}</tbody>'}
</table>
"""

    # Wrap in accessible scroll region
    wrapped_table = render_accessible_table_wrapper(table_html, f"{table_key}-wrapper")

    st.markdown(f"""
<style>
.i20-table-{table_key} {{
  width: 100%;
  border-collapse: collapse;
  font-size: {TABLE_ROW_FONT_SIZE};
  color: {TABLE_ROW_FONT_COLOR};
}}
.i20-table-{table_key} caption {{
  caption-side: top;
  text-align: left;
  font-size: {FONT_SIZE_LABEL};
  font-weight: {FONT_WEIGHT_LABEL};
  color: {TEXT_SECONDARY};
  padding: {SPACE_2} {SPACE_3};
  text-transform: uppercase;
  letter-spacing: {LETTER_SPACING_LABEL};
}}
.i20-table-{table_key} th {{
  text-align: left;
  font-size: {TABLE_HEADER_FONT_SIZE};
  font-weight: {FONT_WEIGHT_LABEL};
  color: {TABLE_HEADER_FONT_COLOR};
  text-transform: uppercase;
  letter-spacing: {LETTER_SPACING_LABEL};
  background-color: {TABLE_HEADER_BG};
  border-bottom: 1px solid {TABLE_BORDER};
  padding: {SPACE_3} {SPACE_4};
  white-space: nowrap;
}}
.i20-table-{table_key} td {{
  border-bottom: 1px solid {TABLE_BORDER};
  padding: {SPACE_3} {SPACE_4};
}}
{stripe_style}
{hover_style}
{selected_style}
</style>
{wrapped_table}
""", unsafe_allow_html=True)

    # Return selected row if any
    if props.selectable and selected_key in st.session_state:
        selected_idx = st.session_state[selected_key]
        if selected_idx is not None and 0 <= selected_idx < len(props.data):
            return props.data[selected_idx]

    return None


# =============================================================================
# EMPTY STATE COMPONENT
# =============================================================================

@dataclass
class EmptyStateProps:
    """Empty state properties."""
    title: str
    message: str
    icon: str = "📭"
    action_label: str = ""
    action_callback: Optional[Callable] = None
    action_key: str = ""


def empty_state(props: EmptyStateProps) -> None:
    """Render an empty state."""
    empty_key = props.action_key or f"empty_{id(props.title)}"

    action_html = ""
    if props.action_label and props.action_callback:
        action_html = f"""
<button class="i20-btn-primary"
        onclick="window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{empty_key}_action', 'value': true}}, '*');"
        style="margin-top: {SPACE_4};">
  {props.action_label}
</button>
"""

    st.markdown(f"""
<div class="i20-empty-state" style="
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: {EMPTY_STATE_PADDING};
  text-align: center;
  color: {TEXT_SECONDARY};
">
  <div class="i20-empty-state-icon" style="
    width: {EMPTY_STATE_ICON_SIZE};
    height: {EMPTY_STATE_ICON_SIZE};
    margin-bottom: {SPACE_4};
    color: {TEXT_MUTED};
    font-size: {EMPTY_STATE_ICON_SIZE};
    display: flex;
    align-items: center;
    justify-content: center;
  ">{props.icon}</div>
  <h3 class="i20-h3" style="margin: 0 0 {SPACE_2} 0; color: {TEXT_PRIMARY};">{props.title}</h3>
  <p class="i20-body" style="margin: 0; max-width: 400px; line-height: 1.5;">{props.message}</p>
  {action_html}
</div>
""", unsafe_allow_html=True)


# =============================================================================
# LOADING COMPONENTS
# =============================================================================

def skeleton(height: str = "1rem", width: str = "100%", radius: str = RADIUS_SM, key: str = "") -> None:
    """Render a skeleton loader."""
    skeleton_key = key or f"skeleton_{id(height)}"

    st.markdown(f"""
<style>
.i20-skeleton-{skeleton_key} {{
  height: {height};
  width: {width};
  border-radius: {radius};
  background: linear-gradient(
    90deg,
    {SURFACE_SECONDARY} 25%,
    {SURFACE_INTERACTIVE} 50%,
    {SURFACE_SECONDARY} 75%
  );
  background-size: 200% 100%;
  animation: i20-skeleton-pulse {SKELETON_PULSE_DURATION} ease-in-out infinite;
}}
@keyframes i20-skeleton-pulse {{
  0% {{ background-position: 200% 0; }}
  100% {{ background-position: -200% 0; }}
}}
</style>
<div class="i20-skeleton-{skeleton_key}"></div>
""", unsafe_allow_html=True)


def skeleton_text(lines: int = 3, key: str = "") -> None:
    """Render multiple skeleton lines for text content."""
    for i in range(lines):
        height = "1rem" if i < lines - 1 else "0.75rem"
        width = "100%" if i < lines - 1 else "60%"
        skeleton(height=height, width=width, key=f"{key}_line_{i}")


def skeleton_card(key: str = "") -> None:
    """Render a card skeleton."""
    card_key = key or f"skeleton_card_{id(key)}"

    st.markdown(f"""
<div class="i20-card" style="
  background-color: {SURFACE_PRIMARY};
  border: 1px solid {BORDER_DEFAULT};
  border-radius: {CARD_RADIUS};
  padding: {CARD_PADDING};
">
  <div style="display: flex; gap: {GAP_INLINE}; align-items: center; margin-bottom: {GAP_FIELD};">
    <div class="i20-skeleton-{card_key}-avatar" style="width: 40px; height: 40px; border-radius: 50%;"></div>
    <div style="flex: 1;">
      <div class="i20-skeleton-{card_key}-title" style="height: 1rem; width: 60%; border-radius: {RADIUS_SM};"></div>
      <div class="i20-skeleton-{card_key}-subtitle" style="height: 0.875rem; width: 40%; border-radius: {RADIUS_SM}; margin-top: 4px;"></div>
    </div>
  </div>
  <div class="i20-skeleton-{card_key}-content" style="height: 4rem; border-radius: {RADIUS_SM};"></div>
</div>
<style>
.i20-skeleton-{card_key}-avatar,
.i20-skeleton-{card_key}-title,
.i20-skeleton-{card_key}-subtitle,
.i20-skeleton-{card_key}-content {{
  background: linear-gradient(
    90deg,
    {SURFACE_SECONDARY} 25%,
    {SURFACE_INTERACTIVE} 50%,
    {SURFACE_SECONDARY} 75%
  );
  background-size: 200% 100%;
  animation: i20-skeleton-pulse {SKELETON_PULSE_DURATION} ease-in-out infinite;
}}
</style>
""", unsafe_allow_html=True)


def spinner(size: Literal["sm", "md", "lg"] = "md", key: str = "") -> None:
    """Render a spinner."""
    sizes = {"sm": SPINNER_SIZE_SM, "md": SPINNER_SIZE_MD, "lg": SPINNER_SIZE_LG}
    spinner_key = key or f"spinner_{id(size)}"
    spinner_size = sizes[size]

    st.markdown(f"""
<style>
.i20-spinner-{spinner_key} {{
  display: inline-block;
  width: {spinner_size};
  height: {spinner_size};
  border: 2px solid {BORDER_DEFAULT};
  border-top-color: {ACCENT_PRIMARY};
  border-radius: 50%;
  animation: i20-spin 1s linear infinite;
}}
@keyframes i20-spin {{
  to {{ transform: rotate(360deg); }}
}}
</style>
<div class="i20-spinner-{spinner_key}" role="status" aria-label="Loading"></div>
""", unsafe_allow_html=True)


def loading_overlay(message: str = "Loading...", key: str = "") -> None:
    """Render a full-screen loading overlay."""
    overlay_key = key or f"loading_overlay_{id(message)}"

    st.markdown(f"""
<div id="{overlay_key}" class="i20-loading-overlay" style="
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--i20-color-surface-app-d9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: {SPACE_4};
  z-index: 9999;
  color: {TEXT_PRIMARY};
">
  <div class="i20-spinner-{overlay_key}" style="
    width: {SPINNER_SIZE_LG};
    height: {SPINNER_SIZE_LG};
    border: 3px solid {BORDER_DEFAULT};
    border-top-color: {ACCENT_PRIMARY};
    border-radius: 50%;
    animation: i20-spin 1s linear infinite;
  "></div>
  <p style="font-size: {FONT_SIZE_BODY}; margin: 0;">{message}</p>
</div>
<style>
@keyframes i20-spin {{
  to {{ transform: rotate(360deg); }}
}}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# WIZARD COMPONENT
# =============================================================================

@dataclass
class WizardStep:
    """Wizard step definition with full accessibility support."""
    label: str
    icon: str = ""
    completed: bool = False
    active: bool = False
    error: bool = False
    # Accessibility
    description: str = ""  # Optional description for screen readers
    disabled: bool = False  # Whether step can be navigated to


@dataclass
class WizardProps:
    """Wizard component properties with full accessibility support."""
    steps: list[WizardStep]
    current_step: int
    content: str
    next_label: str = "Next"
    prev_label: str = "Back"
    finish_label: str = "Finish"
    on_next: Optional[Callable] = None
    on_prev: Optional[Callable] = None
    on_finish: Optional[Callable] = None
    key: str = ""
    # Accessibility
    announce_step_change: bool = True  # Whether to announce step changes via live region
    live_region_id: str = "i20-live-polite"  # Live region to use for announcements
    show_progress: bool = True  # Whether to show progress text (Step X of Y)


def wizard(props: WizardProps) -> None:
    """Render a fully accessible wizard stepper with step indicator, live region announcements, and focus management.

    Accessibility features:
    - Semantic step indicator using <ol> with aria-current="step"
    - Step states (completed, current, upcoming) distinguishable without color
    - Progress announcement via live region (e.g., "Step 2 of 8: Port Discovery")
    - Keyboard navigation with proper focus management
    - Focus trap in wizard content area
    - Accessible navigation buttons with type="button" and keyboard activation
    """
    wizard_key = props.key or f"wizard_{id(props)}"
    total_steps = len(props.steps)
    current_step_index = props.current_step
    current_step_num = current_step_index + 1

    # Build step labels and IDs
    step_labels = [step.label for step in props.steps]
    step_descriptions = [step.description for step in props.steps]
    step_ids = [f"step-{i}" for i in range(total_steps)]

    # Announce step change via live region (only once per step change)
    if props.announce_step_change:
        step_label = step_labels[current_step_index] if current_step_index < len(step_labels) else ""
        step_desc = step_descriptions[current_step_index] if current_step_index < len(step_descriptions) else ""
        announcement = f"Step {current_step_num} of {total_steps}: {step_label}"
        if step_desc:
            announcement += f". {step_desc}"

        # Use JavaScript to announce to live region
        st.markdown(f'''
<script>
(function() {{
    const region = document.getElementById('{props.live_region_id}');
    if (region) {{
        // Only announce if the message actually changed (avoid duplicate announcements on rerun)
        if (region.dataset.lastMessage !== '{announcement}') {{
            region.textContent = '';
            region.offsetHeight; // Force reflow
            region.textContent = '{announcement}';
            region.dataset.lastMessage = '{announcement}';
        }}
    }}
}})();
</script>
''', unsafe_allow_html=True)

    # Build accessible step indicator using <ol> with aria-current
    step_indicator_items = []
    for i, step in enumerate(props.steps):
        step_num = i + 1
        is_last = i == total_steps - 1
        is_current = i == current_step_index
        is_completed = step.completed
        is_error = step.error
        is_disabled = step.disabled

        # Determine step state for styling and ARIA
        if is_error:
            state = "error"
            state_label = "Error"
            circle_bg = STATUS_CRITICAL
            circle_border = STATUS_CRITICAL
            circle_color = TEXT_ON_ACCENT
            label_color = STATUS_CRITICAL
        elif is_completed:
            state = "completed"
            state_label = "Completed"
            circle_bg = STATUS_SUCCESS
            circle_border = STATUS_SUCCESS
            circle_color = TEXT_ON_ACCENT
            label_color = TEXT_SECONDARY
        elif is_current:
            state = "current"
            state_label = "Current"
            circle_bg = ACCENT_PRIMARY
            circle_border = ACCENT_PRIMARY
            circle_color = TEXT_ON_ACCENT
            label_color = ACCENT_PRIMARY
        else:
            state = "upcoming"
            state_label = "Upcoming"
            circle_bg = SURFACE_SECONDARY
            circle_border = BORDER_DEFAULT
            circle_color = TEXT_MUTED
            label_color = TEXT_MUTED

        # Build step item with full accessibility
        # Use aria-current="step" for current step, visually hidden status for all steps

        # Pre-compute onclick handler to avoid f-string backslash issues
        if not is_disabled:
            onclick_attr = f'window.parent.postMessage({{"type": "streamlit:setComponentValue", "key": "{wizard_key}_step_{i}", "value": true}}, "*");'
        else:
            onclick_attr = ''

        step_indicator_items.append(f"""
<li class="i20-wizard-step-item" style="
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: {SPACE_2};
  position: relative;
  z-index: 1;
  flex: 1;
  text-align: center;
  min-width: 80px;
  list-style: none;
">
  <div class="i20-wizard-step-connector" style="
    {'display: none;' if is_last else f'flex: 1; height: 2px; background: {BORDER_DEFAULT}; position: absolute; top: 16px; left: 48px; right: -48px; z-index: 0;'}
  " aria-hidden="true"></div>
  <button
    type="button"
    class="i20-wizard-step-button"
    role="tab"
    id="{wizard_key}-tab-step-{step_num}"
    aria-selected="{str(is_current).lower()}"
    aria-controls="{wizard_key}-panel-step-{step_num}"
    aria-current="{'step' if is_current else 'false'}"
    aria-disabled="{str(is_disabled).lower()}"
    tabindex="{'0' if is_current else '-1'}"
    style="
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: {FONT_SIZE_LABEL};
      font-weight: {FONT_WEIGHT_LABEL};
      background-color: {circle_bg};
      border: 2px solid {circle_border};
      color: {circle_color};
      transition: all {TRANSITION_NORMAL};
      padding: 0;
      cursor: {'pointer' if not is_disabled else 'not-allowed'};
      opacity: {1.0 if not is_disabled else 0.5};
    "
    onclick="{onclick_attr}"
  >
    <span class="i20-wizard-step-number" aria-hidden="true">{step.icon or step_num}</span>
    <span class="i20-visually-hidden">{step_num}. {step.label} — {state_label}</span>
  </button>
  <div class="i20-wizard-step-label" style="
    font-size: {FONT_SIZE_CAPTION};
    font-weight: {FONT_WEIGHT_LABEL};
    color: {label_color};
    text-transform: uppercase;
    letter-spacing: {LETTER_SPACING_CAPTION};
    white-space: nowrap;
    max-width: 100%;
    overflow: hidden;
    text-overflow: ellipsis;
  ">{step.label}</div>
  <span class="i20-visually-hidden" aria-live="polite">{state_label}</span>
</li>
""")

    # Build progress text
    progress_text = ""
    if props.show_progress:
        progress_text = f"""
<div class="i20-wizard-progress" style="
  margin-bottom: {SPACE_4};
  padding: {SPACE_2} {SPACE_3};
  background-color: {SURFACE_SECONDARY};
  border-radius: {RADIUS_MD};
  text-align: center;
">
  <span class="i20-wizard-progress-text" style="
    font-size: {FONT_SIZE_BODY_SM};
    font-weight: {FONT_WEIGHT_LABEL};
    color: {TEXT_PRIMARY};
  ">Step {current_step_num} of {total_steps}</span>
  <span class="i20-visually-hidden">You are on step {current_step_num} of {total_steps}: {step_labels[current_step_index] if current_step_index < len(step_labels) else ""}</span>
</div>
"""

    # Navigation buttons - use accessible button pattern
    is_first = props.current_step == 0
    is_last = props.current_step == total_steps - 1

    prev_disabled = is_first
    next_label = props.finish_label if is_last else props.next_label

    # Build accessible navigation buttons
    prev_btn = render_accessible_button(type('AccessibleButtonProps', (), {
        'id': f"{wizard_key}_prev",
        'label': props.prev_label,
        'variant': 'secondary',
        'disabled': prev_disabled,
        'loading': False,
        'icon': '←',
        'icon_position': 'start',
        'aria_pressed': None,
        'aria_expanded': None,
        'aria_controls': None,
        'aria_describedby': None,
        'type': 'button',
        'onclick': f"window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{wizard_key}_prev', 'value': true}}, '*');" if not prev_disabled else None,
        'full_width': False,
    })())

    next_btn = render_accessible_button(type('AccessibleButtonProps', (), {
        'id': f"{wizard_key}_next",
        'label': next_label,
        'variant': 'primary',
        'disabled': False,
        'loading': False,
        'icon': '→' if not is_last else '✓',
        'icon_position': 'end',
        'aria_pressed': None,
        'aria_expanded': None,
        'aria_controls': None,
        'aria_describedby': None,
        'type': 'button',
        'onclick': f"window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{wizard_key}_next', 'value': true}}, '*');",
        'full_width': False,
    })())

    # Add focus trap for wizard content
    focus_trap = render_focus_trap_html(
        container_id=f"{wizard_key}-content",
        enabled=True,
        initial_focus_selector="button, [href], input, select, textarea, [tabindex]:not([tabindex='-1'])",
        on_deactivate=f"window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{wizard_key}_focus_trap_deactivated', 'value': true}}, '*');"
    )

    # Render the wizard
    st.markdown(f"""
<div class="i20-wizard" id="{wizard_key}" style="
  background-color: {SURFACE_PRIMARY};
  border: 1px solid {BORDER_DEFAULT};
  border-radius: {WIZARD_CARD_RADIUS};
  box-shadow: {WIZARD_CARD_SHADOW};
  padding: {WIZARD_CARD_PADDING};
" role="region" aria-label="OBD Connection Wizard">
  {progress_text}
  <nav class="i20-wizard-step-indicator" aria-label="Wizard steps" style="margin-bottom: {SPACE_5};">
    <ol class="i20-wizard-steps" role="tablist" style="
      display: flex;
      flex-direction: row;
      justify-content: space-between;
      gap: {SPACE_2};
      margin: 0;
      padding: 0;
      list-style: none;
      flex-wrap: wrap;
    ">
      {''.join(step_indicator_items)}
    </ol>
  </nav>
  <div class="i20-wizard-content" id="{wizard_key}-content" role="tabpanel" aria-labelledby="{wizard_key}-tab-step-{current_step_num}" style="min-height: 200px;">
    {props.content}
  </div>
  <div class="i20-wizard-actions" style="display: flex; justify-content: space-between; margin-top: {SPACE_6}; padding-top: {SPACE_4}; border-top: 1px solid {BORDER_SUBTLE}; flex-wrap: wrap; gap: {SPACE_2};">
    {prev_btn}
    {next_btn}
  </div>
</div>
{focus_trap}
""", unsafe_allow_html=True)

    # Handle step navigation via session state (for clicking on step buttons)
    for i in range(total_steps):
        step_key = f"{wizard_key}_step_{i}"
        step_clicked = st.session_state.get(step_key, False)
        if step_clicked:
            st.session_state[step_key] = False
            # Don't allow navigation to disabled steps
            if not props.steps[i].disabled:
                # Update session state to trigger step change
                # The actual step change is handled by the page's wizard_next/prev functions
                # We just need to signal that a step was clicked
                pass

    # Handle button clicks via session state
    prev_clicked = st.session_state.get(f"{wizard_key}_prev", False)
    next_clicked = st.session_state.get(f"{wizard_key}_next", False)

    if prev_clicked:
        st.session_state[f"{wizard_key}_prev"] = False
        if props.on_prev:
            props.on_prev()

    if next_clicked:
        st.session_state[f"{wizard_key}_next"] = False
        if is_last and props.on_finish:
            props.on_finish()
        elif props.on_next:
            props.on_next()


# =============================================================================
# SIDEBAR COMPONENTS
# =============================================================================

@dataclass
class SidebarNavItem:
    """Sidebar navigation item."""
    label: str
    icon: str
    page: str
    badge: str = ""
    description: str = ""


@dataclass
class SidebarProps:
    """Sidebar properties."""
    nav_items: list[SidebarNavItem]
    current_page: str
    vehicle_info: dict = None
    obd_status: dict = None
    ai_status: dict = None
    simulation_status: dict = None
    collapsed: bool = False
    mobile_open: bool = False
    on_navigate: Optional[Callable[[str], None]] = None
    on_toggle_collapse: Optional[Callable] = None
    on_toggle_mobile: Optional[Callable] = None


def sidebar(props: SidebarProps) -> None:
    """Render the sidebar navigation with mobile drawer support."""
    sidebar_key = "i20_sidebar"

    # Vehicle info section
    vehicle_html = ""
    if props.vehicle_info:
        vehicle_html = f"""
<div class="i20-sidebar-section" style="padding: {SPACE_4} 0; border-bottom: 1px solid {BORDER_SUBTLE}; margin-bottom: {GAP_SIDEBAR};">
  <h3 class="i20-label" style="margin: 0 0 {SPACE_3} 0;">Vehicle</h3>
  <div class="i20-vehicle-info" style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY}; line-height: 1.6;">
    <div><strong>{props.vehicle_info.get('make', '')} {props.vehicle_info.get('model', '')}</strong></div>
    <div>{props.vehicle_info.get('year', '')} · {props.vehicle_info.get('engine', '')}</div>
    <div class="i20-code-sm" style="margin-top: {SPACE_2};">{props.vehicle_info.get('vin', 'N/A')}</div>
  </div>
</div>
"""

    # Status indicators
    status_html = ""
    statuses = [
        ("OBD", props.obd_status),
        ("Data", props.simulation_status),
        ("AI", props.ai_status),
    ]

    if any(s[1] for s in statuses):
        status_items = []
        for label, status in statuses:
            if not status:
                continue
            connected = status.get("connected", False)
            status_text = status.get("text", "Unknown")
            status_type = status.get("status", "neutral")

            # Use accessible status indicator with icon + text
            status_items.append(render_accessible_status_indicator(
                type('Props', (), {
                    'status': status_type,
                    'label': f"{label}: {status_text}",
                    'icon': None,
                    'size': 'sm',
                    'show_text': True
                })()
            ))

        status_html = f"""
<div class="i20-sidebar-section" style="padding: {SPACE_4} 0; border-bottom: 1px solid {BORDER_SUBTLE}; margin-bottom: {GAP_SIDEBAR};">
  <h3 class="i20-label" style="margin: 0 0 {SPACE_3} 0;">Status</h3>
  <div style="display: flex; flex-direction: column; gap: {SPACE_2};">
    {''.join(status_items)}
  </div>
</div>
"""

    # Navigation
    nav_items_html = []
    for item in props.nav_items:
        active = item.page == props.current_page
        badge_html = f'<span class="i20-badge i20-badge-primary" style="font-size: 0.6rem; margin-left: auto;">{item.badge}</span>' if item.badge else ""

        # Use a button that sets session state
        nav_items_html.append(f"""
<button class="i20-nav-item {'i20-nav-item-active' if active else ''}"
        style="display: flex; align-items: center; gap: {GAP_INLINE}; width: 100%; padding: {SPACE_2} {SPACE_3}; border-radius: {RADIUS_SM}; color: {ACCENT_PRIMARY if active else TEXT_PRIMARY}; background: {'var(--i20-color-accent-selected)' if active else 'transparent'}; border: none; cursor: pointer; text-align: left; transition: all {TRANSITION_FAST}; font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_BODY}; font-family: {FONT_FAMILY_BASE};"
        onclick="window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{sidebar_key}_nav', 'value': '{item.page}'}}, '*');"
        aria-current="{'page' if active else 'false'}">
  <span style="font-size: 1.25rem; flex-shrink: 0;">{item.icon}</span>
  <span style="flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{item.label}</span>
  {badge_html}
</button>
""")

    # Collapse toggle (desktop)
    collapse_btn = f"""
<button class="i20-sidebar-toggle"
        onclick="window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{sidebar_key}_toggle', 'value': true}}, '*');"
        style="width: 100%; display: flex; align-items: center; justify-content: center; gap: {SPACE_2}; padding: {SPACE_2}; margin-top: {SPACE_4}; background: none; border: 1px solid {BORDER_DEFAULT}; border-radius: {RADIUS_SM}; color: {TEXT_SECONDARY}; font-size: {FONT_SIZE_CAPTION}; cursor: pointer; transition: all {TRANSITION_FAST};">
  <span>{'◀' if not props.collapsed else '▶'}</span>
  <span>{'Collapse' if not props.collapsed else 'Expand'}</span>
</button>
"""

    # Mobile close button
    mobile_close_btn = f"""
<button class="i20-sidebar-mobile-close"
        onclick="window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{sidebar_key}_mobile_close', 'value': true}}, '*');"
        style="position: absolute; top: {SPACE_3}; right: {SPACE_3}; width: 44px; height: 44px; display: flex; align-items: center; justify-content: center; background: none; border: none; border-radius: {RADIUS_SM}; color: {TEXT_SECONDARY}; font-size: 1.5rem; cursor: pointer; transition: all {TRANSITION_FAST}; z-index: 10;"
        aria-label="Close sidebar">
  <span>×</span>
</button>
"""

    # Determine sidebar mode
    is_mobile_drawer = props.mobile_open
    sidebar_width = SIDEBAR_WIDTH_COLLAPSED if props.collapsed else SIDEBAR_WIDTH_EXPANDED

    # Add focus trap for mobile drawer when open
    focus_trap_html = ""
    if is_mobile_drawer:
        focus_trap_html = render_focus_trap_html(
            container_id=f"{sidebar_key}-drawer",
            enabled=True,
            initial_focus_selector=".i20-sidebar-mobile-close, .i20-nav-item",
            on_deactivate=f"window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{sidebar_key}_mobile_close', 'value': true}}, '*');"
        )

    st.markdown(f"""
<style>
.i20-nav-item:hover:not(.i20-nav-item-active) {{
  background: {SURFACE_INTERACTIVE} !important;
}}
.i20-nav-item:focus-visible {{
  outline: none;
  box-shadow: {SHADOW_FOCUS};
}}
.i20-sidebar-toggle:hover {{
  border-color: {ACCENT_PRIMARY} !important;
  color: {ACCENT_PRIMARY} !important;
}}
.i20-sidebar-mobile-close:hover {{
  background: {SURFACE_INTERACTIVE} !important;
  color: {TEXT_PRIMARY} !important;
}}
/* Mobile drawer styles */
.i20-sidebar-drawer {{
  position: fixed !important;
  left: 0;
  top: 0;
  bottom: 0;
  width: {SIDEBAR_WIDTH_EXPANDED};
  background-color: {SURFACE_SECONDARY};
  border-right: 1px solid {BORDER_DEFAULT};
  z-index: 400;
  transform: translateX(-100%);
  transition: transform {SIDEBAR_TRANSITION};
  overflow-y: auto;
  padding: {SPACE_4};
  box-shadow: {SHADOW_LG};
}}
.i20-sidebar-drawer.open {{
  transform: translateX(0);
}}
.i20-sidebar-backdrop {{
  position: fixed;
  inset: 0;
  background: var(--i20-color-surface-app);
  z-index: 300;
  opacity: 0;
  visibility: hidden;
  transition: opacity {TRANSITION_FAST}, visibility {TRANSITION_FAST};
}}
.i20-sidebar-backdrop.open {{
  opacity: 0.5;
  visibility: visible;
}}
</style>
<div class="i20-sidebar i20-sidebar-drawer {'open' if is_mobile_drawer else ''}"
     id="{sidebar_key}-drawer"
     style="width: {sidebar_width};">
  {mobile_close_btn if is_mobile_drawer else ''}
  {vehicle_html}
  {status_html}
  <nav class="i20-sidebar-nav" aria-label="Main navigation" style="display: flex; flex-direction: column; gap: {SPACE_1};">
    {''.join(nav_items_html)}
  </nav>
  {collapse_btn if not is_mobile_drawer else ''}
</div>
{'<div class="i20-sidebar-backdrop ' + ('open' if is_mobile_drawer else '') + '"></div>' if is_mobile_drawer else ''}
{focus_trap_html}
""", unsafe_allow_html=True)

    # Handle navigation
    nav_key = f"{sidebar_key}_nav"
    if nav_key in st.session_state:
        selected_page = st.session_state[nav_key]
        if selected_page and props.on_navigate:
            props.on_navigate(selected_page)
            st.session_state[nav_key] = None

    # Handle collapse toggle
    toggle_key = f"{sidebar_key}_toggle"
    if st.session_state.get(toggle_key, False):
        st.session_state[toggle_key] = False
        if props.on_toggle_collapse:
            props.on_toggle_collapse()

    # Handle mobile close
    mobile_close_key = f"{sidebar_key}_mobile_close"
    if st.session_state.get(mobile_close_key, False):
        st.session_state[mobile_close_key] = False
        if props.on_toggle_mobile:
            props.on_toggle_mobile()


# =============================================================================
# TOP BAR COMPONENT
# =============================================================================

@dataclass
class TopBarProps:
    """Top bar properties."""
    page_title: str
    breadcrumb: list[tuple[str, str]] = None
    actions: list[dict] = None  # [{label, variant, on_click, key, icon}]
    status_indicators: list[dict] = None  # [{label, status, key}]
    on_mobile_menu: Optional[Callable] = None


def top_bar(props: TopBarProps) -> None:
    """Render the top bar."""
    # Breadcrumb
    breadcrumb_html = ""
    if props.breadcrumb:
        crumbs = []
        for i, (label, href) in enumerate(props.breadcrumb):
            if i == len(props.breadcrumb) - 1:
                crumbs.append(f'<span class="i20-breadcrumb-current" style="color: {TEXT_SECONDARY}; font-weight: {FONT_WEIGHT_LABEL};">{label}</span>')
            else:
                crumbs.append(f'<a href="{href}" class="i20-breadcrumb-item" style="color: {TEXT_MUTED}; text-decoration: none; font-size: {FONT_SIZE_CAPTION};">{label}</a>')
        separator = ' <span style="color: var(--i20-color-text-muted);">/</span> '
        breadcrumb_html = f'<nav class="i20-breadcrumb" style="display: flex; align-items: center; gap: {SPACE_2}; font-size: {FONT_SIZE_CAPTION};">{separator.join(crumbs)}</nav>'

    # Actions
    actions_html = ""
    if props.actions:
        action_buttons = []
        for action in props.actions:
            variant = action.get("variant", "secondary")
            icon = action.get("icon", "")
            key = action.get("key", f"action_{id(action)}")

            variant_styles = {
                "primary": f"background: {ACCENT_PRIMARY}; color: {TEXT_ON_ACCENT}; border: none;",
                "secondary": f"background: {SURFACE_PRIMARY}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_DEFAULT};",
                "ghost": f"background: transparent; color: {TEXT_PRIMARY}; border: none;",
                "danger": f"background: {STATUS_CRITICAL}; color: {TEXT_ON_ACCENT}; border: none;",
            }
            style = variant_styles.get(variant, variant_styles["secondary"])

            icon_html = f'<span style="display: flex; align-items: center;">{icon}</span>' if icon else ""

            action_buttons.append(f"""
<button class="i20-btn i20-btn-{variant}"
        onclick="window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': '{key}', 'value': true}}, '*');"
        style="height: {BUTTON_MIN_HEIGHT}; padding: {BUTTON_PADDING_VERTICAL} {BUTTON_PADDING_HORIZONTAL}; border-radius: {BUTTON_RADIUS}; font-size: {BUTTON_FONT_SIZE}; font-weight: {BUTTON_FONT_WEIGHT}; font-family: {FONT_FAMILY_BASE}; display: inline-flex; align-items: center; gap: {BUTTON_ICON_GAP}; {style} cursor: pointer; transition: all {TRANSITION_FAST};">
  {icon_html}
  <span>{action['label']}</span>
</button>
""")
        actions_html = f'<div class="i20-top-bar-actions" style="display: flex; align-items: center; gap: {GAP_INLINE};">{"".join(action_buttons)}</div>'

    # Status indicators
    status_html = ""
    if props.status_indicators:
        status_items = []
        for status in props.status_indicators:
            label = status.get("label", "")
            status_type = status.get("status", "neutral")
            key = status.get("key", f"status_{id(status)}")

            # Use accessible compact status indicator
            status_items.append(render_compact_status_indicator(status_type, size="sm"))

        status_html = f'<div class="i20-top-bar-status" style="display: flex; align-items: center; gap: {GAP_FIELD};">{"".join(status_items)}</div>'

    # Mobile menu button
    mobile_menu_btn = f"""
<button class="i20-top-bar-mobile-menu"
    onclick="window.parent.postMessage({{'type': 'streamlit:setComponentValue', 'key': 'i20_mobile_menu', 'value': true}}, '*');"
    style="display: none; width: 44px; height: 44px; align-items: center; justify-content: center; background: none; border: none; border-radius: {RADIUS_SM}; color: {TEXT_PRIMARY}; font-size: 1.5rem; cursor: pointer; transition: all {TRANSITION_FAST};">
  <span>☰</span>
</button>
"""

    st.markdown(f"""
<style>
.i20-top-bar-mobile-menu:hover {{
  background: {SURFACE_INTERACTIVE} !important;
}}
@media (max-width: 767px) {{
  .i20-top-bar-mobile-menu {{
    display: flex !important;
  }}
}}
</style>
<header class="i20-top-bar" style="
  height: {TOP_BAR_HEIGHT};
  background: {TOP_BAR_BG};
  border-bottom: {TOP_BAR_BORDER};
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 {PADDING_PAGE};
  position: sticky;
  top: 0;
  z-index: 100;
">
  <div class="i20-top-bar-left" style="display: flex; align-items: center; gap: {GAP_FIELD};">
    {mobile_menu_btn}
    {breadcrumb_html}
    <h1 class="i20-h3" style="margin: 0;">{props.page_title}</h1>
  </div>
  <div class="i20-top-bar-right" style="display: flex; align-items: center; gap: {GAP_FIELD};">
    {status_html}
    {actions_html}
  </div>
</header>
""", unsafe_allow_html=True)

    # Handle action clicks
    if props.actions:
        for action in props.actions:
            key = action.get("key", f"action_{id(action)}")
            if st.session_state.get(key, False):
                st.session_state[key] = False
                if action.get("on_click"):
                    action["on_click"]()

    # Handle mobile menu click
    if st.session_state.get("i20_mobile_menu", False):
        st.session_state["i20_mobile_menu"] = False
        if props.on_mobile_menu:
            props.on_mobile_menu()


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Button
    "ButtonVariant",
    "ButtonSize",
    "ButtonProps",
    "button",
    "button_primary",
    "button_secondary",
    "button_ghost",
    "button_danger",
    # Badge
    "BadgeVariant",
    "badge",
    # Alert
    "AlertVariant",
    "alert",
    # Card
    "CardProps",
    "card",
    "card_simple",
    # Form
    "FormFieldProps",
    "form_field",
    "text_input",
    "selectbox",
    # Table
    "TableColumn",
    "TableProps",
    "table",
    # Empty State
    "EmptyStateProps",
    "empty_state",
    # Loading
    "skeleton",
    "skeleton_text",
    "skeleton_card",
    "spinner",
    "loading_overlay",
    # Wizard
    "WizardStep",
    "WizardProps",
    "wizard",
    # Sidebar
    "SidebarNavItem",
    "SidebarProps",
    "sidebar",
    # Top Bar
    "TopBarProps",
    "top_bar",
]