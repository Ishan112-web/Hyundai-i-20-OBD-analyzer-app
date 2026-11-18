# Phase 6 Stage 6: Responsive & Mobile — Phase 0 Read-Only Responsive Audit

**Date:** 2026-11-18  
**Status:** AUDIT COMPLETE — READY FOR IMPLEMENTATION  
**Baseline:** 415/415 tests passing, Stages 1-5.12 complete  

---

## Executive Summary

Completed read-only responsive audit across all **9 main pages** + **4 standalone report pages** (13 total) and the global shell. The application already has a **strong responsive foundation** through the Stage 3 Design System's grid system and CSS variable architecture. No fixed-width layouts were found — all pages use design system responsive grids (`AUTO_FIT_CARD_CSS`, `AUTO_FIT_METRIC_CSS`, `responsive_grid_css`) or native Streamlit columns.

**Key Finding:** The application is **~70% responsive-ready** out of the box. Remaining work is primarily: (1) canonical breakpoint enforcement across all CSS, (2) mobile navigation drawer, (3) touch target sizing, (4) table responsiveness strategy, (5) chart container responsiveness, and (6) semantic HTML/ARIA for custom content.

---

## 1. Breakpoint Architecture Audit

### 1.1 Current Breakpoint Definitions (tokens.py)

| Token | Value | Usage |
|-------|-------|-------|
| `BREAKPOINT_MOBILE` | `768px` | Mobile (<768px) |
| `BREAKPOINT_TABLET` | `1024px` | Tablet (768-1023px) |
| `BREAKPOINT_LAPTOP` | `1280px` | Laptop (1024-1279px) |
| `BREAKPOINT_DESKTOP` | `1280px` | Desktop (≥1280px) |

**Issues Found:**
- `BREAKPOINT_LAPTOP` and `BREAKPOINT_DESKTOP` both = `1280px` — laptop range undefined
- Missing: `BREAKPOINT_MOBILE_LANDSCAPE` (common at 568px)
- Missing: `BREAKPOINT_TABLET_PORTRAIT` / `LANDSCAPE` distinction
- No CSS variables exposed for these breakpoints (only Python constants)

### 1.2 Breakpoint Usage in Layout CSS (layout.py)

**Existing Media Queries in `LAYOUT_CSS`:**
```css
@media (max-width: 768px) {
  .i20-top-bar { padding: var(--i20-space-2) var(--i20-space-3); }
  .i20-top-bar__breadcrumb { display: none; }
  .i20-top-bar__status { gap: var(--i20-space-2); }
  .i20-wizard__steps { flex-wrap: wrap; gap: var(--i20-space-1); }
  .i20-wizard__step { padding: var(--i20-space-1) var(--i20-space-2); font-size: var(--i20-font-size-caption); }
  .i20-page-container { padding: var(--i20-space-3); }
  .i20-numeric { font-size: var(--i20-font-size-body-sm); }
}
```

**Gaps:**
- Only `max-width: 768px` breakpoint implemented
- No tablet (768-1023px) or laptop (1024-1279px) specific adjustments
- No CSS variable references for breakpoints (hardcoded `768px`)

### 1.3 Grid System Responsiveness (layout.py)

| Grid Helper | Implementation | Breakpoints |
|-------------|---------------|-------------|
| `responsive_grid_css(min_col, max_col)` | `grid-template-columns: repeat(auto-fit, minmax(min_col, 1fr));` | None (fluid) |
| `auto_fit_grid_css(min_width)` | `grid-template-columns: repeat(auto-fit, minmax(min_width, 1fr));` | None (fluid) |
| `fixed_grid_css(cols)` | `grid-template-columns: repeat(cols, 1fr);` | None (fixed) |
| `GAUGE_GRID_CSS` | 4-col desktop, auto-fit ≥280px | Mobile: 1-col via auto-fit |
| `AUTO_FIT_CARD_CSS` | auto-fit ≥320px | Fluid |
| `AUTO_FIT_METRIC_CSS` | auto-fit ≥200px | Fluid |

