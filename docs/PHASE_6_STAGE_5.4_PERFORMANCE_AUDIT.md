# Performance Page Redesign - Stage 5.4 Read-Only Audit

**Date:** 2026-11-17  
**Phase:** 6 Stage 5.4  
**Status:** Audit Complete - Ready for Implementation

---

## 1. Existing Session State Keys (Performance-Specific)

The following session state keys are initialized and managed by `modules/performance.py`:

| Key | Type | Default | Purpose |
|-----|------|---------|---------|
| `sim_running` | bool | `False` | Whether simulation/recording is active |
| `sim_scenario` | str | `"idle"` | Current simulation scenario |
| `telemetry_history` | List[Dict] | `[]` | Live telemetry data points (max 300) |
| `session_id` | int | `None` | Active recording session ID |
| `last_update` | float | `time.time()` | Timestamp of last telemetry update |
| `selected_session_ids` | List[int] | `[]` | Selected sessions for comparison/bulk actions |
| `compare_sessions` | List[int] | `None` | Sessions selected for comparison view |

**Total Performance-specific keys: 7**

These must be preserved exactly - no renaming, deletion, or structure changes.

---

## 2. Existing Functions & Callbacks

### Core Render Functions
- `render_performance()` - Main entry point, orchestrates 4-tab layout
- `render_header(obd)` - Page header with vehicle info, connection status, mode badges
- `render_live_charts()` - Live telemetry charts (6 charts in 2-column grid)
- `render_session_statistics(db)` - Session statistics tab
- `render_sessions_panel(db)` - Session management (recording controls + session list)
- `render_compare_sessions(db)` - Session comparison tab

### Chart Rendering Functions (Custom Plotly)
- `render_rpm_chart(df)` - RPM history with redline reference
- `render_speed_chart(df)` - Speed history
- `render_coolant_chart(df)` - Coolant temp with normal/overheating bands
- `render_engine_load_chart(df)` - Engine load history
- `render_throttle_chart(df)` - Throttle position history
- `render_fuel_trim_chart(df)` - STFT/LTFT with normal range bands

### Statistics Functions
- `calculate_session_stats(df, session)` - Comprehensive session statistics
- `format_duration(seconds)` - Human-readable duration formatting
- `render_stat_cards(stats)` - Key metric cards (4 cards)
- `render_detailed_stats(stats, df)` - Detailed statistics table
- `render_time_distribution(df)` - RPM and Speed histograms

### Session Management Functions
- `render_sessions_table(db, sessions)` - Interactive session table with checkboxes
- `get_record_count(db, session_id)` - Count records in session
- `view_session_details(db, session_id)` - Expandable session detail view
- `export_session_csv(db, session_id)` - Single session CSV download
- `export_multiple_sessions_csv(db, session_ids)` - Combined CSV download
- `delete_session(db, session_id)` - Delete session and records

### Recording Workflow Functions
- `start_recording(db)` - Create session, start simulation, initialize state
- `stop_recording()` - Stop simulation, update state
- `save_session(db)` - End session in database, calculate stats
- `update_telemetry_history(obd, db)` - Append live data to history + database

### Comparison Functions
- `render_session_comparison(db, session_ids)` - Overlay charts + summary table

### Data Classes
- None (uses dicts for session/record data)

---

## 3. Backend Service Dependencies

| Service | Methods Used | Purpose |
|---------|-------------|---------|
| `get_database()` | `get_active_session()`, `get_telemetry_sessions()`, `get_session_records()`, `create_telemetry_session()`, `end_telemetry_session()`, `add_telemetry_record()`, `export_session_csv()` | Session/telemetry persistence |
| `get_obd_service()` | `get_status()`, `get_all_readings()`, `start_simulation()`, `stop_simulation()` | Vehicle communication & simulation |

### Database Schema (Telemetry)
- `telemetry_sessions` - Session metadata (name, scenario, times, peak/avg stats)
- `telemetry_records` - Individual data points (rpm, speed, coolant, throttle, load, fuel trims, etc.)

---

## 4. UI Layout Structure (Current)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER: "Performance Analytics" + Connection Status Badge + Warnings       │
├─────────────────────────────────────────────────────────────────────────────┤
│  FOUR TABS                                                                  │
│ ┌─────────────┐ ┌────────────────┐ ┌─────────────┐ ┌────────────────────┐  │
│ │ Live Charts │ │Session Stats   │ │ Sessions    │ │ Compare Sessions   │  │
│ └─────────────┘ └────────────────┘ └─────────────┘ └────────────────────┘  │
│                                                                             │
│ Tab 1 - Live Charts: 6 charts in 2×3 grid (RPM, Speed, Coolant, Load,     │
│         Throttle, Fuel Trim) - uses telemetry_history session state        │
│                                                                             │
│ Tab 2 - Session Stats: Stat cards (4) + Detailed table + Histograms (2)   │
│                                                                             │
│ Tab 3 - Sessions: Recording controls (Start/Stop/Save) + Session table    │
│         with checkboxes, view/export/delete per row, bulk actions          │
│                                                                             │
│ Tab 4 - Compare: Session selector → Overlay charts (5 metrics) + Table    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Custom CSS (To Be Replaced with Design System)

