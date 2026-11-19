"""
i20 AI Garage - AI Assistant Module (Redesigned with Phase 6 Design System)

Local AI automotive assistant powered by LM Studio.
Supports both chat mode and diagnostic mode.

FULLY RESPONSIVE: mobile-first fluid grid, auto-fit cards, responsive chat layout.
"""

import streamlit as st
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from config import AI_SYSTEM_PROMPT
from services import get_ai_service, get_database, get_diagnostic_engine, AIServiceError
from services.diagnostic_models import DiagnosticResult, DiagnosticSeverity, DataSource

from components.ui import (
    # Styles & Layout
    inject_global_css,
    initialize_layout,
    page_header,
    section_header,
    card_container,
    grid_container,
    AUTO_FIT_CARD_CSS,
    AUTO_FIT_METRIC_CSS,
    # Components
    ButtonVariant,
    ButtonSize,
    ButtonProps,
    button,
    button_primary,
    button_secondary,
    button_ghost,
    button_danger,
    BadgeVariant,
    badge,
    AlertVariant,
    alert,
    CardProps,
    card,
    card_simple,
    FormFieldProps,
    form_field,
    text_input,
    selectbox,
    TableColumn,
    TableProps,
    table,
    EmptyStateProps,
    empty_state,
    skeleton,
    skeleton_text,
    skeleton_card,
    spinner,
    loading_overlay,
    # Tokens
    ACCENT_PRIMARY,
    ACCENT_PRIMARY_HOVER,
    ACCENT_PRIMARY_ACTIVE,
    ACCENT_SECONDARY,
    ACCENT_SELECTED,
    STATUS_SUCCESS,
    STATUS_WARNING,
    STATUS_CRITICAL,
    STATUS_INFO,
    STATUS_NEUTRAL,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_MUTED,
    TEXT_ON_ACCENT,
    SURFACE_PRIMARY,
    SURFACE_SECONDARY,
    SURFACE_INTERACTIVE,
    BORDER_DEFAULT,
    BORDER_SUBTLE,
    BORDER_STRONG,
    BORDER_FOCUS,
    DIAG_CRITICAL,
    DIAG_MAJOR,
    DIAG_MINOR,
    DIAG_INFO,
    DATASOURCE_SIMULATION,
    DATASOURCE_REAL,
    SPACE_1,
    SPACE_2,
    SPACE_3,
    SPACE_4,
    SPACE_5,
    SPACE_6,
    GAP_FIELD,
    GAP_CARD_GRID,
    GAP_INLINE,
    GAP_SECTION,
    RADIUS_SM,
    RADIUS_MD,
    RADIUS_LG,
    RADIUS_PILL,
    FONT_SIZE_LABEL,
    FONT_SIZE_BODY,
    FONT_SIZE_BODY_SM,
    FONT_SIZE_CAPTION,
    BUTTON_FONT_WEIGHT,
    TRANSITION_FAST,
    TRANSITION_NORMAL,
    CARD_RADIUS,
    CARD_PADDING,
    CARD_BORDER,
    INPUT_HEIGHT,
    INPUT_PADDING_VERTICAL,
    INPUT_PADDING_HORIZONTAL,
    INPUT_RADIUS,
    INPUT_FONT_SIZE,
    SHADOW_SM,
    SHADOW_MD,
    SHADOW_FOCUS,
)


def render_ai_assistant():
    """Render the AI Assistant page using design system - FULLY RESPONSIVE."""
    ai = get_ai_service()
    db = get_database()

    # Initialize session state (preserving all 9 AI-specific + 34 shared keys)
    if "ai_session_id" not in st.session_state:
        st.session_state.ai_session_id = str(uuid.uuid4())[:8]
    if "ai_messages" not in st.session_state:
        st.session_state.ai_messages = []
    if "ai_loading" not in st.session_state:
        st.session_state.ai_loading = False
    if "ai_mode" not in st.session_state:
        st.session_state.ai_mode = "chat"  # "chat" or "diagnostic"
    if "ai_diagnostic_result" not in st.session_state:
        st.session_state.ai_diagnostic_result = None
    if "ai_status" not in st.session_state:
        st.session_state.ai_status = "checking"

    # Inject design system CSS
    inject_global_css()
    initialize_layout()

    # Page header using design system layout
    page_header(
        title="AI Assistant",
        subtitle="Local AI chat & diagnostic assistance powered by LM Studio",
        icon="🤖"
    )

    # AI connection status header
    render_ai_header(ai)

    # Mode selector - RESPONSIVE
    render_mode_selector()

    # Main content area - different layout based on mode
    if st.session_state.ai_mode == "chat":
        # Chat mode: responsive columns (stack on mobile)
        col1, col2 = st.columns([3, 1], gap="large")

        with col1:
            render_chat_interface(ai, db)

        with col2:
            render_ai_sidebar(ai, db)
    else:
        # Diagnostic mode: full width with diagnostic panel
        render_diagnostic_interface(ai, db)

    # Check for AI response after rendering (async flow)
    check_ai_response()


