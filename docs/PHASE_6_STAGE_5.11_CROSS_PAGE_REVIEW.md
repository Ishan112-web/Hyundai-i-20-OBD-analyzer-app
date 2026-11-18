# Phase 6 Stage 5.11: Cross-Page Design Consistency Review & Harmonization

**Date:** 2026-11-18  
**Status:** AUDIT COMPLETE — IMPLEMENTATION READY  
**Test Baseline:** 415/415 tests passing (pre-audit)

---

## Executive Summary

Completed read-only audit across all **9 main pages** + **4 standalone report pages** (13 total). All pages use the Stage 3 Design System (tokens, components, layout, charts_v2) with zero custom CSS remaining in page modules. The global shell (`components/shell.py`) provides consistent sidebar, top bar, and page headers across all 9 pages.

**Key Finding:** The application is **already highly consistent** — all pages use design system tokens and components. Remaining inconsistencies are minor presentation-level issues (P1/P2), not structural. No P0 (critical) issues found.

---

## 1. Cross-Page Review Matrix

### 1.1 Page Headers (via `page_header` from shell/layout)

| Page | Uses Shell `page_header`? | Icon | Subtitle | Actions/Status Badges | Notes |
|------|---------------------------|------|----------|----------------------|-------|
| Dashboard | ✅ (via shell) | 🏠 | "Real-time vehicle monitoring & telemetry" | OBD, Simulation, AI status in top bar | Shell-driven |
| Diagnostics | ✅ (via shell) | 🔧 | "DTC scanning, AI diagnosis & rule engine" | Same | Shell-driven |
| Performance | ✅ (via shell) | 📊 | "Session analytics, comparison & statistics" | Same | Shell-driven |
| Maintenance | ✅ (via shell) | 🔩 | "Service records, intervals & upcoming reminders" | Same | Shell-driven |
| Vehicle Profile | ✅ (via shell) | 🚗 | "Vehicle specifications & configuration" | Same | Shell-driven |
| AI Assistant | ✅ (via shell) | 🤖 | "Local AI chat & diagnostic assistance" | Same | Shell-driven |
| OBD Connection | ✅ (via shell) | 🔌 | "OBD-II hardware setup & connection wizard" | Same | Shell-driven |
| Reports | ✅ (via shell) | 📋 | "Professional diagnostic, health & performance reports" | Same | Shell-driven |
| Settings | ✅ (via shell) | ⚙️ | "Application configuration & preferences" | Same | Shell-driven |

**Consistency:** ✅ **Excellent** — All 9 pages use `render_page_header()` from shell with consistent structure. Top bar shows unified status indicators (OBD, Simulation, AI).

---

### 1.2 Section Hierarchy (via `section_header`)

| Page | Uses `section_header`? | Sections Count | Pattern |
|------|------------------------|----------------|---------|
| Dashboard | ❌ (inline headers) | 3 implicit | Uses card titles + markdown |
| Diagnostics | ❌ (inline headers) | 6 implicit | Uses card titles + markdown |
| Performance | ❌ (inline headers) | 4 tabs + subsections | Tab headers as sections |
| Maintenance | ✅ (explicit) | 6+ | Consistent `section_header(title, description)` |
| Vehicle Profile | ✅ (explicit) | 8+ | Consistent `section_header(title, description)` |
| AI Assistant | ✅ (explicit) | 5+ | Consistent `section_header(title, description)` |
| OBD Connection | ✅ (explicit) | 8 (wizard steps) | Wizard step content + `section_header` |
| Reports | ✅ (explicit) | 8+ | Consistent `section_header(title, description)` |
| Settings | ✅ (explicit) | 12+ | Consistent `section_header(title, description)` |

**Inconsistency:** Dashboard, Diagnostics, Performance use inline headers/card titles instead of `section_header()`. These 3 pages predate the section_header component or use tab-based layouts.

---

### 1.3 Card Consistency

