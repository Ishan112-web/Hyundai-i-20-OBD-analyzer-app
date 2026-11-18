# Diagnostics Page Redesign - Stage 5.3 Read-Only Audit

**Date:** 2026-11-17  
**Phase:** 6 Stage 5.3  
**Status:** Audit Complete - Ready for Implementation

---

## 1. Existing Session State Keys (Diagnostics-Specific)

The following 12 session state keys are initialized and managed by `modules/diagnostics.py`:

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `scan_results` | List[DiagnosticCode] | `[]` | DTC scan results from OBD service |
| `scan_status` | str | `"idle"` | Scan state: `idle`, `scanning`, `complete`, `error` |
| `selected_dtc` | str | `None` | Currently selected DTC code from list |
| `last_scan_time` | datetime | `None` | Timestamp of last completed scan |
| `scan_mode` | str | `"demo"` | Scan mode: `demo` or `real` |
| `ai_diagnosis_result` | DiagnosticResult | `None` | AI diagnosis result object |
| `ai_diagnosis_status` | str | `"idle"` | AI diagnosis state: `idle`, `running`, `complete`, `error` |
| `ai_diagnosis_time` | datetime | `None` | Timestamp of last AI diagnosis |
| `rule_evaluation_result` | RuleEvaluationResult | `None` | Rule engine evaluation result |
| `rule_evaluation_status` | str | `"idle"` | Rule engine state: `idle`, `running`, `complete`, `error` |
| `rule_evaluation_time` | datetime | `None` | Timestamp of last rule evaluation |

**Total Diagnostics-specific keys: 11** (plus shared keys from global shell)

---

## 2. Existing Functions & Callbacks

### Core Render Functions
- `render_diagnostics()` - Main entry point, orchestrates 3-column layout + history panel
- `render_header(obd)` - Page header with vehicle info, connection status, mode badges
- `render_scan_panel(obd)` - DTC scan controls (Scan/Rescan/Clear buttons, status indicator)
- `render_dtc_list()` - Scrollable DTC list with clickable items and severity badges
- `render_dtc_detail()` - Detailed DTC info panel (description, severity, causes, verification, freeze frame)
- `render_report_panel(obd, db)` - Report preview + Save/Download buttons
- `render_ai_diagnosis_panel(obd, db)` - AI diagnosis trigger + results display
- `render_rule_engine_panel(obd, db)` - Rule engine trigger + findings + statistics + history
- `render_history_panel(db)` - Historical diagnostic reports table

### Data Processing Functions
- `get_demo_dtcs()` - Converts config DEMO_DTCS to DiagnosticCode objects
- `get_severity_info(severity)` - Returns display info from config DTC_SEVERITY
- `perform_scan(obd)` - Executes DTC scan (simulation or real), updates session state
- `generate_report_text(obd)` - Generates formatted text diagnostic report
- `save_report(db, report_text)` - Saves report to database
- `run_rule_evaluation(obd, db)` - Runs deterministic rule engine evaluation
- `run_ai_diagnosis(obd, db)` - Runs AI-powered diagnosis via diagnostic_engine
- `render_rule_evaluation_result(result)` - Renders rule findings with severity grouping
- `render_rule_finding(finding)` - Renders individual rule finding detail
- `render_rule_statistics()` - Shows rule engine stats (loaded/enabled/history)
- `render_rule_history()` - Historical rule evaluations table
- `render_ai_diagnosis_result(result)` - Renders full AI diagnosis (primary/secondary, causes, actions, safety)
- `get_severity_color(severity)` - Maps DiagnosticSeverity to theme colors

### Data Classes
- `DiagnosticCode` - Structured DTC with code, description, severity, causes, verification, demo flag, status, freeze_frame

---

## 3. Backend Service Dependencies

| Service | Methods Used | Purpose |
|---------|-------------|---------|
| `get_obd_service()` | `get_status()`, `scan_dtcs()`, `get_all_readings()` | Vehicle communication |
| `get_database()` | `get_active_session()`, `save_diagnostic_report()`, `get_diagnostic_reports()` | Persistence |
| `get_diagnostic_engine()` | `run_diagnosis()` | AI diagnosis orchestration |
| `get_rule_engine()` | `evaluate()`, `get_statistics()`, `get_evaluation_history()` | Deterministic rules |
| `get_ai_service()` | `check_connection()` | AI availability check |