def render_ai_header(ai):
    """Render AI assistant header with connection status using design system - RESPONSIVE."""
    # Check connection status
    if "ai_status" not in st.session_state:
        st.session_state.ai_status = "checking"

    if st.session_state.ai_status == "checking":
        with st.spinner("Checking LM Studio connection..."):
            connected = ai.check_connection()
            models = ai.get_available_models() if connected else []
            model_available = ai.is_model_available() if connected else False
            st.session_state.ai_status = "online" if (connected and model_available) else "offline"
            st.session_state.ai_models = models
            st.session_state.ai_model_available = model_available

    status = st.session_state.ai_status
    status_text = {
        "online": "LM STUDIO CONNECTED",
        "offline": "LM STUDIO UNAVAILABLE",
        "checking": "CHECKING CONNECTION..."
    }.get(status, "UNKNOWN")

    status_variant = {
        "online": BadgeVariant.SUCCESS,
        "offline": BadgeVariant.CRITICAL,
        "checking": BadgeVariant.WARNING
    }.get(status, BadgeVariant.NEUTRAL)

    model_name = ai.model
    if st.session_state.get("ai_model_available"):
        model_name += " ✓"
    else:
        model_name += " ✗"

    # Header card using design system - RESPONSIVE (flex-wrap)
    card(CardProps(
        title="",
        subtitle="",
        content=f"""
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: {SPACE_4};">
            <div style="display: flex; align-items: center; gap: {SPACE_3};">
                <span style="font-size: 2rem;">🤖</span>
                <span style="font-size: var(--i20-font-size-h3); font-weight: var(--i20-font-weight-h3); color: {TEXT_PRIMARY};">i20 AI Assistant</span>
            </div>
            <div style="text-align: right;">
                {badge(label=status_text, variant=status_variant, key="ai_header_status")}
                <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY}; margin-top: {SPACE_1};">
                    Model: {model_name}
                </div>
            </div>
        </div>
        """,
        elevated=False,
        bordered=True,
        class_name="ai-header-card",
    ))

    # Show warning if offline using design system alert
    if status == "offline":
        alert(
            title="LM Studio Unavailable",
            message="""
            **LM Studio is not available.** Please ensure:
            1. LM Studio is running on localhost:1234
            2. The model 'qwen2.5-3b-instruct' is loaded
            3. The local server is started in LM Studio (Developer → Start Server)
            """,
            variant=AlertVariant.CRITICAL,
            key="ai_offline_alert"
        )


def render_mode_selector():
    """Render mode selector between Chat and Diagnostic mode using design system buttons - RESPONSIVE."""
    mode = st.session_state.ai_mode

    col1, col2 = st.columns(2, gap="small")

    with col1:
        chat_selected = mode == "chat"
        if button(
            ButtonProps(
                label="💬 Chat Mode",
                variant=ButtonVariant.PRIMARY if chat_selected else ButtonVariant.SECONDARY,
                size=ButtonSize.MD,
                use_container_width=True,  # RESPONSIVE
                key="mode_chat",
                disabled=chat_selected,
            )
        ):
            if not chat_selected:
                st.session_state.ai_mode = "chat"
                st.rerun()

    with col2:
        diag_selected = mode == "diagnostic"
        if button(
            ButtonProps(
                label="🔍 Diagnostic Mode",
                variant=ButtonVariant.PRIMARY if diag_selected else ButtonVariant.SECONDARY,
                size=ButtonSize.MD,
                use_container_width=True,  # RESPONSIVE
                key="mode_diagnostic",
                disabled=diag_selected,
            )
        ):
            if not diag_selected:
                st.session_state.ai_mode = "diagnostic"
                st.rerun()

    # Mode description
    if mode == "chat":
        st.caption("💬 General automotive Q&A with vehicle context awareness")
    else:
        st.caption("🔍 Structured AI diagnosis for specific DTCs and symptoms")