**Finding:** Grid system is **fluid-first** (auto-fit/minmax) — excellent foundation. No explicit breakpoint overrides needed for grid columns; they respond naturally.

---

## 2. Global Shell Responsiveness

### 2.1 Sidebar (components/sidebar.py + shell.py)

**Current State:**
- Fixed width ~300px (Streamlit default)
- No collapsible/drawer behavior
- Navigation labels truncate on narrow viewports
- Vehicle status, connection indicators, simulation status all stacked vertically

**Mobile Issues:**
- ❌ No hamburger menu / drawer toggle
- ❌ Sidebar consumes ~40% of mobile viewport
- ❌ No `sidebar_collapsed` state handling in shell (exists in session_state but unused)
- ❌ Connection indicators too wide for mobile

**Tablet Issues:**
- ⚠️ Labels may truncate at 768-1024px
- ⚠️ Vehicle info rows (label/value) may wrap awkwardly

### 2.2 Top Bar (shell.py + layout.py TopBar component)

**Current State:**
- Breadcrumbs hidden at ≤768px (via `LAYOUT_CSS`)
- Status indicators stack at ≤768px
- Page title + icon always visible

**Mobile Issues:**
- ⚠️ Three status pills (OBD, Sim, AI) may overflow at <400px
- ⚠️ No priority-based hiding (AI status less critical than OBD)
- ❌ No mobile-specific compact mode

### 2.3 Page Header (layout.py page_header)

**Current State:**
- Title + icon + subtitle
- Optional actions/status badges

**Mobile Issues:**
- ⚠️ Subtitle may wrap on long text
- ⚠️ Action buttons (if present) need touch target sizing

### 2.4 Page Container (shell.py page_container)

**Current State:**
- Padding: `var(--i20-space-4)` desktop, `var(--i20-space-3)` mobile (via LAYOUT_CSS)

**Finding:** ✅ Already responsive via CSS variable.

---

## 3. Page-by-Page Responsive Audit

### 3.1 Dashboard (`modules/dashboard.py`)

**Layout Structure:**
```
- Gauge Cluster: GAUGE_GRID_CSS (4-col desktop, auto-fit ≥280px)
- Telemetry Cards: AUTO_FIT_CARD_CSS (auto-fit ≥320px) × 10 cards
- Live Chart: create_line_chart() full-width
- Simulation Controls: 3 columns (scenario, interval, buttons)
- Status Panel: AUTO_FIT_CARD_CSS (3 cards)
```

**Responsive Behavior:**
| Breakpoint | Gauges | Telemetry | Chart | Controls | Status |
|------------|--------|-----------|-------|----------|--------|
| Mobile (<768) | 1-col stack | 1-col stack | Full width | 1-col stack | 1-col stack |
| Tablet (768-1023) | 2-col | 2-col | Full width | 2-col | 2-3 col |
| Laptop (1024-1279) | 3-col | 3-col | Full width | 3-col | 3-col |
| Desktop (≥1280) | 4-col | 4-col | Full width | 3-col | 3-col |

**Issues:**
- ✅ Grid system handles column collapse automatically
- ⚠️ Gauge minimum width 280px → 1-col at ~560px viewport (not 768px)
- ⚠️ Simulation controls: 3 `st.columns` don't collapse gracefully
- ⚠️ Status panel: 3 `st.columns` same issue

### 3.2 Diagnostics (`modules/diagnostics.py`)

**Layout Structure:**
```
- Tab 1 (Scan): Scan button + DTC table (full width) + live snapshot cards (AUTO_FIT_CARD_CSS)
- Tab 2 (Detail): DTC detail cards (card() full width)
- Tab 3 (AI Diagnosis): Full-width card() with structured content
- Tab 4 (Rule Engine): Findings cards (card()) + stats cards (AUTO_FIT_METRIC_CSS) + history table
- Tab 5 (History): table() component
```

