# Performance Page Layout Definition - Stage 5.4

**Date:** 2026-11-17  
**Phase:** 6 Stage 5.4  
**Based on:** Stage 5.4 Specification Document

---

## Design System Components Mapping

### Available Components (from audit)
- **Header**: `page_header()` from layout.py
- **Charts**: `create_line_chart()`, `create_bar_chart()`, `create_comparison_chart()`, `create_gauge()`, `create_sparkline()`
- **UI**: `card_simple()`, `button_primary()`, `button_secondary()`, `button_ghost()`, `button_danger()`, `badge()`, `alert()`, `empty_state()`, `table()`, `selectbox()`, `spinner()`, `skeleton_card()`
- **Tokens**: All color, typography, spacing, radius, shadow tokens
- **Layout**: `responsive_grid_css()`, `auto_fit_grid_css()`, `metric_row_columns()`, `chart_columns()`

---

## ASCII Layout - Overall Page Structure

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ GLOBAL SHELL (components/shell.py)                                                          │
│ ┌─────────────────────┐ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ SIDEBAR (300px)     │ │ MAIN CONTENT AREA                                               │ │
│ │ Navigation          │ │ ┌─────────────────────────────────────────────────────────────┐ │ │
│ │ Vehicle Context     │ │ │ TOP BAR (components/shell.py - top_bar)                     │ │ │
│ │                     │ │ │ [Breadcrumb: Performance] [OBD Status] [AI Status] [Sim Badge]│ │ │
│ └─────────────────────┘ │ └─────────────────────────────────────────────────────────────┘ │ │
│                         │ ┌─────────────────────────────────────────────────────────────┐ │ │
│                         │ │ PAGE HEADER (layout.page_header)                              │ │ │
│                         │ │ ┌──────────────────────────┐  ┌────────────────────────────┐ │ │ │
│                         │ │ │ "Performance Analytics"  │  │ [Connection Status Badge]  │ │ │ │
│                         │ │ │ "Real-time telemetry,    │  │ [Simulation Warning Badge] │ │ │ │
│                         │ │ │  session recording, and  │  │ [Recording Indicator]      │ │ │ │
│                         │ │ │  comparative analysis"   │  │                            │ │ │ │
│                         │ │ └──────────────────────────┘  └────────────────────────────┘ │ │ │
│                         │ └─────────────────────────────────────────────────────────────┘ │ │
│                         │ ┌─────────────────────────────────────────────────────────────┐ │ │
│                         │ │ CONTENT CONTAINER (responsive_container)                      │ │ │
│                         │ │                                                               │ │ │
│                         │ │  ┌─────────────────────────────────────────────────────────┐  │ │ │
│                         │ │  │ TAB BAR (st.tabs) - 4 tabs                               │  │ │ │
│                         │ │  │ [Live Telemetry] [Session Statistics] [Sessions] [Compare]│  │ │ │
│                         │ │  └─────────────────────────────────────────────────────────┘  │ │ │
│                         │ │                                                               │ │ │
│                         │ │  ┌─────────────────────────────────────────────────────────┐  │ │ │
│                         │ │  │ TAB CONTENT (switches per tab)                           │  │ │ │
│                         │ │  └─────────────────────────────────────────────────────────┘  │ │ │
│                         │ │                                                               │ │ │
│                         │ │  ┌─────────────────────────────────────────────────────────┐  │ │ │
│                         │ │  │ DISCLAIMER (persistent, bottom of content)               │  │ │ │
│                         │ │  │ ⚠ Simulation data - No HP/torque estimation             │  │ │ │
│                         │ │  └─────────────────────────────────────────────────────────┘  │ │ │
│                         │ └─────────────────────────────────────────────────────────────┘ │ │
│                         └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## TAB 1: Live Telemetry

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TAB 1: LIVE TELEMETRY                                                                       │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ RECORDING CONTROLS (card_simple, horizontal layout)                                 │   │
│  │ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌──────────────────────────────────────────┐  │   │
│  │ │ ▶ Start │ │ ■ Stop  │ │ 💾 Save │ │ [● RECORDING] 00:02:15  (alert INFO)     │  │   │
│  │ │ Primary │ │Secondary│ │Secondary│ │ pulse animation when sim_running          │  │   │
│  │ └─────────┘ └─────────┘ └─────────┘ └──────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 6 CHART GRID (responsive_grid_css - 2 columns on desktop, 1 on mobile)             │   │
│  │                                                                                     │   │
│  │  ┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐   │   │
│  │  │ RPM (create_line_chart)         │ │ SPEED (create_line_chart)               │   │   │
│  │  │ ┌─────────────────────────────┐ │ │ ┌─────────────────────────────────────┐ │   │   │
│  │  │ │ LineChart: rpm series       │ │ │ │ LineChart: speed series           │ │   │   │
│  │  │ │ Red reference line @ 6500   │ │ │ │ Clean line, no ref lines          │ │   │   │
│  │  │ │ SERIES_1 color              │ │ │ │ SERIES_2 color                    │ │   │   │
│  │  │ │ Height: 300px               │ │ │ │ Height: 300px                     │ │   │   │
│  │  │ └─────────────────────────────┘ │ │ └─────────────────────────────────────┘ │   │   │
│  │  └─────────────────────────────────┘ └─────────────────────────────────────────┘   │   │
│  │                                                                                     │   │
│  │  ┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐   │   │
│  │  │ COOLANT TEMP (create_line_chart)│ │ ENGINE LOAD (create_line_chart)         │   │   │
│  │  │ ┌─────────────────────────────┐ │ │ ┌─────────────────────────────────────┐ │   │   │
│  │  │ │ LineChart: coolant_temp     │ │ │ │ LineChart: engine_load            │ │   │   │
│  │  │ │ Green band: 85-95°C (GOOD)  │ │ │ │ Range: 0-105%                     │ │   │   │
│  │  │ │ Yellow band: 95-105°C (WARN)│ │ │ │ SERIES_3 color                    │ │   │   │
│  │  │ │ Red band: 105-125°C (CRIT)  │ │ │ │ Height: 300px                     │ │   │   │
│  │  │ │ SERIES_4 color              │ │ │ └─────────────────────────────────────┘ │   │   │
│  │  │ └─────────────────────────────┘ │ └─────────────────────────────────────────┘   │   │
│  │  └─────────────────────────────────┘                                              │   │
│  │                                                                                     │   │
│  │  ┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐   │   │
│  │  │ THROTTLE (create_line_chart)    │ │ FUEL TRIM (create_line_chart - multi)   │   │   │
│  │  │ ┌─────────────────────────────┐ │ │ ┌─────────────────────────────────────┐ │   │   │
│  │  │ │ LineChart: throttle_pos     │ │ │ │ LineChart: stft (SERIES_1)        │ │   │   │
│  │  │ │ Range: 0-105%               │ │ │ │ LineChart: ltft (SERIES_2)        │ │   │   │
│  │  │ │ SERIES_5 color              │ │ │ │ Zero reference line                 │ │   │   │
│  │  │ │ Height: 300px               │ │ │ │ Green band: ±10% (GOOD)           │ │   │   │
│  │  │ └─────────────────────────────┘ │ │ │ Yellow band: ±20% (WARN)          │ │   │   │
│  │  └─────────────────────────────────┘ │ │ Red band: ±30% (CRITICAL)         │ │   │   │
│  │                                      │ └─────────────────────────────────────┘ │   │   │
│  │                                      └─────────────────────────────────────────┘   │   │
│  │                                                                                     │   │
│  │  EMPTY STATE (empty_state component) - when len(telemetry_history) < 2            │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │ 📊 No Live Data                                                            │   │   │
│  │  │ Start a recording or simulation to see real-time telemetry charts.        │   │   │
│  │  └─────────────────────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## TAB 2: Session Statistics

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TAB 2: SESSION STATISTICS                                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SESSION SELECTOR (card_simple)                                                        │   │
│  │ Active Session: [Session Name - Scenario - Date ▼]  (selectbox)                      │   │
│  │ ─────────────────────────────────────────────────────────────────────────────────   │   │
│  │ Shows: Active recording session (session_id) OR most recent completed session       │   │
│  │ Empty state when no sessions exist                                                  │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ KEY METRIC CARDS (auto_fit_grid_css - min 200px, 4 cards on desktop, 2 on mobile)  │   │
│  │                                                                                     │   │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐              │   │
│  │  │ ⬆ PEAK RPM   │ │ 🏁 MAX SPEED │ │ 📊 AVG SPEED │ │ ⏱ DURATION   │              │   │
│  │  │ 6,234 RPM    │ │ 142 km/h     │ │ 48 km/h      │ │ 12m 34s      │              │   │
│  │  │ (card_simple)│ │ (card_simple)│ │ (card_simple)│ │ (card_simple)│              │   │
│  │  │ Value: H2    │ │ Value: H2    │ │ Value: H2    │ │ Value: H2    │              │   │
│  │  │ Label: LABEL │ │ Label: LABEL │ │ Label: LABEL │ │ Label: LABEL │              │   │
│  │  │ + sparkline  │ │ + sparkline  │ │ + sparkline  │ │ + sparkline  │              │   │
│  │  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘              │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ DETAILED STATISTICS (table component)                                                │   │
│  │ ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │ │ Metric                      │ Value                              │ Unit        │ │   │
│  │ ├─────────────────────────────┼────────────────────────────────────┼─────────────┤ │   │
│  │ │ Session Name                │ Highway Run #3                     │ -           │ │   │
│  │ │ Scenario                    │ highway                            │ -           │ │   │
│  │ │ Start Time                  │ 2026-11-17 14:23:12                │ -           │ │   │
│  │ │ End Time                    │ 2026-11-17 14:35:46                │ -           │ │   │
│  │ │ Duration                    │ 12m 34s                            │ seconds     │ │   │
│  │ │ Distance (est.)             │ 9.8                                │ km          │ │   │
│  │ │ Records                     │ 754                                │ count       │ │   │
│  │ │ Data Source                 │ SIMULATION                         │ -           │ │   │
│  │ │ Peak RPM                    │ 6,234                              │ RPM         │ │   │
│  │ │ Avg RPM                     │ 2,156                              │ RPM         │ │   │
│  │ │ Max Speed                   │ 142                                │ km/h        │ │   │
│  │ │ Avg Speed                   │ 48                                 │ km/h        │ │   │
│  │ │ Peak Coolant                │ 98                                 │ °C          │ │   │
│  │ │ Avg Coolant                 │ 92                                 │ °C          │ │   │
│  │ │ Peak Engine Load            │ 94                                 │ %           │ │   │
│  │ │ Avg Engine Load             │ 38                                 │ %           │ │   │
│  │ │ Peak Throttle               │ 98                                 │ %           │ │   │
│  │ │ Avg Throttle                │ 22                                 │ %           │ │   │
│  │ │ Avg STFT                    │ +2.3                               │ %           │ │   │
│  │ │ Min STFT                    │ -8.5                               │ %           │ │   │
│  │ │ Max STFT                    │ +12.1                              │ %           │ │   │
│  │ │ Avg LTFT                    │ -1.8                               │ %           │ │   │
│  │ │ Min LTFT                    │ -5.2                               │ %           │ │   │
│  │ │ Max LTFT                    │ +3.4                               │ %           │ │   │
│  │ └─────────────────────────────┴────────────────────────────────────┴─────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ TIME DISTRIBUTION HISTOGRAMS (responsive_grid_css - 2 columns)                     │   │
│  │                                                                                     │   │
│  │  ┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐   │   │
│  │  │ RPM DISTRIBUTION                │ │ SPEED DISTRIBUTION                    │   │   │
│  │  │ (create_bar_chart)              │ │ (create_bar_chart)                    │   │   │
│  │  │ ┌─────────────────────────────┐ │ │ ┌─────────────────────────────────────┐ │   │   │
│  │  │ │ BarChart: RPM bins          │ │ │ │ BarChart: Speed bins              │ │   │   │
│  │  │ │ SERIES_1 color              │ │ │ │ SERIES_2 color                    │ │   │   │
│  │  │ │ X: RPM range (500 RPM bins) │ │ │ │ X: Speed range (10 km/h bins)     │ │   │   │
│  │  │ │ Y: Time (seconds)           │ │ │ │ Y: Time (seconds)                 │ │   │   │
│  │  │ │ Height: 300px               │ │ │ │ Height: 300px                     │ │   │   │
│  │  │ └─────────────────────────────┘ │ │ └─────────────────────────────────────┘ │   │   │
│  │  └─────────────────────────────────┘ └─────────────────────────────────────────┘   │   │
│  │                                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  EMPTY STATES (empty_state component):                                                     │
│  - "No Active Session" - when no session_id and no completed sessions                     │
│  - "No Telemetry Records" - when session exists but has no records                        │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## TAB 3: Sessions

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TAB 3: SESSIONS                                                                             │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ RECORDING CONTROLS PANEL (card_simple)                                              │   │
│  │ ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │ │ SESSION NAME: [________________________] (text_input, placeholder: "My Session")│ │   │
│  │ │ SCENARIO:     [idle ▼] (selectbox: idle, city, highway, acceleration, custom) │ │   │
│  │ └─────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │ │ [▶ Start Recording] [■ Stop] [💾 Save Session]   [● RECORDING 00:01:23]        │ │   │
│  │ │   Primary              Secondary    Secondary       alert(INFO) w/ pulse       │ │   │
│  │ │   (disabled when       (disabled                                              │ │   │
│  │    recording)          when not                                                               │   │
│  │    recording)                                                            │ │   │
│  │ └─────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                     │   │
│  │ ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │ │ ⚠ Simulation Mode Active - Data is simulated, not from real vehicle            │ │   │
│  │ │    (alert WARNING when sim_scenario != "idle" or OBD mode is simulation)       │ │   │
│  │ └─────────────────────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ BULK ACTIONS BAR (shown when selected_session_ids not empty)                        │   │
│  │ [☐ Select All]  3 selected  [📊 Compare] [📥 Export CSV] [🗑 Delete]               │   │
│  │                    badge        button_ghost    button_ghost    button_danger       │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SESSIONS TABLE (table component)                                                     │   │
│  │ ┌────┬────┬─────────────────┬─────────┬────────────────┬─────┬──────┬──────┬────┬────┐│   │
│  │ │☐   │ ID │ Name            │Scenario │ Date/Time      │ Dur │Peak │ Max  │Avg │Act ││   │
│  │ │    │    │                 │         │                │     │RPM  │Speed │Spd │    ││   │
│  │ ├────┼────┼─────────────────┼─────────┼────────────────┼─────┼─────┼──────┼────┼────┤│   │
│  │ │☑   │ 42 │ Highway Run #3  │ highway │ 2026-11-17     │12m34│6234 │ 142  │ 48 │👁⬇🗑││   │
│  │ │☐   │ 41 │ City Commute    │ city    │ 2026-11-16     │28m11│ 4821│  65  │ 22 │👁⬇🗑││   │
│  │ │☐   │ 40 │ Idle Test       │ idle    │ 2026-11-15     │ 5m02│  892│   0  │  0 │👁⬇🗑││   │
│  │ │☐   │ 39 │ Accel Run       │ accel   │ 2026-11-14     │ 3m45│ 6800│ 180  │ 72 │👁⬇🗑││   │
│  │ └────┴────┴─────────────────┴─────────┴────────────────┴─────┴─────┴──────┴────┴────┘│   │
│  │                                                                                     │   │
│  │ Columns: Select (checkbox), ID, Name, Scenario, Date/Time, Duration, Peak RPM,    │   │
│  │          Max Speed, Avg Speed, Records, Actions (View/Export/Delete)               │   │
│  │                                                                                     │   │
│  │ Row Actions (per row):                                                             │   │
│  │ - 👁 View: Expander with session details (same as statistics tab)                  │   │
│  │ - ⬇ Export: st.download_button with CSV                                           │   │
│  │ - 🗑 Delete: button_danger with confirmation                                       │   │
│  │                                                                                     │   │
│  │ Table Props:                                                                       │   │
│  │ - TableProps(striped=True, hoverable=True, compact=True)                          │   │
│  │ - TableColumn(key="select", header="", width="40px")                              │   │
│  │ - TableColumn(key="id", header="ID", width="60px", align="right")                 │   │
│  │ - TableColumn(key="name", header="Name", width="200px")                          │   │
│  │ - TableColumn(key="scenario", header="Scenario", width="100px", badge=True)      │   │
│  │ - TableColumn(key="date", header="Date/Time", width="160px")                     │   │
│  │ - TableColumn(key="duration", header="Dur", width="80px", align="right")         │   │
│  │ - TableColumn(key="peak_rpm", header="Peak RPM", width="90px", align="right",    │   │
│  │                format="numeric")                                                  │   │
│  │ - TableColumn(key="max_speed", header="Max Speed", width="90px", align="right",  │   │
│  │                format="numeric", suffix=" km/h")                                  │   │
│  │ - TableColumn(key="avg_speed", header="Avg Speed", width="90px", align="right",  │   │
│  │                format="numeric", suffix=" km/h")                                  │   │
│  │ - TableColumn(key="records", header="Records", width="80px", align="right")      │   │
│  │ - TableColumn(key="actions", header="Actions", width="120px")                    │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  EMPTY STATE (empty_state component):                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ 📁 No Sessions Recorded                                                             │   │
│  │ Start a recording session to capture telemetry data for analysis.                   │   │
│  │ [▶ Start Recording] (button_primary)                                                │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## TAB 4: Compare Sessions

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ TAB 4: COMPARE SESSIONS                                                                     │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ SESSION SELECTOR (card_simple)                                                        │   │
│  │                                                                                     │   │
│  │ When compare_sessions is None/empty:                                               │   │
│  │ ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │ │ 📊 Select Sessions to Compare                                                   │ │   │
│  │ │ Choose 2 or more sessions from the Sessions tab, or select below:               │ │   │
│  │ │                                                                                 │ │   │
│  │ │ Session A: [Session Name ▼] (selectbox - all sessions)                         │ │   │
│  │ │ Session B: [Session Name ▼] (selectbox - all sessions, different from A)       │ │   │
│  │ │ Session C: [Session Name ▼] (selectbox - optional, up to 5)                    │ │   │
│  │ │ Session D: [Session Name ▼] (selectbox - optional)                             │ │   │
│  │ │ Session E: [Session Name ▼] (selectbox - optional)                             │ │   │
│  │ │                                                                                 │ │   │
│  │ │ [📊 Compare Selected] (button_primary, disabled if < 2 selected)               │ │   │
│  │ │ [🗑 Clear] (button_ghost)                                                       │ │   │
│  │ └─────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                                     │   │
│  │ When compare_sessions has 2+ sessions:                                             │   │
│  │ ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │ │ Comparing: [Session A - highway] [Session B - city] [Session C - idle]  [🗑]   │ │   │
│  │ │ (badge NEUTRAL per session with × to remove)                                   │ │   │
│  │ └─────────────────────────────────────────────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ COMPARISON CHARTS (create_comparison_chart OR create_line_chart multi-series)       │   │
│  │                                                                                     │   │
│  │  ┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐   │   │
│  │  │ RPM COMPARISON                  │ │ SPEED COMPARISON                      │   │   │
│  │  │ (create_comparison_chart)       │ │ (create_comparison_chart)             │   │   │
│  │  │ ┌─────────────────────────────┐ │ │ ┌─────────────────────────────────────┐ │   │   │
│  │  │ │ ComparisonChart:            │ │ │ │ ComparisonChart:                  │ │   │   │
│  │  │ │ Series A: Session A RPM     │ │ │ │ Series A: Session A Speed         │ │   │   │
│  │  │ │ Series B: Session B RPM     │ │ │ │ Series B: Session B Speed         │ │   │   │
│  │  │ │ Series C: Session C RPM     │ │ │ │ Series C: Session C Speed         │ │   │   │
│  │  │ │ Normalized X: elapsed sec   │ │ │ │ Normalized X: elapsed sec         │ │   │   │
│  │  │ │ SERIES_1, SERIES_2, SERIES_3│ │ │ │ SERIES_1, SERIES_2, SERIES_3      │ │   │   │
│  │  │ │ Height: 300px               │ │ │ │ Height: 300px                     │ │   │   │
│  │  │ └─────────────────────────────┘ │ │ └─────────────────────────────────────┘ │   │   │
│  │  └─────────────────────────────────┘ └─────────────────────────────────────────┘   │   │
│  │                                                                                     │   │
│  │  ┌─────────────────────────────────┐ ┌─────────────────────────────────────────┐   │   │
│  │  │ COOLANT COMPARISON              │ │ ENGINE LOAD COMPARISON                │   │   │
│  │  │ (create_comparison_chart)       │ │ (create_comparison_chart)             │   │   │
│  │  │ ┌─────────────────────────────┐ │ │ ┌─────────────────────────────────────┐ │   │   │
│  │  │ │ ComparisonChart:            │ │ │ │ ComparisonChart:                  │ │   │   │
│  │  │ │ Coolant temp per session    │ │ │ │ Engine load per session           │ │   │   │
│  │  │ │ Normal bands shown          │ │ │ │ 0-105% range                      │ │   │   │
│  │  │ └─────────────────────────────┘ │ │ └─────────────────────────────────────┘ │   │   │
│  │  └─────────────────────────────────┘ └─────────────────────────────────────────┘   │   │
│  │                                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐   │   │
│  │  │ THROTTLE COMPARISON                                                         │   │   │
│  │  │ (create_comparison_chart)                                                   │   │   │
│  │  │ ┌─────────────────────────────────────────────────────────────────────────┐ │   │   │
│  │  │ │ ComparisonChart: Throttle position per session                          │ │   │   │
│  │  │ │ 0-105% range                                                            │ │   │   │
│  │  │ └─────────────────────────────────────────────────────────────────────────┘ │   │   │
│  │  └─────────────────────────────────────────────────────────────────────────────┘   │   │
│  │                                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│  │ COMPARISON SUMMARY TABLE (table component)                                          │   │
│  │ ┌────────────────────────┬──────────────────┬──────────────────┬──────────────────┐ │   │
│  │ │ Metric                 │ Session A        │ Session B        │ Session C        │ │   │
│  │ │                        │ (highway)        │ (city)           │ (idle)           │ │   │
│  │ ├────────────────────────┼──────────────────┼──────────────────┼──────────────────┤ │   │
│  │ │ Duration               │ 12m 34s          │ 28m 11s          │ 5m 02s           │ │   │
│  │ │ Distance               │ 9.8 km           │ 12.3 km          │ 0.0 km           │ │   │
│  │ │ Peak RPM               │ 6,234            │ 4,821            │ 892              │ │   │
│  │ │ Avg RPM                │ 2,156            │ 1,456            │ 780              │ │   │
│  │ │ Max Speed              │ 142 km/h         │ 65 km/h          │ 0 km/h           │ │   │
│  │ │ Avg Speed              │ 48 km/h          │ 22 km/h          │ 0 km/h           │ │   │
│  │ │ Peak Coolant           │ 98°C             │ 92°C             │ 88°C             │ │   │
│  │ │ Avg Coolant            │ 92°C             │ 89°C             │ 86°C             │ │   │
│  │ │ Peak Engine Load       │ 94%              │ 68%              │ 12%              │ │   │
│  │ │ Avg Engine Load        │ 38%              │ 24%              │ 8%               │ │   │
│  │ │ Peak Throttle          │ 98%              │ 72%              │ 15%              │ │   │
│  │ │ Avg Throttle           │ 22%              │ 18%              │ 5%               │ │   │
│  │ │ Avg STFT               │ +2.3%            │ -1.2%            │ +0.5%            │ │   │
│  │ │ Avg LTFT               │ -1.8%            │ -3.4%            │ -0.2%            │ │   │
│  │ │ Data Source            │ SIMULATION       │ SIMULATION       │ SIMULATION       │ │   │
│  │ └────────────────────────┴──────────────────┴──────────────────┴──────────────────┘ │   │
│  │                                                                                     │   │
│  │ Table Props: TableProps(striped=True, hoverable=True, compact=True)                │   │
│  │ Columns: Metric + dynamic columns per session (numeric align right)                │   │
│  └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│  EMPTY STATE (empty_state component):                                                     │
│  - When no sessions selected: Instruction to select sessions                              │
│  - When < 2 sessions: "Select at least 2 sessions to compare"                            │
│  - When selected sessions have no data: "No telemetry data available for comparison"     │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Persistent Disclaimer (Bottom of All Tabs)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│ PERSISTENT DISCLAIMER (alert component, WARNING variant, compact)                          │
│                                                                                             │
│  ⚠  IMPORTANT: This application displays SIMULATED vehicle data for demonstration purposes. │
│     • No horsepower or torque estimation is performed                                       │
│     • No acceleration time claims are made                                                  │
│     • All metrics are derived from OBD-II PID readings only                                 │
│     • For real vehicle data, connect an ELM327 adapter and select "Real OBD" mode          │
│     • CSV exports include `is_simulated` column for data provenance                        │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Design Token Usage Reference