def render_diagnostic_interface(ai, db):
    """Render the diagnostic mode interface using design system - RESPONSIVE."""
    # Check AI connection
    if not ai.check_connection():
        alert(
            title="AI Not Connected",
            message="LM Studio is not connected. Cannot run diagnostic mode. Please check your LM Studio server.",
            variant=AlertVariant.CRITICAL,
            key="diag_ai_offline"
        )
        return

    # Get OBD service for current data
    from services import get_obd_service
    obd = get_obd_service()

    # Input section
    section_header(
        title="Run Diagnostic Analysis",
        description="Enter DTC codes, describe symptoms, or run a full vehicle scan"
    )

    # DTC input - RESPONSIVE (columns stack on mobile)
    col1, col2 = st.columns([2, 1], gap="medium")
    with col1:
        dtc_input = text_input(
            label="DTC Code(s)",
            placeholder="e.g., P0300, P0171, P0420",
            key="diag_dtc_input",
            help_text="Enter one or more DTC codes separated by commas",
        )
    with col2:
        st.markdown(f"<div style='margin-top: {SPACE_6};'></div>", unsafe_allow_html=True)
        if button_primary("🧠 Analyze", key="diag_analyze_dtc", use_container_width=True, disabled=not dtc_input.strip()):
            run_diagnostic_analysis(ai, db, obd, dtc_input.strip())

    # Symptoms input
    st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)
    section_header("Or describe symptoms", level=4)
    symptoms = text_input(
        label="Symptoms",
        placeholder="e.g., Engine misfire at idle, rough running, check engine light flashing, coolant temp rising...",
        key="diag_symptoms_input",
        help_text="Describe the symptoms you're experiencing",
    )

    col1, col2, col3 = st.columns([1, 1, 2], gap="small")
    with col1:
        if button_primary("🔍 Analyze Symptoms", key="diag_analyze_symptoms", use_container_width=True, disabled=not symptoms.strip()):
            run_diagnostic_analysis(ai, db, obd, "", symptoms.strip())
    with col2:
        if button_secondary("🚗 Full Vehicle Scan", key="diag_full_scan", use_container_width=True):
            run_diagnostic_analysis(ai, db, obd, "", "")

    st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # Results section - RESPONSIVE
    if st.session_state.ai_diagnostic_result:
        render_ai_diagnostic_result(st.session_state.ai_diagnostic_result)
    else:
        empty_state(EmptyStateProps(
            title="Ready for Analysis",
            message="Enter DTC codes, describe symptoms, or run a full vehicle scan to get AI-powered diagnostic analysis",
            icon="🔍",
        ))


def run_diagnostic_analysis(ai, db, obd, dtc_input: str, symptoms: str = ""):
    """Run diagnostic analysis using the diagnostic engine."""
    try:
        from services import get_diagnostic_engine
        engine = get_diagnostic_engine()

        # If DTC input provided, we could manually set DTCs in the OBD service
        # For now, use the engine which will scan for actual DTCs
        with st.spinner("Running AI diagnosis..."):
            result = engine.run_diagnosis()

        st.session_state.ai_diagnostic_result = result
        alert(
            title="Analysis Complete",
            message="Diagnostic analysis completed successfully!",
            variant=AlertVariant.SUCCESS,
            key="diag_complete"
        )
        st.rerun()

    except Exception as e:
        alert(
            title="Analysis Failed",
            message=f"Diagnostic analysis failed: {str(e)}",
            variant=AlertVariant.CRITICAL,
            key="diag_failed"
        )
        import traceback
        st.code(traceback.format_exc())