**Responsive Behavior:**
| Breakpoint | Scan Panel | Detail | AI Diag | Rule Engine | History |
|------------|------------|--------|---------|-------------|---------|
| Mobile | Stacked | Stacked | Stacked | Stacked | Stacked |
| Tablet | Stacked | Stacked | Stacked | 2-col stats | Stacked |
| Laptop | 2-col (DTC + snapshot) | Stacked | Stacked | 2-col stats | Stacked |
| Desktop | 2-col | Stacked | Stacked | 2-col stats | Stacked |

**Issues:**
- ✅ DTC table uses `table()` component — needs horizontal scroll strategy
- ✅ Cards naturally stack
- ⚠️ Rule Engine stats: `AUTO_FIT_METRIC_CSS` (min 200px) works well
- ⚠️ No mobile-specific DTC table handling

### 3.3 Performance (`modules/performance.py`)

**Layout Structure:**
```
- Tab 1 (Live): 6 create_line_chart() in responsive_grid_css(min_col="500px")
- Tab 2 (Stats): Detailed table + 2 histograms (create_bar_chart)
- Tab 3 (Sessions): Session table with checkboxes + bulk actions
- Tab 4 (Compare): Comparison charts (create_comparison_chart) + summary table
```

**Responsive Behavior:**
| Breakpoint | Live Charts | Stats | Sessions | Compare |
|------------|-------------|-------|----------|---------|
| Mobile | 1-col (500px min) | Stacked | Stacked | Stacked |
| Tablet | 1-col | Stacked | Stacked | Stacked |
| Laptop | 2-col | 2-col | Stacked | 2-col |
| Desktop | 2-col | 2-col | Stacked | 2-col |

**Issues:**
- ⚠️ `responsive_grid_css(min_column_width="500px")` → single column until 1000px viewport
- ⚠️ Session table needs horizontal scroll
- ⚠️ Comparison charts side-by-side only at ≥1000px

### 3.4 Maintenance (`modules/maintenance.py`)

**Layout Structure:**
```
- Tab 1 (Records): Filter bar + record cards (card()) in auto_fit_grid_css(min_width="320px")
- Tab 2 (Add/Edit): Form (design system inputs) + quick-add buttons (button_ghost)
- Tab 3 (Upcoming): Upcoming cards (card()) in auto_fit_grid_css(min_width="320px")
```

**Responsive Behavior:**
| Breakpoint | Records Grid | Form | Upcoming Grid |
|------------|--------------|------|---------------|
| Mobile | 1-col | Stacked | 1-col |
| Tablet | 2-col | Stacked | 2-col |
| Laptop | 3-col | 2-col | 3-col |
| Desktop | 4-col | 2-col | 4-col |

**Issues:**
- ✅ Excellent — `auto_fit_grid_css(min_width="320px")` provides smooth scaling
- ✅ Form uses design system components (naturally responsive)
- ⚠️ Quick-add buttons: 9 `button_ghost` in row — need wrapping

### 3.5 Vehicle Profile (`modules/vehicle_profile.py`)

**Layout Structure:**
```
- Tab 1 (Info): Identity header + info grid (AUTO_FIT_CARD_CSS) + edit form
- Tab 2 (Engine Specs): Spec cards (AUTO_FIT_METRIC_CSS) + derived metrics (AUTO_FIT_CARD_CSS)
- Tab 3 (Connections): OBD/AI status cards (card())
- Tab 4 (Diagnostics): DTC cards (card()) + stat cards (card_simple + AUTO_FIT_METRIC_CSS) + actions
```

**Responsive Behavior:**
| Breakpoint | Info Grid | Specs Grid | Connections | Diagnostics |
|------------|-----------|------------|-------------|-------------|
| Mobile | 1-col | 1-col | Stacked | Stacked |
| Tablet | 2-col | 2-col | 2-col | 2-col stats |
| Laptop | 3-4 col | 3-col | 2-col | 2-col stats |
| Desktop | 4-5 col | 4-col | 2-col | 3-col stats |