The current implementation has **~300 lines of custom CSS** in `get_performance_css()` covering:
- Header styling (`.perf-header`, `.perf-title`, `.perf-subtitle`)
- Stat grid/cards (`.stat-grid`, `.stat-card`, `.stat-icon`, `.stat-value`, `.stat-label`)
- Chart containers (`.chart-container`, `.chart-title`)
- Session panels (`.session-panel`)
- Session table (`.session-table`, `.session-row`, `.session-label`, `.session-value`)
- Comparison selector (`.compare-selector`)
- Warning/Info boxes (`.warning-box`, `.info-box`)
- Empty state (`.empty-state`)
- Recording indicator (`.recording-indicator` with pulse animation)
- Control buttons (`.control-buttons`)
- Tab styling (`.stTabs` overrides)
- Block container padding
- Download button styling

---

## 6. Design System Integration Points (Available)

### Charts (charts_v2.py) - USE THESE
- `create_gauge()` / `GaugeConfig` - For peak RPM, max speed, coolant temp, engine load
- `create_line_chart()` / `LineChartConfig` / `LineSeries` - For live telemetry history, comparison overlays
- `create_sparkline()` / `SparklineConfig` - For metric card trends
- `create_comparison_chart()` / `ComparisonConfig` / `ComparisonSeries` - For session comparison
- `create_bar_chart()` / `BarChartConfig` / `BarSeries` - For histograms (RPM/Speed distribution)
- `create_subplot_figure()` / `SubplotConfig` - For multi-chart layouts
- `create_heatmap()` - Could be used for correlation analysis
- `create_status_indicator()` - For telemetry card status dots

### UI Components (components/ui/components.py) - USE THESE
- `button_primary()`, `button_secondary()`, `button_ghost()`, `button_danger()` - Action buttons
- `badge()` / `BadgeVariant` - Status badges (simulation, recording, data source)
- `alert()` / `AlertVariant` - Status messages (recording, warnings, empty states)
- `card()` / `card_simple()` / `CardProps` - Panel containers
- `empty_state()` / `EmptyStateProps` - Empty charts, no sessions, no data
- `table()` / `TableProps` / `TableColumn` - Session list, comparison tables
- `spinner()`, `skeleton()`, `skeleton_card()` - Loading states
- `selectbox()` - Session comparison selectors

### Design Tokens (components/ui/tokens.py) - USE THESE
- **Colors**: STATUS_SUCCESS, STATUS_WARNING, STATUS_CRITICAL, STATUS_INFO, ACCENT_PRIMARY, SERIES_1-5, CHART_GOOD/WARNING/SERIOUS/CRITICAL, DATASOURCE_REAL/SIMULATION
- **Typography**: FONT_SIZE_H1-H4, FONT_SIZE_BODY, FONT_SIZE_LABEL, FONT_SIZE_CAPTION, FONT_FAMILY_MONO, FONT_WEIGHT_NUMERIC, LETTER_SPACING_LABEL
- **Spacing**: SPACE_1-6, GAP_INLINE, GAP_FIELD, GAP_CARD, GAP_SECTION
- **Radius**: RADIUS_SM, RADIUS_MD, RADIUS_LG, RADIUS_PILL
- **Shadows**: SHADOW_SM, SHADOW_MD, SHADOW_LG

### Layout (components/ui/layout.py) - USE THESE
- `page_header()` - Page header with title, subtitle, actions
- `responsive_container()` - Responsive content container
- `responsive_grid_css()`, `auto_fit_grid_css()` - Grid layouts for metric cards
- `metric_row_columns()`, `chart_columns()` - Column helpers

### Global Shell (components/shell.py) - ALREADY INTEGRATED
- `page_header` from layout already used
- Sidebar navigation, top bar, vehicle context automatically handled by app.py

---

## 7. Functionality Preservation Checklist

### Live Charts Tab
- [ ] 6 telemetry charts rendered from `telemetry_history` session state
- [ ] RPM chart with redline reference (ENGINE_SPECS['redline_rpm'])
- [ ] Speed chart
- [ ] Coolant chart with normal range (85-95°C) and overheating (105-125°C) bands
- [ ] Engine load chart (0-105% range)
- [ ] Throttle chart (0-105% range)
- [ ] Fuel trim chart with STFT/LTFT, zero line, normal range bands (±10%, ±20%, ±30%)
- [ ] Empty state when < 2 data points
- [ ] Charts update when simulation running

