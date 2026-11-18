# Phase 6: UI/UX Modernization — Stage 1 Read-Only Audit Summary

**Project:** i20 AI Garage  
**Date:** 2026-11-16  
**Phase:** 6 — UI/UX Modernization (Stage 1: Read-Only Audit Complete)

---

## 1. Project Architecture Overview

### 1.1 Application Structure

```
i20-AI/
├── app.py                      # Main entry point (global CSS, session state, routing)
├── config.py                   # Centralized config: THEME, vehicle specs, scenarios, thresholds
├── components/
│   ├── sidebar.py             # Navigation, vehicle status, connection indicators
│   └── charts.py              # Plotly chart components (gauges, lines, multi-series)
├── modules/                   # 9 page modules
│   ├── dashboard.py           # Real-time gauges, telemetry cards, live charts
│   ├── diagnostics.py         # DTC scan, AI diagnosis, rule engine, history
│   ├── performance.py         # Session analytics, comparison, statistics
│   ├── maintenance.py         # Records CRUD, upcoming service, intervals
│   ├── vehicle_profile.py     # Vehicle info, engine specs, connections, diagnostics
│   ├── ai_assistant.py        # Chat mode + Diagnostic mode with LM Studio
│   ├── obd_connection.py      # 8-step wizard: Mode → Port → Connect → ECU → PIDs
│   ├── reports.py             # 4 report types × 2 formats (HTML/PDF)
│   └── settings.py            # 6 tabs: AI, OBD, Simulation, Data, Backup, About
├── services/
│   ├── database.py            # SQLite with migration integration
│   ├── ai_service.py          # LM Studio client
│   ├── obd_service.py         # ELM327 adapter + simulation
│   ├── diagnostic_engine.py   # YAML rule engine + AI diagnosis
│   ├── rule_engine.py         # Deterministic diagnostic rules
│   ├── report_generator.py    # HTML/PDF report generation
│   └── migrations/            # Custom migration framework (baseline + versions)
└── tests/                     # 89 migration tests + database tests (all passing)
```

### 1.2 Technology Stack

| Layer | Technology |
|-------|------------|
| UI Framework | Streamlit 1.38+ |
| Visualization | Plotly 5.24+ (gauges, lines, multi-series, subplots) |
| Database | SQLite 3 + custom migration framework |
| AI/LLM | LM Studio (local OpenAI-compatible API) |
| OBD-II | python-OBD (real) + custom simulation engine |
| Diagnostics | YAML rule engine + structured AI output |
| Reporting | HTML (interactive) + PDF (print-ready) |

---

## 2. Complete Page Inventory (9 Pages)

### 2.1 Dashboard (`modules/dashboard.py`) — ~550 lines
**Purpose:** Real-time vehicle monitoring hub

**Key Components:**
- **Gauge Cluster** (6 gauges): RPM, Speed, Coolant Temp, Throttle, Engine Load, Battery Voltage
- **Telemetry Cards**: Compact metric cards with sparklines
- **Live Charts**: Multi-series time-series (RPM/Speed, Coolant/Load, Throttle/Fuel Trim)
- **Simulation Controls**: Scenario selector, start/stop, interval config
- **Status Panel**: Connection, AI, simulation status indicators

**Session State Dependencies:**
- `sim_running`, `sim_scenario`, `telemetry_history` (300 points), `session_id`
- `obd_connected`, `ai_connected`

**Visual Patterns:**
- Custom CSS cards with `THEME` colors
- Plotly `Indicator` gauges with threshold zones (green/amber/red)
- `create_multi_series_chart` for small-multiples telemetry
- Responsive column layouts (3/2/1 column breakpoints)

---

### 2.2 Diagnostics (`modules/diagnostics.py`) — ~900 lines
**Purpose:** DTC scanning, AI diagnosis, rule engine evaluation, history

**Tabs:**
1. **Scan Panel** — OBD scan trigger, DTC list with severity badges, live telemetry snapshot
2. **DTC Detail** — Expandable DTC cards with causes, verification steps, urgency
3. **AI Diagnosis** — Structured AI output: primary/secondary diagnoses, probable causes (confidence), recommended actions (priority/safety), safety warnings, missing info
4. **Rule Engine** — Deterministic rule matches with evidence, confidence, severity
5. **History** — Previous diagnostic reports with session linkage