**Issues:**
- ✅ Grids use design system auto-fit → smooth responsive
- ⚠️ **12 custom card HTML blocks** (P1 from Stage 5.11) — need migration to `card_simple()`
- ⚠️ Identity header: badge + text may need wrapping

### 3.6 AI Assistant (`modules/ai_assistant.py`)

**Layout Structure:**
```
- Chat Mode: 3:1 split (st.columns([3, 1])) — chat area + sidebar
- Diagnostic Mode: Full width card() with form + results
- Sidebar: Model info, quick prompts (6 chips), conversation management
```

**Responsive Behavior:**
| Breakpoint | Chat Mode | Diagnostic Mode | Sidebar |
|------------|-----------|-----------------|---------|
| Mobile | **Broken** — 3:1 split forces narrow chat | Full width ✅ | Hidden (needs drawer) |
| Tablet | 3:1 split (chat ~500px min) | Full width ✅ | Visible but cramped |
| Laptop | 3:1 split ✅ | Full width ✅ | Visible ✅ |
| Desktop | 3:1 split ✅ | Full width ✅ | Visible ✅ |

**Issues:**
- ❌ **Critical:** Chat mode 3:1 split using `st.columns([3, 1])` — sidebar doesn't collapse on mobile
- ❌ No mobile sidebar drawer implementation
- ⚠️ Quick prompt chips: 6 in row — need wrapping/flex
- ⚠️ Message bubbles: custom HTML — need touch-friendly padding

### 3.7 OBD Connection (`modules/obd_connection.py`)

**Layout Structure:**
```
- 8-step Wizard (wizard() component) — full width
- Connected State: Metric cards (AUTO_FIT_METRIC_CSS) + health check + quick nav
- PID Grid: AUTO_FIT_CARD_CSS (supported/unsupported badges)
```

**Responsive Behavior:**
| Breakpoint | Wizard | Connected Metrics | PID Grid |
|------------|--------|-------------------|----------|
| Mobile | Full width ✅ | 1-col | 1-col |
| Tablet | Full width ✅ | 2-col | 2-col |
| Laptop | Full width ✅ | 3-col | 3-col |
| Desktop | Full width ✅ | 4-col | 4-col |

**Issues:**
- ✅ Wizard component full-width — works at all breakpoints
- ✅ Grids use auto-fit → responsive
- ⚠️ **8 custom wizard/metric cards** (P1 from Stage 5.11) — need migration
- ⚠️ Wizard step indicators: may need mobile-friendly compact mode
- ⚠️ PID grid: badge + text in card — verify touch targets

### 3.8 Reports (`modules/reports.py`)

**Layout Structure:**
```
- Sidebar config (report type, format, session, diagnosis, vehicle override)
- Tab 1 (Generate): Report type cards (card_simple) in grid + batch generate
- Tab 2 (Preview): iframe preview + open in new tab
- Tab 3 (Download): Download buttons + saved reports list
```

**Responsive Behavior:**
| Breakpoint | Config Sidebar | Generate Grid | Preview | Download |
|------------|----------------|---------------|---------|----------|
| Mobile | Stacked (native sidebar) | 1-col | Full width iframe | Stacked |
| Tablet | Stacked | 2-col | Full width | Stacked |
| Laptop | Side-by-side | 3-col | Full width | 2-col |
| Desktop | Side-by-side | 4-col | Full width | 3-col |

**Issues:**
- ✅ Native Streamlit sidebar collapses on mobile
- ✅ Generate grid uses `card_simple` + auto-fit
- ⚠️ **3 custom report cards** (P1 from Stage 5.11) — need migration
- ⚠️ iframe preview: fixed height may need adjustment
- ⚠️ Saved reports list: custom cards — verify mobile layout

### 3.9 Settings (`modules/settings.py`)

