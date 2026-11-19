"""
i20 AI Garage - Maintenance Module (Redesigned with Design System)

Maintenance tracker for oil services, filter replacements, spark plugs,
coolant, battery, tyre services, and general maintenance records.

FULLY RESPONSIVE: mobile-first fluid grid, auto-fit cards, responsive tables.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional

from config import MAINTENANCE_INTERVALS, VEHICLE_INFO
from services import get_database

# Design System imports
from components.ui.tokens import (
    # Colors
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, STATUS_NEUTRAL,
    ACCENT_PRIMARY, ACCENT_PRIMARY_HOVER, ACCENT_PRIMARY_ACTIVE, ACCENT_SECONDARY,
    ACCENT_SELECTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_ON_ACCENT,
    SURFACE_PRIMARY, SURFACE_SECONDARY, SURFACE_ELEVATED, SURFACE_INTERACTIVE,
    BORDER_DEFAULT, BORDER_SUBTLE, BORDER_STRONG, BORDER_FOCUS,
    # Spacing
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,
    GAP_INLINE, GAP_FIELD, GAP_CARD, GAP_SECTION,
    # Radius
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    # Shadows
    SHADOW_SM, SHADOW_MD, SHADOW_LG, SHADOW_FOCUS,
    # Typography
    FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_H4,
    FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_LABEL, FONT_SIZE_CAPTION,
    FONT_FAMILY_BASE, FONT_FAMILY_MONO, FONT_WEIGHT_LABEL, FONT_WEIGHT_BODY,
    FONT_WEIGHT_NUMERIC, LETTER_SPACING_LABEL, LETTER_SPACING_CAPTION,
    # Component constants
    BUTTON_MIN_HEIGHT, BUTTON_PADDING_VERTICAL, BUTTON_PADDING_HORIZONTAL,
    BUTTON_ICON_GAP, BUTTON_RADIUS, BUTTON_FONT_SIZE, BUTTON_FONT_WEIGHT,
    BADGE_PADDING_VERTICAL, BADGE_PADDING_HORIZONTAL, BADGE_RADIUS,
    BADGE_FONT_SIZE, BADGE_FONT_WEIGHT,
    CARD_RADIUS, CARD_PADDING, CARD_BORDER,
    INPUT_HEIGHT, INPUT_PADDING_VERTICAL, INPUT_PADDING_HORIZONTAL,
    INPUT_RADIUS, INPUT_FONT_SIZE,
    EMPTY_STATE_PADDING, EMPTY_STATE_ICON_SIZE,
    SKELETON_PULSE_DURATION, SPINNER_SIZE_SM, SPINNER_SIZE_MD, SPINNER_SIZE_LG,
    TRANSITION_FAST, TRANSITION_NORMAL,
)

from components.ui.components import (
    ButtonVariant, ButtonSize, ButtonProps, button, button_primary, button_secondary,
    button_ghost, button_danger,
    BadgeVariant, badge,
    AlertVariant, alert,
    CardProps, card, card_simple,
    FormFieldProps, text_input, selectbox,
    EmptyStateProps, empty_state,
    skeleton_card, spinner,
    TableColumn, TableProps, table,
)

from components.ui.layout import (
    page_header,
    responsive_container,
    auto_fit_grid_css,
    metric_row_columns,
    AUTO_FIT_CARD_CSS,
    AUTO_FIT_METRIC_CSS,
    grid_container,
)


def render_maintenance():
    """Render the maintenance tracker page - FULLY RESPONSIVE."""
    db = get_database()

    # Initialize session state - PRESERVE EXISTING KEYS EXACTLY
    if "maint_edit_id" not in st.session_state:
        st.session_state.maint_edit_id = None
    if "maint_show_form" not in st.session_state:
        st.session_state.maint_show_form = False
    if "maint_current_odometer" not in st.session_state:
        st.session_state.maint_current_odometer = 0
    if "maint_filter_type" not in st.session_state:
        st.session_state.maint_filter_type = "All"
    if "maint_sort_order" not in st.session_state:
        st.session_state.maint_sort_order = "Date (Newest)"

    # Page header using design system
    _render_page_header()

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["Records", "Add / Edit", "Upcoming"])

    with tab1:
        _render_records_tab(db)

    with tab2:
        _render_add_edit_tab(db)

    with tab3:
        _render_upcoming_tab(db)


def _render_page_header():
    """Render the maintenance page header using design system page_header - RESPONSIVE."""
    # Current mileage display as action
    mileage_html = f"""
    <div style="
        background: {SURFACE_SECONDARY};
        border: 1px solid {BORDER_DEFAULT};
        border-radius: {RADIUS_MD};
        padding: {SPACE_3} {SPACE_4};
        display: flex;
        align-items: center;
        gap: {GAP_INLINE};
        font-family: {FONT_FAMILY_MONO};
        font-size: {FONT_SIZE_BODY};
        font-weight: {FONT_WEIGHT_NUMERIC};
        color: {ACCENT_PRIMARY};
    ">
        <span style="color: {TEXT_SECONDARY}; font-weight: {FONT_WEIGHT_LABEL}; font-size: {FONT_SIZE_LABEL};">ODO</span>
        <span>{st.session_state.maint_current_odometer:,} km</span>
    </div>
    """

    page_header(
        title="Maintenance Tracker",
        subtitle=f"{VEHICLE_INFO['make']} {VEHICLE_INFO['model']} ({VEHICLE_INFO['year']}) - Service History & Schedule",
        actions=[{"type": "custom", "html": mileage_html}]
    )

    # Odometer input - responsive (full width on mobile)
    col1, col2, col3 = st.columns([2, 1, 2], gap="medium")
    with col2:
        new_odometer = st.number_input(
            "Current Odometer (km)",
            min_value=0,
            max_value=1000000,
            value=st.session_state.maint_current_odometer,
            step=100,
            key="odometer_input",
            label_visibility="collapsed"
        )
        if new_odometer != st.session_state.maint_current_odometer:
            st.session_state.maint_current_odometer = new_odometer
            st.rerun()


def _get_service_type_options() -> List[str]:
    """Get list of service type options from MAINTENANCE_INTERVALS and custom types."""
    base_types = [v["description"] for v in MAINTENANCE_INTERVALS.values()]
    custom_types = [
        "Engine Oil Change",
        "Oil Filter Replacement",
        "Air Filter Replacement",
        "Cabin Air Filter Replacement",
        "Spark Plug Replacement",
        "Coolant Replacement",
        "Brake Fluid Replacement",
        "Manual Transmission Oil",
        "Front Brake Pads Inspection",
        "Rear Brake Pads Inspection",
        "Tyre Rotation",
        "Battery Health Check",
        "Tyre Replacement",
        "Wheel Alignment",
        "Brake Service",
        "General Inspection",
        "Other"
    ]
    # Combine and deduplicate
    all_types = list(dict.fromkeys(base_types + custom_types))
    return sorted(all_types)


def _render_records_tab(db):
    """Render the maintenance records tab using design system components - RESPONSIVE."""
    records = db.get_maintenance_records(limit=1000)
    total_records = len(records)
    total_cost = sum(r.get("cost", 0) or 0 for r in records)
    last_service = records[0]["service_date"] if records else "Never"

    # Stats cards row using design system AUTO_FIT_METRIC_CSS - RESPONSIVE
    st.markdown(AUTO_FIT_METRIC_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-auto-fit-metric">', unsafe_allow_html=True)

    # Stat 1: Total Records
    card_simple(f"""
        <div style="text-align: center;">
            <div style="font-size: {FONT_SIZE_H2}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {ACCENT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{total_records}</div>
            <div style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL}; margin-top: {SPACE_1};">Total Records</div>
        </div>
    """, elevated=True)

    # Stat 2: Total Cost
    card_simple(f"""
        <div style="text-align: center;">
            <div style="font-size: {FONT_SIZE_H2}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {ACCENT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">₹{total_cost:,.0f}</div>
            <div style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL}; margin-top: {SPACE_1};">Total Cost</div>
        </div>
    """, elevated=True)

    # Stat 3: Last Service
    card_simple(f"""
        <div style="text-align: center;">
            <div style="font-size: {FONT_SIZE_H2}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {ACCENT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{last_service}</div>
            <div style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL}; margin-top: {SPACE_1};">Last Service</div>
        </div>
    """, elevated=True)

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown(f'<div style="margin-bottom: {GAP_SECTION};"></div>', unsafe_allow_html=True)

    if not records:
        empty_state(EmptyStateProps(
            title="No Maintenance Records",
            message="Add your first service record using the \"Add / Edit\" tab",
            icon="🔧",
            action_label="Add First Record",
            action_callback=lambda: _set_show_form(True),
            action_key="empty_add_first"
        ))
        return

    # Filter and Sort controls - RESPONSIVE (flex-wrap handles mobile)
    st.markdown(f'<div style="display: flex; gap: {GAP_FIELD}; flex-wrap: wrap; margin-bottom: {GAP_CARD}; align-items: center;">', unsafe_allow_html=True)

    # Filter dropdown
    filter_types = ["All"] + sorted(list(set(r["service_type"] for r in records)))
    current_filter = st.session_state.maint_filter_type
    if current_filter not in filter_types:
        current_filter = "All"

    filter_type = selectbox(
        label="Filter by Type",
        options=filter_types,
        index=filter_types.index(current_filter),
        key="maint_filter_type_select",
        help_text="Filter records by service type"
    )
    st.session_state.maint_filter_type = filter_type

    # Sort dropdown
    sort_options = ["Date (Newest)", "Date (Oldest)", "Odometer (High)", "Odometer (Low)", "Cost (High)", "Cost (Low)"]
    sort_order = selectbox(
        label="Sort By",
        options=sort_options,
        index=sort_options.index(st.session_state.maint_sort_order) if st.session_state.maint_sort_order in sort_options else 0,
        key="maint_sort_order_select",
        help_text="Sort records"
    )
    st.session_state.maint_sort_order = sort_order

    st.markdown('</div>', unsafe_allow_html=True)

    # Apply filters
    filtered_records = records
    if filter_type != "All":
        filtered_records = [r for r in filtered_records if r["service_type"] == filter_type]

    # Apply sorting
    sort_key_map = {
        "Date (Newest)": ("service_date", True),
        "Date (Oldest)": ("service_date", False),
        "Odometer (High)": ("odometer_km", True),
        "Odometer (Low)": ("odometer_km", False),
        "Cost (High)": ("cost", True),
        "Cost (Low)": ("cost", False),
    }
    sort_key, reverse = sort_key_map.get(sort_order, ("service_date", True))
    filtered_records.sort(key=lambda x: x.get(sort_key) or 0, reverse=reverse)

    # Render records as cards using design system AUTO_FIT_CARD_CSS - RESPONSIVE
    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-auto-fit-card">', unsafe_allow_html=True)

    for record in filtered_records:
        _render_single_record_card(db, record)

    st.markdown('</div>', unsafe_allow_html=True)


def _render_single_record_card(db, record: Dict[str, Any]):
    """Render a single maintenance record as a design system card - RESPONSIVE."""
    service_date = record["service_date"]
    odometer = record["odometer_km"]
    cost = record.get("cost")
    notes = record.get("notes", "")
    description = record.get("description", "")
    next_service_km = record.get("next_service_km")
    next_service_date = record.get("next_service_date")

    # Calculate km since service
    km_since = st.session_state.maint_current_odometer - odometer if st.session_state.maint_current_odometer > odometer else 0

    # Determine status badge based on next service
    if next_service_km:
        km_remaining = next_service_km - st.session_state.maint_current_odometer
        if km_remaining <= 0:
            status_variant = BadgeVariant.CRITICAL
            status_label = "Overdue"
        elif km_remaining <= 1000:
            status_variant = BadgeVariant.WARNING
            status_label = "Due Soon"
        else:
            status_variant = BadgeVariant.SUCCESS
            status_label = "Up to Date"
    else:
        status_variant = BadgeVariant.NEUTRAL
        status_label = "—"

    # Create badge using design system component
    status_badge = badge(label=status_label, variant=status_variant, key=f"maint_status_{record['id']}")

    # Card content - RESPONSIVE grid for details (auto-fit minmax)
    details_html = f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: {GAP_FIELD}; margin-bottom: {GAP_FIELD};">
        <div style="background: {SURFACE_SECONDARY}; border-radius: {RADIUS_SM}; padding: {SPACE_3};">
            <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_1};">Odometer</div>
            <div style="font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{odometer:,} km</div>
        </div>
        <div style="background: {SURFACE_SECONDARY}; border-radius: {RADIUS_SM}; padding: {SPACE_3};">
            <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_1};">KM Since Service</div>
            <div style="font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{km_since:,} km</div>
        </div>
        <div style="background: {SURFACE_SECONDARY}; border-radius: {RADIUS_SM}; padding: {SPACE_3};">
            <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_1};">Cost</div>
            <div style="font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">₹{cost:,.2f}</div>
        </div>
        <div style="background: {SURFACE_SECONDARY}; border-radius: {RADIUS_SM}; padding: {SPACE_3};">
            <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_1};">Next Service (km)</div>
            <div style="font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{next_service_km:,} km</div>
        </div>
        <div style="background: {SURFACE_SECONDARY}; border-radius: {RADIUS_SM}; padding: {SPACE_3};">
            <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_1};">Next Service (Date)</div>
            <div style="font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{next_service_date or '—'}</div>
        </div>
    </div>
    """

    notes_html = ""
    if description:
        notes_html += f'<div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY}; padding-top: {SPACE_3}; border-top: 1px solid {BORDER_SUBTLE}; font-style: italic;">{description}</div>'
    if notes:
        notes_html += f'<div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY}; padding-top: {SPACE_2}; font-style: italic;">{notes}</div>'

    # Action buttons footer - RESPONSIVE (flex-wrap)
    edit_key = f"edit_{record['id']}"
    delete_key = f"delete_{record['id']}"
    dup_key = f"dup_{record['id']}"

    footer_html = f"""
    <div style="display: flex; gap: {GAP_INLINE}; margin-top: {GAP_FIELD}; padding-top: {GAP_FIELD}; border-top: 1px solid {BORDER_SUBTLE}; flex-wrap: wrap;">
        <button id="{edit_key}_btn" class="i20-btn-edit" style="
            height: 32px; padding: 4px {SPACE_3}; border-radius: {BUTTON_RADIUS};
            font-size: {FONT_SIZE_CAPTION}; font-weight: {BUTTON_FONT_WEIGHT};
            background: {SURFACE_PRIMARY}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_DEFAULT};
            cursor: pointer; transition: all {TRANSITION_FAST}; display: inline-flex; align-items: center; gap: 4px;
        " onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: '{edit_key}', value: true}}, '*');">
            ✏️ Edit
        </button>
        <button id="{delete_key}_btn" class="i20-btn-delete" style="
            height: 32px; padding: 4px {SPACE_3}; border-radius: {BUTTON_RADIUS};
            font-size: {FONT_SIZE_CAPTION}; font-weight: {BUTTON_FONT_WEIGHT};
            background: {SURFACE_PRIMARY}; color: {STATUS_CRITICAL}; border: 1px solid {STATUS_CRITICAL};
            cursor: pointer; transition: all {TRANSITION_FAST}; display: inline-flex; align-items: center; gap: 4px;
        " onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: '{delete_key}', value: true}}, '*');">
            🗑️ Delete
        </button>
        <button id="{dup_key}_btn" class="i20-btn-dup" style="
            height: 32px; padding: 4px {SPACE_3}; border-radius: {BUTTON_RADIUS};
            font-size: {FONT_SIZE_CAPTION}; font-weight: {BUTTON_FONT_WEIGHT};
            background: {SURFACE_PRIMARY}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_DEFAULT};
            cursor: pointer; transition: all {TRANSITION_FAST}; display: inline-flex; align-items: center; gap: 4px;
        " onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: '{dup_key}', value: true}}, '*');">
            📋 Duplicate
        </button>
    </div>
    """

    # Render card with badge in subtitle
    card(CardProps(
        title=record['service_type'],
        subtitle=f"{service_date}  •  {odometer:,} km  |  {status_badge}",
        content=details_html + notes_html,
        footer=footer_html,
        elevated=False,
        bordered=True,
        padding=CARD_PADDING,
        radius=CARD_RADIUS,
    ))

    # Handle button clicks via session state
    if st.session_state.get(edit_key, False):
        st.session_state[edit_key] = False
        st.session_state.maint_edit_id = record["id"]
        st.session_state.maint_show_form = True
        st.rerun()

    if st.session_state.get(delete_key, False):
        st.session_state[delete_key] = False
        _confirm_delete(db, record["id"])

    if st.session_state.get(dup_key, False):
        st.session_state[dup_key] = False
        _duplicate_record(record)


