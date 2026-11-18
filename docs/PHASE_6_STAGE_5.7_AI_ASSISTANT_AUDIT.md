# Phase 6 Stage 5.7: AI Assistant Page — Read-Only Audit

**Date:** 2026-11-17  
**Status:** AUDIT COMPLETE — Ready for Implementation  
**Target:** `modules/ai_assistant.py` (915 lines)

---

## 1. Current Implementation Overview

### File Structure
```
modules/ai_assistant.py — 915 lines
├── get_ai_css() — ~200 lines of embedded custom CSS
├── render_ai_assistant() — Main entry point
├── render_ai_header() — Header with LM Studio status
├── render_mode_selector() — Chat/Diagnostic mode toggle
├── render_chat_interface() — Full chat UI (messages, input, form)
├── render_diagnostic_interface() — DTC/symptom analysis UI
├── run_diagnostic_analysis() — Calls DiagnosticEngine
├── render_ai_diagnostic_result() — ~200 lines of inline HTML for results
├── render_message() — Individual message bubbles
├── render_loading_message() — Typing indicator
├── handle_user_message() — User message processing
├── get_ai_response() — AI response handling (async via rerun)
├── clear_conversation() — History clearing
├── render_ai_sidebar() — Model info, quick prompts, session mgmt
└── check_ai_response() — Called from app.py for async responses
```

### Two Modes
| Mode | Layout | Key Features |
|------|--------|--------------|
| **Chat** | 3:1 split (chat + sidebar) | Conversation history, quick prompts, model info, session management |
| **Diagnostic** | Full width | DTC input, symptom input, full vehicle scan, structured AI diagnosis results |

---

## 2. Custom CSS Audit (~200 lines to Remove)

### `get_ai_css()` — Lines 60-249

**CSS Classes Defined:**
| Class | Purpose | Design System Replacement |
|-------|---------|---------------------------|
| `.ai-header` | Page header with gradient | `page_header()` + tokens |
| `.ai-title` | Title styling | `page_header()` |
| `.ai-status-badge` | Connection status pill | `badge()` with `BadgeVariant` |
| `.ai-status-online/offline/checking` | Status variants | `badge()` variants (SUCCESS/WARNING/CRITICAL) |
| `.chat-container` | Chat area wrapper | `card()` or container |
| `.chat-messages` | Message list flex container | CSS Grid/flex via tokens |
| `.message` | Message bubble wrapper | Custom HTML with tokens |
| `.message-user/assistant` | Alignment variants | Token-based styling |
| `.message-avatar` | Avatar circles | Inline token styling |
| `.avatar-user/assistant` | Avatar colors | `ACCENT_PRIMARY` / `ACCENT_SECONDARY` |
| `.message-content` | Message text bubble | `card_simple()` or tokens |
| `.message-time` | Timestamps | `FONT_SIZE_CAPTION` + `TEXT_MUTED` |
| `.chat-input-area` | Input footer | `card()` footer or tokens |
| `.stTextArea` overrides | Textarea styling | `text_input()` component |
| `.ai-sidebar-panel` | Sidebar card | `card()` |
| `.ai-sidebar-title` | Sidebar section header | `FONT_SIZE_LABEL` + `TEXT_SECONDARY` |
| `.model-info` | Model detail rows | Token styling |
| `.model-label` | Model field labels | `FONT_SIZE_LABEL` + `FONT_WEIGHT_LABEL` |
| `.quick-prompts` | Prompt button column | `button_ghost()` in column |
| `.quick-prompt-btn` | Prompt buttons | `button_ghost()` |
| `.clear-btn` | Clear conversation | `button_danger()` or `button_ghost()` |

**Inline Styles in Render Functions (Additional ~100 lines):**
- `render_ai_diagnostic_result()` — Lines 431-627: ~200 lines of inline HTML with hardcoded colors
- `render_message()` — Lines 700-725: Message bubble HTML
- `render_loading_message()` — Lines 728-740: Loading animation
- `render_ai_header()` — Lines 252-310: Header HTML
- `render_mode_selector()` — Lines 313-345: Button styling
- `render_diagnostic_interface()` — Lines 348-407: Input forms, empty state
- `render_ai_sidebar()` — Lines 839-911: Sidebar panels