**Layout Structure:**
```
- 6 Tabs (native st.tabs)
- Each tab: section_header() + forms (design system inputs) in columns
```

**Responsive Behavior:**
| Breakpoint | Tabs | Forms |
|------------|------|-------|
| Mobile | Vertical stack (native) | 1-col stack |
| Tablet | Horizontal | 1-2 col |
| Laptop | Horizontal | 2-col |
| Desktop | Horizontal | 2-col |

**Issues:**
- ✅ Native `st.tabs` responsive
- ✅ Forms use design system components
- ⚠️ Some tabs use `st.columns(2)` — verify mobile stacking

---

## 4. Shared Components Responsive Audit

### 4.1 Design System Components (components/ui/components.py)

| Component | Responsive Behavior | Issues |
|-----------|---------------------|--------|
| `button_*` | `width: 100%` on mobile via CSS | ✅ Touch targets need 44×44px minimum |
| `badge()` | Inline-flex, wraps naturally | ✅ Good |
| `card()` / `card_simple()` | Full width, content-driven | ✅ Good |
| `alert()` | Full width | ✅ Good |
| `table()` | **Horizontal overflow** — needs wrapper | ⚠️ Needs `.i20-table-wrapper { overflow-x: auto; }` |
| `form` inputs | `width: 100%` | ✅ Good |
| `empty_state()` | Full width, centered | ✅ Good |
| `skeleton_card()` | Matches card dimensions | ✅ Good |
| `wizard()` | Full width, steps flex-wrap | ✅ Good (via LAYOUT_CSS) |
| `sidebar()` / `top_bar()` | See Global Shell | See above |
| `status_indicator()` | Inline-flex | ✅ Good |
| `section_header()` | Full width | ✅ Good |

### 4.2 Chart Components (components/charts_v2.py)

**Current Behavior:**
- Charts render at container width (Plotly default)
- No explicit responsive configuration
- Height fixed per chart type (gauge: 250px, line: 300px, sparkline: 60px)

**Issues:**
- ⚠️ Gauge height 250px may be tall on mobile
- ⚠️ Sparkline height 60px — verify touch interaction
- ⚠️ No `config.responsive: true` in Plotly config
- ⚠️ Legend positioning may overlap on narrow containers

---

## 5. CSS Variable Architecture Audit (styles.py)

### 5.1 Current CSS Variables (100+ variables)

**Categories:**
- Colors: `--i20-color-*` (53 tokens)
- Spacing: `--i20-space-*` (12 base + aliases)
- Typography: `--i20-font-size-*`, `--i20-font-family-*`, `--i20-font-weight-*`, `--i20-letter-spacing-*`
- Radius: `--i20-radius-*` (7 tokens)
- Elevation: `--i20-shadow-*` (8 tokens)
- Transitions: `--i20-transition-*` (4 tokens)
- Z-index: `--i20-z-*` (6 tokens)
- Layout: `--i20-container-*`, `--i20-sidebar-width`, `--i20-topbar-height`
- Breakpoints: **MISSING** — no CSS variables for breakpoints

### 5.2 Missing CSS Variables for Responsive

```css
/* Needed for Phase 1 */
--i20-breakpoint-mobile: 768px;
--i20-breakpoint-tablet: 1024px;
--i20-breakpoint-laptop: 1280px;
--i20-breakpoint-desktop: 1280px;

/* Container max-widths */
--i20-container-mobile: 100%;
--i20-container-tablet: 720px;
--i20-container-laptop: 960px;
--i20-container-desktop: 1200px;

/* Touch targets */
--i20-touch-target-min: 44px;
--i20-touch-target-comfortable: 48px;
```

---

## 6. Session State & Functionality Preservation

### 6.1 34 Shared Session State Keys (from PHASE_6_PROGRESS.md)

