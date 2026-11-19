# Phase 6 Stage 7: Accessibility — Test Matrix

**Date:** 2026-11-18  
**Source:** `docs/PHASE_6_STAGE_7_ACCESSIBILITY_AUDIT.md` (65 findings)  
**Implementation Plan:** `docs/PHASE_6_STAGE_7_IMPLEMENTATION.md`  
**Purpose:** Map each finding to specific test cases for verification

---

## Test Matrix Structure

| Column | Description |
|--------|-------------|
| **Finding ID** | From audit (A1.1, B1.1, C1.1, D1.1) |
| **WCAG SC** | Success Criterion reference |
| **Phase** | Implementation phase (7A/7B/7C/7D) |
| **Test Type** | Automated (axe/Playwright), Manual (KB/SR/Zoom), or Both |
| **Test Case** | Specific verification steps |
| **Expected Result** | Pass criteria |
| **File(s)** | Primary file(s) to test |
| **Status** | Not Started / In Progress / Pass / Fail |

---

## Phase 7A: Critical Foundations (10 P0 Findings)

### A1.1 — Skip Link
| Field | Value |
|-------|-------|
| **WCAG SC** | 2.4.1 Bypass Blocks (A) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: `page.locator('.i20-skip-link').first` exists, focused on first Tab, click navigates to `#main-content` |
| **Manual Test** | Keyboard: Tab from address bar → skip link visible → Enter → focus on main content |
| **Expected** | Skip link is first focusable element; activates on Enter; moves focus to main |
| **Files** | `components/shell.py` |
| **Status** | Not Started |

### A1.2 — Sidebar `aria-current`
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.3.1 (A), 2.4.7 (AA) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: Active nav item has `aria-current="page"`; axe-core: no violation on `aria-current` |
| **Manual Test** | NVDA: Navigate sidebar → active item announced as "Current page, [Page Name]" |
| **Expected** | Active page has `aria-current="page"`; screen reader identifies current location |
| **Files** | `components/ui/components.py`, `components/shell.py` |
| **Status** | Not Started |

### A1.3 — Custom Buttons: `type="button"` + Keyboard
| Field | Value |
|-------|-------|
| **WCAG SC** | 4.1.2 (A), 2.1.1 (A) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: All custom `<button>` have `type="button"`; keydown Enter/Space triggers click |
| **Manual Test** | Keyboard: Tab to each custom button → Enter/Space activates; no form submission |
| **Expected** | All custom buttons have `type="button"`; keyboard activation works; no accidental form submit |
| **Files** | `modules/maintenance.py`, `modules/obd_connection.py`, `modules/reports.py`, `components/ui/components.py` |
| **Status** | Not Started |

### A1.4 — Form `aria-invalid` + `aria-describedby`
| Field | Value |
|-------|-------|
| **WCAG SC** | 3.3.1 (A), 3.3.3 (AA) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: Invalid fields have `aria-invalid="true"`; `aria-describedby` references error element; error has `role="alert"` |
| **Manual Test** | NVDA: Focus invalid field → error announced; JAWS: Same |
| **Expected** | Screen reader announces error on field focus; error programmatically linked |
| **Files** | `components/ui/components.py` |
| **Status** | Not Started |

### A1.5 — Live Regions for Dynamic Updates
| Field | Value |
|-------|-------|
| **WCAG SC** | 4.1.3 (AA) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: `#i20-live-polite` and `#i20-live-assertive` exist; content updates reflected in live region |
| **Manual Test** | NVDA: Trigger each async operation (scan, AI chat, wizard step, recording, report gen) → status announced without focus change |
| **Expected** | All dynamic updates announced via live regions; polite for status, assertive for errors |
| **Files** | `modules/ai_assistant.py`, `modules/diagnostics.py`, `modules/obd_connection.py`, `modules/performance.py`, `modules/reports.py`, `modules/settings.py` |
| **Status** | Not Started |

### A1.6 — Color-Only Indicators
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.4.1 (A) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright + axe: No color-only violations; custom check: status dots have text/icon alternative |
| **Manual Test** | Color blindness simulation (Chrome DevTools: Protanopia/Deuteranopia/Tritanopia) — all states distinguishable; high contrast mode |
| **Expected** | Every status indicator has non-color cue (icon, text, pattern); charts have dash patterns + markers + labels |
| **Files** | `components/shell.py`, `components/charts_v2.py`, `modules/diagnostics.py` |
| **Status** | Not Started |