def render_ai_diagnostic_result(result: DiagnosticResult):
    """Render AI diagnostic result in diagnostic mode using design system - RESPONSIVE."""
    # Determine data source badge
    data_source_label = "SIMULATION" if result.data_source == DataSource.SIMULATION else "REAL VEHICLE"
    data_source_variant = BadgeVariant.WARNING if result.data_source == DataSource.SIMULATION else BadgeVariant.SUCCESS
    data_source_color = DATASOURCE_SIMULATION if result.data_source == DataSource.SIMULATION else DATASOURCE_REAL

    # Header card - RESPONSIVE (flex-wrap)
    card(CardProps(
        title="AI Diagnostic Result",
        subtitle="",
        content=f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: {GAP_FIELD}; flex-wrap: wrap; gap: {SPACE_2};">
            {badge(label=data_source_label, variant=data_source_variant, key="diag_source")}
        </div>

        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: {GAP_CARD_GRID}; margin-bottom: {GAP_FIELD};">
            <div>
                <strong style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Diagnosis ID</strong><br>
                <code style="font-size: {FONT_SIZE_BODY_SM};">{result.diagnosis_id}</code>
            </div>
            <div>
                <strong style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Status</strong><br>
                <span style="text-transform: capitalize; font-size: {FONT_SIZE_BODY};">{result.diagnostic_status.value.replace('_', ' ')}</span>
            </div>
            <div>
                <strong style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Overall Severity</strong><br>
                <span style="color: {_get_severity_color_hex(result.severity)}; font-weight: 600; text-transform: uppercase; font-size: {FONT_SIZE_BODY};">
                    {result.severity.value}
                </span>
            </div>
            <div>
                <strong style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Confidence</strong><br>
                <span style="font-family: monospace; font-weight: 600; font-size: {FONT_SIZE_BODY};">{result.confidence:.0%}</span>
            </div>
            <div>
                <strong style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Data Quality</strong><br>
                <span style="text-transform: capitalize; font-size: {FONT_SIZE_BODY};">{result.data_quality.value}</span>
            </div>
        </div>

        <div style="padding: {SPACE_4}; background: {SURFACE_SECONDARY}; border-radius: {RADIUS_MD}; margin-bottom: {GAP_FIELD}; border: 1px solid {BORDER_SUBTLE};">
            <strong>Summary:</strong> {result.summary or 'No summary provided'}
        </div>
        """,
        elevated=False,
        bordered=True,
    ))

    # Primary Diagnosis
    if result.primary_diagnosis:
        pd = result.primary_diagnosis
        card(CardProps(
            title=f"Primary Diagnosis: {pd.code} - {pd.description}",
            subtitle=f"Confidence: {pd.confidence:.0%} | Severity: {pd.severity.value.upper()}",
            content="",
            elevated=False,
            bordered=True,
            class_name="primary-diagnosis-card",
        ))

        for i, cause in enumerate(pd.probable_causes):
            conf_variant = BadgeVariant.SUCCESS if cause.confidence >= 0.7 else BadgeVariant.WARNING if cause.confidence >= 0.4 else BadgeVariant.CRITICAL
            urgency_variant = BadgeVariant.CRITICAL if cause.urgency == "immediate" else BadgeVariant.WARNING if cause.urgency == "soon" else BadgeVariant.INFO if cause.urgency == "schedule" else BadgeVariant.PRIMARY

            card(CardProps(
                title=f"{i+1}. {cause.cause}",
                subtitle="",
                content=f"""
                <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY}; margin-bottom: {GAP_FIELD};">{cause.explanation}</div>

                {f'<div style="margin-bottom: {GAP_FIELD};"><strong>Supporting Evidence:</strong><ul style="margin: {SPACE_2} 0; padding-left: {SPACE_5}; font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">{"".join([f"<li>{e}</li>" for e in cause.supporting_evidence])}</ul></div>' if cause.supporting_evidence else ''}
                {f'<div style="margin-bottom: {GAP_FIELD};"><strong>Contradictory Evidence:</strong><ul style="margin: {SPACE_2} 0; padding-left: {SPACE_5}; font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">{"".join([f"<li>{e}</li>" for e in cause.contradictory_evidence])}</ul></div>' if cause.contradictory_evidence else ''}

                <div style="margin-bottom: {GAP_FIELD};"><strong>Verification Steps:</strong><ul style="margin: {SPACE_2} 0; padding-left: {SPACE_5}; font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">{"".join([f"<li>{step}</li>" for step in cause.verification_steps])}</ul></div>

                {badge(label=cause.urgency.upper(), variant=urgency_variant, key=f"pc_urg_{i}")}
                """,
                footer=badge(label=f'{cause.confidence:.0%}', variant=conf_variant, key=f"pc_conf_{i}"),
                elevated=False,
                bordered=True,
            ))

    # Secondary Diagnoses
    if result.secondary_diagnoses:
        st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)
        section_header(title="Secondary Diagnoses", description="")

        for sd in result.secondary_diagnoses:
            card(CardProps(
                title=f"{sd.code} - {sd.description}",
                subtitle=f"Confidence: {sd.confidence:.0%} | Severity: {sd.severity.value.upper()}{f' | Relation: {sd.relationship_to_primary}' if sd.relationship_to_primary else ''}",
                content="",
                elevated=False,
                bordered=True,
            ))

            for i, cause in enumerate(sd.probable_causes):
                conf_variant = BadgeVariant.SUCCESS if cause.confidence >= 0.7 else BadgeVariant.WARNING if cause.confidence >= 0.4 else BadgeVariant.CRITICAL
                urgency_variant = BadgeVariant.CRITICAL if cause.urgency == "immediate" else BadgeVariant.WARNING if cause.urgency == "soon" else BadgeVariant.INFO if cause.urgency == "schedule" else BadgeVariant.PRIMARY

                card(CardProps(
                    title=f"{i+1}. {cause.cause}",
                    subtitle="",
                    content=f"""
                    <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY}; margin-bottom: {GAP_FIELD};">{cause.explanation}</div>

                    <div style="margin-bottom: {GAP_FIELD};"><strong>Verification Steps:</strong><ul style="margin: {SPACE_2} 0; padding-left: {SPACE_5}; font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">{"".join([f"<li>{step}</li>" for step in cause.verification_steps])}</ul></div>

                    {badge(label=cause.urgency.upper(), variant=urgency_variant, key=f"sd_pc_urg_{i}")}
                    """,
                    footer=badge(label=f'{cause.confidence:.0%}', variant=conf_variant, key=f"sd_pc_conf_{i}"),
                    elevated=False,
                    bordered=True,
                ))

    # Recommended Actions
    if result.recommended_actions:
        st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)
        section_header(title="Recommended Actions", description="")

        for i, rec in enumerate(result.recommended_actions):
            safety_variant_map = {
                "safe": BadgeVariant.SUCCESS,
                "caution": BadgeVariant.WARNING,
                "professional": BadgeVariant.CRITICAL,
            }
            safety_variant = safety_variant_map.get(rec.safety_level.value, BadgeVariant.NEUTRAL)

            card(CardProps(
                title=f"{i+1}. {rec.recommendation}",
                subtitle="",
                content=f"""
                <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY}; margin-bottom: {GAP_FIELD};">{rec.rationale}</div>

                <div style="display: flex; gap: {SPACE_2}; flex-wrap: wrap; margin-bottom: {GAP_FIELD};">
                    {badge(label=rec.safety_level.value.upper(), variant=safety_variant, key=f"rec_safe_{i}")}
                    {badge(label="PROFESSIONAL REQUIRED", variant=BadgeVariant.CRITICAL, key=f"rec_prof_{i}") if rec.requires_professional else ''}
                </div>

                <div style="font-size: {FONT_SIZE_LABEL}; color: {TEXT_SECONDARY};">
                    <strong>Priority:</strong> {rec.priority}/10
                    {f' | <strong>Estimated Cost:</strong> {rec.estimated_cost_inr}' if rec.estimated_cost_inr else ''}
                </div>
                """,
                elevated=False,
                bordered=True,
            ))

    # Safety Warnings
    if result.safety_warnings:
        st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)
        alert(
            title="⚠ Safety Warnings",
            message="<ul style='margin: 0; padding-left: 1.25rem;'>" + "".join([f"<li>{warning}</li>" for warning in result.safety_warnings]) + "</ul>",
            variant=AlertVariant.CRITICAL,
            key="diag_safety_warnings"
        )

    # Missing Information
    if result.missing_information:
        st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)
        alert(
            title="Missing Information",
            message="<ul style='margin: 0; padding-left: 1.25rem;'>" + "".join([f"<li>{info}</li>" for info in result.missing_information]) + "</ul>",
            variant=AlertVariant.INFO,
            key="diag_missing_info"
        )

    # Metadata
    st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)
    card(CardProps(
        title="Metadata",
        subtitle="",
        content=f"""
        <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_SECONDARY};">
            <strong>Model:</strong> {result.model_information.get('model', 'Unknown')}<br>
            <strong>Temperature:</strong> {result.model_information.get('temperature', 'N/A')}<br>
            <strong>Max Tokens:</strong> {result.model_information.get('max_tokens', 'N/A')}<br>
            <strong>Rule Engine Findings:</strong> {', '.join(result.rule_engine_findings) if result.rule_engine_findings else 'None'}<br>
            <strong>RAG Sources:</strong> {', '.join(result.rag_sources) if result.rag_sources else 'None'}
        </div>
        """,
        elevated=False,
        bordered=True,
    ))

    # Simulation disclaimer
    if result.data_source == DataSource.SIMULATION:
        alert(
            title="⚠ Simulation Data",
            message="This diagnosis is based on simulated telemetry data and does not represent an actual diagnosis of your vehicle. Always verify with a real OBD-II scan and consult a qualified technician before any repair.",
            variant=AlertVariant.WARNING,
            key="diag_simulation_disclaimer"
        )


def _get_severity_color_hex(severity: DiagnosticSeverity) -> str:
    """Get hex color for severity level using design system tokens."""
    colors = {
        DiagnosticSeverity.CRITICAL: DIAG_CRITICAL,
        DiagnosticSeverity.MAJOR: DIAG_MAJOR,
        DiagnosticSeverity.MINOR: DIAG_MINOR,
        DiagnosticSeverity.INFO: DIAG_INFO,
        DiagnosticSeverity.UNKNOWN: STATUS_NEUTRAL,
    }
    return colors.get(severity, STATUS_NEUTRAL)


def render_chat_interface(ai, db):
    """Render the main chat interface using design system - RESPONSIVE with B1.9 accessibility."""
    # Live region for chat announcements (new messages, loading state)
    chat_live_region_id = "ai-chat-live"
    loading_live_region_id = "ai-loading-live"

    # Messages area with ARIA live region for conversation
    messages_html = _render_chat_messages()
    card_html = f"""
    <div class="chat-messages-container i20-card" style="max-height: 500px; overflow-y: auto; padding: {SPACE_4}; display: flex; flex-direction: column; gap: {GAP_FIELD};" role="log" aria-live="polite" aria-label="Conversation history" aria-atomic="false">
        {messages_html}
    </div>
    <div id="{chat_live_region_id}" class="i20-live-region i20-visually-hidden" aria-live="polite" aria-atomic="true" aria-label="Chat messages"></div>
    <div id="{loading_live_region_id}" class="i20-live-region i20-visually-hidden" aria-live="assertive" aria-atomic="true" aria-label="AI status"></div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

    # Input area - RESPONSIVE
    st.markdown(f"<div style='margin-top: {GAP_FIELD};'></div>", unsafe_allow_html=True)
    _render_chat_input(ai, db, chat_live_region_id, loading_live_region_id)


