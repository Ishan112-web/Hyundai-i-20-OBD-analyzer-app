# Phase 6 Stage 7: Accessibility (WCAG 2.1 AA) — Implementation Plan

**Date:** 2026-11-18  
**Prerequisite:** Stage 6 (Responsive) must be verified complete before implementation begins  
**Source Audit:** `docs/PHASE_6_STAGE_7_ACCESSIBILITY_AUDIT.md` (65 findings)  
**Target:** WCAG 2.1 Level AA compliance across 13 pages + shared components

---

## Implementation Approach

### Constraints (from Audit)
1. **Streamlit native widgets lack ARIA control** — Use custom HTML forms for critical flows
2. **`unsafe_allow_html` required** — Semantic HTML + explicit ARIA only
3. **34 shared session-state keys** — No renaming/deletion/structure changes
4. **Plotly chart theming via layout dict** — Token-driven factory must output chart + accessible table
5. **Single dark theme** — Design system v1 is dark-only; respect `prefers-contrast`
6. **Sidebar fixed ~300px** — Collapsible drawer for mobile (focus trap required)

### Strategy
- **Phase 7A (Critical):** Fix 10 P0 blockers — foundation for all other work
- **Phase 7B (High):** Fix 13 P1 items — major barriers
- **Phase 7C (Medium):** Fix 24 P2 items — polish
- **Phase 7D (Low):** Fix 11 P3 items — optional enhancements
- **Testing:** Automated (axe-core + Playwright) + Manual (keyboard, screen reader, zoom, contrast) after each phase
- **Regression:** Full 415-test suite + new accessibility tests after each phase

---

## Phase 7A: Critical Foundations (Week 1-2)
**Goal:** Resolve all 12 P0 blockers — without these, WCAG 2.1 AA is impossible

### A1.1 — Skip Link Rendering
- **File:** `components/shell.py` → `render_shell()`
- **Action:** Add `<a href="#main-content" class="i20-skip-link">Skip to main content</a>` as first focusable element
- **CSS:** Already exists in `styles.py` (`.i20-skip-link`)
- **Test:** Tab from browser address bar → skip link appears → Enter jumps to main

### A1.2 — Sidebar `aria-current` on Active Item
- **Files:** `components/ui/components.py` (Sidebar component), `components/shell.py`
- **Action:** Add `aria-current="page"` to active navigation item button
- **Test:** Screen reader announces "Current page, Dashboard" on active item

### A1.3 — Custom Buttons: `type="button"` + Keyboard Activation
- **Files:** `modules/maintenance.py`, `modules/obd_connection.py`, `modules/reports.py`, `components/ui/components.py` (Wizard, Alert)
- **Action:** 
  - Add `type="button"` to all custom `<button>` elements
  - Add `keydown` handler for Enter/Space: `onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault();this.click();}"`
- **Test:** Keyboard-only activation of all custom buttons

### A1.4 — Form Inputs: `aria-invalid` + `aria-describedby`
- **File:** `components/ui/components.py` → `text_input()`, `selectbox()`, `FormFieldProps`
- **Action:** 
  - Generate unique error `id` per field
  - Add `aria-invalid="true"` when error exists
  - Add `aria-describedby="error-id help-id"` linking to error/help elements
  - Render error with `id="error-id"` and `role="alert"`
- **Test:** Screen reader announces error on invalid field focus

### A1.5 — Live Regions for Dynamic Updates
- **Files:** All pages with async operations
- **Action:** Add persistent `aria-live` regions:
  ```html
  <div id="i20-live-polite" class="i20-live-region" aria-live="polite" aria-atomic="true"></div>
  <div id="i20-live-assertive" class="i20-live-region" aria-live="assertive" aria-atomic="true"></div>
  ```
- **Pages requiring updates:**
  - `modules/ai_assistant.py` — Chat messages, loading, diagnostic results
  - `modules/diagnostics.py` — Scan status, AI diagnosis
  - `modules/obd_connection.py` — Wizard steps, connection status
  - `modules/performance.py` — Recording state, session load
  - `modules/reports.py` — Generation progress, preview ready
  - `modules/settings.py` — Save confirmations, destructive actions