### A1.7 — Contrast: Token-Only Usage
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.4.3 (AA) |
| **Phase** | 7A |
| **Test Type** | Automated |
| **Automated Test** | CI grep: `grep -r "color:" --include="*.py" | grep -v "var(--i20-color"` returns 0; axe-core: all text ≥4.5:1, large text ≥3:1 |
| **Manual Test** | High contrast mode (Windows/macOS) — all text readable |
| **Expected** | Zero hardcoded colors in custom HTML; all contrast ratios meet AA |
| **Files** | All `.py` files with `unsafe_allow_html` |
| **Status** | Not Started |

### A1.8 — Focus Trap (Modals/Wizards/Drawer)
| Field | Value |
|-------|-------|
| **WCAG SC** | 2.4.3 (A), 4.1.2 (A) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: Tab cycles within modal/wizard/drawer; Escape closes; focus returns to trigger |
| **Manual Test** | Keyboard: Open each modal/wizard/drawer → Tab stays inside → Escape closes → focus on trigger |
| **Expected** | Focus trapped in overlay; Escape closes; focus restored |
| **Files** | `components/ui/components.py` (Wizard, Alert), `components/shell.py` (drawer) |
| **Status** | Not Started |

### A1.9 — Table Semantic Structure
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.3.1 (A) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: `<table>` has `<caption>`; all `<th>` have `scope="col"`; scroll wrapper has `role="region" tabindex="0"` |
| **Manual Test** | NVDA: Navigate table → headers announced with column scope; caption read; scroll region accessible |
| **Expected** | Tables have caption, scoped headers, accessible scroll wrapper |
| **Files** | `components/ui/components.py` |
| **Status** | Not Started |

### A1.10 — Chart Text Alternatives + Data Tables
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.1.1 (A), 2.1.1 (A) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: Each chart has adjacent `<table>` with all data points; chart has `aria-hidden="true"` |
| **Manual Test** | NVDA: Navigate to chart → data table read; chart skipped; JAWS: Same |
| **Expected** | Every chart (gauge, line, sparkline, comparison, bar, pie, scatter, heatmap) has accessible data table |
| **Files** | `components/charts_v2.py` |
| **Status** | Not Started |

### A1.11 — Reduced Motion for Plotly
| Field | Value |
|-------|-------|
| **WCAG SC** | 2.3.3 (AAA), 2.3.1 (A) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: Emulate `prefers-reduced-motion: reduce` → chart layout has `transition: {duration: 0}` |
| **Manual Test** | OS reduced motion ON → chart animations disabled; skeleton pulse stopped; spinner stopped |
| **Expected** | All animations respect `prefers-reduced-motion` |
| **Files** | `components/charts_v2.py`, `components/ui/styles.py` |
| **Status** | Not Started |

### A1.12 — Touch Targets ≥ 44×44px
| Field | Value |
|-------|-------|
| **WCAG SC** | 2.5.5 (AAA), 2.5.1 (A) |
| **Phase** | 7A |
| **Test Type** | Both |
| **Automated Test** | Playwright: At 375px viewport, all interactive elements ≥44×44px; adjacent targets ≥8px apart |
| **Manual Test** | Mobile Chrome DevTools (375px) — tap all buttons, tabs, inputs, badges — all activatable |
| **Expected** | All touch targets meet 44×44px minimum at mobile viewport |
| **Files** | `components/ui/components.py`, `components/ui/styles.py`, all pages |
| **Status** | Not Started |

---

## Phase 7B: High-Impact Fixes (13 P1 Findings)

### B1.1 — Heading Hierarchy
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.3.1 (A) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright + axe: Heading order valid (no skipped levels); `section_header()` used consistently |
| **Manual Test** | NVDA: Heading list (Insert+F6) shows logical hierarchy |
| **Expected** | All pages: h1 → h2 → h3 logical; no skipped levels |
| **Files** | All pages, `components/ui/layout.py` |
| **Status** | Not Started |

### B1.2 — Landmarks
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.3.1 (A) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright: `<nav aria-label="Main navigation">`, `<main id="main-content">`, `<footer role="contentinfo">` present |
| **Manual Test** | NVDA: Landmark list (Insert+F3) shows nav, main, footer |
| **Expected** | All landmarks present and labeled |
| **Files** | `components/shell.py` |
| **Status** | Not Started |