**Data Models Used:**
- `DiagnosticResult`, `DiagnosticSeverity`, `DataSource`, `PrimaryDiagnosis`, `ProbableCause`, `RecommendedAction`, `SafetyLevel`

**Visual Patterns:**
- Severity color coding (critical=red, major=amber, minor=blue, info=purple)
- Confidence badges (green≥70%, amber≥40%, red<40%)
- Urgency tags (immediate/soon/schedule/monitor)
- Structured card layouts with evidence lists

---

### 2.3 Performance (`modules/performance.py`) — ~700 lines
**Purpose:** Driving session analytics and comparison

**Tabs:**
1. **Live Charts** — Real-time session telemetry overlay
2. **Session Statistics** — Peak/avg RPM, speed, coolant, load, distance, fuel
3. **Sessions Panel** — List with export CSV/JSON, delete
4. **Compare Sessions** — Side-by-side metric comparison (small multiples)

**Visual Patterns:**
- Metric cards with tabular-nums font
- Comparison charts using `create_comparison_chart` (categorical colors)
- Session list with action buttons per row

---

### 2.4 Maintenance (`modules/maintenance.py`) — ~600 lines
**Purpose:** Service records, upcoming/overdue tracking, manufacturer intervals

**Tabs:**
1. **Records** — CRUD with modal forms, cost tracking, next service km/date
2. **Upcoming** — Calculated from intervals + current odometer (1000km window)
3. **Add/Edit** — Form with service type selector (predefined intervals)

**Key Logic:**
- `calculate_upcoming_from_intervals()` — computes due/overdue from `MAINTENANCE_INTERVALS`
- Odometer-based window (±1000km)
- Cost summaries and interval compliance

---

### 2.5 Vehicle Profile (`modules/vehicle_profile.py`) — ~400 lines
**Purpose:** Read-only vehicle specification reference

**Tabs:**
1. **Vehicle Info** — Make, model, year, engine, transmission, fuel, market, ECU, VIN
2. **Engine Specs** — Displacement, cylinders, power/torque curves, compression, fuel system, emissions, redline/idle
3. **Connections** — OBD port, baudrate, protocol, supported PIDs count
4. **Diagnostics** — DTC history summary, AI diagnosis count, rule evaluations

---

### 2.6 AI Assistant (`modules/ai_assistant.py`) — ~930 lines
**Purpose:** Local AI chat + structured diagnostic mode

**Modes:**
- **Chat Mode** (3:1 split): Full-width conversation + sidebar (model info, quick prompts, session mgmt)
- **Diagnostic Mode**: Structured DTC/symptom input → AI diagnosis result rendering

**Features:**
- Conversation persistence (SQLite)
- Vehicle context injection (live OBD readings)
- Quick prompt chips (P0300, coolant, fuel trim, battery, load, maintenance)
- Loading animation with pulsing dots
- LM Studio connection status badge (online/offline/checking)

**Session State:**
- `ai_session_id`, `ai_messages[]`, `ai_loading`, `ai_mode`, `ai_diagnostic_result`
- `ai_status`, `ai_models`, `ai_model_available`

---

### 2.7 OBD Connection (`modules/obd_connection.py`) — ~1100 lines
**Purpose:** 8-step guided wizard for real OBD-II hardware setup

**Wizard Steps:**
1. **Mode Selection** — Simulation vs Real OBD-II
2. **Port Discovery** — Auto-scan serial ports, identify likely ELM327 adapters (VID/PID heuristics)
3. **Port Selection** — Manual port pick + baudrate/protocol/timeout config
4. **Connection** — Multi-baudrate fallback (38400→115200→9600→57600), progress bar
5. **ECU Detection** — VIN, CALID, CVN, ECU name, fuel status, runtime
6. **PID Discovery** — Grid of supported/unsupported standard PIDs
7. **Success** — Summary metrics + navigation to Dashboard/Diagnostics
8. **Error** — Troubleshooting guide (hardware, power, pairing, drivers, settings, vehicle)

**Connected State View:**
- Health check (connected, query test, PID count)
- Quick navigation + disconnect