- **Test:** Screen reader announces status changes without focus movement

### A1.6 — Color-Only Indicators: Add Icons/Text
- **Files:** `components/shell.py` (status dots), `components/charts_v2.py` (gauges, charts), `modules/diagnostics.py`
- **Action:**
  - Status dots: Add visually-hidden text + icon (e.g., `<span class="i20-visually-hidden">OBD Connected</span>`)
  - Gauge charts: Add adjacent text display "RPM: 2,450 (Normal: 800–6,500)"
  - Chart series: Add dash patterns + markers + direct labels
- **Test:** Colorblind simulation (protanopia/deuteranopia) — all states distinguishable

### A1.7 — Contrast Audit: Enforce Token-Only Usage
- **Files:** All `unsafe_allow_html` custom HTML
- **Action:** 
  - Scan for hardcoded colors (regex: `#[0-9a-fA-F]{3,8}|rgb\(|rgba\(`)
  - Replace with design token CSS variables
  - Add CI check: `grep -r "color:" --include="*.py" | grep -v "var(--i20-color"`
- **Test:** Automated contrast check on all custom HTML output

### A1.8 — Focus Trap for Modals/Wizards/Drawer
- **Files:** `components/ui/components.py` (Wizard, Alert), `components/shell.py` (mobile drawer)
- **Action:** Create `focusTrap.js` utility:
  - On open: trap focus within element, focus first focusable
  - On close: restore focus to trigger element
  - Handle Escape key to close
  - Use `tabindex="-1"` on non-focusable containers
- **Test:** Tab cycles within modal/wizard/drawer; Escape closes; focus returns

### A1.9 — Table Semantic Structure
- **File:** `components/ui/components.py` → `table()` function
- **Action:**
  - Add `caption` prop to `TableProps`
  - Render `<caption>` element
  - Add `scope="col"` to all `<th>`
  - Ensure horizontal scroll wrapper has `role="region" aria-label="Scrollable table" tabindex="0"`
- **Test:** Screen reader navigates table with headers announced

### A1.10 — Chart Text Alternatives + Accessible Data Tables
- **File:** `components/charts_v2.py` — All chart factory functions
- **Action:** Each chart function returns tuple: `(fig, accessible_table_html)`
  - `accessible_table_html`: `<table>` with caption, headers, all data points
  - Chart rendered with `aria-hidden="true"`
  - Adjacent accessible table visually hidden but screen-reader accessible
- **Charts affected:** gauge, line, sparkline, comparison, bar, pie, scatter, heatmap
- **Test:** Screen reader reads data table; chart hidden from AT

### A1.11 — Reduced Motion for Plotly
- **File:** `components/charts_v2.py`
- **Action:** Detect `prefers-reduced-motion` via CSS media query, pass to chart config:
  ```python
  config = {'responsive': True, 'staticPlot': False}
  layout = {'transition': {'duration': 0}}  # when reduced motion
  ```
- **CSS:** Extend `@media (prefers-reduced-motion: reduce)` in `styles.py`
- **Test:** Enable reduced motion in OS → chart animations disabled

### A1.12 — Touch Targets ≥ 44×44px
- **Files:** `components/ui/components.py` (all interactive), `components/ui/styles.py`
- **Action:**
  - Enforce `min-height: 44px; min-width: 44px` on all interactive elements
  - Increase custom button heights (currently 32px in maintenance.py)
  - Add mobile media query: increase gaps between targets to ≥8px
  - Use `use_container_width=True` for full-width mobile buttons
- **Test:** Mobile viewport (375px) — all targets ≥44px, 8px spacing

---

## Phase 7B: High-Impact Fixes (Week 2-3)

### B1.1 — Heading Hierarchy Standardization
- **Files:** All pages, `components/ui/layout.py` → `section_header()`
- **Action:** 
  - Audit all pages for heading levels
  - Use `section_header(level=2/3)` consistently
  - Replace `st.subheader()`, `st.markdown('###')` with component
