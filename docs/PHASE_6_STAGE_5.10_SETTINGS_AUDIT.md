# Phase 6 Stage 5.10: Settings Page - Read-Only Audit

**Date:** 2026-11-17  
**Status:** AUDIT COMPLETE

---

## 1. File Overview

**File:** `modules/settings.py`  
**Lines:** ~1312  
**Custom CSS:** ~220 lines (in `get_settings_css()`)

---

## 2. Current Architecture

### Main Page Structure (`render_settings()`)
| Tab | ID | Function | Description |
|-----|----|----------|-------------|
| 1 | 🤖 AI & LM Studio | `render_ai_settings()` | LM Studio URL, model selection, AI parameters |
| 2 | 🔌 OBD Connection | `render_obd_settings()` | OBD mode (simulation/real), hardware config |
| 3 | 🎮 Simulation | `render_simulation_settings()` | Update intervals, scenarios, UI preferences |
| 4 | 📊 Data & Export | `render_data_export_settings()` | Export sessions, diagnostics, maintenance, full archive |
| 5 | 💾 Backup & Restore | `render_backup_settings()` | Create/restore/delete backups, database stats |
| 6 | ℹ️ About | `render_about_settings()` | App info, vehicle profile, engine specs, disclaimers |

### Session State Keys (Page-Specific - 14 keys)
| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `lm_studio_base_url` | str | `LM_STUDIO_BASE_URL` | AI service endpoint |
| `lm_studio_model` | str | `LM_STUDIO_MODEL` | Selected AI model |
| `lm_studio_temperature` | float | `LM_STUDIO_TEMPERATURE` | AI temperature (0.0-2.0) |
| `lm_studio_timeout` | int | `LM_STUDIO_TIMEOUT` | Request timeout in seconds |
| `obd_mode` | str | `OBD_MODE` | "simulation" or "real" |
| `obd_port` | str | "COM3" | Serial port for OBD adapter |
| `obd_baudrate` | int | 38400 | Communication baud rate |
| `obd_protocol` | str | "auto" | OBD-II protocol |
| `simulation_interval` | float | `SIMULATION_INTERVAL` | Simulation update interval |
| `telemetry_refresh_interval` | float | `TELEMETRY_REFRESH_INTERVAL` | Dashboard refresh interval |
| `theme_mode` | str | "dark" | UI theme: dark/light/auto |
| `auto_refresh` | bool | True | Auto-refresh dashboard |
| `confirm_delete_{session_id}` | bool | False | Delete confirmation flag |
| `confirm_restore` | bool | False | Restore confirmation flag |

### Shared Session State Keys (34 total - must preserve)
- Navigation: `current_page`, `sidebar_collapsed`
- Dashboard: 5 keys
- Diagnostics: 11 keys
- Performance: 7 keys
- Maintenance: 6 keys
- Vehicle Profile: uses shared
- AI Assistant: 9 keys
- OBD Connection: 10 keys
- Reports: 6 keys
- Settings: 14 page-specific (above)

---

## 3. Configuration Dependencies (from `config.py`)

### AI Settings
| Config Key | Default | Type | Env Var |
|------------|---------|------|---------|
| `LM_STUDIO_BASE_URL` | "http://localhost:1234/v1" | str | `LM_STUDIO_BASE_URL` |
| `LM_STUDIO_MODEL` | "qwen2.5-3b-instruct" | str | `LM_STUDIO_MODEL` |
| `LM_STUDIO_TEMPERATURE` | 0.7 | float | `LM_STUDIO_TEMPERATURE` |
| `LM_STUDIO_TIMEOUT` | 30 | int | `LM_STUDIO_TIMEOUT` |

### OBD Settings
| Config Key | Default | Type | Env Var |
|------------|---------|------|---------|
| `OBD_MODE` | "simulation" | str | `OBD_MODE` |
| `OBD_PORT` | "COM3" | str | `OBD_PORT` |
| `OBD_BAUDRATE` | 38400 | int | `OBD_BAUDRATE` |
| `OBD_PROTOCOL` | "auto" | str | `OBD_PROTOCOL` |

### Simulation Settings
| Config Key | Default | Type | Env Var |
|------------|---------|------|---------|
| `SIMULATION_INTERVAL` | 0.5 | float | `SIMULATION_INTERVAL` |
| `TELEMETRY_REFRESH_INTERVAL` | 1.0 | float | `TELEMETRY_REFRESH_INTERVAL` |

### Vehicle Info (from config.py)
- `VEHICLE_INFO`: Make, model, year, engine, transmission, fuel_type, market, ecu_tuning, vin
- `ENGINE_SPECS`: displacement_cc, cylinders, max_power_ps, max_power_rpm, max_torque_nm, max_torque_rpm, compression_ratio, fuel_system, emission_standard, redline_rpm, idle_rpm
- `SIMULATION_SCENARIOS`: idle, city, highway, acceleration, overheating

