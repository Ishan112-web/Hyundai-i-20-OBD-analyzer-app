"""
i20 AI Garage - Accessibility Utilities

Shared accessibility infrastructure for WCAG 2.1 AA compliance.
Provides live region helpers, focus trap utilities, ARIA utilities,
and accessible HTML generation for custom components.
"""

from typing import Optional, Literal
from dataclasses import dataclass
from components.ui.tokens import SEMANTIC_COLORS


# =============================================================================
# LIVE REGION UTILITIES
# =============================================================================

@dataclass
class LiveRegionProps:
    """Properties for a live region."""
    id: str
    aria_live: Literal["polite", "assertive"] = "polite"
    aria_atomic: bool = True
    aria_relevant: str = "additions text"
    visually_hidden: bool = True


def render_live_region(props: LiveRegionProps) -> str:
    """
    Render an ARIA live region for dynamic content announcements.

    Args:
        props: LiveRegionProps with id, aria_live, aria_atomic, aria_relevant

    Returns:
        HTML string for the live region
    """
    visually_hidden_style = ""
    if props.visually_hidden:
        visually_hidden_style = (
            'style="position:absolute;width:1px;height:1px;padding:0;margin:-1px;'
            'overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;'
            'border:0;"'
        )

    return f'''
<div id="{props.id}"
     role="status"
     aria-live="{props.aria_live}"
     aria-atomic="{str(props.aria_atomic).lower()}"
     aria-relevant="{props.aria_relevant}"
     {visually_hidden_style}>
</div>
'''


def render_persistent_live_regions() -> str:
    """
    Render persistent live regions for the application shell.
    Includes both polite and assertive regions for different priority announcements.
    """
    return f'''
{render_live_region(LiveRegionProps(id="i20-live-polite", aria_live="polite"))}
{render_live_region(LiveRegionProps(id="i20-live-assertive", aria_live="assertive"))}
'''


def announce_to_live_region(message: str, priority: Literal["polite", "assertive"] = "polite") -> str:
    """
    Generate JavaScript to announce a message to a live region.

    Args:
        message: The message to announce
        priority: "polite" or "assertive"

    Returns:
        JavaScript code string
    """
    region_id = "i20-live-assertive" if priority == "assertive" else "i20-live-polite"
    escaped_message = message.replace("'", "\\'")
    return f'''
<script>
(function() {{
    const region = document.getElementById('{region_id}');
    if (region) {{
        region.textContent = '';
        // Force reflow to ensure announcement
        region.offsetHeight;
        region.textContent = '{escaped_message}';
    }}
}})();
</script>
'''


# =============================================================================
# FOCUS TRAP UTILITIES
# =============================================================================

@dataclass
class FocusTrapProps:
    """Properties for focus trap initialization."""
    container_selector: str
    enabled: bool = True
    on_deactivate: Optional[str] = None  # JavaScript callback
    initial_focus_selector: Optional[str] = None
    fallback_focus_selector: Optional[str] = None


def render_focus_trap_script(props: FocusTrapProps) -> str:
    """
    Render a focus trap script for a container element.
    Traps focus within the container when enabled (for modals, drawers, wizards).

    Args:
        props: FocusTrapProps with container_selector and options

    Returns:
        HTML script tag with focus trap logic
    """
    return f'''
<script>
(function() {{
    const container = document.querySelector('{props.container_selector}');
    if (!container) return;

    let focusTrapEnabled = {str(props.enabled).lower()};
    let lastFocusedElement = null;
    const focusableSelector = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"]), [role="button"], [role="tab"], [role="menuitem"]';

    function getFocusableElements() {{
        return Array.from(container.querySelectorAll(focusableSelector))
            .filter(el => !el.disabled && !el.hidden && el.offsetParent !== null);
    }}

    function trapFocus(event) {{
        if (!focusTrapEnabled) return;
        if (event.key !== 'Tab') return;

        const focusableElements = getFocusableElements();
        if (focusableElements.length === 0) return;

        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        if (event.shiftKey) {{
            if (document.activeElement === firstElement) {{
                event.preventDefault();
                lastElement.focus();
            }}
        }} else {{
            if (document.activeElement === lastElement) {{
                event.preventDefault();
                firstElement.focus();
            }}
        }}
    }}

    function handleEscape(event) {{
        if (!focusTrapEnabled) return;
        if (event.key === 'Escape') {{
            event.preventDefault();
            deactivateFocusTrap();
            {props.on_deactivate or ''}
        }}
    }}

    function activateFocusTrap() {{
        focusTrapEnabled = true;
        lastFocusedElement = document.activeElement;
        container.addEventListener('keydown', trapFocus);
        container.addEventListener('keydown', handleEscape);

        // Set initial focus
        const focusableElements = getFocusableElements();
        if (props.initial_focus_selector) {{
            const initialEl = container.querySelector(props.initial_focus_selector);
            if (initialEl) {{
                initialEl.focus();
                return;
            }}
        }}
        if (focusableElements.length > 0) {{
            focusableElements[0].focus();
        }} else if (props.fallback_focus_selector) {{
            const fallback = container.querySelector(props.fallback_focus_selector);
            if (fallback) fallback.focus();
        }}
    }}

    function deactivateFocusTrap() {{
        focusTrapEnabled = false;
        container.removeEventListener('keydown', trapFocus);
        container.removeEventListener('keydown', handleEscape);
        if (lastFocusedElement && typeof lastFocusedElement.focus === 'function') {{
            lastFocusedElement.focus();
        }}
    }}

    // Expose control functions globally for external triggers
    window.i20FocusTrap = window.i20FocusTrap || {{}};
    window.i20FocusTrap[props.container_selector] = {{
        activate: activateFocusTrap,
        deactivate: deactivateFocusTrap,
        setEnabled: (enabled) => {{ focusTrapEnabled = enabled; }}
    }};

    // Auto-activate if container is visible (for modals/drawers that are rendered open)
    const observer = new MutationObserver(() => {{
        if (container.offsetParent !== null && !focusTrapEnabled) {{
            activateFocusTrap();
        }} else if (container.offsetParent === null && focusTrapEnabled) {{
            deactivateFocusTrap();
        }}
    }});
    observer.observe(container, {{ attributes: true, attributeFilter: ['style', 'class', 'hidden'] }});

    // Initial check
    if (container.offsetParent !== null) {{
        activateFocusTrap();
    }}
}})();
</script>
'''