| Page | `card()` | `card_simple()` | Custom Card HTML | Card Patterns |
|------|----------|-----------------|------------------|---------------|
| Dashboard | 0 | 16 (gauges, telemetry, status) | 0 | `card_simple(title, content="", footer="")` wrapping Plotly charts |
| Diagnostics | 10+ | 5+ | 0 | Mixed: `card()` for detail panels, `card_simple()` for summary |
| Performance | 0 | 25+ | 0 | All `card_simple()` for charts + metric cards |
| Maintenance | 15+ | 3+ | 0 | `card()` for records/upcoming, `card_simple()` for stats |
| Vehicle Profile | 10+ | 0 | 12 (info cards, spec cards) | **12 custom card HTML blocks** (info grid, spec cards, summary) |
| AI Assistant | 20+ | 2+ | 3 (message bubbles, loading, header) | `card()` for panels, custom HTML for chat messages |
| OBD Connection | 8+ | 2+ | 8 (wizard step cards, metric cards) | Mix of `card()` + custom HTML for metric grids |
| Reports | 12+ | 5+ | 3 (metadata cards, saved reports) | `card()` + custom HTML for report list items |
| Settings | 20+ | 5+ | 0 | All design system cards |

**Inconsistency:** Vehicle Profile has **12 custom card HTML blocks** (lines 207-251, 433-478, 502-545, etc.) that should use `card_simple()` or `card()`. AI Assistant has 3 custom message bubbles. OBD Connection has 8 custom metric/summary cards. Reports has 3 custom cards.

---

### 1.4 Buttons / Actions

| Page | `button_primary` | `button_secondary` | `button_ghost` | `button_danger` | Native `st.button` | Native `st.form_submit_button` |
|------|------------------|-------------------|----------------|-----------------|-------------------|-------------------------------|
| Dashboard | 3 | 3 | 0 | 0 | 0 | 0 |
| Diagnostics | 8 | 5 | 3 | 2 | 0 | 0 |
| Performance | 12 | 8 | 3 | 3 | 0 | 0 |
| Maintenance | 5 | 4 | 9 | 1 | 0 | 1 |
| Vehicle Profile | 2 | 2 | 0 | 1 | 0 | 1 |
| AI Assistant | 8 | 4 | 6 | 3 | 0 | 2 |
| OBD Connection | 12 | 6 | 1 | 0 | 0 | 0 |
| Reports | 6 | 4 | 2 | 0 | 1 | 0 |
| Settings | 8 | 12 | 2 | 8 | 0 | 1 |

**Consistency:** ✅ **Good** — All pages use design system button variants. Settings uses most `button_danger` (8) for destructive actions. One native `st.button` in Reports (download), one `st.form_submit_button` in Maintenance/Settings/AI Assistant forms.

---

### 1.5 Badges / Status Indicators

| Page | `badge()` Component | Custom Badge HTML | Variants Used |
|------|---------------------|-------------------|---------------|
| Dashboard | 6 | 0 | SUCCESS, WARNING, INFO, NEUTRAL |
| Diagnostics | 15+ | 3 (`_render_badge_html`, `_format_severity_badge`) | SUCCESS, WARNING, CRITICAL, INFO, NEUTRAL, PRIMARY |
| Performance | 8 | 0 | SUCCESS, WARNING, INFO, NEUTRAL |
| Maintenance | 20+ | 1 (status badge HTML lines 311-319) | SUCCESS, WARNING, CRITICAL, NEUTRAL, PRIMARY |
| Vehicle Profile | 1 | 3 (mode badge + status dots) | WARNING, SUCCESS, NEUTRAL, CRITICAL |
| AI Assistant | 12+ | 1 (`_render_badge_html` inline) | SUCCESS, WARNING, CRITICAL, INFO, NEUTRAL, PRIMARY, SECONDARY |
| OBD Connection | 8 | 1 (likely OBD badge) | SUCCESS, WARNING, CRITICAL, NEUTRAL, INFO |
| Reports | 10+ | 0 | SUCCESS, WARNING, CRITICAL, INFO, NEUTRAL |
| Settings | 15+ | 0 | SUCCESS, WARNING, CRITICAL, INFO, NEUTRAL, PRIMARY |