- **Test:** Heading outline tool shows logical hierarchy

### B1.2 — Landmarks ✅ **IMPLEMENTED** (2026-11-18)
- **File:** `components/shell.py` → `render_shell()`, `components/ui/accessibility.py` → `render_footer()`, `render_landmark_fix_script()`
- **Action Completed:**
  - Added `aria-label="Main navigation"` to sidebar `<nav>` in `components/ui/components.py` Sidebar component (line 1267)
  - Added `<div role="contentinfo">` footer with app info via `render_footer()` in `components/ui/accessibility.py` — uses `div` instead of `<footer>` tag to survive DOMPurify sanitization in Streamlit 1.67.0
  - Ensured `<main id="main-content">` exists (already present in shell.py page_container)
  - Added `render_landmark_fix_script()` that runs via `st.html(unsafe_allow_javascript=True)` to enforce landmark attributes at runtime
  - Footer rendered AFTER page content in shell.py to ensure proper document order
  - Wrapped page renderer in try/except to ensure footer renders even if page errors
- **Test Results:** 
  - Playwright + axe-core: 36/63 tests passing (all Desktop 1440×900 and Laptop 1100×800 viewports pass for all 9 pages)
  - Mobile/Tablet viewports fail on pre-existing `scrollable-region-focusable` (Streamlit native `<pre>` elements) — NOT related to landmarks
  - Screen reader landmark navigation (NVDA Insert+F3): `<nav aria-label="Main navigation">`, `<main id="main-content">`, `<div role="contentinfo">` all detected correctly
  - Skip link targets `#main-content` correctly
- **Files Modified:** `components/shell.py`, `components/ui/accessibility.py`, `components/ui/components.py`

### B1.3 — Custom Wizard ARIA Tabs Pattern ✅ **IMPLEMENTED** (2026-11-19)
- **File:** `components/ui/components.py` → `wizard()` function (lines ~1045-1337), `modules/obd_connection.py` (lines ~105-221)
- **Action Completed:**
  - **WizardStep dataclass** (line ~1020): Added `description: str = ""` and `disabled: bool = False` fields for accessibility
  - **WizardProps dataclass** (line ~1030): Added `announce_step_change`, `live_region_id`, `show_progress` properties
  - **wizard() function** (lines ~1045-1337): Completely rewritten with full accessibility:
    - Semantic step indicator using `<ol>` with `role="tablist"` and `<li>` with `<button role="tab">`
    - Step buttons have `aria-selected`, `aria-controls`, `aria-current="step"`, `aria-disabled`, `tabindex` management
    - Visually hidden status text for each step state (Completed, Current, Upcoming, Error) — distinguishable without color
    - Progress display: "Step X of 8" with visually hidden full context
    - Live region announcements via JavaScript: "Step X of 8: Step Label" using existing `#i20-live-polite` region
    - Duplicate announcement prevention via `data-last-message` attribute check
    - Accessible navigation buttons (Previous/Next/Finish) with keyboard support
    - Focus trap in content area using `focusTrap.js` utility
    - Responsive design with flex-wrap for mobile
  - **modules/obd_connection.py** (lines ~105-221):
    - Updated `wizard_steps` with 8 steps, each with accessibility `description`
    - Added step state management logic (completed/active/error based on `wizard_step` session state)
    - Enabled accessibility features: `announce_step_change=True`, `live_region_id="i20-live-polite"`, `show_progress=True`
- **Test Results:**
  - Wizard CSS injected globally (verified via Playwright)
  - Sidebar navigation item present
  - Manual verification needed for full screen reader testing (Playwright navigation limitation)
- **Files Modified:** `components/ui/components.py`, `modules/obd_connection.py`
- **Test File Created:** `tests/browser/test_obd_wizard_accessibility.py`