### B1.3 — Wizard ARIA Tabs
| Field | Value |
|-------|-------|
| **WCAG SC** | 4.1.2 (A), 1.3.1 (A) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright: Wizard has `role="tablist"`; steps have `role="tab" aria-selected aria-controls`; panels have `role="tabpanel" aria-labelledby` |
| **Manual Test** | NVDA: Wizard announced as tabs; step selection works; panel content associated |
| **Expected** | Full ARIA tabs pattern implemented |
| **Files** | `components/ui/components.py` |
| **Status** | Not Started |

### B1.4 — Form Label Association
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.3.1 (A), 3.3.2 (A) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright: All custom `<input>`/`<select>` have `<label for="id">` pairing |
| **Manual Test** | Click label → focuses input; NVDA: Label announced on focus |
| **Expected** | All custom form controls programmatically labeled |
| **Files** | `modules/obd_connection.py`, `modules/reports.py`, `components/ui/components.py` |
| **Status** | Not Started |

### B1.5 — Error Message Linking
| Field | Value |
|-------|-------|
| **WCAG SC** | 3.3.1 (A), 3.3.3 (AA) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright: Error elements have `id`; inputs have `aria-describedby` referencing error `id` |
| **Manual Test** | NVDA: Focus field with error → error announced |
| **Expected** | All validation errors programmatically linked |
| **Files** | `components/ui/components.py` |
| **Status** | Not Started |

### B1.6 — Required Fields `aria-required`
| Field | Value |
|-------|-------|
| **WCAG SC** | 3.3.2 (A) |
| **Phase** | 7B |
| **Test Type** | Automated |
| **Automated Test** | Playwright: Required inputs have `aria-required="true"` |
| **Manual Test** | NVDA: Required field announced as "Required" |
| **Expected** | All required fields programmatically indicated |
| **Files** | `components/ui/components.py` |
| **Status** | Not Started |

### B1.7 — Focus Visible on Native Widgets
| Field | Value |
|-------|-------|
| **WCAG SC** | 2.4.7 (AA) |
| **Phase** | 7B |
| **Test Type** | Manual |
| **Automated Test** | Playwright: Focus styles applied to `.stButton button`, `.stTextInput input`, `.stSelectbox`, `.stTabs`, `.stCheckbox` |
| **Manual Test** | Keyboard: Tab through every page — focus ring visible on every interactive element |
| **Expected** | Clear focus indicator on all native Streamlit widgets |
| **Files** | `components/ui/styles.py` |
| **Status** | Not Started |

### B1.8 — Sidebar Drawer Focus Trap
| Field | Value |
|-------|-------|
| **WCAG SC** | 2.4.3 (A), 4.1.2 (A) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright: At 375px, open drawer → Tab trapped inside → Escape closes → focus on hamburger |
| **Manual Test** | Mobile viewport: Open drawer → keyboard nav works → Escape closes |
| **Expected** | Mobile drawer fully keyboard accessible with focus management |
| **Files** | `components/shell.py`, `components/ui/components.py` |
| **Status** | Not Started |

### B1.9 — AI Assistant Chat
| Field | Value |
|-------|-------|
| **WCAG SC** | 4.1.2 (A), 4.1.3 (AA), 1.3.1 (A) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright: Chat has `role="log" aria-live="polite"`; messages have `article[aria-label]`; loading has `aria-live="assertive"` |
| **Manual Test** | NVDA: New messages announced; user/assistant distinguished; loading announced |
| **Expected** | Chat fully accessible: live region, message roles, loading status |
| **Files** | `modules/ai_assistant.py` |
| **Status** | Not Started |

### B1.10 — Diagnostic Scan Live Region
| Field | Value |
|-------|-------|
| **WCAG SC** | 4.1.3 (AA) |
| **Phase** | 7B |
| **Test Type** | Manual |
| **Manual Test** | NVDA: Run scan → "Scan complete. X codes found." announced |
| **Expected** | Scan completion announced via live region |
| **Files** | `modules/diagnostics.py` |
| **Status** | Not Started |

### B1.11 — OBD Wizard Step Announcements
| Field | Value |
|-------|-------|
| **WCAG SC** | 4.1.3 (AA), 2.4.3 (A) |
| **Phase** | 7B |
| **Test Type** | Manual |
| **Manual Test** | NVDA: Next step → "Step 2 of 8, Select Port" announced; focus on step content |
| **Expected** | Step changes announced; focus managed |
| **Files** | `modules/obd_connection.py` |
| **Status** | Not Started |

