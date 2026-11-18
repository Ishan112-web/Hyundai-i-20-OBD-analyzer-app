"""
i20 AI Garage - Status Card Components

Reusable status card components including KPI cards, connection status cards,
and alert/notification cards. All components use THEME from config.py
for consistent styling.
"""

from typing import Optional, List, Dict, Any, Literal
import streamlit as st
from config import THEME


StatusColor = Literal["green", "amber", "red", "blue", "purple", "gray"]


def _get_theme_styles() -> Dict[str, str]:
    """Return CSS styles derived from THEME."""
    return {
        "bg_primary": THEME["bg_primary"],
        "bg_secondary": THEME["bg_secondary"],
        "bg_card": THEME["bg_card"],
        "border": THEME["border"],
        "text_primary": THEME["text_primary"],
        "text_secondary": THEME["text_secondary"],
        "accent_blue": THEME["accent_blue"],
        "accent_green": THEME["accent_green"],
        "accent_amber": THEME["accent_amber"],
        "accent_red": THEME["accent_red"],
        "accent_purple": THEME["accent_purple"],
    }


def _get_status_color(status: StatusColor) -> str:
    """Map status color name to THEME color."""
    color_map = {
        "green": THEME["accent_green"],
        "amber": THEME["accent_amber"],
        "red": THEME["accent_red"],
        "blue": THEME["accent_blue"],
        "purple": THEME["accent_purple"],
        "gray": THEME["text_secondary"],
    }
    return color_map.get(status, THEME["text_secondary"])