All 34 keys must be preserved. Key categories:
- **Navigation:** `current_page`, `sidebar_collapsed`
- **Simulation:** `sim_running`, `sim_scenario`, `telemetry_history`, `session_id`
- **Connection:** `obd_connected`, `ai_connected`, `obd_mode`, `obd_port`, `supported_pids`
- **AI:** `ai_session_id`, `ai_messages`, `ai_loading`, `ai_mode`, `ai_diagnostic_result`, `ai_status`, `ai_models`, `ai_model_available`
- **OBD Wizard:** `wizard_step`, `wizard_mode`, `wizard_port`, `wizard_baudrate`, `wizard_protocol`, `ecu_info`, `supported_pids_list`, `connection_logs`
- **Reports:** `generated_reports`, `report_preview_html`, `selected_report_type`, `selected_format`, `selected_session`, `selected_diagnosis`, `vehicle_override`

**Audit Result:** ✅ No responsive changes should affect session state. All state is logical, not visual.

---

## 7. P2 Items from Stage 5.11 (Deferred to Stage 6)

| # | Issue | Pages | Stage 6 Action |
|---|-------|-------|----------------|
| 1 | Add semantic HTML (`<section>`, `<article>`) to custom card blocks | Vehicle Profile, OBD Connection, AI Assistant, Reports | Phase 7: Semantic HTML |
| 2 | Add ARIA labels to chat message bubbles | AI Assistant | Phase 7: Semantic HTML / Phase 8: Touch |
| 3 | Add `prefers-reduced-motion` support for skeleton pulse | OBD Connection, all pages with skeletons | Phase 2: Design System Foundation |
| 4 | Ensure all custom HTML uses `role` attributes | All pages with custom HTML | Phase 7: Semantic HTML |
| 5 | Validate responsive behavior of wizard component at mobile | OBD Connection | Phase 4: Page-by-page |
| 6 | Standardize metric card implementation across Performance, Vehicle Profile, OBD Connection | Performance, Vehicle Profile, OBD Connection | Phase 2: Card behavior / Phase 4 |

---

## 8. Responsive Audit Summary Matrix

| Area | Status | Priority | Phase |
|------|--------|----------|-------|
| **Breakpoint Tokens** | Python only, no CSS vars, laptop=desktop | P0 | Phase 1 |
| **Global Shell - Sidebar** | Fixed width, no mobile drawer | P0 | Phase 3 |
| **Global Shell - Top Bar** | Partial (breadcrumbs hidden) | P1 | Phase 3 |
| **Global Shell - Page Header** | Good | P2 | Phase 2 |
| **Grid System** | Fluid auto-fit — excellent | ✅ Done | — |
| **Dashboard** | Good (grids), controls need work | P1 | Phase 4 |
| **Diagnostics** | Good, table needs scroll | P1 | Phase 5 |
| **Performance** | Chart grid threshold high (500px) | P1 | Phase 4 |
| **Maintenance** | Excellent | ✅ Done | — |
| **Vehicle Profile** | Good grids, 12 custom cards | P1 | Phase 4 + P1 fixes |
| **AI Assistant** | Broken chat split on mobile | P0 | Phase 3 + Phase 4 |
| **OBD Connection** | Good, 8 custom cards | P1 | Phase 4 + P1 fixes |
| **Reports** | Good, 3 custom cards | P1 | Phase 4 + P1 fixes |
| **Settings** | Good | ✅ Done | — |
| **Table Component** | No horizontal scroll wrapper | P0 | Phase 5 |
| **Chart Responsiveness** | No Plotly responsive config | P1 | Phase 6 |
| **Touch Targets** | Not enforced (44×44px) | P0 | Phase 8 |
| **Semantic HTML** | Custom HTML uses `<div>` | P2 | Phase 7 |
| **Reduced Motion** | Not implemented | P2 | Phase 2 |
| **CSS Breakpoint Vars** | Missing | P0 | Phase 1 |

---

## 9. Implementation Phases Mapping (from Stage 6 Spec)