---

## 4. Backend Services (Must Preserve)

| Service | Methods Used |
|---------|--------------|
| `DatabaseService` | `get_setting()`, `set_setting()`, `get_telemetry_sessions()`, `get_session_records()`, `get_diagnostic_reports()`, `get_maintenance_records()`, `get_database_stats()`, `get_vehicle_profile()`, `backup_database()` |
| `AIService` | `check_connection()`, `get_available_models()`, `get_available_models(force_refresh=True)` |
| `OBDService` | Not directly used (connection wizard is in OBD Connection page) |

---

## 5. Configuration Inventory

### AI Settings
| Display Name | Config Key | Type | Default | Persistence | Validation | Apply Behavior |
|--------------|------------|------|---------|-------------|------------|----------------|
| LM Studio Base URL | `lm_studio_base_url` | string | "http://localhost:1234/v1" | DB + session | URL format | Immediate (on change) |
| AI Model | `lm_studio_model` | string | "qwen2.5-3b-instruct" | DB + session | Must be in available models | Immediate |
| Temperature | `lm_studio_temperature` | float | 0.7 | DB + session | 0.0-2.0 | Immediate |
| Request Timeout | `lm_studio_timeout` | int | 30 | DB + session | 5-300 seconds | Immediate |
| Test Connection | N/A | action | N/A | N/A | Calls `AIService.check_connection()` | On button click |
| Refresh Models | N/A | action | N/A | N/A | Calls `AIService.get_available_models(force_refresh=True)` | On button click |

### OBD Settings
| Display Name | Config Key | Type | Default | Persistence | Validation | Apply Behavior |
|--------------|------------|------|---------|-------------|------------|----------------|
| Connection Mode | `obd_mode` | string | "simulation" | DB + session | "simulation" or "real" | Immediate + rerun |
| Serial Port | `obd_port` | string | "COM3" | DB + session | Non-empty | Immediate |
| Baud Rate | `obd_baudrate` | int | 38400 | DB + session | In [9600, 19200, 38400, 57600, 115200] | Immediate |
| Protocol | `obd_protocol` | string | "auto" | DB + session | In ["auto", "1", "2", "3", "4", "5", "6", "7", "8", "9", "A"] | Immediate |
| Test OBD Connection | N/A | action | N/A | N/A | Placeholder only | On button click |

### Simulation Settings
| Display Name | Config Key | Type | Default | Persistence | Validation | Apply Behavior |
|--------------|------------|------|---------|-------------|------------|----------------|
| Simulation Interval | `simulation_interval` | float | 0.5 | DB + session | 0.1-5.0 seconds | Immediate |
| Telemetry Refresh | `telemetry_refresh_interval` | float | 1.0 | DB + session | 0.1-5.0 seconds | Immediate |
| Theme Mode | `theme_mode` | string | "dark" | DB + session | "dark", "light", "auto" | Immediate |
| Auto-refresh | `auto_refresh` | bool | True | DB + session | Boolean | Immediate |

### Data Export
| Action | Description | Persistence |
|--------|-------------|-------------|
| Export Session CSV | Exports telemetry records to CSV | File only |
| Export Session JSON | Exports session + records to JSON | File only |
| Delete Session | Deletes session and records from DB | DB + confirmation |
| Export Diagnostic JSON | Exports diagnostic report to JSON | File only |
| Export Maintenance CSV | Exports all maintenance records to CSV | File only |
| Export Complete Archive | Exports all data to single JSON | File only |

### Backup & Restore
| Action | Description | Persistence |
|--------|-------------|-------------|
| Create Backup | SQLite backup to `data/backups/` | File + DB |
| Open Backup Folder | Opens folder in OS file explorer | N/A |
| Restore Backup | Copies backup over current DB | DB + confirmation |
| Delete Backup | Deletes backup file | File + confirmation |
| Database Stats | Shows DB size and record counts | Read-only |

### About
| Display | Source |
|---------|--------|
| Application name/version/build | Hardcoded in module |
| Python version | `sys.version` |
| Vehicle profile | `config.VEHICLE_INFO` |
| Engine specifications | `config.ENGINE_SPECS` |
| Disclaimers | Hardcoded in module |

---

## 6. Custom CSS Classes to Replace

### Page Structure
- `.settings-header` → **page_header()**
- `.settings-section` → **card()** or **card_simple()**
- `.settings-section-title` → **section_header()** title
- `.settings-section-description` → **section_header()** description
- `.divider` → **st.divider()** or token-based border

### Form Layout
- `.setting-row` → Flex layout with design tokens
- `.setting-info` → Label/description layout
- `.setting-label` → **FONT_SIZE_LABEL**, **FONT_WEIGHT_LABEL**, **TEXT_PRIMARY**
- `.setting-description` → **FONT_SIZE_CAPTION**, **TEXT_SECONDARY**
- `.setting-control` → Input width handling