### B1.12 — Performance Recording Status
| Field | Value |
|-------|-------|
| **WCAG SC** | 4.1.3 (AA) |
| **Phase** | 7B |
| **Test Type** | Manual |
| **Manual Test** | NVDA: Start recording → "Recording started" announced; Stop → "Recording stopped" |
| **Expected** | Recording state changes announced |
| **Files** | `modules/performance.py` |
| **Status** | Not Started |

### B1.13 — Report Generation Progress
| Field | Value |
|-------|-------|
| **WCAG SC** | 4.1.3 (AA) |
| **Phase** | 7B |
| **Test Type** | Manual |
| **Manual Test** | NVDA: Generate report → progress announced; complete → "Report ready" announced |
| **Expected** | Generation progress and completion announced |
| **Files** | `modules/reports.py` |
| **Status** | Not Started |

### B1.14 — Settings Changes Confirmed
| Field | Value |
|-------|-------|
| **WCAG SC** | 3.3.3 (AA), 4.1.3 (AA) |
| **Phase** | 7B |
| **Test Type** | Manual |
| **Manual Test** | NVDA: Save settings → "Settings saved" announced; Delete backup → "Are you sure?" alert announced |
| **Expected** | Save confirmations and destructive action alerts announced |
| **Files** | `modules/settings.py` |
| **Status** | Not Started |

### B1.15 — Vehicle Profile Form Validation
| Field | Value |
|-------|-------|
| **WCAG SC** | 3.3.1 (A), 3.3.3 (AA) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright: Edit form validation errors linked via `aria-describedby` |
| **Manual Test** | NVDA: Submit invalid form → errors announced on each field |
| **Expected** | Profile form validation accessible |
| **Files** | `modules/vehicle_profile.py` |
| **Status** | Not Started |

### B1.17 — Chart Keyboard Navigation
| Field | Value |
|-------|-------|
| **WCAG SC** | 2.1.1 (A) |
| **Phase** | 7B |
| **Test Type** | Both |
| **Automated Test** | Playwright: Plotly config has `staticPlot: false, displayModeBar: true, responsive: true` |
| **Manual Test** | Keyboard: Tab into chart → arrow keys navigate data points → tooltip shows |
| **Expected** | Charts keyboard navigable |
| **Files** | `components/charts_v2.py` |
| **Status** | Not Started |

### B1.18 — Print Styles for Reports
| Field | Value |
|-------|-------|
| **WCAG SC** | 1.3.1 (A) |
| **Phase** | 7B |
| **Test Type** | Manual |
| **Manual Test** | Print preview (Ctrl+P) on each standalone report → clean output, no nav, readable |
| **Expected** | Reports print cleanly |
| **Files** | `components/ui/styles.py` |
| **Status** | Not Started |

---

## Phase 7C: Medium Polish (24 P2 Findings)