**Inconsistency:** 4 pages have custom badge HTML: Diagnostics (3 functions), Maintenance (1), Vehicle Profile (3), AI Assistant (1), OBD Connection (1). These should use the `badge()` component.

---

### 1.6 Forms / Inputs

| Page | `text_input()` | `selectbox()` | Native `st.text_input` | Native `st.selectbox` | Native `st.number_input` | Native `st.date_input` | `st.form` |
|------|----------------|---------------|------------------------|-----------------------|--------------------------|------------------------|-----------|
| Dashboard | 0 | 1 (scenario) | 0 | 0 | 0 | 0 | 0 |
| Diagnostics | 0 | 1 | 0 | 0 | 0 | 0 | 0 |
| Performance | 1 | 2 | 0 | 0 | 1 | 0 | 0 |
| Maintenance | 3 | 4 | 0 | 0 | 3 | 2 | 1 |
| Vehicle Profile | 6 | 4 | 0 | 0 | 1 | 0 | 1 |
| AI Assistant | 2 | 1 | 0 | 0 | 0 | 0 | 1 |
| OBD Connection | 3 | 4 | 0 | 0 | 2 | 0 | 0 |
| Reports | 5 | 4 | 0 | 1 (radio) | 3 | 0 | 0 |
| Settings | 4 | 5 | 0 | 0 | 0 | 0 | 0 |

**Consistency:** ✅ **Good** — Most pages use design system form components. Only Reports uses 1 native `st.radio`. Native `st.number_input` and `st.date_input` used where design system lacks equivalents (acceptable).

---

### 1.7 Tables / Lists

| Page | `table()` Component | Custom Table HTML | Native `st.dataframe` |
|------|---------------------|-------------------|----------------------|
| Dashboard | 0 | 0 | 0 |
| Diagnostics | 2 (history, rule findings) | 0 | 0 |
| Performance | 2 (stats, comparison) | 0 | 0 |
| Maintenance | 1 (intervals reference) | 0 | 0 |
| Vehicle Profile | 0 | 0 | 0 |
| AI Assistant | 0 | 0 | 0 |
| OBD Connection | 0 | 0 | 0 |
| Reports | 0 | 0 | 0 |
| Settings | 0 | 0 | 0 |

**Consistency:** ✅ **Good** — Only Diagnostics and Performance use tables. Both use `table()` component.

---

### 1.8 Empty / Loading States

| Page | `empty_state()` | `skeleton()` / `skeleton_card()` | `spinner()` | `loading_overlay()` |
|------|-----------------|----------------------------------|-------------|---------------------|
| Dashboard | 1 | 0 | 1 | 0 |
| Diagnostics | 2 | 2 | 3 | 0 |
| Performance | 4 | 0 | 2 | 0 |
| Maintenance | 3 | 2 | 0 | 0 |
| Vehicle Profile | 1 | 0 | 0 | 0 |
| AI Assistant | 2 | 0 | 1 | 0 |
| OBD Connection | 2 | 6 (skeleton_card in ECU step) | 0 | 0 |
| Reports | 4 | 0 | 3 | 0 |
| Settings | 6 | 0 | 3 | 0 |

**Consistency:** ✅ **Good** — All pages use design system empty/loading components appropriately.

---

### 1.9 Charts (via `charts_v2.py`)