**Visual Patterns:**
- Step indicator with active/completed/error states
- Port cards with likely-obd badging
- PID grid (green=supported, amber=unsupported)
- Connection log (expander with timestamped entries)

---

### 2.8 Reports (`modules/reports.py`) — ~650 lines
**Purpose:** Professional report generation (4 types × 2 formats)

**Report Types:**
1. **Comprehensive Diagnostic** — DTCs, AI diagnosis, rule findings, telemetry, recommendations
2. **Vehicle Health** — Component status, maintenance history, safety observations
3. **Performance** — Session metrics, sensor statistics, time-series analysis
4. **Maintenance** — History, upcoming/overdue, cost summaries, intervals

**Tabs:**
1. **Generate** — Type/format/session/diagnosis selectors + vehicle override
2. **Preview** — HTML iframe preview + "Open in new tab" link
3. **Download** — Direct download buttons (HTML/PDF) + saved reports browser

**Batch Generation:** All 4 reports at once

---

### 2.9 Settings (`modules/settings.py`) — ~1300 lines
**Purpose:** Comprehensive configuration across 6 tabs

**Tabs:**
1. **AI & LM Studio** — Base URL, model selector (live refresh), temperature (slider), timeout
2. **OBD Connection** — Mode radio (simulation/real), port/baudrate/protocol (real mode only)
3. **Simulation** — Update interval, refresh interval, scenario reference cards
4. **Data & Export** — Per-session CSV/JSON, diagnostic JSON, maintenance CSV, full archive JSON
5. **Backup & Restore** — Create backup, list with restore/delete, DB stats (8 metrics)
6. **About** — App info, vehicle profile, engine specs, legal disclaimers

**Persistence:** All settings saved to SQLite `settings` table via `db.set_setting()`/`get_setting()`

---

## 3. Shared Components & Design Tokens

### 3.1 Theme System (`config.py:145-157`)
```python
THEME = {
    "bg_primary": "#1a1d21",      # Dark graphite
    "bg_secondary": "#23272e",    # Slightly lighter
    "bg_card": "#2a2e36",         # Card background
    "border": "#3a3f4a",          # Subtle borders
    "text_primary": "#e8eaed",    # Main text
    "text_secondary": "#9aa3ad",  # Secondary text
    "accent_blue": "#00b4d8",     # Telemetry cyan
    "accent_green": "#2ecc71",    # Healthy/OK
    "accent_amber": "#f39c12",    # Warning
    "accent_red": "#e74c3c",      # Critical/Error
    "accent_purple": "#9b59b6",   # AI/Assistant
}
```

**Usage:** Injected globally via `app.py:inject_global_css()` and locally in each module via `st.markdown(css, unsafe_allow_html=True)`

### 3.2 Chart Color System (`components/charts.py`)
- **SERIES_COLORS** (fixed categorical order for CVD safety): [blue, amber, green, purple, red]
- **STATUS_COLORS** (semantic, distinct from series): good/warning/serious/critical
- **GAUGE_THRESHOLDS** — Per-metric green/amber/red zones

### 3.3 Sidebar (`components/sidebar.py`)
- **NAVIGATION_ITEMS** — 9 pages with icons, labels, descriptions
- **Vehicle Status Summary** — Read-only spec card
- **Connection Indicators** — OBD, Data Source, AI (dots + details)
- **Simulation Status** — Badge + scenario description

### 3.4 Session State Architecture (`app.py:359-396`)
| Key | Purpose | Scope |
|-----|---------|-------|
| `current_page` | Active navigation | Global |
| `sim_running`, `sim_scenario` | Simulation control | Global |
| `telemetry_history` | 300-point rolling buffer | Global |
| `session_id` | Active telemetry session | Global |
| `obd_connected`, `ai_connected` | Connection status | Global |
| `wizard_step` | OBD wizard progress | OBD page |
| `ai_session_id`, `ai_messages[]`, `ai_mode` | AI assistant | AI page |

---

## 4. Visual & UX Audit Findings