| Finding | WCAG SC | Test Type | Key Verification |
|---------|---------|-----------|------------------|
| C1.1 Heading levels in custom HTML | 1.3.1 (A) | Both | `section_header()` used everywhere |
| C1.2 Semantic lists | 1.3.1 (A) | Both | `<ul>`/`<li>` for evidence, actions |
| C1.3 Alt text for icons | 1.1.1 (A) | Both | Decorative emoji `aria-hidden="true"`; functional have labels |
| C1.4 Lang attribute | 3.1.1 (A) | Automated | HTML has `lang="en"` |
| C1.5 Abbreviations | 3.1.4 (AAA) | Manual | `<abbr title="...">` on first use |
| C1.6 Table captions | 1.3.1 (A) | Both | Complex tables have `<caption>` |
| C1.7 Horizontal scroll table region | 2.1.1 (A), 2.4.3 (A) | Both | Wrapper has `role="region" tabindex="0"` |
| C1.8 Gauge text equivalent | 1.1.1 (A) | Both | Adjacent text: "RPM: 2450 (Normal: 800-6500)" |
| C1.9 Sparkline accessibility | 1.1.1 (A) | Both | Data table or text summary provided |
| C1.10 Multi-series: patterns/markers | 1.4.1 (A) | Both | Dash patterns + markers + direct labels |
| C1.11 Comparison: unique patterns | 1.4.1 (A), 1.3.1 (A) | Both | Per-session dash+marker+legend shape |
| C1.12 Bar charts: patterns/labels | 1.4.1 (A) | Both | Hatch fill or direct labels |
| C1.13 Heatmap accessibility | 1.1.1 (A), 1.4.1 (A) | Both | Data table + cell text values |
| C1.14 Pie chart accessibility | 1.1.1 (A), 1.4.1 (A) | Both | Direct labels + data table |
| C1.15 Scatter accessibility | 1.1.1 (A) | Both | Data table + distinct markers |
| C1.16 Drawer announcements | 4.1.3 (AA) | Manual | "Navigation opened/closed" announced |
| C1.17 Tab heading order mobile | 1.3.1 (A) | Manual | Stacked tabs have proper headings |
| C1.18 Card grid focus order | 2.4.3 (A) | Manual | DOM order = logical reading order |
| C1.19 Touch target spacing | 2.5.5 (AAA) | Automated | ≥8px between targets at 375px |
| C1.20 Reflow at 200% zoom | 1.4.10 (AA) | Manual | No horizontal scroll at 320px equivalent |
| C1.21 Text spacing override | 1.4.12 (AA) | Automated | No `!important` on line-height/letter-spacing |
| C1.22 Custom select accessible | 4.1.2 (A), 2.1.1 (A) | Both | Use `FormFieldProps`/`selectbox()` consistently |
| C1.23 Loading announcements | 4.1.3 (AA) | Both | Skeleton/spinner in `aria-live="polite"` |
| C1.24 Empty state announcements | 4.1.3 (AA) | Both | `role="status" aria-live="polite"` |

---

## Phase 7D: Low Polish (11 P3 Findings)

| Finding | WCAG SC | Test Type | Key Verification |
|---------|---------|-----------|------------------|
| D1.1 Focus ring consistency | 2.4.7 (AA) | Automated | All focus use `--color-border-focus` |
| D1.2 High contrast charts | 1.4.6 (AAA) | Manual | Charts adapt to `prefers-contrast: high` |
| D1.3 Reduced motion Plotly | 2.3.3 (AAA) | Automated | Chart transitions disabled |
| D1.4 Unique page titles | 2.4.2 (A) | Automated | Each standalone report has unique title |
| D1.5 Semantic breadcrumbs | 2.4.8 (AAA) | Both | `<nav aria-label="Breadcrumb"><ol><li>` |
| D1.6 Search role on filters | 4.1.2 (A) | Both | `type="search"` or `role="search"` |
| D1.7 Accessible tooltips | 1.3.1 (A), 2.1.1 (A) | Manual | Help text on focus + hover; `aria-describedby` |
| D1.8 Status text equivalents | 1.4.1 (A) | Both | Visually-hidden text for dots; legend shapes |
| D1.9 Keyboard shortcuts | 2.1.1 (A), 2.1.2 (A) | Manual | `?` key shows help; documented in About |
| D1.10 Session timeout | 2.2.1 (A) | N/A | Future: if implemented, must be accessible |
| D1.11 Help accessible | 3.3.5 (AAA) | Manual | Help content in heading order; searchable |

---

## Automated Test Infrastructure

### Required Setup
```bash
pip install playwright axe-core
playwright install chromium
```

### Test Files to Create

| File | Purpose |
|------|---------|
| `tests/accessibility/conftest.py` | Playwright fixtures, viewport configs |
| `tests/accessibility/test_skip_link.py` | A1.1 |
| `tests/accessibility/test_aria_current.py` | A1.2 |
| `tests/accessibility/test_custom_buttons.py` | A1.3 |
| `tests/accessibility/test_form_aria.py` | A1.4, B1.4, B1.5, B1.6 |
| `tests/accessibility/test_live_regions.py` | A1.5, B1.10-B1.14 |
| `tests/accessibility/test_color_only.py` | A1.6 |
| `tests/accessibility/test_contrast.py` | A1.7 |
| `tests/accessibility/test_focus_trap.py` | A1.8, B1.8 |
| `tests/accessibility/test_table_semantics.py` | A1.9, C1.6, C1.7 |
| `tests/accessibility/test_chart_alternatives.py` | A1.10, C1.8-C1.15 |
| `tests/accessibility/test_reduced_motion.py` | A1.11, D1.3 |
| `tests/accessibility/test_touch_targets.py` | A1.12, C1.19 |
| `tests/accessibility/test_headings.py` | B1.1 |
| `tests/accessibility/test_landmarks.py` | B1.2 |
| `tests/accessibility/test_wizard_aria.py` | B1.3 |
| `tests/accessibility/test_focus_visible.py` | B1.7 |
| `tests/accessibility/test_chat_accessibility.py` | B1.9 |
| `tests/accessibility/test_keyboard_nav.py` | C1.18, C1.20 |