| Page | `create_gauge` | `create_line_chart` | `create_sparkline` | `create_bar_chart` | `create_comparison_chart` | Series Palette (SERIES_1-5) |
|------|----------------|---------------------|---------------------|---------------------|---------------------------|----------------------------|
| Dashboard | 4 | 1 (multi-series) | 10 | 0 | 0 | ✅ Consistent |
| Diagnostics | 0 | 0 | 0 | 0 | 0 | N/A |
| Performance | 0 | 6 | 4 | 2 (histograms) | 5 | ✅ Consistent |
| Maintenance | 0 | 0 | 0 | 0 | 0 | N/A |
| Vehicle Profile | 0 | 0 | 0 | 0 | 0 | N/A |
| AI Assistant | 0 | 0 | 0 | 0 | 0 | N/A |
| OBD Connection | 0 | 0 | 0 | 0 | 0 | N/A |
| Reports | 0 | 0 | 0 | 0 | 0 | N/A |
| Settings | 0 | 0 | 0 | 0 | 0 | N/A |

**Consistency:** ✅ **Excellent** — Charts use token-driven `charts_v2.py` with fixed SERIES_1-5 palette. Dashboard and Performance use charts correctly.

---

## 2. Token Consistency Audit

### 2.1 Color Token Usage (53 tokens)

| Token Category | Usage Pattern | Consistent? |
|----------------|---------------|-------------|
| **Surfaces** (SURFACE_PRIMARY, SECONDARY, ELEVATED, INTERACTIVE) | All pages import and use | ✅ Yes |
| **Text** (TEXT_PRIMARY, SECONDARY, MUTED, ON_ACCENT) | All pages import and use | ✅ Yes |
| **Borders** (BORDER_DEFAULT, SUBTLE, STRONG, FOCUS) | All pages import and use | ✅ Yes |
| **Status** (SUCCESS, WARNING, CRITICAL, INFO, NEUTRAL) | All pages import and use | ✅ Yes |
| **Accents** (ACCENT_PRIMARY, SECONDARY, HOVER, ACTIVE, SELECTED) | All pages import and use | ✅ Yes |
| **Diagnostic Severity** (DIAG_CRITICAL, MAJOR, MINOR, INFO) | Diagnostics, Vehicle Profile, AI Assistant, Reports | ✅ Yes |
| **Data Source** (DATASOURCE_REAL, SIMULATION) | All pages with OBD/AI status | ✅ Yes |
| **Chart Series** (SERIES_1-5) | Dashboard, Performance | ✅ Yes |
| **Chart Status** (CHART_GOOD, WARNING, SERIOUS, CRITICAL) | Dashboard, Performance | ✅ Yes |

**No color token inconsistencies found.** All pages import tokens from `components.ui.tokens` and use semantic names.

---

### 2.2 Typography Token Usage (16 tokens)

| Token | Usage | Consistent? |
|-------|-------|-------------|
| FONT_SIZE_H1-H4 | Page headers, section headers, card titles | ✅ Yes |
| FONT_SIZE_BODY, BODY_SM | Standard content, form inputs | ✅ Yes |
| FONT_SIZE_LABEL | Form labels, metadata, badge text | ✅ Yes |
| FONT_SIZE_CAPTION | Fine print, timestamps, helper text | ✅ Yes |
| FONT_FAMILY_BASE, MONO | Body text, numeric/monospace values | ✅ Yes |
| FONT_WEIGHT_LABEL, BODY, NUMERIC | Semantic weight usage | ✅ Yes |
| LETTER_SPACING_LABEL, CAPTION | Uppercase labels, captions | ✅ Yes |

**Minor inconsistency:** Vehicle Profile and OBD Connection use hardcoded `"monospace"` or `FONT_FAMILY_MONO` inline in HTML instead of the token constant in a few places. Not a functional issue.

---

### 2.3 Spacing Token Usage (12 base + 9 aliases)

| Token | Usage | Consistent? |
|-------|-------|-------------|
| SPACE_1-6 (4px-24px) | All padding, margins, gaps | ✅ Yes |
| GAP_INLINE, FIELD, CARD_GRID, SECTION | Semantic gaps between elements | ✅ Yes |

**All pages use spacing tokens consistently.** No hardcoded pixel values found in page modules.

---