---

## 3. Session State Keys (Must Preserve)

### AI Assistant Specific Keys (Defined in `render_ai_assistant()` lines 24-35)
| Key | Type | Purpose | Preservation |
|-----|------|---------|--------------|
| `ai_session_id` | str | Conversation session UUID | ✅ Keep |
| `ai_messages` | List[Dict] | Chat message history | ✅ Keep |
| `ai_loading` | bool | AI response pending flag | ✅ Keep |
| `ai_mode` | str | "chat" or "diagnostic" | ✅ Keep |
| `ai_diagnostic_result` | DiagnosticResult | Last diagnostic result | ✅ Keep |
| `ai_status` | str | "online"/"offline"/"checking" | ✅ Keep |
| `ai_models` | List[ModelInfo] | Available LM Studio models | ✅ Keep |
| `ai_model_available` | bool | Configured model loaded | ✅ Keep |
| `ai_history_loaded` | bool | DB history loaded flag | ✅ Keep |

### Shared Keys Used (34 Total — Do Not Rename/Delete)
| Category | Keys |
|----------|------|
| Navigation | `current_page`, `sidebar_collapsed` |
| Dashboard | `dash_scenario`, `dash_recording`, `dash_session_id`, `dash_refresh_rate`, `dash_gauge_layout` |
| Diagnostics | `diag_last_scan`, `diag_selected_dtc`, `diag_ai_result`, `diag_rule_result`, `diag_report_preview`, `diag_history_filter`, `diag_auto_refresh`, `diag_simulate_mode`, `diag_sim_scenario`, `diag_view_mode` |
| Performance | `perf_active_session`, `perf_recording`, `perf_selected_sessions`, `perf_compare_mode`, `perf_chart_range`, `perf_stat_view` |
| Maintenance | `maint_filter_status`, `maint_filter_category`, `maint_sort_by`, `maint_edit_mode`, `maint_edit_record_id`, `maint_confirm_delete` |
| Vehicle Profile | Uses shared keys only |
| AI Assistant | Uses shared keys only |
| OBD Connection | Uses shared keys only |
| Reports | Uses shared keys only |
| Settings | Uses shared keys only |

---

## 4. Backend Service Integrations (Must Preserve)

| Service | Methods Used | Purpose |
|---------|--------------|---------|
| **AIService** (`services/ai_service.py`) | `check_connection()`, `get_available_models()`, `is_model_available()`, `chat_completion()`, `create_conversation_context()`, `get_system_status()` | LM Studio communication, chat, model management |
| **DatabaseService** (`services/database.py`) | `get_ai_conversation()`, `add_ai_message()`, `clear_ai_conversation()` | Conversation persistence |
| **DiagnosticEngine** (`services/diagnostic_engine.py`) | `run_diagnosis()` | Structured AI diagnosis from DTCs/symptoms |
| **OBDService** (`services/obd_service.py`) | `get_all_readings()`, `scan_dtcs()` | Vehicle context for chat, DTC scanning |

### AIService Key Capabilities
- **Structured Output**: `structured_completion()` with Pydantic validation for diagnostic JSON
- **Streaming**: `chat_completion_stream()` for real-time responses
- **Vehicle Context**: `create_conversation_context()` injects live telemetry
- **System Prompt**: `AI_SYSTEM_PROMPT` from config (automotive specialist)

### DiagnosticEngine Integration
- Called via `run_diagnostic_analysis()` in diagnostic mode
- Uses `DiagnosticContextBuilder` to gather: vehicle profile, sensor readings, DTCs, freeze frame, telemetry trends, diagnostic history, knowledge base passages, rule engine findings
- Returns `DiagnosticResult` (Pydantic model with primary/secondary diagnoses, probable causes, recommendations, safety warnings)

---

## 5. Design System Components Available