def render_focus_trap_html(container_id: str, enabled: bool = True,
                          initial_focus_selector: Optional[str] = None,
                          on_deactivate: Optional[str] = None) -> str:
    """
    Render focus trap initialization for a specific container ID.

    Args:
        container_id: ID of the container element
        enabled: Whether focus trap is initially enabled
        initial_focus_selector: CSS selector for initial focus target
        on_deactivate: JavaScript callback when focus trap deactivates (e.g., on Escape)

    Returns:
        HTML script tag
    """
    props = FocusTrapProps(
        container_selector=f"#{container_id}",
        enabled=enabled,
        initial_focus_selector=initial_focus_selector,
        on_deactivate=on_deactivate
    )
    return render_focus_trap_script(props)


# =============================================================================
# SKIP LINK UTILITIES
# =============================================================================

def render_skip_link(main_content_id: str = "main-content") -> str:
    """
    Render a skip-to-main-content link.

    Args:
        main_content_id: ID of the main content element

    Returns:
        HTML for skip link
    """
    return f'''
<a href="#{main_content_id}" class="i20-skip-link" tabindex="0">
    Skip to main content
</a>
'''


# =============================================================================
# ARIA UTILITIES
# =============================================================================

def aria_describedby_ids(*ids: str) -> str:
    """Generate aria-describedby attribute value from multiple IDs."""
    valid_ids = [id_ for id_ in ids if id_]
    return ' '.join(valid_ids) if valid_ids else ''


def aria_labelledby_ids(*ids: str) -> str:
    """Generate aria-labelledby attribute value from multiple IDs."""
    valid_ids = [id_ for id_ in ids if id_]
    return ' '.join(valid_ids) if valid_ids else ''


def generate_id(prefix: str, suffix: Optional[str] = None) -> str:
    """Generate a unique ID with prefix."""
    import uuid
    unique = str(uuid.uuid4())[:8]
    if suffix:
        return f"{prefix}-{suffix}-{unique}"
    return f"{prefix}-{unique}"


# =============================================================================
# STATUS INDICATOR UTILITIES
# =============================================================================

@dataclass
class StatusIndicatorProps:
    """Properties for an accessible status indicator."""
    status: Literal["success", "warning", "critical", "info", "neutral"]
    label: str
    icon: Optional[str] = None
    size: Literal["sm", "md", "lg"] = "md"
    show_text: bool = True


STATUS_ICONS = {
    "success": "✓",
    "warning": "⚠",
    "critical": "✕",
    "info": "ℹ",
    "neutral": "●",
}

STATUS_LABELS = {
    "success": "Connected",
    "warning": "Warning",
    "critical": "Critical",
    "info": "Information",
    "neutral": "Unknown",
}

STATUS_COLORS = {
    "success": SEMANTIC_COLORS["success"],
    "warning": SEMANTIC_COLORS["warning"],
    "critical": SEMANTIC_COLORS["critical"],
    "info": SEMANTIC_COLORS["info"],
    "neutral": SEMANTIC_COLORS["neutral"],
}

SIZE_STYLES = {
    "sm": {"dot_size": "8px", "font_size": "0.625rem", "gap": "4px"},
    "md": {"dot_size": "10px", "font_size": "0.75rem", "gap": "6px"},
    "lg": {"dot_size": "12px", "font_size": "0.875rem", "gap": "8px"},
}


def render_accessible_status_indicator(props: StatusIndicatorProps) -> str:
    """
    Render an accessible status indicator with color + icon + text.
    Addresses WCAG 1.4.1 Use of Color (color-only information).

    Args:
        props: StatusIndicatorProps with status, label, icon, size, show_text

    Returns:
        HTML string for the status indicator
    """
    icon = props.icon or STATUS_ICONS.get(props.status, "●")
    label = props.label or STATUS_LABELS.get(props.status, props.status.capitalize())
    color = STATUS_COLORS.get(props.status, SEMANTIC_COLORS["neutral"])
    size_style = SIZE_STYLES[props.size]

    # ARIA: status role for live region behavior, or img with alt for decorative
    # Using role="status" with aria-live="polite" for dynamic status changes
    # For static indicators, use role="img" with aria-label

    text_content = f"{icon} {label}" if props.show_text else ""
    aria_label = f"{label} status"

    return f'''
<span class="i20-status-indicator i20-status-{props.status}"
      role="img"
      aria-label="{aria_label}"
      style="display:inline-flex;align-items:center;gap:{size_style['gap']};font-size:{size_style['font_size']};">
    <span class="i20-status-dot"
          style="width:{size_style['dot_size']};height:{size_style['dot_size']};
                 border-radius:50%;background-color:{color};
                 flex-shrink:0;"
          aria-hidden="true"></span>
    <span class="i20-status-text" aria-hidden="false">{text_content}</span>
</span>
'''