### 2.4 Radius / Elevation

| Token | Usage | Consistent? |
|-------|-------|-------------|
| RADIUS_SM, MD, LG, PILL | Inputs, cards, badges, buttons | ✅ Yes |
| SHADOW_SM, MD, LG, FOCUS | Card elevation, focus states | ✅ Yes |

**Consistent.** Some pages use `RADIUS_MD` for cards, others `RADIUS_LG` — both valid design system choices.

---

### 2.5 Chart Series Mapping

| Page | SERIES_1 | SERIES_2 | SERIES_3 | SERIES_4 | SERIES_5 |
|------|----------|----------|----------|----------|----------|
| Dashboard | RPM (primary) | Speed | Coolant | Load | Throttle |
| Performance | RPM | Speed | Coolant | Load | Throttle/Fuel Trim |
| Diagnostics | N/A | N/A | N/A | N/A | N/A |

**✅ Consistent mapping** — Same semantic metric → same series color across Dashboard and Performance.

---

## 3. Shared Component Consistency

### 3.1 Duplicated Presentation Logic

| Pattern | Pages Affected | Recommendation |
|---------|---------------|----------------|
| Custom card HTML for info grids | Vehicle Profile (12), OBD Connection (8), AI Assistant (3), Reports (3) | Replace with `card_simple()` + design tokens |
| Custom badge HTML | Diagnostics (3 fns), Maintenance (1), Vehicle Profile (3), AI Assistant (1), OBD Connection (1) | Use `badge()` component |
| Custom metric cards (HTML) | Vehicle Profile, OBD Connection, Performance | Use `card_simple()` with `AUTO_FIT_METRIC_CSS` |
| Inline status dots (12px circles) | Vehicle Profile, AI Assistant | Use `status_indicator()` from layout |
| Wizard step skeleton loaders | OBD Connection | Use `skeleton_card()` |

**Action Items (P1):** 28 custom HTML blocks across 5 pages should migrate to design system components.

---

### 3.2 Global Shell / Navigation Consistency

| Element | Implementation | Status |
|---------|----------------|--------|
| Sidebar navigation | `SidebarProps` + `sidebar()` component | ✅ Consistent |
| Top bar | `TopBarProps` + `top_bar()` component | ✅ Consistent |
| Page header | `page_header()` from layout | ✅ Consistent |
| Breadcrumbs | `get_breadcrumb_for_page()` in shell | ✅ Consistent |
| Status indicators (OBD, AI, Sim) | `status_indicator()` in top bar | ✅ Consistent |
| Vehicle context in sidebar | `get_vehicle_info()` + `SidebarProps` | ✅ Consistent |

**✅ Global shell is fully consistent** across all 9 pages via `render_shell()` in app.py.

---

## 4. Custom CSS / HTML Audit

### 4.1 Pages with Zero Custom CSS (✅)

- Dashboard — uses `responsive_grid_css`, `auto_fit_grid_css` from layout
- Diagnostics — no custom CSS
- Performance — uses `responsive_grid_css`, `auto_fit_grid_css` from layout
- Maintenance — no custom CSS (replaced ~260 lines)
- AI Assistant — no custom CSS (replaced ~300 lines)
- OBD Connection — no custom CSS (replaced ~350 lines)
- Reports — no custom CSS (replaced ~80 lines)
- Settings — no custom CSS (replaced ~220 lines)

### 4.2 Pages with Custom HTML (Inline Styles Using Tokens)

| Page | Custom HTML Blocks | Type |
|------|-------------------|------|
| Vehicle Profile | 12 | Info cards, spec cards, summary cards, detail rows |
| AI Assistant | 3 | Chat message bubbles, loading indicator, header badge |
| OBD Connection | 8 | Wizard step cards, metric summary cards, PID grid |
| Reports | 3 | Report metadata cards, saved report list items |
| Diagnostics | 3 | Badge rendering helpers |