### 4.1 Strengths (Preserve)
1. **Consistent Dark Theme** — Professional automotive aesthetic, good contrast
2. **Semantic Color Coding** — Severity/status colors used consistently across pages
3. **Component Reuse** — Charts, sidebar, gauges shared via components/
4. **Responsive Layouts** — Column-based grids adapt (3/2/1)
5. **Rich Interactions** — Wizards, expandable cards, tabs, progress bars, loading states
6. **Data Density** — Telemetry dashboards pack information efficiently
7. **Contextual Help** — Tooltips, captions, scenario descriptions throughout

### 4.2 Inconsistencies (Address in Redesign)

| Issue | Location | Impact |
|-------|----------|--------|
| **CSS Duplication** | Every module has inline `st.markdown(css, ...)` | Maintenance burden, drift risk |
| **Spacing Inconsistency** | Margins/padding vary (1rem, 1.5rem, 2rem) | Visual rhythm broken |
| **Card Border Radius** | 8px, 10px, 12px, 16px mixed | Component library needed |
| **Button Sizing** | `use_container_width` mixed with fixed widths | Touch targets inconsistent |
| **Typography Scale** | h1-h6, but body/caption sizes ad-hoc | No type scale |
| **Shadow System** | None, some, heavy — no elevation tokens | Depth perception unclear |
| **Focus States** | Missing on custom HTML buttons | Accessibility gap |
| **Loading Patterns** | Spinner, progress bar, skeleton, pulsing dots — no standard | Cognitive load |

### 4.3 Streamlit-Specific Constraints
- **`unsafe_allow_html=True`** used extensively for custom CSS/HTML
- **Widget keys** must be unique across pages (manual management)
- **`st.rerun()`** used for state transitions (wizard steps, mode switches)
- **`st.components.v1.html`** for report previews (iframe limitations)
- **CSS injection** via `st.markdown` — no native theming API
- **Sidebar width** fixed (~300px) — navigation labels truncate

### 4.4 Accessibility Gaps (WCAG 2.1 AA Target)
- ❌ Custom HTML buttons lack `role="button"`, `tabindex`, keyboard handlers
- ❌ Color-only status indicators (no icons/text labels)
- ❌ No focus visible styles on interactive elements
- ❌ Iframe report previews lack title/description
- ❌ Form labels not always associated (`<label for="">`)
- ❌ Heading hierarchy sometimes skipped (h1→h3)
- ❌ No skip-to-main-content link
- ❌ ARIA live regions for dynamic updates (toasts, loading)

---

## 5. Data Flow & Session State Coupling

### 5.1 Cross-Page Dependencies
```
Dashboard ←→ Diagnostics (shared: telemetry_history, session_id)
Dashboard ←→ Performance (shared: session_id, telemetry sessions)
Diagnostics ←→ AI Assistant (shared: ai_diagnostic_result, DTC context)
OBD Connection → All pages (sets: obd_connected, mode, supported_pids)
Settings → All pages (persists: intervals, timeouts, LM Studio config)
Reports ← Diagnostics/Performance/Maintenance (consumes: sessions, diagnoses, records)
```

### 5.2 Service Initialization (`app.py:388-408`)
- Services created once per session via `get_database()`, `get_ai_service()`, `get_obd_service()`
- Singleton pattern via `@st.cache_resource` in `services/__init__.py`
- Connection status checked on startup, cached in session state

---

## 6. Phase 6 Stage 2+ Roadmap (Per Specification)

### Stage 2: Design Direction
- Define visual language (automotive diagnostic professional)
- Finalize palette (extend THEME with semantic tokens)
- Typography scale (display/heading/body/caption/mono)
- Spacing system (4px base unit)
- Component anatomy spec (card, button, input, badge, table, chart)

### Stage 3: Design System Foundations
- `design_tokens.py` — centralized tokens (colors, spacing, radius, shadows, transitions)
- `components/ui.py` — reusable primitives (Button, Card, Badge, Input, Select, Table, Modal, Toast)
- `components/charts_v2.py` — chart factory with token-driven styling
- `utils/css.py` — CSS-in-Python utilities, eliminate inline CSS strings

### Stage 4: Global Shell Redesign
- Sidebar: collapsible, icon-only mode, keyboard navigation
- Top bar: page title, breadcrumb, global actions, user/status
- Navigation: grouped sections, badges, search (Cmd+K)
- Status bar: persistent OBD/AI/Simulation indicators

