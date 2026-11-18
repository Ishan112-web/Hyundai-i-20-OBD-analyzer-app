# Phase 6 Stage 5.8: OBD Connection Page - Read-Only Audit

**Date:** 2026-11-17  
**Status:** AUDIT COMPLETE

---

## 1. File Overview

**File:** `modules/obd_connection.py`  
**Lines:** ~1115  
**Custom CSS:** ~350 lines (in `inject_connection_wizard_css()`)

---

## 2. Current Architecture

### Wizard Steps (8 steps)
| Step | Name | Function |
|------|------|----------|
| 1 | Mode Selection | Choose Simulation vs Real OBD-II |
| 2 | Port Discovery | Scan for serial ports |
| 3 | Port Selection | Select adapter + configure params |
| 4 | Connection | Connect to ELM327 adapter |
| 5 | ECU Detection | Read VIN, CALID, CVN, ECU info |
| 6 | PID Discovery | Query supported PIDs |
| 7 | Success | Connection complete + actions |
| 8 | Error | Troubleshooting + retry |

### Session State Keys (Page-Specific)
| Key | Type | Purpose |
|-----|------|---------|
| `wizard_step` | int | Current wizard step (1-8) |
| `wizard_selected_port` | str | Selected COM port device |
| `wizard_discovered_ports` | List[PortInfo] | Discovered serial ports |
| `wizard_connection_log` | List[Dict] | Connection event log |
| `wizard_auto_connect` | bool | Auto-connect flag |
| `obd_connected` | bool | Global OBD connection state |
| `connection_attempted` | bool | Connection step flag |
| `ecu_detected` | bool | ECU detection step flag |
| `pids_discovered` | bool | PID discovery step flag |
| `vehicle_info` | Dict | Detected vehicle info (VIN, CALID, etc.) |

### Shared Session State Keys (34 total - must preserve)
- Navigation: `current_page`, `sidebar_collapsed`
- Dashboard: 5 keys
- Diagnostics: 11 keys
- Performance: 7 keys
- Maintenance: 6 keys
- Vehicle Profile: uses shared
- AI Assistant: 9 keys
- OBD Connection: 10 page-specific (above)
- Reports: uses shared
- Settings: uses shared

---

## 3. Backend Integrations (Must Preserve)

| Service | Methods Used |
|---------|--------------|
| `OBDService` | `get_status()`, `discover_ports()`, `connect()`, `disconnect()`, `set_mode()`, `start_simulation()`, `real_adapter.get_vin()`, `get_calid()`, `get_cvn()`, `get_ecu_name()`, `get_fuel_system_status()`, `get_runtime()`, `pid_registry` |
| `DatabaseService` | `get_database()` (not actively used but imported) |
| `ConnectionManager` | Imported but not directly used |
| `PortInfo` | Dataclass for port details |
| `ConnectionState` | Enum for connection status |
| `OBDMode` | Enum (SIMULATION, REAL) |
| `OBD_REAL_CONFIG` | Config dict (baudrates, protocols, timeouts) |
| `PID_POLLING_CONFIG` | Config dict |
| `THEME` | Legacy theme dict (for CSS) |
| `VEHICLE_INFO` | Vehicle config |

---

## 4. Custom CSS Classes to Replace

### Wizard Stepper
- `.wizard-container` → Layout container
- `.wizard-steps` + `.wizard-step` + `.wizard-step-number` + `.wizard-step-label` → **wizard component**
- `.wizard-step.active/completed/error` → **WizardStep props (active, completed, error)**

### Cards & Content
- `.wizard-card` → **card()** component
- `.wizard-success` / `.wizard-error` → **card()** with elevated + alert()
- `.wizard-success-icon` / `.wizard-error-icon` → Icons in alert/card

### Port Cards
- `.port-card` → **card()** with custom content
- `.port-card.likely-obd` / `.port-card.selected` → Border color via tokens
- `.port-header`, `.port-device`, `.port-badge` → Badge + text
- `.port-details`, `.port-detail-row`, `.port-detail-label` → Layout

### PID Grid
- `.pid-grid` → **AUTO_FIT_CARD_CSS** grid or custom grid
- `.pid-item` → **card_simple()** or custom
- `.pid-item.supported/unsupported` → Border/bg via tokens
- `.pid-code`, `.pid-name`, `.pid-status` → Typography tokens

### Progress & Loading
- `.progress-container`, `.progress-bar`, `.progress-fill`, `.progress-text` → **spinner()** + custom or native st.progress with styled overlay

### Connection Log
- `.connection-log`, `.log-entry`, `.log-time`, `.log-type.*` → **card_simple()** + monospace text

### Buttons
- `.wizard-button-row` → Flex layout with button components
- `.stButton > button[wizard-primary]` → **button_primary()**

### Form Elements
- Native `st.selectbox`, `st.number_input`, `st.text_input` (disabled) → **selectbox()**, **text_input()** (for consistency)

---

## 5. Design System Components to Use