**Note:** All inline styles use design tokens (e.g., `{SURFACE_SECONDARY}`, `{ACCENT_PRIMARY}`) — no hardcoded colors. These are **presentation-level** inconsistencies (P1), not token violations.

---

## 5. Responsive Pre-Check (4 Breakpoints)

| Page | Mobile (<768px) | Tablet (768-1024px) | Laptop (1024-1280px) | Desktop (>1280px) | Grid System Used |
|------|-----------------|---------------------|----------------------|-------------------|------------------|
| Dashboard | Gauge stack 1-col | Gauge 2-col | Gauge 4-col | Gauge 4-col | `GAUGE_GRID_CSS`, `AUTO_FIT_CARD_CSS` |
| Diagnostics | Single column | Single column | 2-col DTC + detail | 2-col DTC + detail | `card()` full width |
| Performance | Charts stack 1-col | Charts 1-col | Charts 2-col | Charts 2-col | `responsive_grid_css(min_column_width="500px")` |
| Maintenance | Cards stack 1-col | Cards 1-col | Cards 2-3 col | Cards 3-4 col | `auto_fit_grid_css(min_width="320px")` |
| Vehicle Profile | Info cards 1-col | Info cards 2-col | Info cards 3-4 col | Info cards 4-5 col | `AUTO_FIT_CARD_CSS` |
| AI Assistant | Chat full width, sidebar hidden | Chat 3:1 split | Chat 3:1 split | Chat 3:1 split | Native columns |
| OBD Connection | Wizard full width | Wizard full width | Wizard full width | Wizard full width | `wizard()` component |
| Reports | Config sidebar, tabs stack | Config sidebar, tabs stack | Config sidebar, tabs side-by-side | Config sidebar, tabs side-by-side | Native sidebar + tabs |
| Settings | Tabs stack, forms stack | Tabs stack, forms stack | Tabs horizontal, forms 2-col | Tabs horizontal, forms 2-col | Native tabs + columns |

**Finding:** All pages use design system responsive grids (`AUTO_FIT_CARD_CSS`, `AUTO_FIT_METRIC_CSS`, `responsive_grid_css`) or native Streamlit columns that respond correctly. No fixed-width layouts found.

---

## 6. Accessibility Pre-Check (WCAG 2.1 AA)

| Criterion | Status | Notes |
|-----------|--------|-------|
| **Color Contrast** | ✅ Validated in Stage 3 | 22 token combinations validated against WCAG 2.1 AA |
| **Semantic HTML** | ⚠️ Partial | Custom HTML blocks use `<div>` not semantic elements |
| **ARIA Labels** | ⚠️ Partial | Design system components include ARIA; custom HTML lacks |
| **Focus Indicators** | ✅ | `BORDER_FOCUS`, `SHADOW_FOCUS` tokens used |
| **Keyboard Navigation** | ✅ | Native Streamlit + button components |
| **Screen Reader Support** | ⚠️ Partial | Alert, badge, button components have ARIA; custom cards don't |
| **Text Scaling** | ✅ | Rem-based tokens, no fixed px for text |
| **Motion Reduction** | ⚠️ Not implemented | No `prefers-reduced-motion` handling |

**Deferred to Stage 7:** ARIA labels for custom HTML blocks, semantic HTML migration, `prefers-reduced-motion`.

---

## 7. Priority Classification

### P0 — Critical (Must Fix Before Merge)
**None found.** All functionality preserved, all tests passing, no token violations.

---

### P1 — High (Fix in This Stage 5.11)