### Stage 5: Page-by-Page Redesign (9 pages)
| Page | Priority | Key Redesign Targets |
|------|----------|---------------------|
| Dashboard | P0 | Gauge cluster density, telemetry cards, live chart toolbar |
| Diagnostics | P0 | DTC table, diagnosis result panels, evidence trees |
| AI Assistant | P0 | Chat layout, diagnostic mode split, prompt chips |
| OBD Connection | P0 | Wizard stepper, port cards, PID grid, error recovery |
| Reports | P1 | Generation form, preview iframe, download manager |
| Performance | P1 | Session table, comparison builder, stat cards |
| Maintenance | P1 | Record table, upcoming timeline, interval cards |
| Vehicle Profile | P2 | Spec cards, connection health, diagnostic summary |
| Settings | P2 | Tabbed forms, validation, backup/restore UX |

### Stage 6: Responsive & Mobile
- Breakpoints: ≤640px (mobile), 641-1024px (tablet), >1024px (desktop)
- Sidebar drawer on mobile, stacked gauges, scrollable tables

### Stage 7: Accessibility (WCAG 2.1 AA)
- Semantic HTML, ARIA, focus management, color contrast, keyboard support

### Stage 8: Regression Testing
- Visual snapshot tests (Playwright), E2E flows, performance budgets

### Stage 9: Documentation
- Storybook-style component docs, token reference, migration guide

---

## 7. Acceptance Criteria Baseline (Pre-Redesign)

### 7.1 Functional (All Must Pass Post-Redesign)
- [ ] All 9 pages render without console errors
- [ ] Navigation works (sidebar + deep links)
- [ ] Simulation start/stop/scenario change functional
- [ ] OBD wizard completes 8 steps (simulation mode)
- [ ] AI chat sends/receives messages, persists to DB
- [ ] Diagnostic scan runs, shows DTCs, AI diagnosis renders
- [ ] Performance sessions record, statistics calculate, comparison works
- [ ] Maintenance CRUD, upcoming calculation correct
- [ ] Reports generate (4 types × HTML/PDF), preview, download
- [ ] Settings persist to DB, apply on reload

### 7.2 Visual/UX (Target Post-Redesign)
- [ ] Zero inline CSS strings (all via design system)
- [ ] Consistent 4px spacing grid
- [ ] Unified border radius (8px cards, 4px inputs, 16px modals)
- [ ] Semantic color tokens only (no raw hex in components)
- [ ] WCAG 2.1 AA contrast on all text/interactive elements
- [ ] Focus visible on all interactive elements
- [ ] Keyboard navigable: sidebar, wizard, forms, tables
- [ ] Mobile: sidebar drawer, stacked gauges, horizontal table scroll

### 7.3 Performance
- [ ] Initial load < 3s (Streamlit cold start)
- [ ] Page switch < 500ms (cached services)
- [ ] Chart render < 200ms (≤300 data points)
- [ ] No layout shift (CLS < 0.1)

---

## 8. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Streamlit CSS injection breaks on version upgrade | Medium | High | Abstract CSS generation, test on upgrades |
| `unsafe_allow_html` CSP restrictions | Low | Medium | Minimize raw HTML, prefer Streamlit components |
| Session state conflicts during redesign | High | Medium | Feature-flag new pages, parallel routing |
| Chart re-render performance on mobile | Medium | Medium | Virtualize large datasets, limit points |
| Migration of 9 pages in parallel | High | High | Sequential rollout, one page per PR |

---

## 9. Next Actions

1. **Create `docs/DESIGN_SYSTEM.md`** — Token definitions, component specs
2. **Build `components/design_tokens.py`** — Python constants for all design decisions
3. **Build `components/ui.py`** — Primitive component library
4. **Refactor `components/charts.py`** — Token-driven, remove hardcoded colors
5. **Redesign Sidebar** — Collapsible, accessible, icon-only mode
6. **Redesign Dashboard** — First page, proves design system
7. **Iterate through remaining 8 pages** — One per cycle

---

**End of Stage 1 Audit** — Ready for Stage 2: Design Direction