### Status Indicators
- `.status-indicator` → **badge()** with variants
- `.status-connected` → **BadgeVariant.SUCCESS**
- `.status-disconnected` → **BadgeVariant.CRITICAL**
- `.status-checking` → **BadgeVariant.WARNING**

### Badges & Cards
- `.model-badge` → **badge()** with variants
- `.model-badge.current` → **BadgeVariant.PRIMARY** or accent
- `.info-grid` → **AUTO_FIT_CARD_CSS** grid
- `.info-card` → **card_simple()**
- `.info-card-title` → **FONT_SIZE_LABEL**, **TEXT_MUTED**, uppercase
- `.info-card-value` → **FONT_SIZE_BODY**, **TEXT_PRIMARY**

### Messages
- `.success-message` → **alert(AlertVariant.SUCCESS)**
- `.error-message` → **alert(AlertVariant.CRITICAL)**
- `.warning-message` → **alert(AlertVariant.WARNING)**

### Form Elements (Streamlit native overrides)
- `.stSelectbox`, `.stTextInput`, `.stNumberInput`, `.stSlider`, `.stCheckbox` → Use design system form components
- `.stButton > button[kind="primary"]` → **button_primary()**
- `.stButton > button[kind="secondary"]` → **button_secondary()**

### Export & Actions
- `.export-options` → Flex layout with buttons
- `.action-button` → Button spacing via tokens

---

## 7. Design System Components to Use

| Component | Usage |
|-----------|-------|
| `page_header()` | Main page title with icon |
| `section_header()` | Section titles with descriptions (12+ sections) |
| `card()` / `card_simple()` | All content containers (20+) |
| `button_primary()` | Primary actions: Save, Create Backup, Export All, Test Connection |
| `button_secondary()` | Secondary actions: Refresh, Open Folder, individual exports |
| `button_ghost()` | Ghost actions: less prominent actions |
| `button_danger()` | Destructive: Delete session, Delete backup, Restore (with confirmation) |
| `badge()` | Status indicators: connected/disconnected, current model, mode |
| `alert()` | Success/error/warning/info messages (15+) |
| `text_input()` | URL inputs, port input |
| `selectbox()` | Model, baudrate, protocol, theme, scenarios |
| `empty_state()` | No sessions, no reports, no backups |
| `spinner()` | Loading during connection test, model refresh, backup |
| `AUTO_FIT_CARD_CSS` | Responsive grids for info cards, model badges |
| `AUTO_FIT_METRIC_CSS` | Metric cards for database stats |

---

## 8. Design Tokens to Apply