def render_compact_status_indicator(status: str, size: Literal["sm", "md"] = "sm") -> str:
    """
    Render a compact status indicator (dot + tooltip text).
    For use in tight spaces like table cells or top bar.
    """
    icon = STATUS_ICONS.get(status, "●")
    label = STATUS_LABELS.get(status, status.capitalize())
    color = STATUS_COLORS.get(status, SEMANTIC_COLORS["neutral"])
    size_style = SIZE_STYLES[size]

    return f'''
<span class="i20-status-indicator i20-status-{status} i20-status-compact"
      role="img"
      aria-label="{label}"
      style="display:inline-flex;align-items:center;gap:{size_style['gap']};">
    <span class="i20-status-dot"
          style="width:{size_style['dot_size']};height:{size_style['dot_size']};
                 border-radius:50%;background-color:{color};flex-shrink:0;"
          aria-hidden="true"></span>
    <span class="i20-status-text" style="display:none;" aria-hidden="true">{icon} {label}</span>
</span>
'''


# =============================================================================
# ACCESSIBLE TABLE UTILITIES
# =============================================================================

@dataclass
class TableCaptionProps:
    """Properties for table caption."""
    text: str
    id: Optional[str] = None


def render_table_caption(props: TableCaptionProps) -> str:
    """Render an accessible table caption."""
    id_attr = f'id="{props.id}"' if props.id else ''
    return f'<caption {id_attr} class="i20-table-caption">{props.text}</caption>'


@dataclass
class TableHeaderProps:
    """Properties for table header cell."""
    text: str
    scope: Literal["col", "row", "colgroup", "rowgroup"] = "col"
    id: Optional[str] = None
    abbr: Optional[str] = None
    sort_key: Optional[str] = None


def render_table_header(props: TableHeaderProps) -> str:
    """Render an accessible table header cell with scope."""
    id_attr = f'id="{props.id}"' if props.id else ''
    abbr_attr = f'abbr="{props.abbr}"' if props.abbr else ''
    sort_attr = f'data-sort-key="{props.sort_key}"' if props.sort_key else ''
    return f'<th scope="{props.scope}" {id_attr} {abbr_attr} {sort_attr} class="i20-th">{props.text}</th>'


def render_accessible_table_wrapper(table_html: str, wrapper_id: Optional[str] = None) -> str:
    """
    Wrap a table in an accessible scroll region.
    Addresses WCAG 2.1.1 Keyboard - scrollable tables need tabindex="0".
    """
    id_attr = f'id="{wrapper_id}"' if wrapper_id else ''
    return f'''
<div class="i20-table-wrapper" {id_attr} role="region" tabindex="0"
     aria-label="Data table with horizontal scrolling"
     style="overflow-x:auto;max-width:100%;">
    {table_html}
</div>
'''


# =============================================================================
# ACCESSIBLE BUTTON UTILITIES
# =============================================================================

@dataclass
class AccessibleButtonProps:
    """Properties for an accessible button."""
    id: str
    label: str
    variant: Literal["primary", "secondary", "ghost", "danger"] = "primary"
    disabled: bool = False
    loading: bool = False
    icon: Optional[str] = None
    icon_position: Literal["start", "end"] = "start"
    aria_pressed: Optional[bool] = None
    aria_expanded: Optional[bool] = None
    aria_controls: Optional[str] = None
    aria_describedby: Optional[str] = None
    type: Literal["button", "submit", "reset"] = "button"
    onclick: Optional[str] = None
    full_width: bool = False


def render_accessible_button(props: AccessibleButtonProps) -> str:
    """
    Render an accessible button with proper type, ARIA, and keyboard support.
    Addresses WCAG 2.1.1 Keyboard, 4.1.2 Name/Role/Value.
    """
    from components.ui.tokens import SEMANTIC_COLORS

    variant_colors = {
        "primary": {"bg": SEMANTIC_COLORS["primary"], "text": SEMANTIC_COLORS["text.inverse"], "border": "none"},
        "secondary": {"bg": SEMANTIC_COLORS["surface.elevated"], "text": SEMANTIC_COLORS["text.primary"], "border": f"1px solid {SEMANTIC_COLORS['border.default']}"},
        "ghost": {"bg": "transparent", "text": SEMANTIC_COLORS["text.primary"], "border": "none"},
        "danger": {"bg": SEMANTIC_COLORS["critical"], "text": SEMANTIC_COLORS["text.inverse"], "border": "none"},
    }

    colors = variant_colors[props.variant]

    # Build ARIA attributes
    aria_attrs = []
    if props.aria_pressed is not None:
        aria_attrs.append(f'aria-pressed="{str(props.aria_pressed).lower()}"')
    if props.aria_expanded is not None:
        aria_attrs.append(f'aria-expanded="{str(props.aria_expanded).lower()}"')
    if props.aria_controls:
        aria_attrs.append(f'aria-controls="{props.aria_controls}"')
    if props.aria_describedby:
        aria_attrs.append(f'aria-describedby="{props.aria_describedby}"')
    if props.disabled:
        aria_attrs.append('aria-disabled="true"')
    if props.loading:
        aria_attrs.append('aria-busy="true"')

    aria_str = ' '.join(aria_attrs)

    # Button content
    icon_html = f'<span class="i20-btn-icon" aria-hidden="true">{props.icon}</span>' if props.icon else ''
    if props.loading:
        icon_html = '<span class="i20-btn-spinner" aria-hidden="true" style="display:inline-block;width:1em;height:1em;border:2px solid currentColor;border-radius:50%;border-right-color:transparent;animation:spin 0.6s linear infinite;"></span>'

    content = ''
    if props.icon_position == "start":
        content = f'{icon_html}<span class="i20-btn-text">{props.label}</span>'
    else:
        content = f'<span class="i20-btn-text">{props.label}</span>{icon_html}'

    style = f'''
        display:inline-flex;
        align-items:center;
        justify-content:center;
        gap:8px;
        padding:8px 16px;
        min-height:44px;
        min-width:44px;
        border-radius:4px;
        font-size:0.75rem;
        font-weight:500;
        line-height:1.4;
        background-color:{colors['bg']};
        color:{colors['text']};
        border:{colors['border']};
        cursor:{'not-allowed' if props.disabled else 'pointer'};
        opacity:{'0.6' if props.disabled else '1'};
        transition:background-color 0.15s ease, border-color 0.15s ease, opacity 0.15s ease;
        {'width:100%;' if props.full_width else ''}
    '''

    disabled_attr = 'disabled' if props.disabled else ''
    onclick_attr = f'onclick="{props.onclick}"' if props.onclick and not props.disabled else ''

    keydown_handler = "if(event.key==='Enter'||event.key===' '){event.preventDefault();this.click();}"
    return f'''
<button id="{props.id}"
        type="{props.type}"
        class="i20-btn i20-btn-{props.variant}"
        {aria_str}
        {disabled_attr}
        {onclick_attr}
        style="{style}"
        onkeydown="{keydown_handler}">
    {content}
</button>
'''