### B1.4 — Form Label Association ✅ **IMPLEMENTED** (2026-11-19)
- **Files:** `components/ui/components.py`, `modules/dashboard.py`
- **Action Completed:**
  - Added `input_id` field to `FormFieldProps` dataclass (line ~432)
  - Updated `form_field()` function to render label with `for="{input_id}"` attribute for programmatic association
  - Updated `text_input()` and `selectbox()` functions to pass input ID to `FormFieldProps`
  - Fixed custom HTML in `modules/dashboard.py` `_render_simulation_controls_html()`:
    - Changed `<div class="i20-scenario-select">` with `<option>` elements to proper `<select id="sim-scenario-select">` element
    - Added `for="sim-scenario-select"` to the label element
    - Added `type="button"` to all custom button elements for proper keyboard activation
- **Test Results:**
  - All 415/415 unit tests passing
  - Accessibility tests on desktop/laptop: 18/18 passing
  - Labels now programmatically associated with inputs via `for`/`id` pairing

### B1.5 — Error Message Linking
- **File:** `components/ui/components.py` → `FormFieldProps`
- **Action:** Implement `aria-describedby` pattern (see A1.4)
- **Test:** Screen reader reads error on field focus

### B1.6 — Required Fields `aria-required`
- **File:** `components/ui/components.py` → `text_input()`, `selectbox()`
- **Action:** Add `aria-required="true"` when `FormFieldProps.required=True`
- **Test:** Screen reader announces "Required" on required fields

### B1.7 — Focus Visible Verification
- **File:** `components/ui/styles.py`
- **Action:** Test all Streamlit native widgets (`.stButton`, `.stTextInput`, `.stSelectbox`, `.stTabs`, `.stCheckbox`) for visible focus ring; adjust selectors
- **Test:** Keyboard tab through every page — focus ring visible everywhere

### B1.8 — Sidebar Drawer Focus Trap
- **File:** `components/shell.py`, `components/ui/components.py` (Sidebar)
- **Action:** Apply focus trap (see A1.8) to mobile drawer
- **Test:** Mobile viewport — drawer opens, focus trapped, Escape closes, focus returns

### B1.9 — AI Assistant Chat Accessibility
- **File:** `modules/ai_assistant.py`
- **Action:**
  - Wrap chat in `<div role="log" aria-live="polite" aria-label="Conversation">`
  - Each message: `<article aria-label="User message">` / `<article aria-label="Assistant message">`
  - Loading: `<div aria-live="assertive">AI is thinking...</div>`
  - Input form: accessible label on send button
- **Test:** Screen reader navigates conversation, announces new messages

### B1.10-B1.14 — Live Regions for Specific Pages
- **Files:** `modules/diagnostics.py`, `modules/obd_connection.py`, `modules/performance.py`, `modules/reports.py`, `modules/settings.py`
- **Action:** Implement page-specific live region updates (see A1.5)
- **Test:** Each async operation announces completion

### B1.15 — Vehicle Profile Form Validation
- **File:** `modules/vehicle_profile.py`
- **Action:** Apply `aria-invalid` + `aria-describedby` pattern to edit form
- **Test:** Screen reader announces validation errors

### B1.17 — Chart Keyboard Navigation
- **File:** `components/charts_v2.py`
- **Action:** Enable Plotly config: `{'staticPlot': False, 'displayModeBar': True, 'responsive': True}`
- **Test:** Tab into chart, arrow keys navigate data points

### B1.18 — Print Styles for Reports
- **File:** `components/ui/styles.py` → `@media print`
- **Action:** Optimize standalone report pages for print (hide nav, adjust layout)
- **Test:** Print preview shows clean report

---

## Phase 7C: Medium Polish (Week 3-4)

All 24 P2 items — semantic lists, alt text, lang attribute, abbreviations, table captions, scrollable table region, chart accessibility (gauge, sparkline, multi-series, bar, heatmap, pie, scatter), responsive announcements, heading order, focus order, touch spacing, reflow, text spacing, custom select, loading/empty announcements.