### Colors
| Use Case | Token |
|----------|-------|
| RPM chart line | `SERIES_1` (#FF6B35) |
| Speed chart line | `SERIES_2` (#00D4AA) |
| Coolant chart line | `SERIES_3` (#FFD93D) |
| Engine Load chart line | `SERIES_4` (#6C5CE7) |
| Throttle chart line | `SERIES_5` (#E17055) |
| STFT (fuel trim) | `SERIES_1` |
| LTFT (fuel trim) | `SERIES_2` |
| Coolant GOOD band | `CHART_GOOD` |
| Coolant WARNING band | `CHART_WARNING` |
| Coolant CRITICAL band | `CHART_CRITICAL` |
| Fuel trim GOOD band (±10%) | `CHART_GOOD` |
| Fuel trim WARNING band (±20%) | `CHART_WARNING` |
| Fuel trim CRITICAL band (±30%) | `CHART_CRITICAL` |
| Recording indicator | `STATUS_INFO` + pulse |
| Simulation warning | `STATUS_WARNING` |
| Connection badge (connected) | `STATUS_SUCCESS` |
| Connection badge (disconnected) | `STATUS_CRITICAL` |
| Scenario badges | `badge()` with NEUTRAL variant |
| Severity badges | `badge()` with CRITICAL/WARNING/SUCCESS/INFO |
| Data source badge (SIMULATION) | `DATASOURCE_SIMULATION` |
| Data source badge (REAL) | `DATASOURCE_REAL` |

### Typography
| Element | Token |
|---------|-------|
| Page title | `FONT_SIZE_H1`, `FONT_WEIGHT_NUMERIC` |
| Page subtitle | `FONT_SIZE_BODY`, `FONT_WEIGHT_LABEL` |
| Tab labels | `FONT_SIZE_LABEL`, `LETTER_SPACING_LABEL` |
| Card values (metrics) | `FONT_SIZE_H2`, `FONT_WEIGHT_NUMERIC`, `FONT_FAMILY_MONO` |
| Card labels | `FONT_SIZE_LABEL`, `LETTER_SPACING_LABEL` |
| Table headers | `FONT_SIZE_LABEL`, `FONT_WEIGHT_LABEL`, `LETTER_SPACING_LABEL` |
| Table cells | `FONT_SIZE_BODY`, `FONT_FAMILY_MONO` for numeric |
| Chart titles | `FONT_SIZE_H4`, `FONT_WEIGHT_LABEL` |
| Axis labels | `FONT_SIZE_CAPTION` |
| Disclaimer text | `FONT_SIZE_CAPTION` |

### Spacing
| Context | Token |
|---------|-------|
| Page header bottom margin | `GAP_SECTION` (32px) |
| Between tab content sections | `GAP_CARD` (24px) |
| Between cards in grid | `GAP_CARD` (24px) |
| Inside card padding | `SPACE_5` (20px) |
| Between form fields | `GAP_FIELD` (16px) |
| Between buttons inline | `GAP_INLINE` (12px) |
| Chart height | Fixed 300px (not token) |
| Disclaimer margin top | `GAP_SECTION` (32px) |

### Radius
| Element | Token |
|---------|-------|
| Cards | `RADIUS_LG` (12px) |
| Buttons | `RADIUS_MD` (8px) |
| Badges | `RADIUS_PILL` (9999px) |
| Chart containers | `RADIUS_LG` (12px) |
| Table | `RADIUS_MD` (8px) |

### Shadows
| Element | Token |
|---------|-------|
| Cards | `SHADOW_MD` |
| Page header | `SHADOW_SM` |
| Dropdown/popover | `SHADOW_LG` |

---

## Chart Configuration Reference

### Live Charts (Tab 1) - create_line_chart()
```python
LineChartConfig(
    title="RPM",
    x_axis="time",
    y_axis="RPM",
    series=[
        LineSeries(name="RPM", data=..., color=SERIES_1, dash="solid"),
    ],
    reference_lines=[{"value": 6500, "color": STATUS_CRITICAL, "dash": "dash", "label": "Redline"}],
    height=300,
    show_legend=False,
    margin=dict(l=50, r=20, t=40, b=40),
)
```

### Comparison Charts (Tab 4) - create_comparison_chart()
```python
ComparisonConfig(
    title="RPM Comparison",
    x_axis="elapsed_seconds",
    y_axis="RPM",
    series=[
        ComparisonSeries(name=f"Session {sid}", data=..., color=SERIES_PALETTE[i]),
        ...
    ],
    normalize_x=True,  # elapsed seconds from session start
    height=300,
    show_legend=True,
    legend_position="top",
)
```

### Histograms (Tab 2) - create_bar_chart()
```python
BarChartConfig(
    title="RPM Distribution",
    x_axis="RPM Range",
    y_axis="Time (seconds)",
    series=[
        BarSeries(name="Time", data=..., color=SERIES_1),
    ],
    height=300,
    show_legend=False,
    bargap=0.1,
)
```

### Stat Card Sparklines - create_sparkline()
```python
SparklineConfig(
    data=...,
    color=SERIES_1,
    height=40,
    show_area=True,
    area_opacity=0.15,
    reference_line=None,
)
```

---

## Implementation Priority Order

1. **Tab 3 (Sessions)** - Core recording workflow, table, bulk actions
2. **Tab 1 (Live Telemetry)** - 6 charts, recording controls, empty states
3. **Tab 2 (Session Statistics)** - Stat cards, detailed table, histograms
4. **Tab 4 (Compare Sessions)** - Selector, comparison charts, summary table
5. **Global** - Page header, disclaimer, session state initialization, auto-update loop

---

## Session State Initialization (Must Match Existing Exactly)

```python
def _init_performance_state():
    """Initialize performance-specific session state keys."""
    defaults = {
        "sim_running": False,
        "sim_scenario": "idle",
        "telemetry_history": [],
        "session_id": None,
        "last_update": time.time(),
        "selected_session_ids": [],
        "compare_sessions": None,
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default
```

---

## Preservation Notes (Critical)

- ❌ Do NOT rename any session state keys
- ❌ Do NOT change session state structure (dict/list types)
- ❌ Do NOT remove any existing functionality
- ✅ All backend service calls preserved exactly
- ✅ All database operations preserved exactly
- ✅ All OBD service interactions preserved exactly
- ✅ CSV export format preserved exactly (including `is_simulated` column)
- ✅ Recording workflow logic preserved exactly
- ✅ Comparison normalization (elapsed seconds) preserved exactly
- ✅ Telemetry history cap at 300 points preserved exactly
- ✅ Data source labeling (SIMULATION/REAL) preserved exactly