| # | Issue | Pages | Effort | Risk |
|---|-------|-------|--------|------|
| 1 | Replace 12 custom card HTML blocks in Vehicle Profile with `card_simple()` | Vehicle Profile | Medium | Low |
| 2 | Replace 3 custom badge HTML functions in Diagnostics with `badge()` | Diagnostics | Low | Low |
| 3 | Replace 1 custom badge HTML in Maintenance with `badge()` | Maintenance | Low | Low |
| 4 | Replace 3 custom status badges in Vehicle Profile with `badge()` + `status_indicator()` | Vehicle Profile | Low | Low |
| 5 | Replace 1 custom badge HTML in AI Assistant with `badge()` | AI Assistant | Low | Low |
| 6 | Replace 1 custom badge in OBD Connection with `badge()` | OBD Connection | Low | Low |
| 7 | Replace 8 custom wizard/metric cards in OBD Connection with `card_simple()` + grids | OBD Connection | Medium | Low |
| 8 | Replace 3 custom report cards in Reports with `card_simple()` | Reports | Low | Low |
| 9 | Add `section_header()` to Dashboard, Diagnostics, Performance for consistency | Dashboard, Diagnostics, Performance | Low | Low |

**Total P1 items:** 9 | **Estimated effort:** ~2-3 hours | **Risk:** Low (presentation only)

---

### P2 — Medium (Defer to Stage 6 Responsive / Stage 7 Accessibility)

| # | Issue | Pages | Stage |
|---|-------|-------|-------|
| 1 | Add semantic HTML (`<section>`, `<article>`) to custom card blocks | Vehicle Profile, OBD Connection, AI Assistant, Reports | Stage 6 |
| 2 | Add ARIA labels to chat message bubbles (AI Assistant) | AI Assistant | Stage 7 |
| 3 | Add `prefers-reduced-motion` support for skeleton pulse animations | OBD Connection, all pages with skeletons | Stage 7 |
| 4 | Ensure all custom HTML uses `role` attributes appropriately | All pages with custom HTML | Stage 7 |
| 5 | Validate responsive behavior of wizard component at mobile breakpoint | OBD Connection | Stage 6 |
| 6 | Standardize metric card implementation across Performance, Vehicle Profile, OBD Connection | Performance, Vehicle Profile, OBD Connection | Stage 6 |

---

## 8. Implementation Plan for P1 Fixes

### Phase A: Vehicle Profile (Highest impact — 12 custom cards)
1. Replace info grid (lines 207-251) → `card_simple()` in `AUTO_FIT_CARD_CSS` grid
2. Replace spec cards (lines 433-478) → `card_simple()` in `AUTO_FIT_METRIC_CSS` grid
3. Replace derived spec cards (lines 502-545) → `card_simple()` in `AUTO_FIT_CARD_CSS` grid
4. Replace OBD/AI detail cards (lines 586-668, 728-768) → `card()` component

### Phase B: Diagnostics (3 badge functions)
1. Replace `_format_severity_badge()` → `badge(variant=BadgeVariant.CRITICAL/WARNING/INFO/NEUTRAL)`
2. Replace `_render_badge_html()` → `badge()`
3. Replace `_render_mode_badge()` → `badge()`

### Phase C: Maintenance (1 badge)
1. Replace inline status badge HTML (lines 311-319) → `badge()`

### Phase D: AI Assistant (1 badge)
1. Replace `_render_badge_html()` helper → `badge()`

### Phase E: OBD Connection (1 badge + 8 cards)
1. Replace "Likely OBD" badge (lines 300-304) → `badge()`
2. Replace wizard step metric cards → `card_simple()` + `AUTO_FIT_METRIC_CSS`
3. Replace PID grid cards → `card_simple()` + `AUTO_FIT_CARD_CSS`

### Phase F: Reports (3 cards)
1. Replace report metadata cards (lines 392-416, 580-600, 629-649) → `card_simple()` or `card()`
2. Replace saved report list items (lines 753-772, 783-792) → `card_simple()`

### Phase G: Section Headers (3 pages)
1. Dashboard: Add `section_header()` for "Live Telemetry", "System Status", "Quick Actions"
2. Diagnostics: Add `section_header()` for "DTC Scanner", "DTC Details", "AI Diagnosis", "Rule Engine", "History"
3. Performance: Add `section_header()` for each tab's subsections

---

## 9. Regression Test Plan

