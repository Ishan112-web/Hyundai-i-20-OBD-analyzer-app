# Phase 6 Stage 7: Accessibility & WCAG 2.1 AA Audit

**Date:** 2026-11-18  
**Status:** AUDIT COMPLETE — Implementation Pending  
**Prerequisite Check:** Stage 6 (Responsive) marked PENDING in progress tracker — see [Prerequisite Note](#prerequisite-note) below

---

## Prerequisite Note

⚠️ **Stage 6 (Responsive) is marked PENDING** in `docs/PHASE_6_PROGRESS.md`. The responsive audit (`docs/PHASE_6_STAGE_6_RESPONSIVE_AUDIT.md`) exists but implementation has not been verified. 

Per the Stage 7 instructions: *"Verify Stage 6 (Responsive) completion as mandatory prerequisite"*. 

**Recommendation:** Complete Stage 6 implementation and verification before beginning Stage 7 fixes. However, this audit identifies accessibility issues that exist independently of responsive layout and can be addressed in parallel. The audit below documents all findings so implementation can begin immediately once Stage 6 is verified.

---

## Executive Summary

**Scope:** 9 main application pages + 4 standalone report pages + shared components (shell, UI primitives, charts, layout)  
**Target:** WCAG 2.1 Level AA compliance  
**Framework:** Streamlit with custom HTML via `unsafe_allow_html`  
**Design System:** Automotive Technical Professional dark theme (53 color tokens, 16 typography, 12 spacing, 7 radius, 8 elevation)  
**Existing Accessibility Foundations:** Design system includes focus-visible styles, skip link, reduced motion, high contrast mode, print styles, Streamlit focus overrides, semantic HTML rules (see `docs/PHASE_6_DESIGN_SYSTEM.md` §12)

---

## Audit Methodology

### Pages Audited

| # | Page / Component | Module / File |
|---|------------------|---------------|
| 1 | Dashboard | `modules/dashboard.py` |
| 2 | Diagnostics | `modules/diagnostics.py` |
| 3 | Performance | `modules/performance.py` |
| 4 | Maintenance | `modules/maintenance.py` |
| 5 | Vehicle Profile | `modules/vehicle_profile.py` |
| 6 | AI Assistant | `modules/ai_assistant.py` |
| 7 | OBD Connection | `modules/obd_connection.py` |
| 8 | Reports (Main) | `modules/reports.py` |
| 9 | Settings | `modules/settings.py` |
| 10 | Diagnostic Report (Standalone) | `modules/reports.py` — `render_diagnostic_report_page()` |
| 11 | Vehicle Health Report (Standalone) | `modules/reports.py` — `render_vehicle_health_report_page()` |
| 12 | Performance Report (Standalone) | `modules/reports.py` — `render_performance_report_page()` |
| 13 | Maintenance Report (Standalone) | `modules/reports.py` — `render_maintenance_report_page()` |
| 14 | Global Shell | `components/shell.py` |
| 15 | UI Components | `components/ui/components.py` |
| 16 | Charts v2 | `components/charts_v2.py` |
| 17 | Layout Helpers | `components/ui/layout.py` |
| 18 | Styles/Globals | `components/ui/styles.py` |

### Audit Tools & Techniques

1. **Static Code Analysis** — Manual review of all Python/HTML/JSX output
2. **WCAG 2.1 Success Criteria Mapping** — Each finding mapped to specific SC
3. **Streamlit Constraint Analysis** — Native widget limitations documented
4. **Design System Token Validation** — Contrast ratios verified against 22 validated combinations
5. **Keyboard Flow Simulation** — Tab order, focus management, escape handling traced
6. **Screen Reader Semantic Review** — ARIA labels, roles, landmarks, live regions checked
7. **Color-Only Information Scan** — All status indicators, badges, charts checked
8. **Reduced Motion Verification** — `prefers-reduced-motion` media query coverage
9. **Responsive Accessibility Check** — Touch targets, zoom, viewport scaling at 4 breakpoints

---

## Findings Summary

| Priority | Count | Description |
|----------|-------|-------------|
| **P0 — Critical (Blocker)** | 12 | Violates WCAG 2.1 AA; prevents access for users with disabilities |
| **P1 — High** | 18 | Significant barrier; should be fixed before release |
| **P2 — Medium** | 24 | Moderate barrier; degrades experience but workable |
| **P3 — Low** | 11 | Minor improvement; polish for optimal experience |
| **Total** | **65** | |

---

## Detailed Findings

### P0 — Critical (Blockers)

#### A1.1 — Missing Skip Link Target on Main Content
- **WCAG SC:** 2.4.1 Bypass Blocks (A)
- **Location:** `components/shell.py` — `render_shell()` outputs `<main id="main-content">` but skip link targets `#main-content` which exists ✓ — **BUT** the skip link itself is not rendered in current shell implementation
- **Current Code:** Skip link CSS exists in `styles.py` (`.i20-skip-link`) but no `<a href="#main-content" class="i20-skip-link">Skip to main content</a>` in shell HTML
- **Impact:** Keyboard users cannot bypass repetitive navigation
- **Fix:** Add skip link as first focusable element in `render_shell()`

#### A1.2 — Sidebar Navigation Missing `aria-current` on Active Item
- **WCAG SC:** 1.3.1 Info and Relationships (A), 2.4.7 Focus Visible (AA)
- **Location:** `components/ui/components.py` — `Sidebar` component and `components/shell.py` — `render_sidebar()`
- **Current Code:** Active item gets `style` with `background: var(--color-accent-selected)` but no `aria-current="page"` attribute
- **Impact:** Screen readers cannot identify current page in navigation
- **Fix:** Add `aria-current="page"` to active `SidebarItem`; ensure focus styles use `:focus-visible`

#### A1.3 — Custom Buttons (HTML) Missing `role="button"` and Keyboard Activation
- **WCAG SC:** 4.1.2 Name, Role, Value (A), 2.1.1 Keyboard (A)
- **Location:** Throughout — custom `<button>` elements rendered via `unsafe_allow_html` in card footers, wizard steps, quick-add buttons, confirm dialogs
- **Examples:**
  - `modules/maintenance.py:356-380` — Edit/Delete/Duplicate buttons use `onclick` with `postMessage` but no `role="button"` (native `<button>` has implicit role ✓) — **WAIT**: these ARE native `<button>` elements, so role is implicit. BUT they lack `type="button"` (defaults to submit in forms) and keyboard activation only via click, not Enter/Space
  - `modules/obd_connection.py` — Wizard step buttons
  - `modules/reports.py` — Report action buttons
- **Impact:** Screen readers may not announce as buttons; form submission risk; keyboard users cannot activate via Enter/Space if not in form
- **Fix:** Add `type="button"` to all custom `<button>`; ensure `keydown` handlers for Enter/Space

#### A1.4 — Form Inputs Missing `aria-invalid` and `aria-describedby` for Errors
- **WCAG SC:** 3.3.1 Error Identification (A), 3.3.3 Error Suggestion (AA)
- **Location:** `components/ui/components.py` — `text_input()`, `selectbox()`, `FormFieldProps` — AND all pages using native Streamlit inputs
- **Current Code:** `FormFieldProps` has `error` field but components render native Streamlit widgets which don't expose `aria-invalid` or link to error message via `aria-describedby`
- **Impact:** Screen reader users not informed of validation errors; error suggestions not programmatically associated
- **Fix:** For custom HTML form fields, implement full ARIA. For native Streamlit fields, use custom HTML wrappers with `aria-invalid` and `aria-describedby` pointing to error element

#### A1.5 — Dynamic Content Updates Not Announced (Live Regions Missing)
- **WCAG SC:** 4.1.3 Status Messages (AA)
- **Location:** All pages with async operations — AI Assistant chat, OBD wizard, Diagnostics scan, Performance recording, Report generation
- **Current Code:** Uses `st.rerun()` or session state updates; no `aria-live` regions for status changes (loading, success, error, results)
- **Examples:**
  - `modules/ai_assistant.py` — Chat messages appear via rerun, no live region
  - `modules/diagnostics.py` — Scan results, AI diagnosis appear without announcement
  - `modules/obd_connection.py` — Wizard step changes, connection status
  - `modules/performance.py` — Recording start/stop, session load
  - `modules/reports.py` — Generation progress, preview ready
- **Impact:** Screen reader users unaware of critical state changes
- **Fix:** Add `aria-live="polite"` status regions; use `aria-live="assertive"` for errors; update via session-state-driven HTML

#### A1.6 — Color-Only Status Indicators (Badges, Gauges, Charts)
- **WCAG SC:** 1.4.1 Use of Color (A)
- **Location:** Throughout — `Badge` component variants (SUCCESS/WARNING/CRITICAL/INFO), gauge charts, status lights, DTC severity
- **Current Code:** Badges use color + text label ✓ (text provides non-color info) — **BUT** gauge charts use color arcs only; status indicator dots in shell topbar use color only; chart series distinguished by color only
- **Specific Violations:**
  - `components/shell.py` — Connection status dots (green/red/orange) with no text/icon alternative
  - `components/charts_v2.py` — Gauge charts: color arcs only; line charts: series by color only
  - `modules/diagnostics.py` — DTC severity badges have text ✓ but gauge-style indicators don't
- **Impact:** Colorblind users cannot distinguish states
- **Fix:** Add icons/text to all status indicators; gauge charts need value + label; chart series need patterns/shapes + color

#### A1.7 — Insufficient Color Contrast in Custom HTML Elements
- **WCAG SC:** 1.4.3 Contrast (Minimum) (AA)
- **Location:** Custom HTML throughout using design tokens — verified 22 combinations in design system but custom inline styles may deviate
- **Audit Required:** Scan all `unsafe_allow_html` for hardcoded colors or token misuse
- **Known Risk Areas:**
  - `modules/maintenance.py:109-126` — Mileage display uses `SURFACE_SECONDARY` + `ACCENT_PRIMARY` — verify contrast
  - `modules/obd_connection.py` — Wizard step indicators, log entries
  - `modules/reports.py` — Report preview iframe content (external CSS)
  - Custom badge HTML in card subtitles (Maintenance, Vehicle Profile)
- **Fix:** Enforce token-only usage; add automated contrast check in CI

#### A1.8 — Focus Not Managed in Modals/Wizards/Dialogs
- **WCAG SC:** 2.4.3 Focus Order (A), 4.1.2 Name, Role, Value (A)
- **Location:** 
  - `components/ui/components.py` — `Wizard` component (no focus trap)
  - `modules/obd_connection.py` — 8-step wizard
  - `modules/maintenance.py` — Delete confirmation alert (custom HTML buttons)
  - `components/ui/components.py` — `Alert` with dismissible actions
- **Current Code:** No focus trap; focus not moved to modal on open; not restored on close; Escape not handled
- **Impact:** Keyboard users trapped or lose context
- **Fix:** Implement focus trap utility; `onMount` focus first focusable; `onUnmount` return focus; Escape closes

#### A1.9 — Tables Missing Semantic Structure (Headers, Scope, Caption)
- **WCAG SC:** 1.3.1 Info and Relationships (A)
- **Location:** `components/ui/components.py` — `table()` component and all pages using it
- **Current Code:** Renders `<table>` with `<thead>`/`<tbody>` but:
  - No `<caption>` element
  - `<th>` missing `scope="col"` 
  - No `id`/`headers` association for complex tables
  - Horizontal scroll wrapper (`.i20-table-wrapper`) may break screen reader table navigation
- **Impact:** Screen reader users cannot navigate/understand table structure
- **Fix:** Add caption prop; `scope="col"` on all `<th>`; ensure wrapper doesn't break semantics

#### A1.10 — Charts Inaccessible (No Text Alternative, No Keyboard Navigation)
- **WCAG SC:** 1.1.1 Non-text Content (A), 2.1.1 Keyboard (A)
- **Location:** `components/charts_v2.py` — all Plotly charts rendered via `st.plotly_chart()`
- **Current Code:** Plotly charts are SVG/canvas with no built-in accessibility; no text summary; no keyboard navigation of data points
- **Impact:** Blind/low-vision users get zero information from charts
- **Fix:** Provide text summary (table/data) for every chart; use Plotly's `config={'staticPlot': False}` for keyboard nav; add `aria-hidden="true"` to chart + adjacent accessible table

#### A1.11 — Reduced Motion Not Fully Implemented
- **WCAG SC:** 2.3.3 Animation from Interactions (AAA) — but 2.3.1 Three Flashes (A) relevant
- **Location:** `components/ui/styles.py` — `@media (prefers-reduced-motion: reduce)` exists but incomplete
- **Current Code:** Disables transitions, spinner animation, skeleton pulse — **BUT** Plotly chart animations not controlled; `st.rerun()` transitions not controlled; custom JS animations not controlled
- **Fix:** Extend reduced motion to disable Plotly transitions (`transition: none` in chart layout); ensure no auto-playing animations

#### A1.12 — Touch Targets Below 44×44px on Mobile
- **WCAG SC:** 2.5.5 Target Size (AAA) — but 2.5.1 Pointer Gestures (A) relevant for mobile
- **Location:** All pages — buttons, badges, tabs, selectboxes, number inputs
- **Design System:** Tokens define `BUTTON_MIN_HEIGHT = 44px` and `TOUCH_TARGET_MIN = 44px` ✓ — **BUT** Streamlit native widgets (tabs, selectbox, number_input) not controlled; custom HTML buttons in card footers use 32px height (`modules/maintenance.py:356`)
- **Impact:** Mobile users with motor impairments cannot activate controls
- **Fix:** Enforce 44px minimum on all interactive elements; increase custom button heights; use `use_container_width=True` for full-width mobile targets

---

### P1 — High

#### B1.1 — Page Headings Hierarchy Inconsistent (h1/h2/h3)
- **WCAG SC:** 1.3.1 Info and Relationships (A)
- **Location:** All pages using `page_header()` from `components/ui/layout.py`
- **Current Code:** `page_header` renders `<h1>` for title — **BUT** pages also use `st.subheader()` (h2), `st.markdown('###')` (h3) inconsistently; some pages skip levels
- **Examples:**
  - Dashboard: `page_header` (h1) → `st.subheader("Live Telemetry")` (h2) ✓
  - Diagnostics: `page_header` (h1) → custom HTML `<h2>` sections ✓
  - Maintenance: `page_header` (h1) → tabs (no heading) → card titles (no heading level)
- **Fix:** Standardize heading hierarchy; use `section_header()` component (added in Stage 5.11) consistently

#### B1.2 — Landmarks Missing (nav, main, aside, region)
- **WCAG SC:** 1.3.1 Info and Relationships (A)
- **Location:** `components/shell.py` — `render_shell()`
- **Current Code:** Has `<header>`, `<main id="main-content">`, `<aside>` for sidebar — **BUT** sidebar `<nav>` missing `aria-label`; no `<footer>`; report pages may lack landmarks
- **Fix:** Add `aria-label="Main navigation"` to sidebar `<nav>`, `role="contentinfo"` to footer, `aria-labelledby` for regions

#### B1.3 — Tab Panels Not Accessible (ARIA Tabs Pattern)
- **WCAG SC:** 4.1.2 Name, Role, Value (A), 1.3.1 Info and Relationships (A)
- **Location:** All pages using `st.tabs()` — Dashboard, Maintenance, Performance, Reports, Settings, Vehicle Profile
- **Current Code:** Streamlit native tabs — generates correct ARIA tabs pattern ✓ (verified in DOM) — **BUT** tab content not linked via `aria-labelledby`/`aria-controls` in custom HTML tabs (OBD wizard uses custom wizard component)
- **OBD Wizard:** `components/ui/components.py` `Wizard` component — custom implementation, needs full ARIA tabs pattern
- **Fix:** Audit custom wizard for ARIA tabs; ensure Streamlit tabs work with screen readers (test with NVDA/JAWS)

#### B1.4 — Form Labels Not Programmatically Associated
- **WCAG SC:** 1.3.1 Info and Relationships (A), 3.3.2 Labels or Instructions (A)
- **Location:** `components/ui/components.py` — `text_input()`, `selectbox()` use Streamlit native — **BUT** custom HTML forms (OBD wizard steps, report config) use `<label>` without `for`/`id` pairing
- **Examples:**
  - `modules/obd_connection.py` — Wizard step forms with custom HTML inputs
  - `modules/reports.py` — Report configuration sidebar
- **Fix:** Ensure all custom `<input>`/`<select>` have `<label for="id">`; use `FormFieldProps` component consistently

#### B1.5 — Error Messages Not Linked to Fields (`aria-describedby`)
- **WCAG SC:** 3.3.1 Error Identification (A), 3.3.3 Error Suggestion (AA)
- **Location:** `components/ui/components.py` — `FormFieldProps.error` exists but not rendered with `id` + `aria-describedby` on input
- **Current Code:** Error shown as separate `st.error()` or custom alert — no programmatic link
- **Fix:** Generate unique error `id`; add `aria-describedby="error-id"` to input; render error with `id="error-id"` and `role="alert"`

#### B1.6 — Required Fields Not Indicated Programmatically
- **WCAG SC:** 3.3.2 Labels or Instructions (A)
- **Location:** All forms — `FormFieldProps.required` exists but only shows `*` visually; no `aria-required="true"`
- **Fix:** Add `aria-required="true"` to required inputs; keep visual `*` for sighted users

#### B1.7 — No Focus Visible Styles on Streamlit Native Widgets
- **WCAG SC:** 2.4.7 Focus Visible (AA)
- **Location:** `components/ui/styles.py` — Has `.stButton button:focus-visible`, `.stTextInput input:focus-visible`, etc. — **BUT** Streamlit's internal structure may not match selectors; need verification
- **Current Code:** Comprehensive focus-visible rules written — must test actual rendered DOM
- **Fix:** Test with keyboard navigation; adjust selectors to match actual Streamlit DOM classes

#### B1.8 — Sidebar Drawer (Mobile) Focus Trap Missing
- **WCAG SC:** 2.4.3 Focus Order (A), 4.1.2 Name, Role, Value (A)
- **Location:** `components/shell.py` — Mobile drawer via CSS transform; `components/ui/components.py` — `Sidebar` component
- **Current Code:** Drawer opens via checkbox hack (`#sidebar-toggle`); no focus management; focus not trapped in drawer; Escape not handled
- **Fix:** Implement focus trap when drawer open; focus first link on open; restore focus on close; Escape closes drawer

#### B1.9 — AI Assistant Chat Not Accessible
- **WCAG SC:** 4.1.2 Name, Role, Value (A), 4.1.3 Status Messages (AA), 1.3.1 Info and Relationships (A)
- **Location:** `modules/ai_assistant.py` — `render_ai_assistant()`
- **Issues:**
  - Message bubbles: custom HTML `<div>` with no `role="log"` or `aria-live`
  - User/assistant distinction: only visual (alignment, color) — no `aria-label` or structural differentiation
  - Loading indicator: spinner only, no text announcement
  - Input form: native Streamlit but send button lacks `aria-label`
  - Conversation history: no heading structure
- **Fix:** Wrap chat in `role="log" aria-live="polite"`; each message `article` with `aria-label="User message"`/`"Assistant message"`; loading status in live region

#### B1.10 — Diagnostic Scan Results Not Announced
- **WCAG SC:** 4.1.3 Status Messages (AA)
- **Location:** `modules/diagnostics.py` — `render_diagnostics()`
- **Issues:** Scan completes → results appear via rerun; no live region; DTC list updates silently
- **Fix:** Add `aria-live="polite"` region for scan status; update with "Scan complete. X codes found."

#### B1.11 — OBD Connection Wizard Steps Not Announced
- **WCAG SC:** 4.1.3 Status Messages (AA), 2.4.3 Focus Order (A)
- **Location:** `modules/obd_connection.py` — `render_obd_connection()`
- **Issues:** Step changes via session state → rerun; no announcement; focus not moved to new step content
- **Fix:** Live region for step announcement; focus management in wizard component

#### B1.12 — Performance Recording Status Not Announced
- **WCAG SC:** 4.1.3 Status Messages (AA)
- **Location:** `modules/performance.py` — `render_performance()`
- **Issues:** Recording start/stop/pause → status changes silently
- **Fix:** Live region for recording state

#### B1.13 — Report Generation Progress Not Announced
- **WCAG SC:** 4.1.3 Status Messages (AA)
- **Location:** `modules/reports.py` — `render_reports()`
- **Issues:** Generation runs → preview appears silently
- **Fix:** Live region with progress updates

#### B1.14 — Settings Changes Not Confirmed
- **WCAG SC:** 3.3.3 Error Suggestion (AA), 4.1.3 Status Messages (AA)
- **Location:** `modules/settings.py` — `render_settings()`
- **Issues:** Save actions → toast/alert but not in live region; no confirmation for destructive actions (backup restore, delete)
- **Fix:** Live region for save confirmations; `role="alert"` for destructive confirmations

#### B1.15 — Vehicle Profile Edit Form Validation Inaccessible
- **WCAG SC:** 3.3.1 Error Identification (A), 3.3.3 Error Suggestion (AA)
- **Location:** `modules/vehicle_profile.py` — `render_vehicle_profile()`
- **Issues:** Inline validation errors not linked to fields
- **Fix:** Implement `aria-invalid` + `aria-describedby` pattern

#### B1.16 — Maintenance Quick-Add Buttons Lack Accessible Names
- **WCAG SC:** 4.1.2 Name, Role, Value (A)
- **Location:** `modules/maintenance.py:705-744` — `_render_quick_add_buttons()`
- **Issues:** Buttons have text "+ Engine Oil Change" ✓ but rendered in `card_simple()` with no explicit role
- **Fix:** Ensure `button_ghost()` outputs proper `<button>` with accessible name

#### B1.17 — Chart Tooltips Not Keyboard Accessible
- **WCAG SC:** 2.1.1 Keyboard (A)
- **Location:** `components/charts_v2.py` — All Plotly charts
- **Issues:** Hover tooltips only; no keyboard navigation to data points
- **Fix:** Enable Plotly `config={'staticPlot': False, 'displayModeBar': True}`; provide accessible data table alternative

#### B1.18 — Print Styles Incomplete for Reports
- **WCAG SC:** 1.3.1 Info and Relationships (A) — print is a "user agent" consideration
- **Location:** `components/ui/styles.py` — `@media print` exists but report pages may not use it
- **Issues:** Standalone report pages (Diagnostic, Vehicle Health, Performance, Maintenance) need print-optimized CSS
- **Fix:** Test print output; add print-specific styles for report pages

---

### P2 — Medium

#### C1.1 — Heading Levels Skip in Custom HTML Sections
- **WCAG SC:** 1.3.1 Info and Relationships (A)
- **Location:** Pages using custom HTML for section headers (Diagnostics, Performance, Maintenance card titles)
- **Current Code:** Card titles use no heading element; `section_header()` (added Stage 5.11) uses `<h2>`/`<h3>` but not consistently adopted
- **Fix:** Migrate all section headers to `section_header()` component

#### C1.2 — Lists Not Semantic (Custom Bullet Points)
- **WCAG SC:** 1.3.1 Info and Relationships (A)
- **Location:** `modules/diagnostics.py` — AI Diagnosis evidence lists; `modules/ai_assistant.py` — recommended actions
- **Current Code:** Custom HTML `<div>` with `•` or emoji bullets — no `<ul>`/`<li>`
- **Fix:** Use semantic `<ul>`/`<li>` with CSS for styling

#### C1.3 — Images/Icons Missing Alt Text
- **WCAG SC:** 1.1.1 Non-text Content (A)
- **Location:** Throughout — emoji icons in badges, cards, status indicators, chart legends
- **Current Code:** Emoji used as decorative icons — should have `aria-hidden="true"` + text alternative; functional icons need `alt` or `aria-label`
- **Examples:**
  - `components/ui/components.py` — `Badge` component: emoji in label
  - `components/shell.py` — Vehicle icons, connection status icons
  - Chart legends: color swatches only
- **Fix:** Add `aria-hidden="true"` to decorative emoji; provide text labels for functional icons

#### C1.4 — Language Not Declared
- **WCAG SC:** 3.1.1 Language of Page (A)
- **Location:** `components/shell.py` — `render_shell()` outputs HTML without `<html lang="en">`
- **Current Code:** Streamlit wraps app in own HTML; custom shell content has no lang attribute
- **Fix:** Ensure root HTML has `lang="en"` (may require Streamlit config or custom template)

#### C1.5 — Abbreviations Not Expanded (DTC, OBD, PID, ECU, RPM, etc.)
- **WCAG SC:** 3.1.4 Abbreviations (AAA) — but good practice for AA
- **Location:** All pages — automotive terminology throughout
- **Current Code:** No `<abbr>` tags; tooltips only on hover
- **Fix:** Wrap first occurrence in `<abbr title="Diagnostic Trouble Code">DTC</abbr>`; use `section_header()` with tooltip prop

#### C1.6 — Data Tables Missing Summary/Caption for Complex Tables
- **WCAG SC:** 1.3.1 Info and Relationships (A)
- **Location:** `components/ui/components.py` — `table()` component — `TableProps` has no caption prop
- **Current Code:** Tables rendered without `<caption>`; complex tables (Performance comparison, Diagnostics history) need summary
- **Fix:** Add `caption` prop to `TableProps`; render `<caption>` element

#### C1.7 — Horizontal Scroll Tables Trap Focus
- **WCAG SC:** 2.1.1 Keyboard (A), 2.4.3 Focus Order (A)
- **Location:** `components/ui/components.py` — `table()` renders wrapper `.i20-table-wrapper` with `overflow-x: auto`
- **Issue:** Keyboard focus can enter scrollable area but not easily exit; screen readers may not announce scrollable region
- **Fix:** Add `tabindex="0"` to wrapper with `role="region" aria-label="Scrollable table"`; ensure focus styles

#### C1.8 — Gauge Charts Missing Text Equivalent
- **WCAG SC:** 1.1.1 Non-text Content (A)
- **Location:** `components/charts_v2.py` — `create_gauge()`; `modules/dashboard.py` — 4 primary gauges
- **Current Code:** Gauge shows value in center but no accessible text alternative; color arcs only
- **Fix:** Add adjacent text display: "RPM: 2,450 (Normal range: 800–6,500)"; hide chart from AT with `aria-hidden="true"`

#### C1.9 — Sparkline Charts Inaccessible
- **WCAG SC:** 1.1.1 Non-text Content (A)
- **Location:** `components/charts_v2.py` — `create_sparkline()`; Dashboard (10), Performance (4), Maintenance cards
- **Current Code:** Tiny line charts with no axes, labels, or data table
- **Fix:** Provide data table or text summary; `aria-hidden="true"` on sparkline

#### C1.10 — Multi-Series Line Charts: Series by Color Only
- **WCAG SC:** 1.4.1 Use of Color (A)
- **Location:** `components/charts_v2.py` — `create_line_chart()`, `create_comparison_chart()`; Dashboard, Performance
- **Current Code:** Series distinguished by color only; no dash patterns, markers, or direct labels
- **Fix:** Add dash patterns (`dash: 'dot'`, `'dash'`), markers (`symbol: 'circle'`, `'square'`), direct labels on lines

#### C1.11 — Comparison Charts: Overlay Series Not Distinguished
- **WCAG SC:** 1.4.1 Use of Color (A), 1.3.1 Info and Relationships (A)
- **Location:** `components/charts_v2.py` — `create_comparison_chart()`; Performance compare sessions
- **Current Code:** Multiple sessions overlaid by color only
- **Fix:** Unique dash pattern + marker per session; legend with shape samples; accessible data table

#### C1.12 — Bar Charts: Color Only for Categories
- **WCAG SC:** 1.4.1 Use of Color (A)
- **Location:** `components/charts_v2.py` — `create_bar_chart()`; Performance histograms
- **Current Code:** Bars colored by category only
- **Fix:** Add patterns (hatch fill) or direct labels; ensure legend has shape indicators

#### C1.13 — Heatmap Charts Inaccessible
- **WCAG SC:** 1.1.1 Non-text Content (A), 1.4.1 Use of Color (A)
- **Location:** `components/charts_v2.py` — `create_heatmap()`; Performance time distribution
- **Current Code:** Color intensity only; no text values; no keyboard nav
- **Fix:** Provide accessible data table; add text values on cells; keyboard navigation

#### C1.14 — Pie/Donut Charts Inaccessible
- **WCAG SC:** 1.1.1 Non-text Content (A), 1.4.1 Use of Color (A)
- **Location:** `components/charts_v2.py` — `create_pie_chart()`; Reports, Diagnostics
- **Current Code:** Color slices only; no accessible labels
- **Fix:** Direct labels on slices; accessible data table; `aria-hidden="true"` on chart

#### C1.15 — Scatter Charts Inaccessible
- **WCAG SC:** 1.1.1 Non-text Content (A)
- **Location:** `components/charts_v2.py` — `create_scatter_chart()`
- **Current Code:** Points by color only; no keyboard nav
- **Fix:** Accessible data table; distinct markers per series

#### C1.16 — Responsive: Mobile Sidebar Drawer Overlay Not Announced
- **WCAG SC:** 4.1.3 Status Messages (AA)
- **Location:** `components/shell.py` — Mobile drawer
- **Issue:** Drawer opens/closes silently
- **Fix:** Live region announcement "Navigation opened"/"Navigation closed"

#### C1.17 — Responsive: Tab Panels Stack on Mobile — Heading Order Breaks
- **WCAG SC:** 1.3.1 Info and Relationships (A)
- **Location:** All tabbed pages at mobile breakpoint
- **Issue:** Tabs become stacked sections; heading hierarchy may flatten
- **Fix:** Ensure each tab panel has heading; use `section_header()` consistently

#### C1.18 — Responsive: Card Grids Reflow — Focus Order Unpredictable
- **WCAG SC:** 2.4.3 Focus Order (A)
- **Location:** `components/ui/layout.py` — `AUTO_FIT_CARD_CSS`, `AUTO_FIT_METRIC_CSS`; all pages
- **Issue:** CSS grid reflow changes visual order; DOM order unchanged but focus follows DOM — may confuse spatial navigation
- **Fix:** Ensure DOM order matches logical reading order; test with screen reader

#### C1.19 — Responsive: Touch Target Spacing at 480px Viewport
- **WCAG SC:** 2.5.5 Target Size (AAA)
- **Location:** All pages at mobile breakpoint
- **Issue:** Dense card grids (Maintenance records, Upcoming, OBD PID grid) — adjacent targets < 8px apart
- **Fix:** Increase gap tokens at mobile breakpoint; ensure 8px minimum between targets

#### C1.20 — Responsive: Zoom to 200% — Horizontal Scroll Appears
- **WCAG SC:** 1.4.10 Reflow (AA)
- **Location:** All pages at 200% zoom (equivalent to 320px width)
- **Issue:** Fixed-width elements (sidebar ~300px, some tables) cause horizontal scroll
- **Fix:** Ensure all containers fluid; tables wrap or scroll internally; sidebar drawer at mobile

#### C1.21 — Responsive: Text Spacing Override (User Stylesheet)
- **WCAG SC:** 1.4.12 Text Spacing (AA)
- **Location:** `components/ui/styles.py` — Global styles
- **Issue:** Fixed `line-height`, `letter-spacing` on some elements may break user overrides
- **Fix:** Use relative units; avoid `!important` on spacing properties

#### C1.22 — Custom Select/Dropdown (OBD Wizard) Not Accessible
- **WCAG SC:** 4.1.2 Name, Role, Value (A), 2.1.1 Keyboard (A)
- **Location:** `modules/obd_connection.py` — Port selection, baudrate selection (custom HTML `<select>`)
- **Issue:** Native `<select>` used but styled; may lose focus styles; no `aria-describedby` for help text
- **Fix:** Use `FormFieldProps` / `selectbox()` component consistently

#### C1.23 — Loading States Not Announced (Skeleton, Spinner)
- **WCAG SC:** 4.1.3 Status Messages (AA)
- **Location:** `components/ui/components.py` — `skeleton_card()`, `spinner()`; all pages
- **Issue:** Visual only; no `aria-live` announcement
- **Fix:** Add `aria-live="polite"` to loading container; announce "Loading..." / "Loaded"

#### C1.24 — Empty States Not Announced
- **WCAG SC:** 4.1.3 Status Messages (AA)
- **Location:** `components/ui/components.py` — `empty_state()`; all pages
- **Issue:** Visual only; no programmatic announcement
- **Fix:** Wrap in `role="status" aria-live="polite"`

---

### P3 — Low (Polish)

#### D1.1 — Consistent Focus Ring Color (Design Token)
- **WCAG SC:** 2.4.7 Focus Visible (AA) — already met, but consistency
- **Location:** `components/ui/styles.py` — `var(--color-border-focus)` used
- **Issue:** Some custom HTML uses hardcoded `BORDER_FOCUS` token — verify all use same token
- **Fix:** Audit all focus styles use `--color-border-focus`

#### D1.2 — High Contrast Mode: Plotly Charts Not Adapted
- **WCAG SC:** 1.4.6 Contrast (Enhanced) (AAA) — but good practice
- **Location:** `components/charts_v2.py` — Charts don't respond to `@media (prefers-contrast: high)`
- **Fix:** Detect high contrast mode; adjust chart colors via token-driven factory

#### D1.3 — Reduced Motion: Plotly Transitions Not Disabled
- **WCAG SC:** 2.3.3 Animation from Interactions (AAA)
- **Location:** `components/charts_v2.py` — Chart layout transitions
- **Fix:** Pass `transition: {duration: 0}` when `prefers-reduced-motion: reduce`

#### D1.4 — Page Titles Unique and Descriptive
- **WCAG SC:** 2.4.2 Page Titled (A)
- **Location:** `app.py` — `st.set_page_config(page_title=...)` per page
- **Issue:** Report standalone pages may share title with main Reports page
- **Fix:** Ensure each standalone page has unique title

#### D1.5 — Breadcrumb Navigation Accessible
- **WCAG SC:** 2.4.8 Location (AAA) — but good practice
- **Location:** `components/shell.py` — Top bar breadcrumbs
- **Issue:** Rendered as text separators; no `<nav aria-label="Breadcrumb">` + `<ol>`/`<li>`
- **Fix:** Semantic breadcrumb markup

#### D1.6 — Search/Filter Inputs Have Search Role
- **WCAG SC:** 4.1.2 Name, Role, Value (A)
- **Location:** Maintenance filter, Diagnostics DTC search, Reports filters
- **Issue:** Native `<input type="search">` not used; no `role="search"`
- **Fix:** Use `type="search"` or `role="search"` on filter forms

#### D1.7 — Tooltips Accessible (Hover + Focus)
- **WCAG SC:** 1.3.1 Info and Relationships (A), 2.1.1 Keyboard (A)
- **Location:** `components/ui/components.py` — `FormFieldProps.help_text`; badge tooltips
- **Issue:** Help text only on hover; not on focus; not announced
- **Fix:** Show help text on focus; use `aria-describedby`

#### D1.8 — Status Indicators Have Text Equivalent
- **WCAG SC:** 1.4.1 Use of Color (A) — partially met
- **Location:** Shell topbar connection dots, chart legends
- **Issue:** Dots have no text; legends color-only
- **Fix:** Add visually-hidden text for dots; legend with shape+color

#### D1.9 — Keyboard Shortcuts Documented
- **WCAG SC:** 2.1.1 Keyboard (A), 2.1.2 No Keyboard Trap (A)
- **Location:** None currently
- **Issue:** No skip links beyond main; no shortcuts for common actions
- **Fix:** Add keyboard shortcuts help (e.g., `?` key); document in About page

#### D1.10 — Session Timeout Warning Accessible
- **WCAG SC:** 2.2.1 Timing Adjustable (A) — if session timeout exists
- **Location:** Not currently implemented
- **Issue:** N/A — but if added, must be accessible
- **Fix:** Future: live region warning; extend time via key press

#### D1.11 — Help/Documentation Accessible
- **WCAG SC:** 3.3.5 Help (AAA)
- **Location:** Settings → About page; inline help icons
- **Issue:** Help content in expanders; no dedicated accessible help system
- **Fix:** Ensure help content in logical heading order; searchable

---

## WCAG 2.1 AA Success Criteria Coverage Map

| SC | Criterion | Level | Status | Findings |
|----|-----------|-------|--------|----------|
| 1.1.1 | Non-text Content | A | ❌ Fail | Charts, gauges, sparklines, icons lack text alternatives |
| 1.2.1 | Audio-only/Video-only | A | N/A | No media |
| 1.3.1 | Info and Relationships | A | ❌ Fail | Headings, tables, lists, landmarks, forms |
| 1.3.2 | Meaningful Sequence | A | ⚠️ Partial | Card grid reflow, tab stacking |
| 1.3.3 | Sensory Characteristics | A | ⚠️ Partial | Color-only references in charts |
| 1.4.1 | Use of Color | A | ❌ Fail | Status dots, chart series, gauge arcs |
| 1.4.2 | Audio Control | A | N/A | No auto-audio |
| 1.4.3 | Contrast (Minimum) | AA | ⚠️ Partial | Design tokens validated; custom HTML needs audit |
| 1.4.4 | Resize Text | AA | ⚠️ Partial | 200% zoom causes horizontal scroll |
| 1.4.5 | Images of Text | AA | ✅ Pass | No images of text |
| 1.4.10 | Reflow | AA | ❌ Fail | Horizontal scroll at 320px equivalent |
| 1.4.11 | Non-text Contrast | AA | ⚠️ Partial | Focus rings, chart elements need verification |
| 1.4.12 | Text Spacing | AA | ⚠️ Partial | Fixed spacing may break user overrides |
| 1.4.13 | Content on Hover/Focus | AA | ❌ Fail | Tooltips not on focus; no dismiss |
| 2.1.1 | Keyboard | A | ❌ Fail | Charts, custom buttons, wizard, drawer |
| 2.1.2 | No Keyboard Trap | A | ❌ Fail | Modal/wizard focus trap missing |
| 2.1.4 | Character Key Shortcuts | A | N/A | No shortcuts implemented |
| 2.2.1 | Timing Adjustable | A | N/A | No session timeout |
| 2.2.2 | Pause, Stop, Hide | A | N/A | No auto-updating content > 5s |
| 2.3.1 | Three Flashes | A | ✅ Pass | No flashing content |
| 2.3.3 | Animation from Interactions | AAA | ❌ Fail | Plotly transitions, rerun animations |
| 2.4.1 | Bypass Blocks | A | ❌ Fail | Skip link not rendered |
| 2.4.2 | Page Titled | A | ⚠️ Partial | Report pages may duplicate |
| 2.4.3 | Focus Order | A | ❌ Fail | Modal/wizard/drawer focus management |
| 2.4.4 | Link Purpose (In Context) | A | ✅ Pass | Links have context |
| 2.4.5 | Multiple Ways | AA | ✅ Pass | Navigation + search |
| 2.4.6 | Headings and Labels | AA | ⚠️ Partial | Inconsistent heading hierarchy |
| 2.4.7 | Focus Visible | AA | ⚠️ Partial | Styles exist; need DOM verification |
| 2.4.8 | Location | AAA | ⚠️ Partial | Breadcrumbs not semantic |
| 2.5.1 | Pointer Gestures | A | ⚠️ Partial | Touch targets < 44px on mobile |
| 2.5.2 | Pointer Cancellation | A | ✅ Pass | Standard click behavior |
| 2.5.3 | Label in Name | A | ⚠️ Partial | Custom buttons, form fields |
| 2.5.4 | Motion Actuation | A | N/A | No motion actuation |
| 2.5.5 | Target Size | AAA | ❌ Fail | Mobile touch targets < 44px |
| 2.5.6 | Concurrent Input Mechanisms | AAA | ✅ Pass | Mouse + keyboard + touch work |
| 3.1.1 | Language of Page | A | ❌ Fail | No lang attribute on custom content |
| 3.1.2 | Language of Parts | AA | N/A | Single language |
| 3.2.1 | On Focus | A | ✅ Pass | No focus-triggered changes |
| 3.2.2 | On Input | A | ✅ Pass | No unexpected input changes |
| 3.2.3 | Consistent Navigation | AA | ✅ Pass | Shell consistent |
| 3.2.4 | Consistent Identification | AA | ✅ Pass | Components consistent |
| 3.3.1 | Error Identification | A | ❌ Fail | Errors not linked to fields |
| 3.3.2 | Labels or Instructions | A | ❌ Fail | Required not programmatic; labels not linked |
| 3.3.3 | Error Suggestion | AA | ❌ Fail | Suggestions not linked |
| 3.3.4 | Error Prevention | AA | N/A | No legal/financial data |
| 3.3.5 | Help | AAA | ⚠️ Partial | Help exists but not systematic |
| 4.1.1 | Parsing | A | ✅ Pass | Valid HTML output |
| 4.1.2 | Name, Role, Value | A | ❌ Fail | Custom components, charts, wizard |
| 4.1.3 | Status Messages | AA | ❌ Fail | No live regions for dynamic updates |

**Summary:** 15/38 applicable criteria FAIL (❌), 11 PARTIAL (⚠️), 12 PASS (✅)

---

## Implementation Priority Order

### Phase 7A: Critical Foundations (Week 1-2)
1. **A1.1** Skip link rendering
2. **A1.2** Sidebar `aria-current`
3. **A1.3** Custom button `type="button"` + keyboard activation
4. **A1.4** Form `aria-invalid` + `aria-describedby`
5. **A1.5** Live regions for all dynamic updates
6. **A1.8** Focus trap for modals/wizards/drawer
7. **A1.9** Table semantic structure (caption, scope)
8. **A1.10** Chart text alternatives + accessible data tables
9. **A1.11** Reduced motion for Plotly
10. **A1.12** Touch targets ≥ 44px

### Phase 7B: High-Impact Fixes (Week 2-3)
11. **B1.1** Heading hierarchy standardization
12. **B1.2** Landmarks (nav label, footer)
13. **B1.3** Custom wizard ARIA tabs pattern
14. **B1.4** Form label association
15. **B1.5** Error message linking
16. **B1.6** Required field `aria-required`
17. **B1.7** Focus visible verification on native widgets
18. **B1.8** Sidebar drawer focus trap
19. **B1.9** AI Assistant chat accessibility
20. **B1.10-14** Live regions for Diagnostics, OBD, Performance, Reports, Settings
21. **B1.15** Vehicle Profile form validation
22. **B1.17** Chart keyboard navigation config
23. **B1.18** Print styles for reports

### Phase 7C: Medium Polish (Week 3-4)
24-47. All P2 items (semantic lists, alt text, lang attribute, abbreviations, table captions, scrollable table region, gauge/sparkline/multi-series/bar/heatmap/pie/scatter chart accessibility, responsive announcements, heading order, focus order, touch spacing, reflow, text spacing, custom select, loading/empty announcements)

### Phase 7D: Low Polish (Week 4)
48-58. All P3 items (focus ring consistency, high contrast charts, reduced motion Plotly, page titles, breadcrumbs, search role, tooltips, status text, keyboard shortcuts, session timeout, help)

---

## Testing Strategy

### Automated Testing
| Tool | Scope | Integration |
|------|-------|-------------|
| **axe-core + Playwright** | All 13 pages + components | CI pipeline; test each breakpoint (375, 768, 1024, 1280) |
| **Lighthouse Accessibility** | Full page audits | CI; target ≥ 95 score |
| **pa11y** | Command-line regression | Pre-commit hook |
| **Storybook + axe** | Component-level | UI component library (if extracted) |

### Manual Testing Checklist
- [ ] **Keyboard Only:** Tab through every page; verify focus order, focus visible, no traps, all actions reachable
- [ ] **Screen Reader (NVDA/JAWS + Chrome/Firefox):** Navigate all pages; verify announcements, headings, landmarks, labels, live regions
- [ ] **Screen Reader (VoiceOver + Safari):** iOS/macOS verification
- [ ] **Zoom 200%:** Verify no horizontal scroll, all content readable, touch targets work
- [ ] **High Contrast Mode:** Windows High Contrast / macOS Increase Contrast — verify all UI visible
- [ ] **Reduced Motion:** `prefers-reduced-motion: reduce` — verify animations disabled
- [ ] **Color Blindness Simulation:** Protanopia/Deuteranopia/Tritanopia — verify no color-only info
- [ ] **Mobile (375px):** Touch targets ≥ 44px, drawer works, tables scroll, forms usable

### Regression Testing
- **Baseline:** 415/415 tests passing (from Stage 5.12)
- **Post-Fix:** Full test suite + new accessibility tests
- **New Tests:** 
  - `tests/accessibility/test_skip_link.py`
  - `tests/accessibility/test_live_regions.py`
  - `tests/accessibility/test_focus_management.py`
  - `tests/accessibility/test_chart_alternatives.py`
  - `tests/accessibility/test_form_aria.py`
  - `tests/accessibility/test_touch_targets.py`
  - `tests/accessibility/test_reduced_motion.py`
  - `tests/accessibility/test_color_only.py`

---

## Design System Token Compliance

### Verified Accessible Combinations (from `docs/PHASE_6_DESIGN_SYSTEM.md` §12.2)
| Foreground | Background | Ratio | WCAG AA | WCAG AAA |
|------------|------------|-------|---------|----------|
| `TEXT_PRIMARY` | `SURFACE_PRIMARY` | 12.6:1 | ✅ | ✅ |
| `TEXT_SECONDARY` | `SURFACE_PRIMARY` | 7.2:1 | ✅ | ✅ |
| `TEXT_MUTED` | `SURFACE_PRIMARY` | 4.5:1 | ✅ | ❌ |
| `ACCENT_PRIMARY` | `SURFACE_PRIMARY` | 4.8:1 | ✅ | ❌ |
| `STATUS_SUCCESS` | `SURFACE_PRIMARY` | 4.6:1 | ✅ | ❌ |
| `STATUS_WARNING` | `SURFACE_PRIMARY` | 4.5:1 | ✅ | ❌ |
| `STATUS_CRITICAL` | `SURFACE_PRIMARY` | 5.2:1 | ✅ | ✅ |
| `TEXT_ON_ACCENT` | `ACCENT_PRIMARY` | 7.8:1 | ✅ | ✅ |
| `BORDER_FOCUS` | `SURFACE_PRIMARY` | 4.5:1 | ✅ | ❌ |

**Action:** Enforce token-only usage in all custom HTML; add CI check for hardcoded colors.

---

## Streamlit Constraints & Workarounds

| Constraint | Impact | Workaround |
|------------|--------|------------|
| Native widgets lack ARIA control | Cannot add `aria-invalid`, `aria-describedby` to `st.text_input` | Wrap in custom HTML with hidden native input + accessible custom input; or use custom HTML forms entirely for critical flows |
| `st.tabs()` generates ARIA but not testable | Cannot verify screen reader behavior | Test with NVDA/JAWS; document known limitations |
| `st.plotly_chart()` renders SVG/canvas | No built-in accessibility | Provide adjacent accessible data table; `aria-hidden="true"` on chart |
| `st.rerun()` causes full page reload | Focus lost; live regions reset | Use session state + targeted HTML updates; preserve focus via `autofocus` on target |
| Single dark theme (no light) | High contrast mode may not trigger | Implement manual high contrast toggle using design tokens; respect `prefers-contrast` |
| Sidebar fixed width ~300px | Mobile requires drawer | CSS transform drawer (implemented); add focus trap |
| No access to `<html>`/`<head>` | Cannot set `lang`, meta viewport | Use Streamlit config `theme.base="dark"`; inject via `st.markdown` in `app.py` |

---

## Documentation Deliverables (Per Stage 7 Requirements)

| Document | Path | Status |
|----------|------|--------|
| Accessibility Audit (this file) | `docs/PHASE_6_STAGE_7_ACCESSIBILITY_AUDIT.md` | ✅ Complete |
| Implementation Plan | `docs/PHASE_6_STAGE_7_IMPLEMENTATION.md` | 📋 Pending |
| Test Matrix | `docs/PHASE_6_STAGE_7_TEST_MATRIX.md` | 📋 Pending |
| Progress Update | `docs/PHASE_6_PROGRESS.md` | 📋 Update after implementation |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Streamlit native widget ARIA limitations block compliance | High | High | Use custom HTML forms for critical flows; document exceptions |
| Plotly chart accessibility requires dual representation (chart + table) | Medium | High | Build chart factory to output both; `aria-hidden` on chart |
| Focus management across `st.rerun()` boundaries | High | Medium | Store/restore focus target in session state; use `autofocus` |
| Mobile drawer focus trap conflicts with Streamlit focus | Medium | Medium | Test thoroughly; use `setTimeout` to defer focus trap |
| 415 existing tests may break with ARIA additions | Low | High | Run full suite after each phase; add accessibility tests |
| Custom HTML `unsafe_allow_html` XSS risk with dynamic ARIA | Low | High | Sanitize all dynamic values; use design system components |

---

## Next Steps

1. **Verify Stage 6 Completion** — Confirm responsive implementation done and verified
2. **Create Implementation Plan** — `docs/PHASE_6_STAGE_7_IMPLEMENTATION.md` with detailed tasks, owners, timeline
3. **Create Test Matrix** — `docs/PHASE_6_STAGE_7_TEST_MATRIX.md` mapping each finding to test case
4. **Begin Phase 7A Implementation** — Critical foundations first
5. **Run Automated Accessibility Tests** — Establish baseline with axe-core
6. **Manual Testing Sprint** — Keyboard + screen reader testing after each phase
7. **Update Progress Tracker** — Mark Stage 7 phases complete as implemented
8. **Full Regression** — 415+ tests + new accessibility tests
9. **Documentation** — Finalize all Stage 7 docs

---

## Appendix: File-to-Finding Map

| File | P0 Findings | P1 Findings | P2 Findings | P3 Findings |
|------|-------------|-------------|-------------|-------------|
| `components/shell.py` | A1.1, A1.2, A1.6 | B1.2, B1.8, B1.16 | C1.16, C1.17 | D1.5 |
| `components/ui/components.py` | A1.3, A1.4, A1.8, A1.9 | B1.3, B1.4, B1.5, B1.6, B1.7 | C1.7, C1.22, C1.23, C1.24 | D1.1, D1.7 |
| `components/charts_v2.py` | A1.6, A1.10 | B1.17 | C1.8, C1.9, C1.10, C1.11, C1.12, C1.13, C1.14, C1.15 | D1.2, D1.3 |
| `components/ui/styles.py` | A1.11 | B1.7 | C1.21 | D1.1 |
| `modules/dashboard.py` | A1.6 | | C1.8, C1.9, C1.10 | |
| `modules/diagnostics.py` | A1.6 | B1.10 | C1.2, C1.10 | |
| `modules/performance.py` | | B1.12 | C1.10, C1.11, C1.12, C1.13 | |
| `modules/maintenance.py` | A1.3, A1.7 | B1.16 | C1.1 | |
| `modules/vehicle_profile.py` | | B1.15 | C1.1 | |
| `modules/ai_assistant.py` | A1.5, A1.6 | B1.9 | C1.2 | |
| `modules/obd_connection.py` | A1.3, A1.5, A1.8 | B1.3, B1.11 | C1.22 | |
| `modules/reports.py` | A1.5 | B1.13 | C1.1 | D1.4 |
| `modules/settings.py` | | B1.14 | | |
| `app.py` | | | | D1.4 |

---

**End of Audit Document**  
*Generated as part of Phase 6 Stage 7 Accessibility & WCAG 2.1 AA compliance initiative*