def _render_chat_messages() -> str:
    """Render chat messages as HTML string for card content with B1.9 accessibility."""
    # Load conversation history from database on first load
    if not st.session_state.ai_messages and not st.session_state.get("ai_history_loaded"):
        db = get_database()
        history = db.get_ai_conversation(st.session_state.ai_session_id)
        for msg in history:
            st.session_state.ai_messages.append({
                "role": msg["role"],
                "content": msg["content"],
                "timestamp": msg["created_at"]
            })
        st.session_state.ai_history_loaded = True

    messages_html = ""
    for i, msg in enumerate(st.session_state.ai_messages):
        messages_html += _render_message_html(msg, i)

    # Show loading indicator
    if st.session_state.ai_loading:
        messages_html += _render_loading_message_html()

    return messages_html


def _render_message_html(msg: Dict[str, Any], index: int) -> str:
    """Render a single chat message as HTML string with B1.9 accessibility."""
    is_user = msg["role"] == "user"
    avatar = "👤" if is_user else "🤖"
    avatar_bg = ACCENT_PRIMARY if is_user else ACCENT_SECONDARY

    timestamp = msg.get("timestamp", datetime.now().isoformat())
    try:
        if isinstance(timestamp, str):
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = timestamp
        time_str = dt.strftime("%H:%M")
    except:
        time_str = ""

    align_self = "flex-end" if is_user else "flex-start"
    flex_direction = "row-reverse" if is_user else "row"
    content_bg = f"linear-gradient(90deg, {ACCENT_PRIMARY}22, {ACCENT_SECONDARY}22)" if is_user else SURFACE_SECONDARY
    content_border = f"{ACCENT_PRIMARY}44" if is_user else BORDER_DEFAULT
    time_align = "left" if is_user else "right"

    role_label = "You" if is_user else "AI Assistant"
    message_id = f"msg-{index}"

    return f"""
    <article role="article" aria-label="{role_label} message" id="{message_id}" style="
        display: flex;
        gap: {SPACE_3};
        max-width: 85%;
        align-self: {align_self};
        flex-direction: {flex_direction};
        animation: fadeIn 0.3s ease;
    ">
        <div style="
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            flex-shrink: 0;
            background: {avatar_bg};
            color: {TEXT_ON_ACCENT};
        " aria-hidden="true">{avatar}</div>
        <div style="
            background: {content_bg};
            border: 1px solid {content_border};
            border-radius: {RADIUS_LG};
            padding: {SPACE_3} {SPACE_4};
            color: {TEXT_PRIMARY};
            line-height: 1.6;
        ">
            {msg["content"]}
            <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED}; margin-top: {SPACE_1}; text-align: {time_align};">
                <time datetime="{timestamp}">{time_str}</time>
            </div>
        </div>
    </article>
    """