def _inject_status_card_css():
    """Inject custom CSS for status card styling."""
    styles = _get_theme_styles()
    css = f"""
    <style>
    /* Base card styling */
    .status-card {{
        background-color: {styles["bg_card"]};
        border: 1px solid {styles["border"]};
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.2s ease;
    }}

    .status-card:hover {{
        border-color: {styles["accent_blue"]};
        box-shadow: 0 4px 12px rgba(0, 180, 216, 0.1);
    }}

    /* KPI Card */
    .kpi-card {{
        position: relative;
        overflow: hidden;
    }}

    .kpi-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: var(--kpi-accent, {styles["accent_blue"]});
    }}

    .kpi-header {{
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 0.75rem;
    }}

    .kpi-title {{
        font-size: 0.8rem;
        font-weight: 600;
        color: {styles["text_secondary"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        line-height: 1.3;
    }}

    .kpi-icon {{
        font-size: 1.25rem;
        opacity: 0.8;
    }}

    .kpi-value-container {{
        display: flex;
        align-items: baseline;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
    }}

    .kpi-value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {styles["text_primary"]};
        line-height: 1.1;
    }}

    .kpi-unit {{
        font-size: 1rem;
        font-weight: 500;
        color: {styles["text_secondary"]};
        margin-bottom: 0.15rem;
    }}

    .kpi-trend {{
        display: flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.25rem 0.5rem;
        border-radius: 6px;
    }}

    .kpi-trend.positive {{
        background-color: rgba(46, 204, 113, 0.15);
        color: {styles["accent_green"]};
    }}

    .kpi-trend.negative {{
        background-color: rgba(231, 76, 60, 0.15);
        color: {styles["accent_red"]};
    }}

    .kpi-trend.neutral {{
        background-color: rgba(154, 163, 173, 0.15);
        color: {styles["text_secondary"]};
    }}

    .kpi-status {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }}

    /* Connection Status Card */
    .connection-card {{
        display: flex;
        align-items: center;
        gap: 1rem;
    }}

    .connection-icon {{
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        flex-shrink: 0;
    }}

    .connection-info {{
        flex: 1;
        min-width: 0;
    }}

    .connection-label {{
        font-size: 0.9rem;
        font-weight: 600;
        color: {styles["text_primary"]};
        margin-bottom: 0.25rem;
    }}

    .connection-status {{
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
    }}

    .connection-status.connected {{
        background-color: rgba(46, 204, 113, 0.15);
        color: {styles["accent_green"]};
    }}

    .connection-status.connecting {{
        background-color: rgba(243, 156, 18, 0.15);
        color: {styles["accent_amber"]};
    }}

    .connection-status.disconnected {{
        background-color: rgba(231, 76, 60, 0.15);
        color: {styles["accent_red"]};
    }}

    .connection-status.error {{
        background-color: rgba(231, 76, 60, 0.15);
        color: {styles["accent_red"]};
    }}

    .connection-detail {{
        font-size: 0.75rem;
        color: {styles["text_secondary"]};
        margin-top: 0.35rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }}

    .connection-action {{
        flex-shrink: 0;
    }}

    /* Alert/Notification Card */
    .alert-card {{
        border-left: 4px solid var(--alert-color, {styles["accent_blue"]});
    }}

    .alert-header {{
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }}

    .alert-title-row {{
        display: flex;
        align-items: center;
        gap: 0.5rem;
        flex: 1;
    }}

    .alert-icon {{
        font-size: 1.25rem;
        flex-shrink: 0;
    }}

    .alert-title {{
        font-size: 0.95rem;
        font-weight: 600;
        color: {styles["text_primary"]};
    }}

    .alert-severity {{
        font-size: 0.65rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding: 0.15rem 0.5rem;
        border-radius: 4px;
        flex-shrink: 0;
    }}

    .alert-severity.critical {{
        background-color: rgba(231, 76, 60, 0.2);
        color: {styles["accent_red"]};
    }}

    .alert-severity.major {{
        background-color: rgba(243, 156, 18, 0.2);
        color: {styles["accent_amber"]};
    }}

    .alert-severity.minor {{
        background-color: rgba(52, 152, 219, 0.2);
        color: {styles["accent_blue"]};
    }}

    .alert-severity.info {{
        background-color: rgba(155, 89, 182, 0.2);
        color: {styles["accent_purple"]};
    }}

    .alert-message {{
        font-size: 0.85rem;
        color: {styles["text_secondary"]};
        line-height: 1.5;
        margin-bottom: 0.75rem;
    }}

    .alert-meta {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
        font-size: 0.7rem;
        color: {styles["text_secondary"]};
    }}

    .alert-meta-item {{
        display: flex;
        align-items: center;
        gap: 0.35rem;
    }}

    .alert-meta-label {{
        font-weight: 600;
    }}

    .alert-actions {{
        display: flex;
        gap: 0.5rem;
        margin-top: 0.75rem;
        padding-top: 0.75rem;
        border-top: 1px solid {styles["border"]};
    }}

    .alert-action-btn {{
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.4rem 0.75rem;
        border-radius: 6px;
        border: none;
        cursor: pointer;
        transition: all 0.2s ease;
    }}

    .alert-action-btn.primary {{
        background-color: var(--alert-color, {styles["accent_blue"]});
        color: white;
    }}

    .alert-action-btn.primary:hover {{
        opacity: 0.9;
    }}

    .alert-action-btn.secondary {{
        background-color: {styles["bg_secondary"]};
        color: {styles["text_primary"]};
        border: 1px solid {styles["border"]};
    }}

    .alert-action-btn.secondary:hover {{
        background-color: {styles["bg_card"]};
        border-color: {styles["accent_blue"]};
    }}

    /* Grid layout helpers */
    .status-cards-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
        gap: 1rem;
        margin: 1rem 0;
    }}

    @media (max-width: 640px) {{
        .status-cards-grid {{
            grid-template-columns: 1fr;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def create_kpi_card(
    title: str,
    value: str,
    unit: str = "",
    icon: str = "",
    status: StatusColor = "blue",
    trend: Optional[str] = None,
    trend_direction: Literal["positive", "negative", "neutral"] = "neutral",
    status_label: Optional[str] = None,
    key: Optional[str] = None,
) -> None:
    """
    Create a KPI (Key Performance Indicator) card.

    Args:
        title: Card title/label
        value: Main numeric value to display
        unit: Unit of measurement (e.g., "RPM", "°C", "km/h")
        icon: Optional emoji/icon for the card
        status: Status color theme (green, amber, red, blue, purple, gray)
        trend: Optional trend text (e.g., "+5%", "-2.3%")
        trend_direction: Trend direction for styling
        status_label: Optional status badge label
        key: Optional unique key for Streamlit
    """
    _inject_status_card_css()

    accent_color = _get_status_color(status)
    trend_class = trend_direction if trend else "neutral"

    status_badge = ""
    if status_label:
        status_badge = f'<span class="kpi-status" style="background-color: {accent_color}20; color: {accent_color};">{status_label}</span>'

    trend_html = ""
    if trend:
        trend_html = f'<span class="kpi-trend {trend_class}">{trend}</span>'

    icon_html = f'<span class="kpi-icon">{icon}</span>' if icon else ""
    unit_html = f'<span class="kpi-unit">{unit}</span>' if unit else ""

    card_html = f"""
    <div class="status-card kpi-card" style="--kpi-accent: {accent_color};">
        <div class="kpi-header">
            <div class="kpi-title">{title}</div>
            {icon_html}
        </div>
        <div class="kpi-value-container">
            <span class="kpi-value">{value}</span>
            {unit_html}
            {trend_html}
        </div>
        <div>
            {status_badge}
        </div>
    </div>
    """

    if key:
        st.markdown(f'<div id="{key}">{card_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def create_connection_status_card(
    title: str,
    status: Literal["connected", "connecting", "disconnected", "error"],
    icon: str = "",
    detail: str = "",
    action_label: Optional[str] = None,
    action_callback: Optional[callable] = None,
    key: Optional[str] = None,
) -> None:
    """
    Create a connection status card.

    Args:
        title: Connection label (e.g., "OBD-II", "LM Studio", "Bluetooth")
        status: Connection status
        icon: Optional emoji/icon
        detail: Additional detail text
        action_label: Optional button label for action
        action_callback: Optional callback for action button
        key: Optional unique key for Streamlit
    """
    _inject_status_card_css()

    styles = _get_theme_styles()

    status_colors = {
        "connected": styles["accent_green"],
        "connecting": styles["accent_amber"],
        "disconnected": styles["accent_red"],
        "error": styles["accent_red"],
    }

    status_icons = {
        "connected": "●",
        "connecting": "◐",
        "disconnected": "○",
        "error": "✕",
    }

    status_color = status_colors.get(status, styles["text_secondary"])
    status_icon = status_icons.get(status, "?")

    # Default icons for common connection types
    default_icons = {
        "OBD": "🔌",
        "OBD-II": "🔌",
        "Bluetooth": "📱",
        "WiFi": "📶",
        "LM Studio": "🤖",
        "AI": "🤖",
        "Serial": "🔗",
        "USB": "🔌",
    }

    display_icon = icon or default_icons.get(title, "🔌")

    icon_bg_color = f"{status_color}20"
    icon_color = status_color

    action_html = ""
    if action_label and action_callback:
        action_html = f"""
        <div class="connection-action">
            <button class="alert-action-btn primary" style="background-color: {status_color};" onclick="{action_callback.__name__ if hasattr(action_callback, '__name__') else 'void(0)'}">
                {action_label}
            </button>
        </div>
        """

    card_html = f"""
    <div class="status-card connection-card">
        <div class="connection-icon" style="background-color: {icon_bg_color}; color: {icon_color};">
            {display_icon}
        </div>
        <div class="connection-info">
            <div class="connection-label">{title}</div>
            <span class="connection-status {status}">
                {status_icon} {status.capitalize()}
            </span>
            {f'<div class="connection-detail">{detail}</div>' if detail else ''}
        </div>
        {action_html}
    </div>
    """

    if key:
        st.markdown(f'<div id="{key}">{card_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def create_alert_card(
    title: str,
    message: str,
    severity: Literal["critical", "major", "minor", "info"] = "info",
    icon: str = "",
    timestamp: Optional[str] = None,
    source: Optional[str] = None,
    code: Optional[str] = None,
    actions: Optional[List[Dict[str, Any]]] = None,
    dismissible: bool = False,
    key: Optional[str] = None,
) -> None:
    """
    Create an alert/notification card.

    Args:
        title: Alert title
        message: Alert message/description
        severity: Alert severity level
        icon: Optional emoji/icon
        timestamp: Optional timestamp string
        source: Optional source identifier
        code: Optional error/DTC code
        actions: Optional list of action buttons [{"label": "...", "callback": ..., "primary": True/False}]
        dismissible: Whether to show dismiss button
        key: Optional unique key for Streamlit
    """
    _inject_status_card_css()

    styles = _get_theme_styles()

    severity_colors = {
        "critical": styles["accent_red"],
        "major": styles["accent_amber"],
        "minor": styles["accent_blue"],
        "info": styles["accent_purple"],
    }

    severity_icons = {
        "critical": "🔴",
        "major": "🟠",
        "minor": "🔵",
        "info": "🟣",
    }

    alert_color = severity_colors.get(severity, styles["accent_blue"])
    alert_icon = icon or severity_icons.get(severity, "ℹ️")

    meta_items = []
    if timestamp:
        meta_items.append(f'<span class="alert-meta-item"><span class="alert-meta-label">Time:</span> {timestamp}</span>')
    if source:
        meta_items.append(f'<span class="alert-meta-item"><span class="alert-meta-label">Source:</span> {source}</span>')
    if code:
        meta_items.append(f'<span class="alert-meta-item"><span class="alert-meta-label">Code:</span> {code}</span>')

    meta_html = ""
    if meta_items:
        meta_html = f'<div class="alert-meta">{"".join(meta_items)}</div>'

    actions_html = ""
    if actions:
        action_buttons = []
        for action in actions:
            btn_class = "primary" if action.get("primary", False) else "secondary"
            btn_style = f'style="background-color: {alert_color};"' if btn_class == "primary" else ""
            action_buttons.append(
                f'<button class="alert-action-btn {btn_class}" {btn_style}>{action["label"]}</button>'
            )
        actions_html = f'<div class="alert-actions">{"".join(action_buttons)}</div>'

    dismiss_html = ""
    if dismissible:
        dismiss_html = '<button class="alert-action-btn secondary" style="margin-left: auto;">✕ Dismiss</button>'

    card_html = f"""
    <div class="status-card alert-card" style="--alert-color: {alert_color};">
        <div class="alert-header">
            <div class="alert-title-row">
                <span class="alert-icon">{alert_icon}</span>
                <span class="alert-title">{title}</span>
            </div>
            <span class="alert-severity {severity}">{severity.capitalize()}</span>
        </div>
        <div class="alert-message">{message}</div>
        {meta_html}
        {actions_html}
        {dismiss_html}
    </div>
    """

    if key:
        st.markdown(f'<div id="{key}">{card_html}</div>', unsafe_allow_html=True)
    else:
        st.markdown(card_html, unsafe_allow_html=True)


def create_status_cards_grid(cards: List[Dict[str, Any]]) -> None:
    """
    Create a responsive grid of status cards.

    Args:
        cards: List of card configurations, each with:
            - type: "kpi", "connection", or "alert"
            - Other parameters per card type
    """
    _inject_status_card_css()

    cards_html = ['<div class="status-cards-grid">']

    for card in cards:
        card_type = card.get("type", "kpi")

        if card_type == "kpi":
            cards_html.append(f"""
            <div class="status-card kpi-card" style="--kpi-accent: {_get_status_color(card.get('status', 'blue'))};">
                <div class="kpi-header">
                    <div class="kpi-title">{card.get('title', '')}</div>
                    {f'<span class="kpi-icon">{card.get("icon", "")}</span>' if card.get('icon') else ''}
                </div>
                <div class="kpi-value-container">
                    <span class="kpi-value">{card.get('value', '')}</span>
                    {f'<span class="kpi-unit">{card.get("unit", "")}</span>' if card.get('unit') else ''}
                    {f'<span class="kpi-trend {card.get("trend_direction", "neutral")}">{card.get("trend", "")}</span>' if card.get('trend') else ''}
                </div>
                {f'<div><span class="kpi-status" style="background-color: {_get_status_color(card.get("status", "blue"))}20; color: {_get_status_color(card.get("status", "blue"))};">{card.get("status_label", "")}</span></div>' if card.get('status_label') else ''}
            </div>
            """)

        elif card_type == "connection":
            status = card.get("status", "disconnected")
            status_color = _get_status_color(
                "green" if status == "connected" else
                "amber" if status == "connecting" else "red"
            )
            display_icon = card.get("icon", "🔌")

            cards_html.append(f"""
            <div class="status-card connection-card">
                <div class="connection-icon" style="background-color: {status_color}20; color: {status_color};">
                    {display_icon}
                </div>
                <div class="connection-info">
                    <div class="connection-label">{card.get('title', '')}</div>
                    <span class="connection-status {status}">{status.capitalize()}</span>
                    {f'<div class="connection-detail">{card.get("detail", "")}</div>' if card.get('detail') else ''}
                </div>
            </div>
            """)

        elif card_type == "alert":
            severity = card.get("severity", "info")
            alert_color = _get_status_color(
                "red" if severity == "critical" else
                "amber" if severity == "major" else
                "blue" if severity == "minor" else "purple"
            )
            alert_icon = card.get("icon", "ℹ️")

            meta_items = []
            if card.get("timestamp"):
                meta_items.append(f'<span class="alert-meta-item"><span class="alert-meta-label">Time:</span> {card["timestamp"]}</span>')
            if card.get("source"):
                meta_items.append(f'<span class="alert-meta-item"><span class="alert-meta-label">Source:</span> {card["source"]}</span>')
            if card.get("code"):
                meta_items.append(f'<span class="alert-meta-item"><span class="alert-meta-label">Code:</span> {card["code"]}</span>')

            meta_html = f'<div class="alert-meta">{"".join(meta_items)}</div>' if meta_items else ""

            cards_html.append(f"""
            <div class="status-card alert-card" style="--alert-color: {alert_color};">
                <div class="alert-header">
                    <div class="alert-title-row">
                        <span class="alert-icon">{alert_icon}</span>
                        <span class="alert-title">{card.get('title', '')}</span>
                    </div>
                    <span class="alert-severity {severity}">{severity.capitalize()}</span>
                </div>
                <div class="alert-message">{card.get('message', '')}</div>
                {meta_html}
            </div>
            """)

    cards_html.append('</div>')

    st.markdown("".join(cards_html), unsafe_allow_html=True)