# =============================================================================
# ACCESSIBLE FORM UTILITIES
# =============================================================================

# =============================================================================
# FORM FIELD ERROR LINKING (B1.5) & REQUIRED FIELDS (B1.6)
# =============================================================================

@dataclass
class FormFieldErrorProps:
    """Properties for form field error message linking (B1.5).

    Implements aria-describedby/aria-invalid pattern for accessible error handling.
    Addresses WCAG 3.3.1 Error Identification, 3.3.3 Error Suggestion.
    """
    input_id: str
    error_id: str
    error_message: str
    is_invalid: bool = True

    def get_aria_describedby(self) -> str:
        """Get the aria-describedby value for the input."""
        return self.error_id if self.is_invalid else ""

    def get_aria_invalid(self) -> str:
        """Get the aria-invalid value for the input."""
        return "true" if self.is_invalid else "false"

    def render_error_element(self) -> str:
        """Render the error message element with proper ID and role."""
        if not self.is_invalid or not self.error_message:
            return ""
        return f'<div id="{self.error_id}" class="i20-field-error" role="alert" aria-live="polite">{self.error_message}</div>'


@dataclass
class RequiredFieldProps:
    """Properties for required field indication (B1.6).

    Implements aria-required for accessible required field indication.
    Addresses WCAG 3.3.2 Labels or Instructions.
    """
    input_id: str
    is_required: bool = True
    required_marker: str = " *"  # Visual marker for required fields

    def get_aria_required(self) -> str:
        """Get the aria-required value for the input."""
        return "true" if self.is_required else "false"

    def render_required_indicator(self) -> str:
        """Render the required field indicator in label."""
        if not self.is_required:
            return ""
        return f'<span class="i20-required-marker" aria-hidden="true">{self.required_marker}</span>'


@dataclass
class AccessibleFieldProps:
    """Properties for an accessible form field."""
    id: str
    label: str
    type: Literal["text", "email", "password", "number", "tel", "url", "search"] = "text"
    required: bool = False
    disabled: bool = False
    readonly: bool = False
    placeholder: Optional[str] = None
    value: str = ""
    aria_describedby: Optional[str] = None
    aria_invalid: bool = False
    autocomplete: Optional[str] = None
    inputmode: Optional[str] = None
    min: Optional[str] = None
    max: Optional[str] = None
    step: Optional[str] = None
    pattern: Optional[str] = None
    help_text: Optional[str] = None
    error_text: Optional[str] = None


def render_accessible_text_input(props: AccessibleFieldProps) -> str:
    """
    Render an accessible text input with proper labeling, aria-invalid, aria-describedby.
    Addresses WCAG 1.3.1 Info and Relationships, 3.3.1 Error Identification, 3.3.2 Labels or Instructions.
    """
    # Generate IDs for help/error text
    help_id = f"{props.id}-help" if props.help_text else None
    error_id = f"{props.id}-error" if props.error_text else None

    describedby_ids = []
    if props.aria_describedby:
        describedby_ids.append(props.aria_describedby)
    if help_id:
        describedby_ids.append(help_id)
    if error_id:
        describedby_ids.append(error_id)

    describedby = ' '.join(describedby_ids) if describedby_ids else None

    required_attr = 'required' if props.required else ''
    disabled_attr = 'disabled' if props.disabled else ''
    readonly_attr = 'readonly' if props.readonly else ''
    placeholder_attr = f'placeholder="{props.placeholder}"' if props.placeholder else ''
    autocomplete_attr = f'autocomplete="{props.autocomplete}"' if props.autocomplete else ''
    inputmode_attr = f'inputmode="{props.inputmode}"' if props.inputmode else ''
    min_attr = f'min="{props.min}"' if props.min else ''
    max_attr = f'max="{props.max}"' if props.max else ''
    step_attr = f'step="{props.step}"' if props.step else ''
    pattern_attr = f'pattern="{props.pattern}"' if props.pattern else ''
    aria_invalid_attr = 'aria-invalid="true"' if props.aria_invalid else ''
    aria_describedby_attr = f'aria-describedby="{describedby}"' if describedby else ''
    aria_required_attr = 'aria-required="true"' if props.required else ''

    # Label
    label_html = f'<label for="{props.id}" class="i20-label">{props.label}{" *" if props.required else ""}</label>'

    # Help text
    help_html = f'<span id="{help_id}" class="i20-help-text">{props.help_text}</span>' if props.help_text else ''

    # Error text
    error_html = f'<span id="{error_id}" class="i20-error-text" role="alert">{props.error_text}</span>' if props.error_text else ''

    return f'''
<div class="i20-field" style="display:flex;flex-direction:column;gap:4px;">
    {label_html}
    <input type="{props.type}"
           id="{props.id}"
           name="{props.id}"
           value="{props.value}"
           class="i20-input"
           {required_attr}
           {disabled_attr}
           {readonly_attr}
           {placeholder_attr}
           {autocomplete_attr}
           {inputmode_attr}
           {min_attr}
           {max_attr}
           {step_attr}
           {pattern_attr}
           {aria_invalid_attr}
           {aria_describedby_attr}
           {aria_required_attr}
           style="padding:8px 12px;min-height:44px;border-radius:4px;
                  border:1px solid var(--color-border-default);
                  background-color:var(--color-surface-secondary);
                  color:var(--color-text-primary);
                  font-size:0.875rem;
                  transition:border-color 0.15s ease, box-shadow 0.15s ease;"
           onfocus="this.style.borderColor='var(--color-border-focus)';this.style.boxShadow='0 0 0 3px var(--color-accent-primary)33';"
           onblur="this.style.borderColor='var(--color-border-default)';this.style.boxShadow='none';">
    {help_html}
    {error_html}
</div>
'''