### Data Models Used
- `services.diagnostic_models.DiagnosticResult` - AI diagnosis result
- `services.diagnostic_models.DiagnosticSeverity` - CRITICAL/MAJOR/MINOR/INFO/UNKNOWN
- `services.diagnostic_models.DiagnosticStatus` - COMPLETE/INCONCLUSIVE/ERROR/INSUFFICIENT_DATA
- `services.diagnostic_models.DataSource` - SIMULATION/REAL
- `services.rule_models.RuleEvaluationResult` - Rule engine output
- `services.rule_models.RuleFinding` - Individual rule finding
- `services.rule_models.RuleSeverity` - CRITICAL/HIGH/MEDIUM/LOW/INFORMATIONAL
- `services.rule_models.RuleStatus` - TRIGGERED/NOT_TRIGGERED/SKIPPED/ERROR/INSUFFICIENT_DATA
- `services.rule_models.DataSource` - SIMULATION/REAL
- `services.rule_evaluator.SensorReading` - Sensor data for rules
- `services.types.DTC` - Rule engine DTC representation

---

## 4. UI Layout Structure (Current)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER: "Diagnostics" + Connection Status Badge + Demo Warning + Info Box  │
├─────────────────────────────────────────────────────────────────────────────┤
│  THREE-COLUMN LAYOUT (1:1:1 ratio)                                          │
│ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                          │
│ │ COL 1        │ │ COL 2        │ │ COL 3        │                          │
│ │ Scan Panel   │ │ DTC Detail   │ │ AI Diagnosis │                          │
│ │ DTC List     │ │ Report Panel │ │ Rule Engine  │                          │
│ └──────────────┘ └──────────────┘ └──────────────┘                          │
├─────────────────────────────────────────────────────────────────────────────┤
│ HISTORY PANEL (full width) - Diagnostic Reports Table                       │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Custom CSS (To Be Replaced with Design System)

The current implementation has **430+ lines of custom CSS** in `get_diagnostics_css()` covering:
- Header styling (.diag-header, .diag-title, .diag-subtitle)
- Scan panel (.scan-panel, .scan-status with pulse animation)
- DTC list (.dtc-list, .dtc-item, .dtc-code, .dtc-severity-badge, .dtc-demo-badge)
- DTC detail panel (.dtc-detail-panel, .detail-section, .detail-list)
- Report panel (.report-panel, .report-preview)
- History panel (.history-panel, .history-table)
- AI/Rule panels (.ai-diag-panel, .ai-diag-result, .ai-diag-section, etc.)
- Status badges, empty states, buttons, download buttons
- Simulation warning and info boxes

---

## 6. Design System Integration Points (Available)

### Charts (charts_v2.py)
- `create_gauge()` - For DTC severity gauges, confidence indicators
- `create_sparkline()` - For telemetry trend sparklines in DTC list
- `create_line_chart()` - For historical DTC trend charts
- `create_bar_chart()` - For severity distribution, rule findings by category
- `create_pie_chart()` - For DTC status distribution
- `create_status_indicator()` - For telemetry card status dots

### UI Components (components/ui/components.py)
- `card_simple()` / `CardProps` - Panel containers
- `badge()` / `BadgeVariant` - Severity badges (SUCCESS/WARNING/CRITICAL/INFO/NEUTRAL)
- `button_primary()` / `button_secondary()` / `button_ghost()` / `button_danger()` - Action buttons
- `alert()` / `AlertVariant` - Status messages (scan status, AI status, warnings)
- `empty_state()` / `EmptyStateProps` - Empty DTC list, no diagnosis results
- `table()` / `TableProps` / `TableColumn` - History tables, DTC lists
- `spinner()` / `skeleton()` - Loading states
- `selectbox()` / `text_input()` - Form controls (scenario selector, etc.)

### Design Tokens (components/ui/tokens.py)
- **Colors**: STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, ACCENT_PRIMARY, ACCENT_SECONDARY, SERIES_1-5, CHART_GOOD/WARNING/SERIOUS/CRITICAL, DIAG_CRITICAL/MAJOR/MINOR/INFO
- **Typography**: FONT_SIZE_H1-H4, FONT_SIZE_BODY, FONT_SIZE_LABEL, FONT_SIZE_CAPTION, FONT_FAMILY_MONO
- **Spacing**: SPACE_1-6, GAP_INLINE, GAP_FIELD
- **Radius**: RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL
- **Shadows**: SHADOW_SM, SHADOW_MD, SHADOW_LG

---

## 7. Functionality Preservation Checklist

### DTC Scanning Workflow
- [ ] Scan button triggers `perform_scan(obd)`
- [ ] Rescan button re-triggers scan
- [ ] Clear Results button resets all scan state
- [ ] Scan status indicator shows: idle/scanning/complete/error with pulse animation
- [ ] Last scan timestamp displayed
- [ ] Demo mode warning banner when in simulation
- [ ] Info box about limitations (no code clearing, no actuator tests)