**Implementation:** Systematic pass through each file-to-finding map in audit appendix.

---

## Phase 7D: Low Polish (Week 4)

All 11 P3 items — focus ring consistency, high contrast charts, reduced motion Plotly, page titles, breadcrumbs, search role, tooltips, status text, keyboard shortcuts, session timeout, help system.

---

## File-to-Phase Mapping

| File | Phase 7A | Phase 7B | Phase 7C | Phase 7D |
|------|----------|----------|----------|----------|
| `components/shell.py` | A1.1, A1.5, A1.6, A1.8 | B1.2, B1.8 | C1.16, C1.17 | D1.5 |
| `components/ui/components.py` | A1.3, A1.4, A1.8, A1.9, A1.12 | B1.3, B1.4, B1.5, B1.6, B1.7 | C1.7, C1.22, C1.23, C1.24 | D1.1, D1.7 |
| `components/charts_v2.py` | A1.6, A1.10, A1.11 | B1.17 | C1.8-C1.15 | D1.2, D1.3 |
| `components/ui/styles.py` | A1.7, A1.11, A1.12 | B1.7 | C1.21 | D1.1 |
| `modules/dashboard.py` | A1.6 | | C1.8, C1.9, C1.10 | |
| `modules/diagnostics.py` | A1.5, A1.6 | B1.10 | C1.2, C1.10 | |
| `modules/performance.py` | A1.5 | B1.12 | C1.10, C1.11, C1.12, C1.13 | |
| `modules/maintenance.py` | A1.3, A1.7 | B1.16 | C1.1 | |
| `modules/vehicle_profile.py` | | B1.15 | C1.1 | |
| `modules/ai_assistant.py` | A1.5, A1.6 | B1.9 | C1.2 | |
| `modules/obd_connection.py` | A1.3, A1.5, A1.8 | B1.3, B1.11 | C1.22 | |
| `modules/reports.py` | A1.5 | B1.13 | C1.1 | D1.4 |
| `modules/settings.py` | A1.5 | B1.14 | | |
| `app.py` | | | | D1.4 |

---

## Testing Checkpoints

### After Phase 7A (Critical)
- [ ] axe-core scan: 0 critical violations
- [ ] Keyboard-only: All pages navigable, no traps
- [ ] Screen reader (NVDA): Skip link, live regions, forms, tables work
- [ ] Mobile (375px): Touch targets ≥44px, drawer works
- [ ] Reduced motion: Animations disabled
- [ ] Color blindness: No color-only info
- [ ] **Full regression: 415/415 tests pass**

### After Phase 7B (High)
- [ ] axe-core: 0 serious violations
- [ ] Screen reader: Headings, landmarks, wizard, chat accessible
- [ ] Charts: Keyboard nav works, data tables readable
- [ ] **Full regression: 415/415 tests pass**

### After Phase 7C (Medium)
- [ ] axe-core: 0 moderate violations
- [ ] All P2 items verified manually
- [ ] **Full regression: 415/415 tests pass**

### After Phase 7D (Low)
- [ ] Lighthouse accessibility score ≥ 95
- [ ] All P3 items verified
- [ ] **Full regression: 415/415 tests pass + new accessibility tests**

---

## New Accessibility Tests to Create

| Test File | Purpose |
|-----------|---------|
| `tests/accessibility/test_skip_link.py` | Skip link exists, focusable, functional |
| `tests/accessibility/test_live_regions.py` | Live regions present, updated correctly |
| `tests/accessibility/test_focus_management.py` | Focus trap, restore, order |
| `tests/accessibility/test_chart_alternatives.py` | Every chart has accessible table |
| `tests/accessibility/test_form_aria.py` | `aria-invalid`, `aria-describedby`, `aria-required` |
| `tests/accessibility/test_touch_targets.py` | All interactive ≥44×44px at 375px viewport |
| `tests/accessibility/test_reduced_motion.py` | Plotly transitions disabled |
| `tests/accessibility/test_color_only.py` | No color-only status indicators |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Streamlit native widget ARIA limits | Use custom HTML forms for critical flows (wizard, chat, settings) |
| Plotly accessibility requires dual representation | Chart factory outputs both; `aria-hidden` on chart |
| Focus management across `st.rerun()` | Store/restore focus target in session state; `autofocus` |
| Mobile drawer focus trap conflicts | Test thoroughly; defer focus trap with `setTimeout` |
| 415 tests break with ARIA additions | Run suite after each phase; add accessibility tests incrementally |
| XSS with dynamic ARIA values | Sanitize all dynamic values; use design system components |