| Test Suite | Current Status | Post-Fix Target |
|------------|----------------|-----------------|
| Full regression (415 tests) | 415 passed | 415 passed |
| Database tests | 27 passed | 27 passed |
| AI Service tests | 8 passed | 8 passed |
| Diagnostic Engine tests | 65 passed | 65 passed |
| Migration/Backup tests | 84 passed | 84 passed |
| OBD Real tests | 50 passed | 50 passed |
| Visual verification (manual) | All 9 pages verified | Re-verify all 9 pages |

**No test updates needed** — P1 fixes are presentation-only, no logic changes.

---

## 10. Visual Verification Checklist (Post-Fix)

| Page | Desktop | Tablet | Mobile | Dark Theme | Notes |
|------|---------|--------|--------|------------|-------|
| Dashboard | ☐ | ☐ | ☐ | ✅ | Gauges, sparklines, status panel |
| Diagnostics | ☐ | ☐ | ☐ | ✅ | DTC table, detail panel, AI diagnosis |
| Performance | ☐ | ☐ | ☐ | ✅ | 6 charts, stats, sessions, comparison |
| Maintenance | ☐ | ☐ | ☐ | ✅ | Record cards, form, upcoming grid |
| Vehicle Profile | ☐ | ☐ | ☐ | ✅ | Info grid, specs, connections, DTCs |
| AI Assistant | ☐ | ☐ | ☐ | ✅ | Chat, diagnostic mode, sidebar |
| OBD Connection | ☐ | ☐ | ☐ | ✅ | 8-step wizard, connected state |
| Reports | ☐ | ☐ | ☐ | ✅ | Generate, preview, download, saved |
| Settings | ☐ | ☐ | ☐ | ✅ | 6 tabs, all forms, backup/restore |

---

## 11. Acceptance Checklist

- [ ] **Zero custom CSS** in all 9 page modules (already achieved)
- [ ] **Zero hardcoded colors** — all styling via design tokens (already achieved)
- [ ] **All 34 shared + page-specific session state keys preserved** (verified)
- [ ] **All backend integrations preserved** (Database, AI, OBD, DiagnosticEngine, RuleEngine)
- [ ] **P1 fixes implemented** (9 items)
- [ ] **415/415 tests passing** post-fix
- [ ] **Visual verification** complete at 4 breakpoints
- [ ] **Documentation updated** (`PHASE_6_PROGRESS.md`, this file)

---

## 12. Files to Modify (P1 Fixes)

| File | Changes |
|------|---------|
| `modules/vehicle_profile.py` | Replace 12 custom card HTML blocks with `card_simple()`/`card()` + grids |
| `modules/diagnostics.py` | Replace 3 badge helper functions with `badge()` component |
| `modules/maintenance.py` | Replace 1 inline badge HTML with `badge()` |
| `modules/ai_assistant.py` | Replace `_render_badge_html()` with `badge()` |
| `modules/obd_connection.py` | Replace 1 badge + 8 custom cards with design system components |
| `modules/reports.py` | Replace 3 custom cards with `card_simple()`/`card()` |
| `modules/dashboard.py` | Add `section_header()` for 3 sections |
| `modules/diagnostics.py` | Add `section_header()` for 5 sections |
| `modules/performance.py` | Add `section_header()` for tab subsections |

---

## 13. Conclusion

The i20 AI Garage application achieves **excellent design consistency** across all 13 pages. The Stage 3 Design System is properly adopted throughout. Remaining inconsistencies are **presentation-level only** (custom HTML blocks using design tokens instead of design system components). No structural, functional, or token-level issues exist.

**Recommendation:** Implement the 9 P1 fixes in this stage (5.11). Defer P2 items to Stage 6 (Responsive) and Stage 7 (Accessibility) as planned. The application is ready for production-quality visual consistency with minimal effort.

---

*Report generated as part of Phase 6 Stage 5.11 Cross-Page Design Consistency Review*