# =============================================================================
# CHART ACCESSIBILITY UTILITIES
# =============================================================================

@dataclass
class ChartAccessibilityProps:
    """Properties for chart accessibility."""
    chart_id: str
    title: str
    summary: str
    data_table: Optional[str] = None  # HTML table string
    chart_type: Literal["line", "bar", "pie", "scatter", "gauge", "heatmap"] = "line"
    series_names: Optional[list] = None


def render_accessible_chart_container(props: ChartAccessibilityProps) -> str:
    """
    Render an accessible chart container with:
    - aria-hidden on the visual chart (SVG/canvas)
    - Associated accessible data table
    - Proper labeling
    - Keyboard navigation support (B1.17)
    Addresses WCAG 1.1.1 Non-text Content, 1.3.1 Info and Relationships, 2.1.1 Keyboard.
    """
    table_id = f"{props.chart_id}-data-table"
    table_html = props.data_table or ""

    # If no data table provided, create a placeholder notice
    if not table_html:
        table_html = f'''
<table id="{table_id}" class="i20-chart-data-table" style="display:none;">
    <caption>{props.title} - Data Table</caption>
    <thead><tr><th scope="col">No data available</th></tr></thead>
    <tbody><tr><td>Chart data table not generated</td></tr></tbody>
</table>
'''

    # Keyboard navigation script for chart data table
    keyboard_nav_script = f'''
    <script>
    (function() {{
        const table = document.getElementById('{table_id}');
        if (!table) return;

        // Make table focusable for keyboard navigation
        table.setAttribute('tabindex', '0');
        table.setAttribute('role', 'grid');
        table.setAttribute('aria-label', '{props.title} data grid');

        let currentCell = null;
        const cells = () => Array.from(table.querySelectorAll('td:not([style*="display:none"])'));
        const rows = () => Array.from(table.querySelectorAll('tbody tr'));

        function focusCell(cell) {{
            if (!cell) return;
            if (currentCell) {{
                currentCell.classList.remove('i20-chart-cell-focused');
            }}
            currentCell = cell;
            cell.classList.add('i20-chart-cell-focused');
            cell.focus({{ preventScroll: true }});

            // Announce cell coordinates for screen readers
            const row = cell.closest('tr');
            const rowIndex = rows().indexOf(row) + 1;
            const colIndex = Array.from(row.querySelectorAll('td')).indexOf(cell) + 1;
            const header = table.querySelector('thead th:nth-child(' + (colIndex + 1) + ')');
            const headerText = header ? header.textContent.trim() : 'Column ' + colIndex;
            const rowHeader = row.querySelector('th[scope="row"]');
            const rowHeaderText = rowHeader ? rowHeader.textContent.trim() : 'Row ' + rowIndex;

            const liveRegion = document.getElementById('{props.chart_id}-nav-announcer');
            if (liveRegion) {{
                liveRegion.textContent = 'Row ' + rowIndex + ', ' + headerText + ': ' + cell.textContent.trim();
            }}
        }}

        table.addEventListener('keydown', function(e) {{
            if (!currentCell) {{
                // First focus - go to first data cell
                const firstCell = cells()[0];
                if (firstCell) focusCell(firstCell);
                return;
            }}

            const allCells = cells();
            const currentIndex = allCells.indexOf(currentCell);
            const cols = table.querySelectorAll('thead th').length - 1; // minus row header
            let nextIndex = currentIndex;

            switch(e.key) {{
                case 'ArrowRight':
                    e.preventDefault();
                    nextIndex = Math.min(currentIndex + 1, allCells.length - 1);
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    nextIndex = Math.max(currentIndex - 1, 0);
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    nextIndex = Math.min(currentIndex + cols, allCells.length - 1);
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    nextIndex = Math.max(currentIndex - cols, 0);
                    break;
                case 'Home':
                    e.preventDefault();
                    nextIndex = 0;
                    break;
                case 'End':
                    e.preventDefault();
                    nextIndex = allCells.length - 1;
                    break;
                case 'PageDown':
                    e.preventDefault();
                    nextIndex = Math.min(currentIndex + cols * 5, allCells.length - 1);
                    break;
                case 'PageUp':
                    e.preventDefault();
                    nextIndex = Math.max(currentIndex - cols * 5, 0);
                    break;
                case 'Tab':
                    // Allow normal tab navigation out of table
                    currentCell.classList.remove('i20-chart-cell-focused');
                    currentCell = null;
                    return;
                default:
                    return;
            }}

            if (nextIndex !== currentIndex && allCells[nextIndex]) {{
                focusCell(allCells[nextIndex]);
            }}
        }});

        // Focus visible styling
        const style = document.createElement('style');
        style.textContent = `
            .i20-chart-cell-focused {{
                outline: 2px solid var(--i20-color-border-focus, #0066cc) !important;
                outline-offset: -2px !important;
                background-color: var(--i20-color-accent-primary, #0066cc)15 !important;
                z-index: 10;
            }}
            .i20-chart-container:focus-within {{
                outline: 2px solid var(--i20-color-border-focus, #0066cc) !important;
                outline-offset: 2px !important;
                border-radius: 4px;
            }}
        `;
        document.head.appendChild(style);

        // Click on cell to focus
        table.addEventListener('click', function(e) {{
            const cell = e.target.closest('td');
            if (cell && table.contains(cell)) {{
                focusCell(cell);
            }}
        }});
    }})();
    </script>
    '''

    # Live region for cell navigation announcements
    nav_live_region = f'''
    <div id="{props.chart_id}-nav-announcer" class="i20-visually-hidden" aria-live="polite" aria-atomic="true" aria-label="Chart navigation"></div>
    '''

    return f'''
<div class="i20-chart-container" id="{props.chart_id}-container"
     role="region"
     aria-label="{props.title}"
     tabindex="0"
     style="position:relative;">
    {nav_live_region}
    <div id="{props.chart_id}"
         class="i20-chart-visual"
         aria-hidden="true"
         role="img"
         aria-label="{props.summary}">
        <!-- Plotly chart renders here -->
    </div>
    {render_accessible_table_wrapper(table_html, table_id)}
    {keyboard_nav_script}
</div>
'''