### Viewport Test Configurations
```python
VIEWPORTS = [
    {"name": "desktop", "width": 1440, "height": 900},
    {"name": "laptop", "width": 1100, "height": 800},
    {"name": "tablet-landscape", "width": 900, "height": 768},
    {"name": "tablet-portrait", "width": 768, "height": 1024},
    {"name": "mobile", "width": 390, "height": 844},
    {"name": "mobile-small", "width": 360, "height": 800},
    {"name": "mobile-min", "width": 320, "height": 700},
]
```

### axe-core Integration
```python
# In each test
from axe_playwright_python import Axe
async def test_accessibility(page, viewport):
    await page.set_viewport_size(viewport)
    await page.goto(f"http://localhost:8501/{page_name}")
    axe = Axe()
    await axe.inject(page)
    results = await axe.run(page)
    assert len(results.violations) == 0, f"Violations: {results.violations}"
```

---

## Manual Test Checklist Per Phase

### Phase 7A Completion Checklist
- [ ] **Keyboard Only:** Tab through all 13 pages — no traps, all actions reachable, skip link works
- [ ] **NVDA + Chrome:** Skip link, live regions, forms, tables, charts (data tables), color-only check
- [ ] **JAWS + Firefox:** Same as NVDA
- [ ] **VoiceOver + Safari (macOS/iOS):** Mobile drawer, touch targets, gestures
- [ ] **Zoom 200%:** No horizontal scroll, all content readable, touch targets work
- [ ] **High Contrast Mode:** Windows High Contrast / macOS Increase Contrast — all UI visible
- [ ] **Reduced Motion:** OS setting ON — animations disabled
- [ ] **Color Blindness:** Protanopia/Deuteranopia/Tritanopia simulation — no color-only info
- [ ] **Mobile (375px):** Touch targets ≥44px, drawer works, tables scroll, forms usable

### Phase 7B Completion Checklist
- [ ] **Keyboard Only:** Wizard, chat, drawer fully navigable
- [ ] **NVDA:** Headings, landmarks, wizard tabs, chat messages, step announcements
- [ ] **Charts:** Keyboard nav works, data tables readable
- [ ] **Print Preview:** Reports clean

### Phase 7C Completion Checklist
- [ ] All P2 items verified via manual + automated

### Phase 7D Completion Checklist
- [ ] Lighthouse accessibility score ≥ 95 on all pages
- [ ] All P3 items verified

---

## Regression Test Integration

### Existing Test Suite
- **415 tests** — Must pass after each phase
- Run: `python -m pytest tests/ -v`

### New Accessibility Tests
- **8+ new test files** — Integrated into pytest
- Run: `python -m pytest tests/accessibility/ -v`

### CI Pipeline (Future)
```yaml
# .github/workflows/accessibility.yml
jobs:
  accessibility:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt && pip install playwright axe-core
      - run: playwright install chromium
      - run: python -m pytest tests/ -v
      - run: python -m pytest tests/accessibility/ -v
```

---

## Sign-Off Criteria

| Phase | Automated | Manual | Regression | Documentation |
|-------|-----------|--------|------------|---------------|
| 7A | All P0 axe/Playwright pass | Keyboard, NVDA, JAWS, VoiceOver, Zoom, Contrast, Motion, Color, Mobile | 415/415 pass | Update progress tracker |
| 7B | All P1 axe/Playwright pass | Keyboard, NVDA (headings, landmarks, wizard, chat, charts), Print | 415/415 pass | Update progress tracker |
| 7C | All P2 axe/Playwright pass | All P2 manual checks | 415/415 pass | Update progress tracker |
| 7D | Lighthouse ≥ 95 | All P3 manual checks | 415/415 + new tests pass | Final docs, progress tracker COMPLETE |

---

*Test Matrix created 2026-11-18 — Execution pending Stage 6 verification and Phase 7A start*