| Spec Phase | Audit Focus | Key Deliverables |
|------------|-------------|------------------|
| **Phase 0** | This audit document | `PHASE_6_STAGE_6_RESPONSIVE_AUDIT.md` ✅ |
| **Phase 1** | Breakpoint tokens → CSS vars, canonical media queries | `tokens.py` + `styles.py` + `layout.py` updates |
| **Phase 2** | Spacing scale, grid helpers, card behavior, text scaling, container widths | Design system responsive foundation |
| **Phase 3** | Mobile sidebar drawer, top bar compact, page header, shell integration | Global shell mobile-ready |
| **Phase 4** | 9 pages responsive implementation | Each page verified at 4 breakpoints |
| **Phase 5** | Table horizontal scroll, card fallback, column priority | Table strategy implemented |
| **Phase 6** | Plotly responsive config, gauge sizing, legend, sparkline | Charts responsive |
| **Phase 7** | Semantic HTML, ARIA, landmark roles | Custom HTML → semantic |
| **Phase 8** | 44×44px touch targets, gesture support, focus visible | Interaction audit |
| **Phase 9** | Global CSS consolidation, token→CSS var mapping | Single source of truth |
| **Phase 10** | Playwright viewport tests, visual regression, device testing | Test evidence |
| **Phase 11** | Agent orchestration (if available) | Parallel verification |
| **Phase 12** | Responsive design guide, breakpoint reference, migration notes | Documentation |

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Streamlit `st.columns` behavior changes on mobile | Medium | High | Test early, use CSS grid where possible |
| Sidebar drawer requires JS (Streamlit limitation) | High | High | Use session_state + CSS `:has()` or conditional rendering |
| Plotly chart re-render on resize | Medium | Medium | `config.responsive: true`, debounce |
| Custom HTML migration breaks semantics | Low | Medium | Phase 7 addresses systematically |
| 415 test regression | Low | High | Run full suite after each phase |
| Touch target enforcement on native Streamlit widgets | Medium | Medium | CSS `:where()` overrides for `.stButton`, `.stSelectbox` |

---

## 11. Acceptance Criteria Baseline (Pre-Implementation)

### 11.1 Functional (Must Preserve)
- [ ] All 9 pages render without console errors at all 4 breakpoints
- [ ] Navigation works (sidebar + deep links) — desktop sidebar, mobile drawer
- [ ] Simulation start/stop/scenario change functional
- [ ] OBD wizard completes 8 steps (simulation mode)
- [ ] AI chat sends/receives messages, sidebar accessible on mobile
- [ ] Diagnostic scan runs, shows DTCs, AI diagnosis renders
- [ ] Performance sessions record, statistics calculate, comparison works
- [ ] Maintenance CRUD, upcoming calculation correct
- [ ] Reports generate (4 types × HTML/PDF), preview, download
- [ ] Settings persist to DB, apply on reload
- [ ] All 34 shared session-state keys preserved
- [ ] All backend integrations preserved

### 11.2 Responsive Visual/UX (Target)
- [ ] **Mobile (<768px):** Sidebar drawer, stacked gauges, horizontal table scroll, 44×44px touch targets
- [ ] **Tablet (768-1023px):** 2-col grids, sidebar visible, charts side-by-side where space permits
- [ ] **Laptop (1024-1279px):** 3-col grids, full sidebar, all charts visible
- [ ] **Desktop (≥1280px):** 4-col+ grids, full sidebar, optimal density
- [ ] No horizontal scroll on page body (only in table wrappers)
- [ ] No layout shift (CLS < 0.1) on breakpoint transitions
- [ ] Text readable without zoom at all breakpoints
- [ ] Focus visible on all interactive elements at all breakpoints

### 11.3 Performance
- [ ] Initial load < 3s (Streamlit cold start)
- [ ] Page switch < 500ms (cached services)
- [ ] Chart render < 200ms (≤300 data points)
- [ ] No FOUC (Flash of Unstyled Content) on responsive CSS

---

## 12. Files to Modify (Implementation Roadmap)