# =============================================================================
# WIZARD ACCESSIBILITY UTILITIES
# =============================================================================

@dataclass
class WizardAccessibilityProps:
    """Properties for wizard accessibility."""
    wizard_id: str
    current_step: int
    total_steps: int
    step_labels: list
    step_ids: list


def render_wizard_aria_tabs(props: WizardAccessibilityProps) -> str:
    """
    Render ARIA tabs pattern for wizard step navigation.
    Addresses WCAG 1.3.1, 2.4.3, 4.1.2.
    """
    tabs_html = []
    panels_html = []

    for i, (label, step_id) in enumerate(zip(props.step_labels, props.step_ids)):
        is_active = i == props.current_step
        step_num = i + 1

        # Tab button
        tabs_html.append(f'''
<button role="tab"
        id="{props.wizard_id}-tab-{step_id}"
        aria-selected="{str(is_active).lower()}"
        aria-controls="{props.wizard_id}-panel-{step_id}"
        tabindex="{0 if is_active else -1}"
        class="i20-wizard-tab {'' if is_active else 'i20-wizard-tab-inactive'}"
        style="padding:8px 16px;border:none;background:transparent;color:var(--color-text-{'primary' if is_active else 'muted'});font-weight:{'600' if is_active else '400'};cursor:pointer;border-bottom:2px solid {'var(--color-border-focus)' if is_active else 'transparent'};"
        onclick="window.i20Wizard?.activateStep?.('{step_id}')">
    <span class="i20-wizard-step-number" aria-hidden="true">{step_num}</span>
    <span class="i20-wizard-step-label">{label}</span>
</button>
''')

        # Tab panel
        panels_html.append(f'''
<div role="tabpanel"
     id="{props.wizard_id}-panel-{step_id}"
     aria-labelledby="{props.wizard_id}-tab-{step_id}"
     hidden="{str(not is_active).lower()}"
     class="i20-wizard-panel"
     style="{'' if is_active else 'display:none;'}">
    <!-- Step {step_num} content rendered here -->
</div>
''')

    return f'''
<div class="i20-wizard-tabs" role="tablist" aria-label="Wizard steps">
    {''.join(tabs_html)}
</div>
<div class="i20-wizard-panels">
    {''.join(panels_html)}
</div>
'''


# =============================================================================
# REDUCED MOTION UTILITIES
# =============================================================================

REDUCED_MOTION_MEDIA_QUERY = "@media (prefers-reduced-motion: reduce)"

def get_reduced_motion_css() -> str:
    """Get CSS for reduced motion preferences."""
    return f'''
{REDUCED_MOTION_MEDIA_QUERY} {{
    *,
    *::before,
    *::after {{
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }}

    /* Plotly specific */
    .js-plotly-plot .main-svg * {{
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
    }}

    /* Skeleton loading */
    .i20-skeleton {{
        animation: none !important;
        background: var(--color-surface-interactive) !important;
    }}

    /* Spinners */
    .i20-spinner,
    .i20-btn-spinner {{
        animation: none !important;
        border-right-color: currentColor !important;
    }}

    /* Toast/notification animations */
    .i20-toast {{
        animation: none !important;
        opacity: 1 !important;
        transform: none !important;
    }}
}}
'''


def render_reduced_motion_detection_script() -> str:
    """Render script to detect and apply reduced motion preference."""
    return '''
<script>
(function() {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');

    function applyReducedMotion(reduced) {
        document.documentElement.classList.toggle('i20-reduced-motion', reduced);

        // Notify Plotly charts to disable transitions
        if (window.Plotly) {
            document.querySelectorAll('.js-plotly-plot').forEach(plot => {
                if (plot._fullLayout) {
                    Plotly.relayout(plot, { transition: { duration: reduced ? 0 : 300 } });
                }
            });
        }
    }

    // Initial check
    applyReducedMotion(mediaQuery.matches);

    // Listen for changes
    mediaQuery.addEventListener('change', (e) => applyReducedMotion(e.matches));

    // Expose for manual control
    window.i20ReducedMotion = {
        isReduced: () => mediaQuery.matches,
        apply: applyReducedMotion
    };
}})();
</script>
'''