def _render_loading_message_html() -> str:
    """Render loading indicator as HTML string with B1.9 accessibility."""
    return f"""
    <article role="status" aria-live="assertive" aria-label="AI Assistant is typing" aria-atomic="true" style="
        display: flex;
        gap: {SPACE_3};
        max-width: 85%;
        align-self: flex-start;
    ">
        <div style="
            width: 36px;
            height: 36px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
            flex-shrink: 0;
            background: {ACCENT_SECONDARY};
            color: {TEXT_ON_ACCENT};
        " aria-hidden="true">🤖</div>
        <div style="
            background: {SURFACE_SECONDARY};
            border: 1px solid {BORDER_DEFAULT};
            border-radius: {RADIUS_LG};
            padding: {SPACE_3} {SPACE_4};
            color: {TEXT_SECONDARY};
            line-height: 1.6;
        ">
            <span style="display: inline-block; animation: pulse 1.5s infinite;">●</span>
            <span style="display: inline-block; animation: pulse 1.5s infinite 0.2s;">●</span>
            <span style="display: inline-block; animation: pulse 1.5s infinite 0.4s;">●</span>
            <span class="i20-visually-hidden">AI Assistant is typing</span>
            <style>@keyframes pulse {{ 0%, 100% {{ opacity: 0.3; }} 50% {{ opacity: 1; }} }}</style>
        </div>
    </article>
    """