### Phase 1: Canonical Breakpoints
- `components/ui/tokens.py` — Add/fix breakpoint tokens, expose as CSS vars
- `components/ui/styles.py` — Generate breakpoint CSS variables, add to `:root`
- `components/ui/layout.py` — Replace hardcoded `768px` with CSS var references

### Phase 2: Responsive Foundation
- `components/ui/styles.py` — Add spacing scale media queries, container widths, touch target minimums
- `components/ui/layout.py` — Enhance grid helpers with breakpoint awareness
- `components/ui/components.py` — Add touch target enforcement to button, badge, form components

### Phase 3: Mobile Navigation & Shell
- `components/shell.py` — Implement sidebar drawer logic, mobile top bar
- `components/sidebar.py` — Add collapsible/drawer variant
- `components/ui/layout.py` — TopBar mobile compact mode

### Phase 4: Page-by-Page (9 pages)
- `modules/dashboard.py` — Simulation controls stacking, status panel
- `modules/diagnostics.py` — Table wrapper, DTC card stacking
- `modules/performance.py` — Chart grid threshold, session table
- `modules/maintenance.py` — Quick-add button wrapping (verify)
- `modules/vehicle_profile.py` — Migrate 12 custom cards + identity header
- `modules/ai_assistant.py` — Mobile chat layout (sidebar drawer), prompt chip wrapping
- `modules/obd_connection.py` — Migrate 8 custom cards, wizard mobile verify
- `modules/reports.py` — Migrate 3 custom cards, iframe height
- `modules/settings.py` — Verify form column stacking

### Phase 5: Table Strategy
- `components/ui/components.py` — `table()` wrapper with horizontal scroll
- `components/ui/styles.py` — `.i20-table-wrapper` styles

### Phase 6: Chart Responsiveness
- `components/charts_v2.py` — Add `config.responsive: true`, responsive heights
- `components/ui/styles.py` — Chart container media queries

### Phase 7: Semantic HTML
- `modules/vehicle_profile.py` — `<section>`, `<article>` for card blocks
- `modules/ai_assistant.py` — Chat message `<article role="log">`
- `modules/obd_connection.py` — Wizard steps `<section>`
- `modules/reports.py` — Report cards `<article>`

### Phase 8: Touch Targets
- `components/ui/components.py` — Enforce 44×44px on all interactive
- `components/ui/styles.py` — Global touch target rules

### Phase 9: Global CSS
- `components/ui/styles.py` — Consolidate all responsive CSS, single source

### Phase 10: Testing
- Playwright viewport tests (new)
- Visual regression baseline (new)

### Phase 12: Documentation
- `docs/RESPONSIVE_DESIGN_GUIDE.md`
- `docs/BREAKPOINT_REFERENCE.md`
- Update `PHASE_6_PROGRESS.md`

---

## 13. Conclusion

The i20 AI Garage application has a **strong responsive foundation** through its fluid grid system (auto-fit/minmax) and design system token architecture. The majority of pages (Maintenance, Vehicle Profile grids, OBD Connection wizard, Reports, Settings) already behave well across breakpoints.

**Critical Path Items (P0):**
1. **Canonical breakpoints** — CSS variables + media query system (Phase 1)
2. **Mobile sidebar drawer** — Core navigation pattern (Phase 3)
3. **AI Assistant chat layout** — Broken 3:1 split on mobile (Phase 3/4)
4. **Table horizontal scroll** — Data accessibility (Phase 5)
5. **Touch targets 44×44px** — Mobile usability (Phase 8)

**High Priority (P1):**
- Dashboard simulation controls, Performance chart grid, custom card migrations (Vehicle Profile, OBD, Reports)

The audit confirms **no fixed-width layouts** and **no hardcoded colors/spacing** in page modules — all styling flows through the design system. This makes responsive implementation systematic rather than piecemeal.

---

*Report generated as part of Phase 6 Stage 6: Responsive & Mobile Implementation — Phase 0 Read-Only Responsive Audit*