def render_landmark_fix_script() -> str:
    """Render script to fix semantic landmarks after Streamlit renders.

    Avoids innerHTML and complex DOM creation which get stripped by DOMPurify.
    Uses setAttribute, textContent, and MutationObserver which are allowed.
    """
    return '''
<script>
(function() {
    function fixLandmarks() {
        // Fix sidebar navigation - ensure it has proper landmarks
        const sidebarNav = document.querySelector('nav.i20-sidebar-nav, .i20-sidebar nav, [data-testid="stSidebar"] nav');
        if (sidebarNav) {
            if (sidebarNav.tagName !== 'NAV') {
                sidebarNav.setAttribute('role', 'navigation');
            }
            sidebarNav.setAttribute('aria-label', 'Main navigation');
            if (!sidebarNav.classList.contains('i20-sidebar-nav')) {
                sidebarNav.classList.add('i20-sidebar-nav');
            }
        }

        // Fix main content area - ensure it has id="main-content"
        const mainContent = document.getElementById('stMain') || document.querySelector('main[data-testid="stMain"]');
        if (mainContent) {
            mainContent.setAttribute('id', 'main-content');
            if (mainContent.tagName !== 'MAIN') {
                mainContent.setAttribute('role', 'main');
            }
        }

        // Fix top bar - ensure it has proper header role
        const topBar = document.querySelector('header.i20-top-bar, header.stAppHeader');
        if (topBar && topBar.tagName !== 'HEADER') {
            topBar.setAttribute('role', 'banner');
        }

        // Fix footer - ensure it has contentinfo role
        const footer = document.querySelector('.i20-footer[role="contentinfo"], footer.i20-footer, footer[role="contentinfo"]');
        if (footer) {
            footer.setAttribute('role', 'contentinfo');
            if (!footer.classList.contains('i20-footer')) {
                footer.classList.add('i20-footer');
            }
        }

        // Fix skip link target - our custom skip link
        const skipLink = document.querySelector('a[href="#main-content"], a.skip-link');
        if (skipLink) {
            skipLink.setAttribute('href', '#main-content');
        }

        // Fix Streamlit's default skip link (data-testid="stSkipToContent")
        const stSkipLink = document.querySelector('a[data-testid="stSkipToContent"]');
        if (stSkipLink) {
            stSkipLink.setAttribute('href', '#main-content');
        }
    }

    // Run on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', fixLandmarks);
    } else {
        fixLandmarks();
    }

    // Also run after Streamlit hydration
    const observer = new MutationObserver(() => {
        fixLandmarks();
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Expose for manual control
    window.i20FixLandmarks = fixLandmarks;
})();
</script>
'''


def render_scrollable_region_focus_fix_script() -> str:
    """
    Render script to make scrollable regions keyboard-focusable.

    Addresses axe-core 'scrollable-region-focusable' rule (WCAG 2.1.1 Keyboard).
    Streamlit generates <pre> elements (.st-emotion-cache-kg09s) for code blocks
    that become horizontally scrollable on mobile but aren't keyboard-focusable.

    This script:
    - Proactively adds tabindex="0" to elements with overflow styles (pre, code blocks)
    - Preserves existing tabindex values
    - Handles Streamlit rerenders via MutationObserver
    - Adds visible focus indicators
    - Avoids making non-scrollable containers focusable
    """
    return '''
<script>
(function() {
    'use strict';

    console.error('[i20] Scrollable region focus fix script loaded');

    // Selectors for elements that commonly have scrollable content in Streamlit
    // These elements have overflow: auto/scroll styles and can become scrollable
    const SCROLLABLE_SELECTORS = [
        '.st-emotion-cache-kg09s',           // Streamlit code/pre blocks (primary target)
        '.stMarkdown pre',                   // Markdown code blocks
        '.stCodeBlock pre',                  // Code block component
        'pre[style*="overflow"]',            // Inline overflow styles
        'pre[style*="scroll"]',              // Inline scroll styles
        '[class*="st-emotion-cache"][style*="overflow-x: auto"]',
        '[class*="st-emotion-cache"][style*="overflow: auto"]',
        '.i20-table-wrapper',                // Our accessible table wrapper
        '.i20-chart-data-table-wrapper',     // Chart data table wrappers
    ];

    // Check if element has overflow styles that make it potentially scrollable
    function hasOverflowStyles(element) {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;

        const style = window.getComputedStyle(element);
        const overflowX = style.overflowX;
        const overflowY = style.overflowY;

        // Check if overflow is set to scroll or auto
        return overflowX === 'scroll' || overflowX === 'auto' ||
               overflowY === 'scroll' || overflowY === 'auto';
    }

    // Make element focusable if it has overflow styles
    function makeFocusableIfOverflow(element) {
        if (!element || element.hasAttribute('data-i20-scrollable-focus-fixed')) return;

        if (hasOverflowStyles(element)) {
            console.error('[i20] Making scrollable element focusable:', element);
            // Preserve existing tabindex if present
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
            // Mark as processed
            element.setAttribute('data-i20-scrollable-focus-fixed', 'true');

            // Add focus-visible class support for consistent styling
            element.classList.add('i20-scrollable-focusable');

            // Also ensure focus styles work (CSS handles this, but ensure no outline conflicts)
            element.style.setProperty('--i20-scrollable-focusable', 'true', 'important');
        }
    }

    // Process all matching elements
    function processScrollableElements() {
        console.error('[i20] Processing scrollable elements...');
        SCROLLABLE_SELECTORS.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                console.error('[i20] Selector:', selector, 'found:', elements.length, 'elements');
                elements.forEach(makeFocusableIfOverflow);
            } catch (e) {
                console.error('[i20] Invalid selector:', selector, e);
            }
        });
    }

    // Initial processing - run immediately and on DOMContentLoaded
    function runInitial() {
        console.error('[i20] Running initial scrollable element processing');
        processScrollableElements();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runInitial);
    } else {
        runInitial();
    }

    // Also run after a short delay to catch elements rendered after initial load
    setTimeout(runInitial, 100);
    setTimeout(runInitial, 500);
    setTimeout(runInitial, 1000);

    // Handle Streamlit rerenders via MutationObserver
    const observer = new MutationObserver((mutations) => {
        let shouldProcess = false;

        for (const mutation of mutations) {
            // Check if new nodes were added that might be scrollable
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        // Check if the added node matches our selectors or contains matches
                        let matches = false;
                        SCROLLABLE_SELECTORS.forEach(selector => {
                            try {
                                if (node.matches && node.matches(selector)) {
                                    matches = true;
                                } else if (node.querySelectorAll) {
                                    if (node.querySelectorAll(selector).length > 0) {
                                        matches = true;
                                    }
                                }
                            } catch (e) {
                                // Ignore invalid selectors
                            }
                        });
                        if (matches) {
                            shouldProcess = true;
                            break;
                        }
                    }
                }
            }
            // Also check for attribute changes on existing elements (e.g., style changes)
            if (mutation.type === 'attributes' &&
                (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
                const target = mutation.target;
                if (target && target.nodeType === Node.ELEMENT_NODE) {
                    SCROLLABLE_SELECTORS.forEach(selector => {
                        try {
                            if (target.matches && target.matches(selector)) {
                                shouldProcess = true;
                            }
                        } catch (e) {}
                    });
                }
            }
        }

        if (shouldProcess) {
            // Defer to next tick to let layout settle
            requestAnimationFrame(processScrollableElements);
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });

    // Also re-check on window resize (viewport changes can affect scrollability)
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(processScrollableElements, 100);
    });

    // Expose for manual control
    window.i20ScrollableFocusFix = {
        process: processScrollableElements,
        hasOverflowStyles: hasOverflowStyles
    };

    console.error('[i20] Scrollable region focus fix initialized (iframe)');
})();
</script>
'''