### Component Primitives (`components/ui/components.py`)
| Component | Status | Key Features |
|-----------|--------|--------------|
| **Button** | ✅ | `button_primary()`, `button_secondary()`, `button_ghost()`, `button_danger()` with variants/sizes |
| **Badge** | ✅ | `BadgeVariant`: SUCCESS, WARNING, CRITICAL, INFO, NEUTRAL, PRIMARY, SECONDARY |
| **Alert** | ✅ | `AlertVariant`: SUCCESS, WARNING, CRITICAL, INFO; dismissible |
| **Card** | ✅ | `card()`, `card_simple()` with title, subtitle, content, footer, elevated |
| **Form** | ✅ | `text_input()`, `selectbox()` with labels, help, error, required, disabled |
| **Table** | ✅ | `table()` with columns, selection, sorting, empty state |
| **EmptyState** | ✅ | `empty_state()` with icon, title, message, action button |
| **Loading** | ✅ | `skeleton()`, `skeleton_text()`, `skeleton_card()`, `spinner()`, `loading_overlay()` |
| **Wizard** | ✅ | Multi-step with progress indicator |
| **Sidebar** | ✅ | Navigation, vehicle info, status indicators |
| **TopBar** | ✅ | Breadcrumbs, page title, actions, status indicators |

### Layout Helpers (`components/ui/layout.py`)
| Helper | Purpose |
|--------|---------|
| `page_header()` | Consistent page title with icon/subtitle |
| `section_header()` | Section titles with optional action |
| `card_container()` | Wrapper for card content |
| `grid_container()` | Responsive grids (gauge, metric, chart, form, auto-fit) |
| `AUTO_FIT_CARD_CSS` | `minmax(280px, 1fr)` responsive card grid |
| `AUTO_FIT_METRIC_CSS` | `minmax(240px, 1fr)` responsive metric grid |
| `responsive_container()` | Max-width centered container |
| `status_indicator()` | Top bar status dots |
| `visually_hidden()` | Screen-reader only content |