### Session Statistics Tab
- [ ] Active session detection (session_id → active_session → None)
- [ ] Stat cards: Peak RPM, Max Speed, Avg Speed, Duration
- [ ] Detailed statistics table (all fields from `render_detailed_stats`)
- [ ] Time distribution histograms: RPM and Speed
- [ ] Empty states for no session / no records
- [ ] Distance estimation (trapezoidal integration)
- [ ] Fuel trim statistics (avg, min, max for STFT/LTFT)

### Sessions Tab
- [ ] Recording controls: Start (primary), Stop, Save (disabled when recording)
- [ ] Recording indicator with pulse animation
- [ ] Session list table with: Select, ID, Name, Scenario, Date, Duration, Peak RPM, Max Speed, Avg Speed, Records, Actions
- [ ] Checkbox selection for bulk actions
- [ ] Per-row actions: View (expander), Export CSV (download), Delete
- [ ] Bulk actions: Compare Selected, Export All CSV, Delete Selected
- [ ] Empty state when no saved sessions

### Compare Sessions Tab
- [ ] Instruction when no sessions selected (redirect to Sessions tab)
- [ ] Manual session selector fallback (2 selectboxes)
- [ ] Overlay comparison charts for: RPM, Speed, Coolant, Engine Load, Throttle
- [ ] Normalized time axis (elapsed seconds from session start)
- [ ] Summary comparison table with all key metrics
- [ ] Clear comparison button

### Recording Workflow
- [ ] Start Recording: Creates DB session, starts OBD simulation, initializes telemetry_history
- [ ] Stop Recording: Stops OBD simulation
- [ ] Save Session: Calls `end_telemetry_session()` with stats calculation
- [ ] Auto-update: `update_telemetry_history()` called when `sim_running` true
- [ ] Telemetry history capped at 300 points (5 min at 1Hz)

### Data Provenance
- [ ] Simulation mode warning banner
- [ ] Important disclaimer (no HP/torque estimation, no acceleration claims)
- [ ] CSV exports include `is_simulated` column
- [ ] Comparison shows scenario for each session

### Error Handling
- [ ] Database errors caught and displayed
- [ ] Missing telemetry fields handled gracefully
- [ ] Empty sessions handled
- [ ] Invalid sensor readings excluded

---

## 8. Special Considerations

### Simulation Mode Handling
- All live charts use `telemetry_history` (session state) updated by `update_telemetry_history()`
- Simulation controlled from Dashboard (shared `sim_running`, `sim_scenario` state)
- Performance page can also start/stop recording independently
- Data source clearly labeled: `is_simulated` in database and CSV exports

### Real OBD Integration
- When `obd.mode == "real"`, uses actual OBD readings
- Recording works with real OBD data
- `update_telemetry_history()` reads from `obd.get_all_readings()`

### Large Data Handling
- Telemetry history capped at 300 points for live charts
- Session list limited to 50 sessions
- Comparison limited by user selection
- `get_record_count()` queries count without loading records

---

## 9. Next Steps: Implementation Plan

### Phase 0: Audit Complete ✓

### Phase 1: Design System Integration
- Replace 300 lines of custom CSS with design system tokens/components
- Migrate 6 live charts to `create_line_chart()` with `LineSeries`
- Migrate 2 histograms to `create_bar_chart()` with `BarSeries`
- Migrate stat cards to design system `card_simple()` + tokens
- Migrate session table to `table()` component
- Migrate comparison charts to `create_comparison_chart()` or `create_line_chart()`

### Phase 2: Layout Restructure
- Use `page_header()` for consistent header
- Use responsive grid for stat cards (`metric_row_columns` or `auto_fit_grid_css`)
- Use `chart_columns()` or `responsive_grid_css()` for chart layout
- Consistent spacing via `GAP_CARD`, `GAP_SECTION`, `SPACE_4`, `SPACE_6`

### Phase 3: Component Replacement
- Recording indicator → `alert()` with recording variant or custom badge
- Warning/info boxes → `alert()` component
- Empty states → `empty_state()` component
- Buttons → `button_primary()`, `button_secondary()`, `button_ghost()`, `button_danger()`
- Badges for status (simulation, recording, data source)
- Download buttons → keep Streamlit native (no design system equivalent yet)

### Phase 4: Chart Enhancement
- Use `SERIES_PALETTE` for consistent series colors
- Use `CHART_LAYOUT_DEFAULTS` for consistent layout
- Add `create_status_indicator()` for telemetry card status
- Consider `create_sparkline()` for metric card trends

### Phase 5: Testing & Verification
- Run full test suite (target: 415 passing)
- Manual functional verification of all 4 tabs
- Visual verification against Dashboard/Diagnostics design consistency
- Data provenance verification (simulation vs real labeling)