### DTC List & Selection
- [ ] Empty state when no DTCs found
- [ ] List shows: DTC code (monospace), description, severity badge, DEMO badge
- [ ] Click selection updates `selected_dtc` and re-renders detail panel
- [ ] Selected item highlighted with blue left border
- [ ] Severity badge uses config DTC_SEVERITY colors

### DTC Detail Panel
- [ ] Empty state when no DTC selected
- [ ] Header: DTC code, severity badge, status, DEMO badge
- [ ] Description section
- [ ] Severity classification with description
- [ ] Possible causes (bulleted list)
- [ ] Recommended verification (bulleted list)
- [ ] Freeze frame data (if available) - key/value pairs
- [ ] Demo code disclaimer

### Report Generation
- [ ] Empty state when no scan results
- [ ] Report preview in monospace scrollable area
- [ ] Save Report button → `save_report(db, report_text)`
- [ ] Download Report button → text file download
- [ ] Report includes: vehicle info, all DTCs with details, disclaimer

### AI Diagnosis Panel
- [ ] Checks AI service availability
- [ ] Empty state when no scan results or AI unavailable
- [ ] Run AI Diagnosis button (disabled during run)
- [ ] Clear button resets AI diagnosis state
- [ ] Status indicator: idle/running/complete/error
- [ ] Full diagnosis rendering: summary, symptoms, confirmed faults, primary/secondary diagnoses, causes with confidence, evidence, verification steps, urgency badges, recommendations with priority/safety/cost, safety warnings, missing info, metadata, simulation disclaimer

### Rule Engine Panel (Phase 3)
- [ ] Checks RULE_ENGINE_AVAILABLE
- [ ] Empty state when no sensor data
- [ ] Run Rule Evaluation button (disabled during run)
- [ ] Clear button resets rule evaluation state
- [ ] Status indicator
- [ ] Results: summary stats (critical/high/medium/low counts), data source badge, overall severity
- [ ] Findings grouped by severity with: rule ID/name, severity, status, confidence, priority, source, summary, explanation, observed/expected values, evidence, missing data, recommended checks/actions, safety notes, DTC hints, evaluation time
- [ ] Statistics expander: total/enabled rules, by type/category/severity, last evaluation
- [ ] History expander: table with time, rules evaluated, findings, severity breakdown, data quality

### History Panel
- [ ] Empty state when no reports
- [ ] Table: Date/Time, Mode (DEMO/LIVE badge), DTCs Found, Codes (monospace, truncated), Summary (truncated)
- [ ] Hover highlighting on rows

---

## 8. Special Considerations

### Simulation Mode Handling
- All demo DTCs have `is_demo=True`
- Scan in simulation mode uses `DEMO_DTCS` from config
- AI diagnosis and rule engine add "SIMULATION DATA" disclaimers
- Data source badges show "SIMULATION" vs "REAL VEHICLE"

### Error Handling
- Scan errors → `scan_status = "error"`, shows st.error()
- AI diagnosis errors → `ai_diagnosis_status = "error"`, shows st.error() + traceback
- Rule engine errors → `rule_evaluation_status = "error"`, shows st.error() + traceback
- Database save errors → st.error()
- All errors trigger `st.rerun()`

### Real OBD Integration
- When `obd.mode == "real"`, uses actual OBD scan
- Freeze frame data only available in real mode
- Rule engine uses real sensor readings when available

---

## 9. Next Steps: 7-Step Implementation Cycle

### Step 5.3.1: Read-Only Audit ✓ COMPLETE (this document)
### Step 5.3.2: Define Layout per Spec
- Create ASCII layout matching Stage 5.3 specification
- Map design system components to each section

### Step 5.3.3: Implement DTC Workspace
- Scan panel with design system buttons/alerts
- DTC list with table component + badge integration
- DTC detail with card_simple + badge + status indicators

### Step 5.3.4: Implement AI Diagnosis Panel
- Integrate with diagnostic_engine
- Use card/alert/badge components
- Add sparkline/status_indicator for confidence visualization

### Step 5.3.5: Implement Rule Engine Panel
- Rule evaluation trigger
- Findings display with severity grouping
- Statistics and history tables

### Step 5.3.6: Implement Evidence & History
- Report panel with preview + save/download
- History table with design system table component

### Step 5.3.7: Implement Report Integration
- Ensure report generation uses design tokens
- Database save/download preserved

### Step 5.3.8: Visual Review
- Compare against design system spec
- Verify CVD-safe colors, contrast, spacing

### Step 5.3.9: Full Regression
- Run test suite (target 413+ passing)
- Manual functional verification

### Step 5.3.10: Documentation
- Update PHASE_6_PROGRESS.md
- Document any new patterns