### Design Tokens (`components/ui/tokens.py`) — 53 Color Tokens
| Category | Tokens |
|----------|--------|
| **Surface** | `SURFACE_APP`, `SURFACE_PRIMARY`, `SURFACE_SECONDARY`, `SURFACE_ELEVATED`, `SURFACE_INTERACTIVE` |
| **Text** | `TEXT_PRIMARY`, `TEXT_SECONDARY`, `TEXT_MUTED`, `TEXT_INVERSE`, `TEXT_LINK`, `TEXT_ON_ACCENT` |
| **Border** | `BORDER_DEFAULT`, `BORDER_SUBTLE`, `BORDER_STRONG`, `BORDER_FOCUS`, `BORDER_SEPARATOR` |
| **Accent** | `ACCENT_PRIMARY` (#00b4d8), `ACCENT_SECONDARY` (#9b59b6), hover/active variants |
| **Status** | `STATUS_SUCCESS` (#2ecc71), `STATUS_WARNING` (#f39c12), `STATUS_CRITICAL` (#e74c3c), `STATUS_INFO` (#00b4d8), `STATUS_NEUTRAL` (#9aa3ad) |
| **Diagnostic** | `DIAG_CRITICAL`, `DIAG_MAJOR`, `DIAG_MINOR`, `DIAG_INFO` |
| **Data Source** | `DATASOURCE_REAL`, `DATASOURCE_SIMULATION`, `DATASOURCE_AI` |
| **Chart Series** | `SERIES_1`-`SERIES_5` (CVD-safe fixed order) |

### Typography (16 tokens)
| Token | Value | Usage |
|-------|-------|-------|
| `FONT_SIZE_DISPLAY` | 3rem | Hero |
| `FONT_SIZE_H1` | 2rem | Page title |
| `FONT_SIZE_H2` | 1.5rem | Major section |
| `FONT_SIZE_H3` | 1.25rem | Subsection |
| `FONT_SIZE_H4` | 1rem | Card heading |
| `FONT_SIZE_BODY` | 0.875rem | Standard content |
| `FONT_SIZE_BODY_SM` | 0.8125rem | Secondary |
| `FONT_SIZE_LABEL` | 0.75rem | Form labels |
| `FONT_SIZE_CAPTION` | 0.6875rem | Metadata, timestamps |
| `FONT_SIZE_CODE` | 0.8125rem | DTC codes, PIDs, VIN |
| `FONT_WEIGHT_LABEL` | 500 | Labels |
| `FONT_WEIGHT_BODY` | 400 | Body text |
| `BUTTON_FONT_WEIGHT` | 500 | Buttons |
| `BADGE_FONT_WEIGHT` | 600 | Badges |

### Spacing (12 base + 9 semantic aliases)
| Alias | Value | Usage |
|-------|-------|-------|
| `GAP_INLINE` | 8px | Icon+text, button content |
| `GAP_FIELD` | 16px | Form field vertical |
| `GAP_CARD_GRID` | 20px | Card grid gaps |
| `GAP_SECTION` | 24px | Section gaps |
| `GAP_PAGE` | 32px | Page header to content |
| `PADDING_PAGE` | 24px | Page horizontal padding |
| `PADDING_CARD` | 16px | Card internal padding |

### Radius (7 tokens)
| Token | Value | Usage |
|-------|-------|-------|
| `RADIUS_SM` | 4px | Inputs, badges, buttons |
| `RADIUS_MD` | 8px | Standard cards |
| `RADIUS_LG` | 12px | Large cards, wizard |
| `RADIUS_PILL` | 9999px | Badges, pills |
| `RADIUS_CIRCLE` | 50% | Avatars, indicators |

---

## 6. Visual/UX Inconsistencies to Fix

### Current Issues
| Issue | Current | Target (Design System) |
|-------|---------|------------------------|
| **Header** | Custom gradient CSS, inline styles | `page_header()` + `badge()` for status |
| **Mode Selector** | Native `st.button` with type primary/secondary | Design system `button_primary()`/`button_secondary()` with consistent styling |
| **Chat Container** | Fixed 600px height, custom flex CSS | Responsive card with `card()` or container |
| **Message Bubbles** | Inline HTML with hardcoded colors | Token-based colors, consistent radius (`RADIUS_MD`), shadow (`SHADOW_SM`) |
| **Avatars** | Hardcoded blue/purple | `ACCENT_PRIMARY` / `ACCENT_SECONDARY` tokens |
| **Timestamps** | Inline styles | `FONT_SIZE_CAPTION` + `TEXT_MUTED` |
| **Textarea** | `st.text_area` with CSS overrides | `text_input()` component (or styled native) |
| **Sidebar Panels** | Custom `.ai-sidebar-panel` CSS | `card()` component |
| **Quick Prompts** | Custom button CSS | `button_ghost()` in column layout |
| **Model Info** | Inline HTML table | `card()` with structured content |
| **Diagnostic Input** | Native `st.text_input`/`st.text_area` | `text_input()` component |
| **Diagnostic Results** | ~200 lines inline HTML with hardcoded colors | Structured `card()` + `badge()` + tokens |
| **Severity Badges** | Inline style with hex colors | `badge()` with `BadgeVariant` mapping |
| **Confidence Badges** | Inline style with rgba | `badge()` variants |
| **Urgency Badges** | Inline style with hex | `badge()` variants |
| **Safety Level Badges** | Inline style | `badge()` variants |
| **Data Source Banner** | Inline HTML | `alert()` with `AlertVariant.WARNING` |
| **Simulation Disclaimer** | Inline HTML | `alert()` or `card()` with warning styling |
| **Empty States** | Inline HTML | `empty_state()` component |
| **Loading Indicator** | Custom pulse animation | `spinner()` or `skeleton_text()` |
| **Responsive** | Fixed columns, no breakpoints | `AUTO_FIT_CARD_CSS`, responsive grids |
| **Accessibility** | Limited ARIA, color-only status | Semantic HTML, ARIA labels, focus rings (`BORDER_FOCUS`), dual encoding |

### Color Mapping (Hardcoded → Tokens)
| Hardcoded | Token | Usage |
|-----------|-------|-------|
| `#00b4d8` | `ACCENT_PRIMARY` | Primary actions, links, AI accent |
| `#9b59b6` | `ACCENT_SECONDARY` | AI/assistant features |
| `#2ecc71` | `STATUS_SUCCESS` / `DATASOURCE_REAL` | Connected, healthy, real data |
| `#f39c12` | `STATUS_WARNING` / `DATASOURCE_SIMULATION` | Simulation mode, warnings |
| `#e74c3c` | `STATUS_CRITICAL` / `DIAG_CRITICAL` | Errors, critical severity |
| `#3498db` | `DIAG_MINOR` | Minor severity |
| `#9b59b6` | `DIAG_INFO` / `DATASOURCE_AI` | Info severity, AI content |
| `#9aa3ad` | `STATUS_NEUTRAL` / `TEXT_SECONDARY` | Disconnected, muted text |
| `rgba(46,204,113,0.15)` | `STATUS_SUCCESS + opacity` | Success badge backgrounds |
| `rgba(231,76,60,0.15)` | `STATUS_CRITICAL + opacity` | Error badge backgrounds |
| `rgba(243,156,18,0.15)` | `STATUS_WARNING + opacity` | Warning badge backgrounds |

---

## 7. Page Blueprint (Target Layout)

### Chat Mode (3:1 Split)
```
┌─────────────────────────────────────────────────────────────────┐
│ Top Bar (Global Shell)                                           │
├─────────────────────────────────────────────────────────────────┤
│ Page Header: "AI Assistant"  🤖  "Local AI chat & diagnosis"    │
├──────────────────┬──────────────────────────────────────────────┤
│                  │                                              │
│   CHAT AREA      │   SIDEBAR (300px)                           │
│   (75%)          │                                              │
│ ┌──────────────┐ │  ┌────────────────────────────────────────┐  │
│ │ Header       │ │  │ Model Information (card)               │  │
│ │ Mode Toggle  │ │  │ ┌────────────────────────────────────┐ │  │
│ │ (button_grp) │ │  │ │ Model: qwen2.5-3b-instruct         │ │  │
│ └──────────────┘ │  │ │ Temp: 0.7 | Timeout: 30s           │ │  │
│ ┌──────────────┐ │  │ │ Status: ● Connected (badge)        │ │  │
│ │ Messages     │ │  │ │ [Refresh Models] (button_ghost)    │ │  │
│ │ (card, flex) │ │  │ └────────────────────────────────────┘ │  │
│ │ - User msg   │ │  │  ┌────────────────────────────────────┐ │  │
│ │ - Asst msg   │ │  │ │ Quick Prompts (card)               │  │  │
│ │ - Loading    │ │  │ │ [🔧 Explain P0300] (btn_ghost)     │  │  │
│ └──────────────┘ │  │ │ [🌡️ Coolant temp high] (btn_ghost) │  │  │
│ ┌──────────────┐ │  │ │ [⛽ Fuel trim...] (btn_ghost)       │  │  │
│ │ Input Form   │ │  │ │ ...                                │  │  │
│ │ [textarea]   │ │  │ └────────────────────────────────────┘ │  │
│ │ [Send] [Clear]│ │  │  ┌────────────────────────────────────┐ │  │
│ └──────────────┘ │  │ │ Conversation (card)                │  │  │
│                  │  │ │ Session: abc123 | Messages: 12     │  │  │
│                  │  │ │ [🗑️ Clear Conversation] (btn_danger)│  │  │
│                  │  │ └────────────────────────────────────┘ │  │
└──────────────────┴──────────────────────────────────────────────┘
```

### Diagnostic Mode (Full Width)
```
┌─────────────────────────────────────────────────────────────────┐
│ Top Bar (Global Shell)                                           │
├─────────────────────────────────────────────────────────────────┤
│ Page Header: "AI Assistant"  🤖  "Local AI chat & diagnosis"    │
├─────────────────────────────────────────────────────────────────┤
│ Mode Toggle: [💬 Chat] [🔍 Diagnostic] (button group)           │
├─────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Run Diagnostic Analysis (section_header)                    │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ DTC Input: [P0300, P0171...]          [🧠 Analyze] (btn_pri)│ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Symptoms: [textarea...]               [🔍 Analyze] (btn_pri)│ │
│ │                                        [🚗 Full Scan] (btn_sec)│ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Results Area:                                                │ │
│ │ ┌─────────────────────────────────────────────────────────┐ │ │
│ │ │ AI Diagnostic Result (card)                              │ │ │
│ │ │ Header: "AI Diagnostic Result"  [SIMULATION] (badge)    │ │ │
│ │ │ Stats Grid (AUTO_FIT_METRIC_CSS):                        │ │ │
│ │ │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────┐ │ │ │
│ │ │ │ Total   │ │Critical │ │ Major   │ │ Minor   │ │ Info│ │ │ │
│ │ │ │ DTCs    │ │ DTCs    │ │ DTCs    │ │ DTCs    │ │ DTCs│ │ │ │
│ │ │ └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────┘ │ │ │
│ │ │ Summary Card                                               │ │ │
│ │ │ Primary Diagnosis (card with border-left ACCENT_PRIMARY)  │ │ │
│ │ │   Code - Description (confidence badge, severity badge)   │ │ │
│ │ │   Probable Causes (card each):                             │ │ │
│ │ │   1. Cause (confidence badge)                              │ │ │
│ │ │      Explanation                                           │ │ │
│ │ │      Supporting Evidence (list)                            │ │ │
│ │ │      Contradictory Evidence (list)                         │ │ │
│ │ │      Verification Steps (numbered)                         │ │ │
│ │ │      Urgency badge (CRITICAL/MAJOR/MINOR/INFO)            │ │ │
│ │ │ Secondary Diagnoses (similar structure)                    │ │ │
│ │ │ Recommended Actions (card each):                           │ │ │
│ │ │   Priority badge + Safety badge + Professional badge       │ │ │
│ │ │ Safety Warnings (alert CRITICAL)                           │ │ │
│ │ │ Missing Information (alert INFO)                           │ │ │
│ │ │ Metadata (caption): Model, Temp, Tokens, Rules, RAG       │ │ │
│ │ │ Simulation Disclaimer (alert WARNING)                      │ │ │
│ │ └─────────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 8. Migration Strategy

### Phase 0: Complete (This Audit)
- ✅ Read all implementation files
- ✅ Catalog custom CSS (~300 lines total)
- ✅ Map session state keys (9 AI-specific + 34 shared)
- ✅ Document backend integrations (4 services)
- ✅ Inventory design system components available

### Phase 1: Design System Integration
1. **Imports**: Replace `from config import THEME` with `from components.ui import` tokens, components, layout
2. **CSS Removal**: Delete `get_ai_css()` entirely (~200 lines)
3. **Global Styles**: Ensure `inject_global_css()` called via shell (already done in Stage 4)

### Phase 2: Chat Mode Redesign
1. **Header**: `page_header()` + mode toggle with `button_primary()`/`button_secondary()`
2. **Chat Container**: `card()` with flex layout using tokens
3. **Messages**: Custom render using `card_simple()` or token-styled HTML
4. **Input**: `text_input()` component + `button_primary()`/`button_secondary()`
5. **Sidebar**: `card()` panels with `button_ghost()` for quick prompts, `button_danger()` for clear

### Phase 3: Diagnostic Mode Redesign
1. **Input Section**: `section_header()` + `text_input()` for DTC/symptoms + action buttons
2. **Results**: `card()` wrapper with structured content
3. **Stat Grid**: `AUTO_FIT_METRIC_CSS` with `card_simple()` for each stat
4. **Diagnoses**: `card()` per diagnosis with `badge()` for confidence/severity/urgency
5. **Probable Causes**: `card()` each with structured evidence lists
6. **Recommendations**: `card()` with priority/safety/professional badges
7. **Warnings/Missing**: `alert()` components
8. **Metadata**: `FONT_SIZE_CAPTION` + `TEXT_SECONDARY`
9. **Simulation Disclaimer**: `alert(AlertVariant.WARNING)`

### Phase 4: Shared Components
- **Message Bubbles**: Reusable render function using tokens
- **Loading States**: `skeleton_text()` or `spinner()`
- **Empty States**: `empty_state()` component
- **Status Indicators**: `badge()` with semantic variants

### Phase 5: Verification
- [ ] All 415 tests pass
- [ ] Chat mode: send/receive messages, history load/save, quick prompts
- [ ] Diagnostic mode: DTC analysis, symptom analysis, full scan
- [ ] LM Studio connection status updates
- [ ] Model refresh works
- [ ] Conversation clear works
- [ ] Session persistence across reruns
- [ ] Responsive at all breakpoints
- [ ] Dark theme only (no light theme regression)
- [ ] WCAG 2.1 AA contrast (verify token combinations)

---

## 9. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking async AI response flow (`get_ai_response` + `check_ai_response`) | Medium | High | Preserve exact session state logic; only change rendering |
| Diagnostic result rendering complexity (~200 lines) | High | High | Build incrementally; test each section |
| Quick prompt buttons triggering rerun | Low | Medium | Verify `st.rerun()` pattern preserved |
| Streamlit form + custom button interaction | Medium | Medium | Use `st.form` for input, design system buttons for actions |
| Sidebar state persistence | Low | Low | Shell handles sidebar; page only renders content |

---

## 10. File References

### Primary Files to Modify
- `modules/ai_assistant.py` — Main target (915 lines → target ~700 lines)

### Design System Imports Needed
```python
from components.ui import (
    # Tokens
    ACCENT_PRIMARY, ACCENT_SECONDARY,
    STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, STATUS_NEUTRAL,
    DIAG_CRITICAL, DIAG_MAJOR, DIAG_MINOR, DIAG_INFO,
    DATASOURCE_REAL, DATASOURCE_SIMULATION, DATASOURCE_AI,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED,
    SURFACE_PRIMARY, SURFACE_SECONDARY,
    BORDER_DEFAULT, BORDER_SUBTLE, BORDER_FOCUS,
    FONT_SIZE_H1, FONT_SIZE_H2, FONT_SIZE_H3, FONT_SIZE_H4,
    FONT_SIZE_BODY, FONT_SIZE_BODY_SM, FONT_SIZE_LABEL, FONT_SIZE_CAPTION, FONT_SIZE_CODE,
    FONT_WEIGHT_LABEL, FONT_WEIGHT_BODY, BUTTON_FONT_WEIGHT,
    SPACE_1, SPACE_2, SPACE_3, SPACE_4, SPACE_5, SPACE_6,
    GAP_INLINE, GAP_FIELD, GAP_CARD_GRID, GAP_SECTION, PADDING_PAGE,
    RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL,
    SHADOW_SM, SHADOW_MD, SHADOW_FOCUS,
    TRANSITION_FAST, TRANSITION_NORMAL,
    # Components
    ButtonVariant, ButtonSize, ButtonProps, button, button_primary, button_secondary, button_ghost, button_danger,
    BadgeVariant, badge,
    AlertVariant, alert,
    CardProps, card, card_simple,
    text_input, selectbox,
    EmptyStateProps, empty_state,
    skeleton_text, spinner,
    # Layout
    page_header, section_header, AUTO_FIT_CARD_CSS, AUTO_FIT_METRIC_CSS,
    responsive_container, visually_hidden,
)
```

### Backend Imports (Preserve)
```python
from config import AI_SYSTEM_PROMPT
from services import get_ai_service, get_database, get_diagnostic_engine, AIServiceError
from services.diagnostic_models import DiagnosticResult, DiagnosticSeverity, DataSource
```

---

## 11. Success Criteria

| Criterion | Target |
|-----------|--------|
| **Custom CSS Lines** | 0 (from ~300) |
| **Design System Component Usages** | 30+ |
| **Token References** | 50+ |
| **Test Coverage** | 415/415 passing |
| **Session State Keys** | All 9 AI-specific + 34 shared preserved |
| **Backend Integrations** | All 4 services fully functional |
| **Responsive Breakpoints** | Mobile, Tablet, Laptop, Desktop |
| **Accessibility** | WCAG 2.1 AA (contrast, focus, ARIA) |
| **Theme** | Dark only (no light theme) |

---

## 12. Next Steps

1. **Begin Phase 1**: Remove `get_ai_css()`, add design system imports
2. **Implement Chat Mode**: Header, message list, input form, sidebar
3. **Implement Diagnostic Mode**: Input section, results rendering
4. **Shared Utilities**: Message bubble renderer, loading states
5. **Testing**: Run full test suite, manual verification checklist
6. **Document**: Create `PHASE_6_STAGE_5.7_AI_ASSISTANT.md` (like Stage 5.6)

---

**Audit Complete** — Ready for Implementation Phase