def _confirm_delete(db, record_id: int):
    """Show delete confirmation and handle deletion."""
    if st.session_state.get(f"confirm_delete_{record_id}", False):
        # Already confirmed - perform deletion
        if db.delete_maintenance_record(record_id):
            alert("Record Deleted", "Maintenance record has been deleted successfully.", AlertVariant.SUCCESS, dismissible=True, key="delete_success")
        else:
            alert("Delete Failed", "Unable to delete record. Please try again.", AlertVariant.CRITICAL, dismissible=True, key="delete_error")
        st.session_state[f"confirm_delete_{record_id}"] = False
        st.rerun()
    else:
        # Show confirmation
        alert(
            "Confirm Delete",
            "Are you sure you want to delete this maintenance record? This action cannot be undone.",
            AlertVariant.WARNING,
            dismissible=True,
            key=f"confirm_delete_{record_id}"
        )
        # Add confirm buttons via custom HTML - RESPONSIVE (flex-wrap)
        st.markdown(f"""
        <div style="display: flex; gap: {GAP_INLINE}; margin-top: {GAP_FIELD}; flex-wrap: wrap;">
            <button onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: 'cancel_delete_{record_id}', value: true}}, '*');"
                style="height: {BUTTON_MIN_HEIGHT}; padding: {BUTTON_PADDING_VERTICAL} {BUTTON_PADDING_HORIZONTAL}; border-radius: {BUTTON_RADIUS}; font-size: {BUTTON_FONT_SIZE}; font-weight: {BUTTON_FONT_WEIGHT}; background: {SURFACE_PRIMARY}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_DEFAULT}; cursor: pointer;">
                Cancel
            </button>
            <button onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: 'do_delete_{record_id}', value: true}}, '*');"
                style="height: {BUTTON_MIN_HEIGHT}; padding: {BUTTON_PADDING_VERTICAL} {BUTTON_PADDING_HORIZONTAL}; border-radius: {BUTTON_RADIUS}; font-size: {BUTTON_FONT_SIZE}; font-weight: {BUTTON_FONT_WEIGHT}; background: {STATUS_CRITICAL}; color: {TEXT_ON_ACCENT}; border: none; cursor: pointer;">
                Delete
            </button>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.get(f"cancel_delete_{record_id}", False):
            st.session_state[f"cancel_delete_{record_id}"] = False
            st.rerun()

        if st.session_state.get(f"do_delete_{record_id}", False):
            st.session_state[f"do_delete_{record_id}"] = False
            st.session_state[f"confirm_delete_{record_id}"] = True
            st.rerun()


def _duplicate_record(record: Dict[str, Any]):
    """Pre-fill form with record data for duplication."""
    st.session_state.maint_dup_data = {
        "service_type": record["service_type"],
        "description": record.get("description", ""),
        "service_date": record["service_date"],
        "odometer_km": record["odometer_km"],
        "cost": record.get("cost"),
        "notes": record.get("notes", ""),
        "next_service_km": record.get("next_service_km"),
        "next_service_date": record.get("next_service_date"),
    }
    st.session_state.maint_edit_id = None  # Clear edit mode
    st.session_state.maint_show_form = True
    st.rerun()


def _render_add_edit_tab(db):
    """Render the add/edit maintenance record form using design system components - RESPONSIVE."""
    editing = st.session_state.maint_edit_id is not None
    record = None

    if editing:
        records = db.get_maintenance_records(limit=1000)
        record = next((r for r in records if r["id"] == st.session_state.maint_edit_id), None)
        if not record:
            alert("Record Not Found", "The record you're trying to edit no longer exists.", AlertVariant.CRITICAL, dismissible=True, key="edit_not_found")
            st.session_state.maint_edit_id = None
            st.rerun()
            return

    # Check if duplicating
    dup_data = st.session_state.get("maint_dup_data", None)

    # Form card
    card(CardProps(
        title="Add Maintenance Record" if not editing else f"Edit: {record['service_type']}",
        content=_render_maintenance_form(db, record, dup_data, editing),
        elevated=True,
        bordered=True,
        padding=CARD_PADDING,
        radius=CARD_RADIUS,
    ))

    # Quick Add Buttons for common services (only when not editing) - RESPONSIVE
    if not editing:
        _render_quick_add_buttons()


def _render_maintenance_form(db, record: Optional[Dict], dup_data: Optional[Dict], editing: bool) -> str:
    """Render the maintenance form and return HTML content - RESPONSIVE."""
    # This function builds the form HTML, but actual form inputs use Streamlit native
    # We'll render the form directly in the card content area using Streamlit components

    # Determine defaults
    def get_default(key: str, fallback=None):
        if editing and record and key in record:
            return record[key]
        if dup_data and key in dup_data:
            return dup_data[key]
        return fallback

    service_types = _get_service_type_options()
    default_type = get_default("service_type", service_types[0] if service_types else "")
    default_desc = get_default("description", "")
    default_date = get_default("service_date", str(date.today()))
    default_odo = get_default("odometer_km", st.session_state.maint_current_odometer)
    default_cost = get_default("cost", 0.0)
    default_next_km = get_default("next_service_km", 0)
    default_next_date = get_default("next_service_date", None)
    default_notes = get_default("notes", "")

    # Parse date defaults
    try:
        parsed_default_date = datetime.strptime(default_date, "%Y-%m-%d").date()
    except:
        parsed_default_date = date.today()

    try:
        parsed_next_date = datetime.strptime(default_next_date, "%Y-%m-%d").date() if default_next_date else None
    except:
        parsed_next_date = None

    # Form using Streamlit native components (wrapped in design system styling)
    with st.form("maintenance_form", clear_on_submit=False):
        # Service Type Section
        st.markdown(f'<div style="font-size: {FONT_SIZE_LABEL}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_3}; padding-bottom: {SPACE_2}; border-bottom: 1px solid {BORDER_SUBTLE};">Service Details</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="medium")
        with col1:
            service_type = selectbox(
                label="Service Type *",
                options=service_types,
                index=service_types.index(default_type) if default_type in service_types else 0,
                key="form_service_type",
                required=True,
            )
        with col2:
            description = text_input(
                label="Description",
                value=default_desc,
                placeholder="e.g., Full synthetic 5W-30, OEM filter",
                key="form_description",
            )

        # Date and Odometer Section
        st.markdown(f'<div style="font-size: {FONT_SIZE_LABEL}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL}; color: {TEXT_SECONDARY}; margin: {GAP_SECTION} 0 {SPACE_3} 0; padding-bottom: {SPACE_2}; border-bottom: 1px solid {BORDER_SUBTLE};">Service Date & Odometer</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="medium")
        with col1:
            service_date = st.date_input(
                "Service Date *",
                value=parsed_default_date,
                key="form_service_date",
            )
        with col2:
            odometer_km = st.number_input(
                "Odometer (km) *",
                min_value=0,
                max_value=1000000,
                value=default_odo,
                step=100,
                key="form_odometer",
            )

        # Cost and Notes Section
        st.markdown(f'<div style="font-size: {FONT_SIZE_LABEL}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL}; color: {TEXT_SECONDARY}; margin: {GAP_SECTION} 0 {SPACE_3} 0; padding-bottom: {SPACE_2}; border-bottom: 1px solid {BORDER_SUBTLE};">Cost & Notes</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="medium")
        with col1:
            cost = st.number_input(
                "Cost (₹)",
                min_value=0.0,
                max_value=1000000.0,
                value=float(default_cost) if default_cost else 0.0,
                step=100.0,
                format="%.2f",
                key="form_cost",
            )
        with col2:
            next_service_km = st.number_input(
                "Next Service Due (km)",
                min_value=0,
                max_value=1000000,
                value=default_next_km if default_next_km else 0,
                step=1000,
                key="form_next_km",
                help="Leave as 0 to auto-calculate from maintenance intervals"
            )

        col1, col2 = st.columns(2, gap="medium")
        with col1:
            next_service_date = st.date_input(
                "Next Service Due (Date)",
                value=parsed_next_date,
                key="form_next_date",
            )
        with col2:
            # Auto-calculate button - full width on mobile via use_container_width
            if button_secondary("Auto-calculate Next Service", key="auto_calc_next", use_container_width=True):
                for key, interval in MAINTENANCE_INTERVALS.items():
                    if interval["description"].lower() in service_type.lower():
                        next_km = odometer_km + interval["interval_km"]
                        st.session_state.form_next_km = next_km
                        months = interval["interval_km"] / 1500
                        next_date = service_date + timedelta(days=int(months * 30))
                        st.session_state.form_next_date = next_date
                        st.rerun()
                        break

        notes = st.text_area(
            "Notes",
            value=default_notes,
            placeholder="Additional details, parts used, shop name, warranty info...",
            height=100,
            key="form_notes"
        )

        # Submit buttons - RESPONSIVE (flex-wrap)
        st.markdown(f'<div style="margin-top: {GAP_SECTION}; padding-top: {GAP_FIELD}; border-top: 1px solid {BORDER_SUBTLE}; display: flex; gap: {GAP_INLINE}; flex-wrap: wrap;">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 4], gap="small")
        with col1:
            submitted = st.form_submit_button(
                "Save Record",
                type="primary",
                use_container_width=True
            )
        with col2:
            cancelled = st.form_submit_button(
                "Cancel",
                type="secondary",
                use_container_width=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

        if submitted:
            if not service_type or not service_date or not odometer_km:
                alert("Validation Error", "Please fill in all required fields (marked with *)", AlertVariant.CRITICAL, dismissible=True, key="form_validation_error")
            else:
                # Auto-calculate next service if not provided
                if next_service_km == 0:
                    for key, interval in MAINTENANCE_INTERVALS.items():
                        if interval["description"].lower() in service_type.lower():
                            next_service_km = odometer_km + interval["interval_km"]
                            months = interval["interval_km"] / 1500
                            next_service_date = service_date + timedelta(days=int(months * 30))
                            break

                # Prepare data
                data = {
                    "service_type": service_type,
                    "description": description,
                    "service_date": str(service_date),
                    "odometer_km": odometer_km,
                    "cost": cost if cost > 0 else None,
                    "notes": notes,
                    "next_service_km": next_service_km if next_service_km > 0 else None,
                    "next_service_date": str(next_service_date) if next_service_date else None,
                }

                if editing:
                    if db.update_maintenance_record(st.session_state.maint_edit_id, **data):
                        alert("Record Updated", "Maintenance record has been updated successfully!", AlertVariant.SUCCESS, dismissible=True, key="update_success")
                        st.session_state.maint_edit_id = None
                        st.session_state.maint_show_form = False
                        if "maint_dup_data" in st.session_state:
                            del st.session_state.maint_dup_data
                        st.rerun()
                    else:
                        alert("Update Failed", "Failed to update record. Please try again.", AlertVariant.CRITICAL, dismissible=True, key="update_error")
                else:
                    record_id = db.add_maintenance_record(**data)
                    if record_id:
                        alert("Record Added", "Maintenance record has been added successfully!", AlertVariant.SUCCESS, dismissible=True, key="add_success")
                        st.session_state.maint_show_form = False
                        if "maint_dup_data" in st.session_state:
                            del st.session_state.maint_dup_data
                        st.rerun()
                    else:
                        alert("Add Failed", "Failed to add record. Please try again.", AlertVariant.CRITICAL, dismissible=True, key="add_error")

        if cancelled:
            st.session_state.maint_edit_id = None
            st.session_state.maint_show_form = False
            if "maint_dup_data" in st.session_state:
                del st.session_state.maint_dup_data
            st.rerun()

    return ""  # Form is rendered inline, card content handled by Streamlit


def _render_quick_add_buttons():
    """Render quick add buttons for common services - RESPONSIVE."""
    # Live region for quick-add announcements
    quick_add_live_region_id = "maint-quick-add-live"
    st.markdown(f'''
    <div id="{quick_add_live_region_id}" class="i20-live-region i20-visually-hidden" aria-live="polite" aria-atomic="true" aria-label="Quick add status"></div>
    ''', unsafe_allow_html=True)

    st.markdown(f'<div style="margin-top: {GAP_SECTION};">', unsafe_allow_html=True)
    st.markdown(f'<div style="font-size: {FONT_SIZE_LABEL}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_LABEL}; color: {TEXT_SECONDARY}; margin-bottom: {SPACE_3};">Quick Add Common Services</div>', unsafe_allow_html=True)
    st.caption("Pre-filled forms for common maintenance items")

    quick_services = [
        ("Engine Oil Change", "Full synthetic 5W-30, OEM filter"),
        ("Oil Filter Replacement", "OEM oil filter"),
        ("Air Filter Replacement", "OEM air filter"),
        ("Cabin Air Filter Replacement", "OEM cabin filter"),
        ("Spark Plug Replacement", "NGK/Iridium plugs (set of 4)"),
        ("Coolant Replacement", "OEM blue coolant, full flush"),
        ("Brake Fluid Replacement", "DOT 4 brake fluid"),
        ("Tyre Rotation", "Cross rotation pattern"),
        ("Battery Health Check", "Load test & terminal cleaning"),
    ]

    # Render as button grid using AUTO_FIT_CARD_CSS - RESPONSIVE
    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-auto-fit-card">', unsafe_allow_html=True)

    for svc_type, svc_desc in quick_services:
        key = f"quick_{svc_type.lower().replace(' ', '_').replace('/', '_')}"
        # Use custom button with aria-label and keyboard support
        btn_html = f'''
        <button id="{key}_btn" class="i20-btn-quick-add" type="button" aria-label="Add {svc_type} maintenance record"
            style="
                width: 100%; height: {BUTTON_MIN_HEIGHT}; padding: {BUTTON_PADDING_VERTICAL} {BUTTON_PADDING_HORIZONTAL};
                border-radius: {BUTTON_RADIUS}; font-size: {BUTTON_FONT_SIZE}; font-weight: {BUTTON_FONT_WEIGHT};
                background: {SURFACE_INTERACTIVE}; color: {TEXT_PRIMARY}; border: 1px solid {BORDER_DEFAULT};
                cursor: pointer; transition: all {TRANSITION_FAST}; display: inline-flex; align-items: center; justify-content: center; gap: {BUTTON_ICON_GAP};
            "
            onfocus="this.style.outline='2px solid {BORDER_FOCUS}'; this.style.outlineOffset='2px';"
            onblur="this.style.outline=''; this.style.outlineOffset='';"
            onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: '{key}', value: true}}, '*');
                (function() {{
                    const region = document.getElementById('{quick_add_live_region_id}');
                    if (region) {{
                        region.textContent = 'Opened form for {svc_type}';
                    }}
                }})();">
            + {svc_type}
        </button>
        '''
        st.markdown(btn_html, unsafe_allow_html=True)

        # Handle button click via session state
        if st.session_state.get(key, False):
            st.session_state[key] = False
            st.session_state.maint_dup_data = {
                "service_type": svc_type,
                "description": svc_desc,
                "service_date": str(date.today()),
                "odometer_km": st.session_state.maint_current_odometer,
                "cost": 0.0,
                "notes": "",
                "next_service_km": 0,
                "next_service_date": None,
            }
            st.session_state.maint_show_form = True
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def _render_upcoming_tab(db):
    """Render the upcoming maintenance tab using design system components - RESPONSIVE."""
    current_odo = st.session_state.maint_current_odometer

    if current_odo == 0:
        empty_state(EmptyStateProps(
            title="Set Current Odometer",
            message=f"Enter your current odometer reading in the header to see upcoming maintenance items based on {VEHICLE_INFO['make']} {VEHICLE_INFO['model']} service intervals.",
            icon="📏",
        ))

        # Show maintenance intervals reference
        st.markdown(f'<div style="margin-top: {GAP_SECTION};">', unsafe_allow_html=True)
        _render_intervals_reference()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Get upcoming maintenance from database records
    upcoming_from_records = db.get_upcoming_maintenance(current_odo)

    # Also calculate based on intervals and last service of each type
    upcoming_calculated = _calculate_upcoming_from_intervals(db, current_odo)

    # Combine and deduplicate
    all_upcoming = _combine_upcoming(upcoming_from_records, upcoming_calculated)

    if not all_upcoming:
        empty_state(EmptyStateProps(
            title="All Caught Up! 🎉",
            message=f"No upcoming maintenance due at {current_odo:,} km based on recorded services and recommended intervals.",
            icon="✅",
        ))
        st.markdown(f'<div style="margin-top: {GAP_SECTION};">', unsafe_allow_html=True)
        _render_intervals_reference()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    # Sort by urgency (overdue first, then due soon, then OK)
    def urgency_sort(item):
        status = item.get("status", "ok")
        km_remaining = item.get("km_remaining", 999999)
        if status == "overdue":
            return (0, km_remaining)
        elif status == "due_soon":
            return (1, km_remaining)
        return (2, km_remaining)

    all_upcoming.sort(key=urgency_sort)

    # Render upcoming cards in responsive grid using AUTO_FIT_CARD_CSS - RESPONSIVE
    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-auto-fit-card">', unsafe_allow_html=True)

    for item in all_upcoming:
        _render_upcoming_card(item, current_odo)

    st.markdown('</div>', unsafe_allow_html=True)

    # Reference intervals
    with st.expander("View All Recommended Service Intervals"):
        _render_intervals_reference()


def _calculate_upcoming_from_intervals(db, current_odo: int) -> List[Dict[str, Any]]:
    """Calculate upcoming maintenance based on intervals and last service of each type."""
    records = db.get_maintenance_records(limit=1000)
    upcoming = []

    # Get last service for each type
    last_service_by_type = {}
    for record in records:
        svc_type = record["service_type"]
        odo = record["odometer_km"]
        if svc_type not in last_service_by_type or odo > last_service_by_type[svc_type]["odometer_km"]:
            last_service_by_type[svc_type] = record

    # Check each maintenance interval
    for interval_key, interval in MAINTENANCE_INTERVALS.items():
        interval_desc = interval["description"]
        interval_km = interval["interval_km"]

        # Find matching last service (fuzzy match)
        last_service = None
        for svc_type, record in last_service_by_type.items():
            if interval_desc.lower() in svc_type.lower() or svc_type.lower() in interval_desc.lower():
                last_service = record
                break

        if last_service:
            last_odo = last_service["odometer_km"]
            next_due_km = last_odo + interval_km
            km_remaining = next_due_km - current_odo

            # Determine status
            if km_remaining <= 0:
                status = "overdue"
            elif km_remaining <= 1000:
                status = "due_soon"
            else:
                status = "ok"

            # Calculate approximate date
            last_date_str = last_service["service_date"]
            try:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d").date()
                months = interval_km / 1500
                next_date = last_date + timedelta(days=int(months * 30))
            except:
                next_date = None

            upcoming.append({
                "type": "calculated",
                "service_type": interval_desc,
                "description": interval.get("description", ""),
                "last_service_km": last_odo,
                "last_service_date": last_service["service_date"],
                "interval_km": interval_km,
                "next_due_km": next_due_km,
                "next_due_date": str(next_date) if next_date else None,
                "km_remaining": km_remaining,
                "status": status,
                "source": f"Based on last service at {last_odo:,} km"
            })
        else:
            # No previous service recorded - show as due at interval
            km_remaining = interval_km - current_odo
            if km_remaining <= 0:
                status = "overdue"
            elif km_remaining <= 1000:
                status = "due_soon"
            else:
                status = "ok"

            next_date = date.today() + timedelta(days=int((interval_km / 1500) * 30))

            upcoming.append({
                "type": "calculated",
                "service_type": interval_desc,
                "description": f"First {interval_desc.lower()} (no previous record)",
                "last_service_km": 0,
                "last_service_date": "Never",
                "interval_km": interval_km,
                "next_due_km": interval_km,
                "next_due_date": str(next_date),
                "km_remaining": km_remaining,
                "status": status,
                "source": "No previous service recorded"
            })

    return upcoming


def _combine_upcoming(from_records: List[Dict], calculated: List[Dict]) -> List[Dict]:
    """Combine upcoming maintenance from records and calculated intervals."""
    combined = []

    # Add records with next_service_km
    for record in from_records:
        if record.get("next_service_km"):
            next_km = record["next_service_km"]
            km_remaining = next_km - st.session_state.maint_current_odometer

            if km_remaining <= 0:
                status = "overdue"
            elif km_remaining <= 1000:
                status = "due_soon"
            else:
                status = "ok"

            combined.append({
                "type": "record",
                "service_type": record["service_type"],
                "description": record.get("description", ""),
                "last_service_km": record["odometer_km"],
                "last_service_date": record["service_date"],
                "interval_km": None,
                "next_due_km": next_km,
                "next_due_date": record.get("next_service_date"),
                "km_remaining": km_remaining,
                "status": status,
                "source": f"From record at {record['odometer_km']:,} km"
            })

    # Add calculated items, but avoid duplicates
    for calc in calculated:
        is_duplicate = False
        for existing in combined:
            if (existing["service_type"].lower() == calc["service_type"].lower() and
                abs(existing["next_due_km"] - calc["next_due_km"]) < 500):
                is_duplicate = True
                break

        if not is_duplicate:
            combined.append(calc)

    return combined


def _render_upcoming_card(item: Dict[str, Any], current_odo: int):
    """Render an upcoming maintenance card using design system card component - RESPONSIVE."""
    status = item["status"]
    km_remaining = item["km_remaining"]

    # Status badge variant mapping
    status_variant_map = {
        "overdue": BadgeVariant.CRITICAL,
        "due_soon": BadgeVariant.WARNING,
        "ok": BadgeVariant.SUCCESS,
    }
    status_label_map = {
        "overdue": "Overdue",
        "due_soon": "Due Soon",
        "ok": "Up to Date",
    }

    variant = status_variant_map.get(status, BadgeVariant.SUCCESS)
    label = status_label_map.get(status, "OK")

    # Border color based on status
    border_color = {
        "overdue": STATUS_CRITICAL,
        "due_soon": STATUS_WARNING,
        "ok": STATUS_SUCCESS,
    }.get(status, STATUS_SUCCESS)

    km_display = f"{abs(km_remaining):,} km {'overdue' if km_remaining < 0 else 'remaining'}"

    # Card content - RESPONSIVE grid for details
    content_html = f"""
    <div style="margin-bottom: {GAP_FIELD};">
        <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY};">Interval</div>
        <div style="font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {ACCENT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{item.get('interval_km', '—'):,} km</div>
    </div>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: {GAP_FIELD}; margin-top: {GAP_FIELD}; padding-top: {GAP_FIELD}; border-top: 1px solid {BORDER_SUBTLE};">
        <div>
            <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY};">Last Service</div>
            <div style="font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{item['last_service_km']:,} km</div>
            <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">{item['last_service_date']}</div>
        </div>
        <div>
            <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY};">Next Due</div>
            <div style="font-size: {FONT_SIZE_BODY}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {TEXT_PRIMARY}; font-family: {FONT_FAMILY_MONO};">{item['next_due_km']:,} km</div>
            <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">{item.get('next_due_date', '—')}</div>
        </div>
        <div>
            <div style="font-size: {FONT_SIZE_CAPTION}; font-weight: {FONT_WEIGHT_LABEL}; text-transform: uppercase; letter-spacing: {LETTER_SPACING_CAPTION}; color: {TEXT_SECONDARY};">Remaining</div>
            <div style="font-size: {FONT_SIZE_H3}; font-weight: {FONT_WEIGHT_NUMERIC}; color: {border_color}; font-family: {FONT_FAMILY_MONO};">{km_display}</div>
        </div>
    </div>
    <div style="margin-top: {SPACE_3}; font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">{item['source']}</div>
    """

    # Footer with action button for overdue/due_soon
    footer_html = ""
    if status in ["overdue", "due_soon"]:
        action_key = f"log_{item['service_type']}_{item.get('type', '')}"
        footer_html = f"""
        <button id="{action_key}_btn" class="i20-btn-record" style="
            width: 100%; height: {BUTTON_MIN_HEIGHT}; padding: {BUTTON_PADDING_VERTICAL} {BUTTON_PADDING_HORIZONTAL};
            border-radius: {BUTTON_RADIUS}; font-size: {BUTTON_FONT_SIZE}; font-weight: {BUTTON_FONT_WEIGHT};
            background: {ACCENT_PRIMARY}; color: {TEXT_ON_ACCENT}; border: none; cursor: pointer;
            transition: all {TRANSITION_FAST}; display: inline-flex; align-items: center; justify-content: center; gap: {BUTTON_ICON_GAP};
        " onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', key: '{action_key}', value: true}}, '*');">
            ➕ Log {item['service_type']}
        </button>
        """

    # Render card with custom border
    card_key = f"upcoming_{item['service_type']}_{item.get('type', '')}"
    st.markdown(f"""
    <style>
    .i20-card-{card_key} {{
        border-left: 4px solid {border_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

    card(CardProps(
        title=f"{item['service_type']}",
        subtitle=item['description'],
        content=content_html,
        footer=footer_html,
        elevated=False,
        bordered=True,
        padding=CARD_PADDING,
        radius=CARD_RADIUS,
        class_name=f"i20-card-{card_key}",
    ))

    # Handle action button click
    action_key = f"log_{item['service_type']}_{item.get('type', '')}"
    if st.session_state.get(action_key, False):
        st.session_state[action_key] = False
        st.session_state.maint_dup_data = {
            "service_type": item["service_type"],
            "description": item.get("description", ""),
            "service_date": str(date.today()),
            "odometer_km": current_odo,
            "cost": 0.0,
            "notes": "",
            "next_service_km": 0,
            "next_service_date": None,
        }
        st.session_state.maint_show_form = True
        st.rerun()


def _render_intervals_reference():
    """Render the maintenance intervals reference table using design system - RESPONSIVE."""
    st.markdown(f'<div style="font-size: {FONT_SIZE_H4}; font-weight: {FONT_WEIGHT_LABEL}; color: {TEXT_PRIMARY}; margin-bottom: {SPACE_3};">Hyundai i20 Asta 2023 - Recommended Service Intervals</div>', unsafe_allow_html=True)

    interval_data = []
    for key, interval in MAINTENANCE_INTERVALS.items():
        interval_data.append({
            "Service Item": interval["description"],
            "Interval (km)": f"{interval['interval_km']:,}",
            "Interval (months)": f"~{interval['interval_km'] // 1500}",
        })

    df = pd.DataFrame(interval_data)

    # Use design system table component - RESPONSIVE (horizontal scroll on mobile)
    columns = [
        TableColumn(key="Service Item", header="Service Item", width=""),
        TableColumn(key="Interval (km)", header="Interval (km)", align="center"),
        TableColumn(key="Interval (months)", header="Interval (months)", align="center"),
    ]

    table(TableProps(
        columns=columns,
        data=interval_data,
        key="intervals_table",
        selectable=False,
        empty_message="No interval data available",
        striped=True,
        hoverable=True,
    ))

    st.caption("Intervals based on typical manufacturer recommendations for 2023 Hyundai i20 Asta 1.2L Petrol (India). Adjust based on driving conditions and owner's manual.")


def _set_show_form(show: bool):
    """Helper to set form visibility."""
    st.session_state.maint_show_form = show


# Convenience function for testing
if __name__ == "__main__":
    st.set_page_config(page_title="Maintenance Tracker", page_icon="🔧", layout="wide")
    render_maintenance()