### Colors
- `ACCENT_PRIMARY` (#00b4d8) — Primary actions, focus, accents
- `STATUS_SUCCESS` (#2ecc71) — Connected, success, healthy
- `STATUS_WARNING` (#f39c12) — Checking, warnings, simulation mode
- `STATUS_CRITICAL` (#e74c3c) — Disconnected, errors, destructive
- `STATUS_INFO` (#00b4d8) — Info states
- `STATUS_NEUTRAL` (#9aa3ad) — Neutral, secondary
- `TEXT_PRIMARY` / `TEXT_SECONDARY` / `TEXT_MUTED` / `TEXT_ON_ACCENT` — Text hierarchy
- `SURFACE_PRIMARY` / `SURFACE_SECONDARY` / `SURFACE_INTERACTIVE` — Backgrounds
- `BORDER_DEFAULT` / `BORDER_SUBTLE` / `BORDER_FOCUS` — Borders

### Spacing
- `SPACE_1` (4px) through `SPACE_6` (24px) — Consistent spacing
- `GAP_INLINE` / `GAP_FIELD` / `GAP_CARD_GRID` / `GAP_SECTION` — Semantic gaps

### Typography
- `FONT_SIZE_LABEL` (0.75rem) — Form labels, metadata
- `FONT_SIZE_BODY` (0.875rem) — Standard content
- `FONT_SIZE_BODY_SM` (0.8125rem) — Secondary content
- `FONT_SIZE_CAPTION` (0.6875rem) — Fine print, timestamps
- `FONT_SIZE_H1` / `FONT_SIZE_H2` / `FONT_SIZE_H3` — Headers
- `BUTTON_FONT_WEIGHT` (500) — Label weight

### Radius
- `RADIUS_SM` (4px) — Inputs, badges
- `RADIUS_MD` (8px) — Standard cards
- `RADIUS_LG` (12px) — Elevated cards
- `RADIUS_PILL` — Badges, pills

### Shadows
- `SHADOW_SM` / `SHADOW_MD` / `SHADOW_FOCUS` — Elevation

### Transitions
- `TRANSITION_FAST` (0.15s) — Hover, focus
- `TRANSITION_NORMAL` (0.2s) — Card transforms

---

## 9. Migration Strategy

### Phase 1: Setup & Imports
- Replace `get_settings_css()` with `inject_global_css()` + `initialize_layout()`
- Import all needed components and tokens from `components.ui`
- Add `page_header()` at top of `render_settings()`

### Phase 2: Page Structure
- Replace 6 tabs with native `st.tabs()` (preserve tab order)
- Use `page_header()` for main title
- Use `section_header()` for each section within tabs

### Phase 3: AI Settings Tab
- LM Studio URL: `text_input()` + `button_secondary()` for test connection
- Connection status: `badge()` with variant
- Model selection: `selectbox()` + `button_secondary()` for refresh
- Model badges: `badge()` in auto-fit grid
- Temperature: Native `st.slider()` with token-styled labels
- Timeout: `text_input()` (number) or `st.number_input()`
- Temperature guide: `alert(AlertVariant.INFO)` or styled markdown

### Phase 4: OBD Settings Tab
- Mode selector: Native `st.radio()` with design tokens
- Real mode: `text_input()` for port, `selectbox()` for baudrate/protocol
- Simulation mode: `alert(AlertVariant.WARNING)` for simulation notice
- Test connection: `button_secondary()` (placeholder preserved)

### Phase 5: Simulation Settings Tab
- Intervals: `st.number_input()` with token labels
- Scenarios: Expanders with `card_simple()` for info cards
- UI Preferences: `selectbox()` for theme, `st.checkbox()` for auto-refresh

### Phase 6: Data & Export Tab
- Sessions: Expanders with export/delete buttons
- Use `button_primary()` for export, `button_danger()` for delete
- Delete confirmation: `st.session_state` flag + `alert(AlertVariant.WARNING)`
- Diagnostic/Maintenance exports: Same pattern
- Complete export: `button_primary()`

### Phase 7: Backup & Restore Tab
- Create backup: `button_primary()` with `spinner()`
- Open folder: `button_secondary()`
- Backup list: `card_simple()` for each backup with metadata
- Restore: `button_danger()` with confirmation flow
- Delete backup: `button_ghost()` with confirmation
- Database stats: Metric cards using `st.metric()` or `card_simple()`

### Phase 8: About Tab
- App info: `card_simple()` grid with `info-card` pattern
- Vehicle profile: Same pattern
- Engine specs: Two-column grid with `card_simple()`
- Disclaimers: `alert(AlertVariant.WARNING)`
- Open source note: `alert(AlertVariant.SUCCESS)`

### Phase 9: Remove Custom CSS
- Delete `get_settings_css()` entirely
- Verify zero custom CSS remains

### Phase 10: Verification
- Run all 415 tests
- Manual verification of all 6 tabs
- Test credential handling (no exposure)
- Test destructive operations with confirmations
- Check responsive behavior
- Verify dark theme only

---

## 10. Risk Areas

1. **Credential Handling** — LM Studio URL may contain credentials; never render as visible text; preserve existing value on blank input
2. **AI Connection Testing** — Uses actual `AIService`; must preserve async behavior and not trigger on reruns
3. **Model Refresh** — Uses `force_refresh=True`; must not cause excessive API calls
4. **OBD Mode Switching** — Triggers `st.rerun()`; must preserve all state
5. **Delete Confirmation Pattern** — Uses `st.session_state` flags; must preserve exact flow
6. **Restore Confirmation** — Two-click pattern with `confirm_restore` flag; must preserve
7. **Backup/Restore Path Safety** — Must validate paths stay within `data/backups/`
8. **Streamlit Rerun Behavior** — Settings saved on every input change; must not cause duplicate saves
9. **Database Stats** — Calls `db.get_database_stats()`; must preserve
10. **Theme Mode** — Only "dark" actually works; "light"/"auto" are placeholders

---

## 11. Success Criteria

- [ ] Zero custom CSS (remove `get_settings_css()` entirely)
- [ ] 30+ design system component usages
- [ ] All 14 page-specific session state keys preserved
- [ ] All 34 shared session state keys preserved
- [ ] All backend integrations preserved (DatabaseService, AIService)
- [ ] All 6 tabs functional with preserved features
- [ ] Credential security: no exposure, blank input preserves existing
- [ ] AI connection test works
- [ ] Model refresh works
- [ ] OBD mode switching works
- [ ] Simulation settings persist
- [ ] Data export (CSV/JSON) works for all types
- [ ] Delete session with confirmation works
- [ ] Backup create/list/restore/delete works
- [ ] Restore confirmation flow works
- [ ] Database stats display correctly
- [ ] About section displays correct metadata
- [ ] 415/415 tests passing
- [ ] Responsive at all breakpoints
- [ ] Dark theme only (no light theme regression)
- [ ] WCAG 2.1 AA contrast