def _render_chat_input(ai, db, chat_live_region_id: str = "ai-chat-live", loading_live_region_id: str = "ai-loading-live"):
    """Render chat input area using design system form - RESPONSIVE with B1.9 accessibility."""
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = text_input(
            label="Message",
            placeholder="Ask about diagnostics, maintenance, vehicle systems...",
            key="chat_input",
            help_text="Press Enter to send, Shift+Enter for new line",
            required=True,
        )

        col1, col2, col3 = st.columns([1, 1, 4], gap="small")
        with col1:
            send_clicked = button_primary(
                "Send",
                key="chat_send",
                use_container_width=True,
                disabled=st.session_state.ai_loading,
                type="submit"
            )
        with col2:
            clear_clicked = button_secondary(
                "Clear",
                key="chat_clear",
                use_container_width=True,
                type="submit"
            )

    if send_clicked and user_input.strip():
        handle_user_message(ai, db, user_input.strip(), chat_live_region_id, loading_live_region_id)

    if clear_clicked:
        clear_conversation(db)


def handle_user_message(ai, db, user_input: str, chat_live_region_id: str = "ai-chat-live", loading_live_region_id: str = "ai-loading-live"):
    """Handle user message and get AI response with B1.9 live region announcement."""
    # Add user message to history
    user_msg = {
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    }
    st.session_state.ai_messages.append(user_msg)

    # Save to database
    db.add_ai_message(st.session_state.ai_session_id, "user", user_input)

    # Announce user message sent via live region (B1.9)
    announce_script = f'''
    <script>
    (function() {{
        const region = document.getElementById('{chat_live_region_id}');
        if (region) {{
            region.textContent = 'Message sent. Waiting for AI response...';
        }}
    }})();
    </script>
    '''
    st.markdown(announce_script, unsafe_allow_html=True)

    # Set loading state
    st.session_state.ai_loading = True

    # Announce loading state via assertive live region (B1.9)
    loading_announce_script = f'''
    <script>
    (function() {{
        const region = document.getElementById('{loading_live_region_id}');
        if (region) {{
            region.textContent = 'AI Assistant is typing';
        }}
    }})();
    </script>
    '''
    st.markdown(loading_announce_script, unsafe_allow_html=True)

    st.rerun()