---

## P1 Traceability Matrix (Phase 7B)

This section maps all 18 P1 findings from the accessibility audit to implementation tasks, test cases, and verification criteria.

| Audit ID | Description | Component / Page | WCAG Criterion | Source File(s) | Root Cause | Stage 7B Implementation Task | Test Case ID | Acceptance Criteria | Verification Method |
|----------|-------------|------------------|----------------|----------------|------------|------------------------------|--------------|---------------------|---------------------|
| **B1.1** | Page Headings Hierarchy Inconsistent (h1/h2/h3) | All pages using `page_header()` | 1.3.1 (A) | All pages, `components/ui/layout.py` | `page_header` renders h1 but pages use `st.subheader()` (h2), `st.markdown('###')` (h3) inconsistently; some skip levels | Standardize heading hierarchy; use `section_header()` component consistently; replace all `st.subheader()` and markdown headings | TC-B1.1 | All pages: h1 → h2 → h3 logical; no skipped levels; heading outline tool shows valid hierarchy | Automated (axe + Playwright heading order); Manual (NVDA heading list Insert+F6) | ✅ **IMPLEMENTED** - Fixed `section_header()` to accept `level` parameter (2/3/4); replaced 8 raw `st.markdown("###"/"####")` calls in ai_assistant.py, performance.py, reports.py |
| **B1.2** | Landmarks Missing (nav, main, aside, region) | Global shell | 1.3.1 (A) | `components/shell.py` | Shell has `<header>`, `<main id="main-content">`, `<aside>` but sidebar `<nav>` missing `aria-label`; no `<footer>`; report pages may lack landmarks | Add `aria-label="Main navigation"` to sidebar `<nav>`; add `<footer role="contentinfo">` with app info; ensure all pages have proper landmarks | TC-B1.2 | `<nav aria-label="Main navigation">`, `<main id="main-content">`, `<footer role="contentinfo">` present; screen reader landmark navigation works | Automated (Playwright landmark presence); Manual (NVDA landmark list Insert+F3) |
| **B1.3** | Tab Panels Not Accessible (ARIA Tabs Pattern) | All pages using `st.tabs()` + OBD Wizard | 4.1.2 (A), 1.3.1 (A) | `components/ui/components.py` (Wizard), all tabbed pages | Streamlit native tabs generate correct ARIA ✓ BUT custom wizard component needs full ARIA tabs pattern: `role="tablist"`, `role="tab"` with `aria-selected`/`aria-controls`, `role="tabpanel"` with `aria-labelledby` | Implement full ARIA tabs pattern in Wizard component; verify Streamlit tabs work with screen readers | TC-B1.3 | Wizard has `role="tablist"`; steps have `role="tab" aria-selected aria-controls`; panels have `role="tabpanel" aria-labelledby`; screen reader announces "Tab X of Y, Label, selected" | Automated (Playwright ARIA attributes); Manual (NVDA wizard navigation) |
| **B1.4** | Form Labels Not Programmatically Associated | OBD Wizard, Reports config, custom forms | 1.3.1 (A), 3.3.2 (A) | `modules/obd_connection.py`, `modules/reports.py`, `components/ui/components.py` | Custom HTML forms use `<label>` without `for`/`id` pairing; native Streamlit inputs use label_visibility="collapsed" | Ensure all custom `<input>`/`<select>` have `<label for="id">` pairing; use `FormFieldProps` component consistently | TC-B1.4 | All custom form controls programmatically labeled; clicking label focuses input | Automated (Playwright label-for pairing); Manual (click label → focus; NVDA label announced) |
| **B1.5** | Error Messages Not Linked to Fields (`aria-describedby`) | All forms using `FormFieldProps` | 3.3.1 (A), 3.3.3 (AA) | `components/ui/components.py` | `FormFieldProps.error` exists but not rendered with `id` + `aria-describedby` on input; errors shown as separate `st.error()` | Generate unique error `id`; add `aria-describedby="error-id"` to input; render error with `id="error-id"` and `role="alert"` | TC-B1.5 | All validation errors programmatically linked to fields; screen reader reads error on field focus | Automated (Playwright aria-describedby references); Manual (NVDA focus field → error announced) |
| **B1.6** | Required Fields Not Indicated Programmatically | All forms | 3.3.2 (A) | `components/ui/components.py` | `FormFieldProps.required` shows `*` visually only; no `aria-required="true"` | Add `aria-required="true"` to required inputs; keep visual `*` for sighted users | TC-B1.6 | All required fields have `aria-required="true"`; screen reader announces "Required" | Automated (Playwright aria-required); Manual (NVDA required field announcement) |
| **B1.7** | No Focus Visible Styles on Streamlit Native Widgets | All pages | 2.4.7 (AA) | `components/ui/styles.py` | Focus-visible rules written but Streamlit's internal DOM structure may not match selectors | Test with keyboard navigation; adjust CSS selectors to match actual Streamlit DOM classes for `.stButton`, `.stTextInput`, `.stSelectbox`, `.stTabs`, `.stCheckbox` | TC-B1.7 | Clear focus indicator visible on every native Streamlit widget at all viewports | Manual (Keyboard tab through every page); Automated (Playwright focus style verification) |
| **B1.8** | Sidebar Drawer (Mobile) Focus Trap Missing | Mobile viewport | 2.4.3 (A), 4.1.2 (A) | `components/shell.py`, `components/ui/components.py` (Sidebar) | Drawer opens via checkbox hack; no focus management; focus not trapped; Escape not handled | Implement focus trap when drawer open: focus first link on open; restore focus on close; Escape closes drawer | TC-B1.8 | Mobile drawer fully keyboard accessible: focus trapped, Escape closes, focus returns to hamburger | Automated (Playwright at 375px: open drawer → Tab trapped → Escape closes); Manual (mobile viewport keyboard nav) |
| **B1.9** | AI Assistant Chat Not Accessible | AI Assistant page | 4.1.2 (A), 4.1.3 (AA), 1.3.1 (A) | `modules/ai_assistant.py` | Message bubbles: no `role="log"`/`aria-live`; user/assistant only visual distinction; loading: spinner only; input: send button lacks `aria-label` | Wrap chat in `role="log" aria-live="polite"`; each message `article` with `aria-label="User/Assistant message"`; loading status in `aria-live="assertive"`; accessible send button | TC-B1.9 | Chat fully accessible: live region announces new messages; user/assistant distinguished; loading announced; keyboard operable | Automated (Playwright ARIA structure); Manual (NVDA: new messages announced, roles correct) |
| **B1.10** | Diagnostic Scan Results Not Announced | Diagnostics page | 4.1.3 (AA) | `modules/diagnostics.py` | Scan completes → results appear via rerun; no live region; DTC list updates silently | Add `aria-live="polite"` region for scan status; update with "Scan complete. X codes found." | TC-B1.10 | Scan completion announced via live region without focus movement | Manual (NVDA: run scan → "Scan complete. X codes found." announced) |
| **B1.11** | OBD Connection Wizard Steps Not Announced | OBD Connection page | 4.1.3 (AA), 2.4.3 (A) | `modules/obd_connection.py` | Step changes via session state → rerun; no announcement; focus not moved to new step content | Live region for step announcement; focus management in wizard component (move focus to step content on change) | TC-B1.11 | Step changes announced ("Step 2 of 8, Select Port"); focus moved to step content | Manual (NVDA: Next step → announcement + focus on content) |
| **B1.12** | Performance Recording Status Not Announced | Performance page | 4.1.3 (AA) | `modules/performance.py` | Recording start/stop/pause → status changes silently | Live region for recording state: "Recording started", "Recording paused", "Recording stopped" | TC-B1.12 | Recording state changes announced via live region | Manual (NVDA: Start/Stop/Pause → announcements) |
| **B1.13** | Report Generation Progress Not Announced | Reports page | 4.1.3 (AA) | `modules/reports.py` | Generation runs → preview appears silently | Live region with progress updates: "Generating report...", "Report ready for preview" | TC-B1.13 | Generation progress and completion announced | Manual (NVDA: Generate → progress → complete announced) |
| **B1.14** | Settings Changes Not Confirmed | Settings page | 3.3.3 (AA), 4.1.3 (AA) | `modules/settings.py` | Save actions → toast/alert but not in live region; no confirmation for destructive actions | Live region for save confirmations ("Settings saved"); `role="alert"` for destructive confirmations (backup restore, delete) | TC-B1.14 | Save confirmations and destructive action alerts announced via live region/alert | Manual (NVDA: Save → "Settings saved"; Delete → alert announced) |
| **B1.15** | Vehicle Profile Form Validation Inaccessible | Vehicle Profile page | 3.3.1 (A), 3.3.3 (AA) | `modules/vehicle_profile.py` | Inline validation errors not linked to fields | Implement `aria-invalid` + `aria-describedby` pattern on edit form fields | TC-B1.15 | Profile form validation errors programmatically linked and announced | Automated (Playwright aria-invalid + aria-describedby); Manual (NVDA: submit invalid → errors announced) |
| **B1.16** | Maintenance Quick-Add Buttons Lack Accessible Names | Maintenance page | 4.1.2 (A) | `modules/maintenance.py:705-744` | Buttons have text "+ Engine Oil Change" ✓ but rendered in `card_simple()` with no explicit role | Ensure `button_ghost()` outputs proper `<button>` with accessible name; verify all quick-add buttons have proper ARIA | TC-B1.16 | All quick-add buttons are proper `<button type="button">` with accessible names | Automated (Playwright button role + accessible name); Manual (NVDA: button announced correctly) |
| **B1.17** | Chart Tooltips Not Keyboard Accessible | All Plotly charts | 2.1.1 (A) | `components/charts_v2.py` | Hover tooltips only; no keyboard navigation to data points | Enable Plotly config: `{'staticPlot': False, 'displayModeBar': True, 'responsive': True}`; provide accessible data table alternative | TC-B1.17 | Charts keyboard navigable: Tab into chart → arrow keys navigate data points → tooltip shows | Automated (Playwright Plotly config); Manual (Keyboard: Tab into chart → arrow nav) |
| **B1.18** | Print Styles Incomplete for Reports | Standalone report pages | 1.3.1 (A) | `components/ui/styles.py` | `@media print` exists but report pages may not use it; need print-optimized CSS | Test print output on each standalone report (Diagnostic, Vehicle Health, Performance, Maintenance); add print-specific styles: hide nav/sidebar, adjust layout, ensure readable | TC-B1.18 | Reports print cleanly: no nav/sidebar, proper layout, all content readable | Manual (Print preview Ctrl+P on each standalone report) |

---

## Success Criteria

1. **WCAG 2.1 AA:** All 38 applicable criteria PASS (currently 15 FAIL, 11 PARTIAL)
2. **Automated:** axe-core 0 violations at all 4 breakpoints (375, 768, 1024, 1280)
3. **Manual:** Keyboard-only, NVDA/JAWS, VoiceOver, 200% zoom, high contrast, color blindness — all pass
4. **Regression:** 415+ existing tests + new accessibility tests all pass
5. **Documentation:** Implementation plan, test matrix, progress tracker updated

---

*Implementation Plan created 2026-11-18 — Pending Stage 6 verification before execution*