# =============================================================================
# TOUCH TARGET UTILITIES
# =============================================================================

TOUCH_TARGET_CSS = '''
/* Minimum touch target enforcement for Streamlit native components */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button,
button[kind="primary"],
button[kind="secondary"],
button[kind="tertiary"] {
    min-height: 44px !important;
    min-width: 44px !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
}

.stSelectbox > div > div,
.stSelectbox [data-baseweb="select"] > div {
    min-height: 44px !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input {
    min-height: 44px !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
}

.stCheckbox > label,
.stRadio > label {
    min-height: 44px !important;
    display: flex !important;
    align-items: center !important;
}

.stCheckbox > label > div:first-child,
.stRadio > label > div:first-child {
    min-width: 20px !important;
    min-height: 20px !important;
}

.stTabs [data-baseweb="tab"],
.stTabs [role="tab"] {
    min-height: 44px !important;
    min-width: 44px !important;
    padding-top: 8px !important;
    padding-bottom: 8px !important;
}

.stSlider > div > div > div[role="slider"] {
    min-width: 24px !important;
    min-height: 24px !important;
}

/* Mobile-specific enhancements */
@media (max-width: 768px) {
    .stButton > button,
    .stDownloadButton > button,
    .stFormSubmitButton > button {
        min-height: 48px !important;
        min-width: 48px !important;
        font-size: 1rem !important; /* Prevent zoom on iOS */
    }

    .stSelectbox > div > div,
    .stSelectbox [data-baseweb="select"] > div {
        min-height: 48px !important;
        font-size: 1rem !important;
    }

    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stNumberInput > div > div > input {
        min-height: 48px !important;
        font-size: 1rem !important; /* Prevent zoom on iOS */
    }

    .stTabs [data-baseweb="tab"],
    .stTabs [role="tab"] {
        min-height: 48px !important;
        min-width: 48px !important;
    }
}

/* Custom component touch targets (design system buttons) */
.i20-btn {
    min-height: 44px !important;
    min-width: 44px !important;
}

@media (max-width: 768px) {
    .i20-btn {
        min-height: 48px !important;
        min-width: 48px !important;
    }
}

/* Status indicators */
.i20-status-dot {
    min-width: 8px !important;
    min-height: 8px !important;
}

/* Badge touch targets */
.i20-badge {
    min-height: 24px !important;
    min-width: 24px !important;
    padding: 4px 10px !important;
}

/* Card interactive areas */
.i20-card-interactive {
    min-height: 44px !important;
}
'''


def get_touch_target_css() -> str:
    """Get CSS for touch target enforcement."""
    return TOUCH_TARGET_CSS


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    # Live regions
    "LiveRegionProps",
    "render_live_region",
    "render_persistent_live_regions",
    "announce_to_live_region",
    # Focus trap
    "FocusTrapProps",
    "render_focus_trap_script",
    "render_focus_trap_html",
    # Skip link
    "render_skip_link",
    # ARIA utilities
    "aria_describedby_ids",
    "aria_labelledby_ids",
    "generate_id",
    # Status indicators
    "StatusIndicatorProps",
    "render_accessible_status_indicator",
    "render_compact_status_indicator",
    # Table utilities
    "TableCaptionProps",
    "render_table_caption",
    "TableHeaderProps",
    "render_table_header",
    "render_accessible_table_wrapper",
    # Button utilities
    "AccessibleButtonProps",
    "render_accessible_button",
    # Form utilities
    "AccessibleFieldProps",
    "render_accessible_text_input",
    # Chart utilities
    "ChartAccessibilityProps",
    "render_accessible_chart_container",
    # Wizard utilities
    "WizardAccessibilityProps",
    "render_wizard_aria_tabs",
    # Reduced motion
    "get_reduced_motion_css",
    "render_reduced_motion_detection_script",
    # Touch targets
    "get_touch_target_css",
    # Scrollable region focus fix
    "render_scrollable_region_focus_fix_script",
]