def get_ai_response(ai, db, chat_live_region_id: str = "ai-chat-live", loading_live_region_id: str = "ai-loading-live"):
    """Get AI response (called after rerun when loading is True)."""
    if not st.session_state.ai_loading:
        return

    try:
        # Get vehicle context from OBD if simulation running
        vehicle_context = None
        try:
            from services import get_obd_service
            obd = get_obd_service()
            readings = obd.get_all_readings()
            if readings:
                vehicle_context = {k: v.value for k, v in readings.items()}
        except:
            pass

        # Build conversation history
        history = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.ai_messages[:-1]  # Exclude current user message
        ]

        # Create context with vehicle data
        messages = ai.create_conversation_context(
            user_message=st.session_state.ai_messages[-1]["content"],
            history=[type('obj', (object,), m) for m in history],
            vehicle_context=vehicle_context
        )

        # Get AI response
        response = ai.chat_completion(messages)

        # Add assistant message
        assistant_msg = {
            "role": "assistant",
            "content": response.content,
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.ai_messages.append(assistant_msg)

        # Save to database
        db.add_ai_message(
            st.session_state.ai_session_id,
            "assistant",
            response.content,
            model=response.model,
            tokens_used=response.usage.get("total_tokens", 0)
        )

    except AIServiceError as e:
        error_msg = {
            "role": "assistant",
            "content": f"❌ **Error**: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.ai_messages.append(error_msg)
    except Exception as e:
        error_msg = {
            "role": "assistant",
            "content": f"❌ **Unexpected error**: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
        st.session_state.ai_messages.append(error_msg)
    finally:
        st.session_state.ai_loading = False

        # Clear loading announcement
        clear_loading_script = f'''
        <script>
        (function() {{
            const region = document.getElementById('{loading_live_region_id}');
            if (region) {{
                region.textContent = '';
            }}
        }})();
        </script>
        '''
        st.markdown(clear_loading_script, unsafe_allow_html=True)

        # Announce AI response to live region
        last_msg = st.session_state.ai_messages[-1].get("content", "")
        if isinstance(last_msg, str) and "Error" not in last_msg:
            announce_script = f'''
            <script>
            (function() {{
                const region = document.getElementById('{chat_live_region_id}');
                if (region) {{
                    region.textContent = 'AI Assistant responded';
                }}
            }})();
            </script>
            '''
            st.markdown(announce_script, unsafe_allow_html=True)

        st.rerun()


def clear_conversation(db):
    """Clear conversation history."""
    db.clear_ai_conversation(st.session_state.ai_session_id)
    st.session_state.ai_messages = []
    st.session_state.ai_session_id = str(uuid.uuid4())[:8]
    st.session_state.ai_history_loaded = False
    st.rerun()


def render_ai_sidebar(ai, db):
    """Render AI sidebar with model info and quick prompts using design system - RESPONSIVE."""
    # Model info panel
    card(CardProps(
        title="Model Information",
        subtitle="",
        content=_render_model_info(ai),
        elevated=False,
        bordered=True,
    ))

    # Refresh models button - RESPONSIVE
    if button_secondary("🔄 Refresh Models", key="sidebar_refresh_models", use_container_width=True):
        ai.get_available_models(force_refresh=True)
        st.session_state.ai_status = "checking"
        st.rerun()

    st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # Quick prompts panel - RESPONSIVE using AUTO_FIT_CARD_CSS
    card(CardProps(
        title="Quick Prompts",
        subtitle="",
        content="",
        elevated=False,
        bordered=True,
    ))

    # Render quick prompt buttons after the card (they need to be Streamlit buttons)
    quick_prompts = [
        ("🔧", "Explain P0300 code", "What does DTC P0300 mean and what are the possible causes?"),
        ("🌡️", "Coolant temp high", "My coolant temperature is reading 110°C. What should I check?"),
        ("⛽", "Fuel trim interpretation", "What do positive vs negative fuel trim values indicate?"),
        ("🔋", "Battery voltage low", "Battery voltage shows 12.2V with engine running. Is this normal?"),
        ("📊", "Engine load meaning", "What does calculated engine load percentage tell me?"),
        ("🛠️", "Maintenance schedule", "When should I change spark plugs on a 2023 i20 1.2L petrol?"),
    ]

    st.markdown(AUTO_FIT_CARD_CSS, unsafe_allow_html=True)
    st.markdown('<div class="i20-grid-auto-fit">', unsafe_allow_html=True)

    for icon, label, prompt in quick_prompts:
        if button_ghost(f"{icon} {label}", key=f"quick_{label.replace(' ', '_')}", use_container_width=True):
            # Add as user message and trigger AI response
            user_msg = {
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().isoformat()
            }
            st.session_state.ai_messages.append(user_msg)
            db.add_ai_message(st.session_state.ai_session_id, "user", prompt)

            # Announce user message sent via live region (B1.9)
            announce_script = f'''
            <script>
            (function() {{
                const region = document.getElementById('ai-chat-live');
                if (region) {{
                    region.textContent = 'Message sent. Waiting for AI response...';
                }}
            }})();
            </script>
            '''
            st.markdown(announce_script, unsafe_allow_html=True)

            # Announce loading state via assertive live region (B1.9)
            loading_announce_script = f'''
            <script>
            (function() {{
                const region = document.getElementById('ai-loading-live');
                if (region) {{
                    region.textContent = 'AI Assistant is typing';
                }}
            }})();
            </script>
            '''
            st.markdown(loading_announce_script, unsafe_allow_html=True)

            st.session_state.ai_loading = True
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"<div style='margin-top: {GAP_SECTION};'></div>", unsafe_allow_html=True)

    # Conversation management
    card(CardProps(
        title="Conversation",
        subtitle="",
        content=f"""
        <div style="font-size: {FONT_SIZE_CAPTION}; color: {TEXT_MUTED};">
            <div>Session: {st.session_state.ai_session_id}</div>
            <div>Messages: {len(st.session_state.ai_messages)}</div>
        </div>
        """,
        footer="",
        elevated=False,
        bordered=True,
    ))

    if button_danger("🗑️ Clear Conversation", key="sidebar_clear_conv", use_container_width=True):
        clear_conversation(db)


def _render_model_info(ai) -> str:
    """Render model info as HTML string."""
    status = ai.get_system_status()

    return f"""
    <div style="display: flex; flex-direction: column; gap: {SPACE_3};">
        <div>
            <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Configured Model</div>
            <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{status['configured_model']}</div>
        </div>
        <div>
            <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Temperature</div>
            <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{status['temperature']}</div>
        </div>
        <div>
            <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Timeout</div>
            <div style="font-size: {FONT_SIZE_BODY}; color: {TEXT_PRIMARY};">{status['timeout']}s</div>
        </div>
        <div>
            <div style="font-size: {FONT_SIZE_LABEL}; font-weight: {BUTTON_FONT_WEIGHT}; color: {TEXT_SECONDARY}; text-transform: uppercase; letter-spacing: 0.05em;">Available Models</div>
            <div style="font-size: {FONT_SIZE_BODY_SM}; color: {TEXT_SECONDARY};">{', '.join(status['available_models']) if status['available_models'] else 'None'}</div>
        </div>
    </div>
    """


# Check for AI response after rerun
def check_ai_response():
    """Check if we need to get AI response (call from main app)."""
    if st.session_state.get("ai_loading", False):
        ai = get_ai_service()
        db = get_database()
        get_ai_response(ai, db, "ai-chat-live", "ai-loading-live")