| Component | Usage |
|-----------|-------|
| `wizard()` | Main stepper (8 steps) |
| `card()` / `card_simple()` | All content cards |
| `button_primary()` | Primary actions (Connect, Continue, Complete) |
| `button_secondary()` | Secondary actions (Back, Rescan) |
| `button_ghost()` | Ghost actions |
| `button_danger()` | Disconnect, Clear Log |
| `badge()` | Port badges (Likely OBD), PID status, mode indicators |
| `alert()` | Success/error/warning/info messages |
| `text_input()` | Form fields (readonly for vehicle info) |
| `selectbox()` | Port selection, baudrate, protocol, timeout |
| `spinner()` / `skeleton_card()` | Loading states |
| `empty_state()` | No ports found |
| `page_header()` | Page title |
| `section_header()` | Section titles |

---

## 6. Design Tokens to Apply

### Colors
- `ACCENT_PRIMARY` — Primary actions, active step, focus
- `STATUS_SUCCESS` — Connected, completed steps, supported PIDs
- `STATUS_WARNING` — Simulation mode, pending, unsupported PIDs
- `STATUS_CRITICAL` — Errors, failed steps, critical states
- `STATUS_INFO` — Info steps, real mode
- `STATUS_NEUTRAL` — Disconnected, unknown
- `DATASOURCE_SIMULATION` / `DATASOURCE_REAL` — Mode indicators
- `TEXT_PRIMARY` / `TEXT_SECONDARY` / `TEXT_MUTED` — Text hierarchy
- `SURFACE_PRIMARY` / `SURFACE_SECONDARY` / `SURFACE_INTERACTIVE` — Backgrounds
- `BORDER_DEFAULT` / `BORDER_SUBTLE` / `BORDER_FOCUS` — Borders

### Spacing
- `SPACE_1` through `SPACE_6` — Consistent spacing
- `GAP_FIELD` / `GAP_INLINE` / `GAP_CARD_GRID` / `GAP_SECTION` — Semantic gaps

### Typography
- `FONT_SIZE_LABEL` / `FONT_SIZE_BODY` / `FONT_SIZE_BODY_SM` / `FONT_SIZE_CAPTION` — Text sizes
- `FONT_WEIGHT_LABEL` / `FONT_WEIGHT_BODY` — Weights
- `LETTER_SPACING_LABEL` / `LETTER_SPACING_CAPTION` — Letter spacing

### Radius
- `RADIUS_SM` / `RADIUS_MD` / `RADIUS_LG` / `RADIUS_PILL` — Border radius

### Shadows
- `SHADOW_SM` / `SHADOW_MD` / `SHADOW_FOCUS` — Elevation

---

## 7. Migration Strategy

### Phase 1: Setup & Imports
- Replace `inject_connection_wizard_css()` with `inject_global_css()` + `initialize_layout()`
- Import all needed components and tokens
- Add `page_header()` at top

### Phase 2: Wizard Stepper
- Replace custom HTML stepper with `wizard()` component
- Map 8 steps to `WizardStep` objects
- Handle navigation via `on_next`/`on_prev` callbacks updating `wizard_step`

### Phase 3: Step Content Migration
- Each step function → uses design system components
- Replace all custom CSS classes with component props/tokens
- Use `card()` for wizard cards
- Use `badge()` for status indicators
- Use `alert()` for messages
- Use `selectbox()`/`text_input()` for forms

### Phase 4: Special Components
- Port discovery → card grid with badges
- PID grid → auto-fit grid with card_simple
- Connection log → card_simple with monospace
- Progress → spinner + progress text

### Phase 5: Connected State & Error State
- `render_connected_state()` → page_header + cards + metrics
- `render_step_error()` → alert + card grid for troubleshooting

### Phase 6: Verification
- Run all 415 tests
- Manual verification of all 8 steps
- Check responsive behavior
- Verify no custom CSS remains

---

## 8. Risk Areas

1. **Wizard component interaction model** - Uses session state for button clicks, need to ensure it works with existing `st.rerun()` flow
2. **Progress bars during connection** - Custom animated progress needs replacement with spinner or skeleton
3. **Async connection flow** - Current code uses `time.sleep()` and progress updates; must preserve UX
4. **Connection log rendering** - Custom HTML log with colors; need to map to design tokens
5. **Port selection UX** - Custom clickable cards; need to use selectbox or card with button
6. **Step state management** - Multiple session state flags (`connection_attempted`, `ecu_detected`, `pids_discovered`) must be preserved exactly

---

## 9. Success Criteria

- [ ] Zero custom CSS (remove `inject_connection_wizard_css()` entirely)
- [ ] 30+ design system component usages
- [ ] All 10 page-specific session state keys preserved
- [ ] All 34 shared session state keys preserved
- [ ] All backend integrations preserved
- [ ] All 8 wizard steps functional
- [ ] 415/415 tests passing
- [ ] Responsive at all breakpoints
- [ ] Dark theme only (no light theme regression)
- [ ] WCAG 2.1 AA contrast