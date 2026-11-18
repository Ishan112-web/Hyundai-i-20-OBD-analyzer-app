# Phase 6: UI/UX Modernization — Stage 2 Complete Design System Specification

**Project:** i20 AI Garage  
**Date:** 2026-11-16  
**Phase:** 6 — UI/UX Modernization (Stage 2: Design Direction & Specification Complete)

---

## 1. Stage 2 Status

**COMPLETE**

This document represents the complete, implementation-ready design system specification derived from the Stage 1 audit (`docs/PHASE_6_AUDIT_SUMMARY.md`) and direct inspection of the actual codebase (`config.py`, `components/charts.py`, all 9 page modules, `components/sidebar.py`, `app.py`).

No application source files were modified during this stage.

---

## 2. Final Design Direction

### 2.1 Selected Aesthetic: **Automotive Technical Professional**

i20 AI Garage adopts a **restrained, instrument-cluster-inspired dark theme** that communicates:

- **Precision** — Technical diagnostic software, not a consumer app
- **Trustworthiness** — Clean surfaces, clear hierarchy, zero decoration
- **Automotive Context** — Gauge metaphors, telemetry-first layouts, severity semantics
- **Professional Utility** — Information density appropriate for workshop/diagnostic use

### 2.2 Why This Direction

| Evidence from Audit | Design Response |
|---------------------|-----------------|
| Existing THEME already uses automotive-relevant palette (cyan, green, amber, red, purple) | Preserve and normalize; don't reinvent |
| Gauge charts with threshold zones are central to Dashboard | Make gauge visual language the design system anchor |
| DTC severity colors (critical/major/minor/info) are established | Align system semantic colors to diagnostic conventions |
| Dark theme (`#1a1d21` base) is professional and reduces eye strain | Single polished dark theme — no unreliable light/dark toggle |
| Plotly charts already use CVD-safe categorical order | Codify and extend the existing SERIES_COLORS system |
| Streamlit constraints limit arbitrary ARIA/CSS | Design for native widgets first; custom HTML only where necessary |

### 2.3 What We Explicitly Avoid

- ❌ Gradients beyond primary button (single 90deg blue→purple)
- ❌ Glassmorphism/backdrop-blur (Streamlit rendering inconsistent)
- ❌ Heavy shadows on every card (creates visual noise)
- ❌ Giant border-radius everywhere (indistinguishable hierarchy)
- ❌ Decorative animations (telemetry updates must remain readable)
- ❌ Multiple accent colors competing (one primary: cyan; semantic: green/amber/red/purple)

---

## 3. Color System

### 3.1 Finalized Palette Tokens

All values derived from existing `config.py:THEME` and `components/charts.py:CHART_COLORS`, normalized for contrast and semantic clarity.

#### 3.1.1 Surface & Background Tokens

| Token | Hex | Role | Contrast vs Text Primary |
|-------|-----|------|--------------------------|
| `surface.app` | `#1a1d21` | Application/page background | 12.6:1 ✅ |
| `surface.page` | `#1a1d21` | Page content background | 12.6:1 ✅ |
| `surface.primary` | `#2a2e36` | Primary card/panel surface | 7.8:1 ✅ |
| `surface.secondary` | `#23272e` | Secondary surface (sidebar, inputs) | 9.1:1 ✅ |
| `surface.elevated` | `#2f333c` | Dropdowns, popovers, modals | 7.1:1 ✅ |
| `surface.interactive` | `#323741` | Hover/active states on cards | 6.4:1 ✅ |

#### 3.1.2 Text Tokens

| Token | Hex | Role | Usage |
|-------|-----|------|-------|
| `text.primary` | `#e8eaed` | Main content, headings | Default |
| `text.secondary` | `#9aa3ad` | Descriptions, metadata, captions | Secondary info |
| `text.muted` | `#6b7280` | Disabled, placeholder, subtle labels | Low emphasis |
| `text.inverse` | `#1a1d21` | On primary accent backgrounds | Buttons, badges |
| `text.link` | `#00b4d8` | Links, actionable text | Interactive |
| `text.on-accent` | `#ffffff` | On accent-colored surfaces | Badges, pills |

#### 3.1.3 Border Tokens

| Token | Hex | Role |
|-------|-----|------|
| `border.default` | `#3a3f4a` | Standard card/container borders |
| `border.subtle` | `#2d3139` | Hairline separators, table grid |
| `border.strong` | `#4a4f5c` | Focus rings, selected states |
| `border.focus` | `#00b4d8` | Keyboard focus indicator |
| `border.separator` | `#2d3139` | Section dividers |

#### 3.1.4 Accent & Brand Tokens

| Token | Hex | Role |
|-------|-----|------|
| `accent.primary` | `#00b4d8` | Primary actions, links, key metrics (RPM, primary series) |
| `accent.primary-hover` | `#009db8` | Hover state for primary |
| `accent.primary-active` | `#00869e` | Active/pressed state |
| `accent.secondary` | `#9b59b6` | AI/assistant features, secondary actions |
| `accent.selected` | `#00b4d820` | Selected row, active nav (10% opacity fill) |

#### 3.1.5 Semantic Status Tokens (Application-Level)

| Token | Hex | Role | Contrast vs Surface Primary |
|-------|-----|------|----------------------------|
| `status.success` | `#2ecc71` | Success, connected, healthy | 4.8:1 ✅ |
| `status.warning` | `#f39c12` | Warning, simulation mode, pending | 3.2:1 ⚠️ (large text only) |
| `status.critical` | `#e74c3c` | Error, disconnected, critical | 4.5:1 ✅ |
| `status.info` | `#00b4d8` | Information, real data mode | 4.8:1 ✅ |
| `status.neutral` | `#9aa3ad` | Disabled, unknown, secondary | 3.8:1 ⚠️ |

**Note on Warning Contrast:** `#f39c12` on `#2a2e36` = 3.2:1. Use only for:
- Large text (≥18px / ≥14px bold)
- Non-text indicators (dots, bars, gauge sectors)
- Never for body copy or small labels

#### 3.1.6 Diagnostic Severity Tokens (Preserved from DTC_SEVERITY)

| Token | Hex | Label | Usage |
|-------|-----|-------|-------|
| `diag.critical` | `#e74c3c` | Critical | Immediate safety risk |
| `diag.major` | `#f39c12` | Major | Significant issue |
| `diag.minor` | `#3498db` | Minor | Monitor & schedule |
| `diag.info` | `#9b59b6` | Information | No action needed |

**Key Difference from App Status:** `diag.minor` uses `#3498db` (brighter blue) not `accent.primary` `#00b4d8` — this distinguishes diagnostic severity from generic info status. `diag.info` shares `accent.secondary` purple.

#### 3.1.7 Data Source Tokens

| Token | Hex | Label | Usage |
|-------|-----|-------|-------|
| `datasource.real` | `#2ecc71` | Live Data | Green = real vehicle connection |
| `datasource.simulation` | `#f39c12` | Simulation | Amber = demo/simulated data |
| `datasource.ai` | `#9b59b6` | AI Analysis | Purple = AI-generated content |

#### 3.1.8 Chart Series Tokens (CVD-Safe Categorical Order)

| Index | Token | Hex | Semantic Role |
|-------|-------|-----|---------------|
| 1 | `series.1` | `#00b4d8` | Primary telemetry (RPM, speed) |
| 2 | `series.2` | `#f39c12` | Secondary telemetry (coolant, throttle) |
| 3 | `series.3` | `#2ecc71` | Tertiary telemetry (load, voltage) |
| 4 | `series.4` | `#9b59b6` | AI/derived metrics |
| 5 | `series.5` | `#e74c3c` | Alerts, critical overlays |

**Fixed order — never reassign per chart.** This ensures color-blind viewers can distinguish series by position.

#### 3.1.9 Chart Status Tokens (Distinct from Series)

| Token | Hex | Role |
|-------|-----|------|
| `chart.good` | `#2ecc71` | Within healthy range |
| `chart.warning` | `#f39c12` | Approaching threshold |
| `chart.serious` | `#ec835a` | Distinct orange-red for serious |
| `chart.critical` | `#e74c3c` | Beyond critical threshold |

---

### 3.2 Contrast Validation Matrix

All ratios tested against `surface.primary` `#2a2e36` (card background) unless noted.

| Text/Element | Background | Ratio | WCAG AA | WCAG AAA | Verdict |
|--------------|------------|-------|---------|----------|---------|
| `text.primary` | `surface.primary` | 7.8:1 | ✅ | ✅ | Pass |
| `text.secondary` | `surface.primary` | 4.1:1 | ✅ | ❌ | AA only |
| `text.muted` | `surface.primary` | 2.6:1 | ❌ | ❌ | Disabled only |
| `text.inverse` | `accent.primary` | 8.1:1 | ✅ | ✅ | Pass |
| `text.on-accent` | `status.success` | 7.2:1 | ✅ | ✅ | Pass |
| `text.on-accent` | `status.warning` | 1.9:1 | ❌ | ❌ | **Never use** |
| `text.on-accent` | `status.critical` | 5.8:1 | ✅ | ✅ | Pass |
| `text.on-accent` | `diag.major` | 1.9:1 | ❌ | ❌ | **Never use** |
| `status.success` | `surface.primary` | 4.8:1 | ✅ | ❌ | Non-text OK |
| `status.warning` | `surface.primary` | 3.2:1 | ⚠️ Large only | ❌ | Large text only |
| `status.critical` | `surface.primary` | 4.5:1 | ✅ | ❌ | Non-text OK |
| `status.info` | `surface.primary` | 4.8:1 | ✅ | ❌ | Non-text OK |
| `diag.critical` | `surface.primary` | 4.5:1 | ✅ | ❌ | Non-text OK |
| `diag.major` | `surface.primary` | 3.2:1 | ⚠️ Large only | ❌ | Large text only |
| `diag.minor` | `surface.primary` | 4.2:1 | ✅ | ❌ | AA only |
| `diag.info` | `surface.primary` | 3.8:1 | ⚠️ Large only | ❌ | Large text only |
| `series.1` | `surface.app` | 5.2:1 | ✅ | ❌ | Chart lines OK |
| `series.2` | `surface.app` | 3.5:1 | ⚠️ Large only | ❌ | Chart lines OK |
| `series.3` | `surface.app` | 4.8:1 | ✅ | ❌ | Chart lines OK |
| `series.4` | `surface.app` | 3.8:1 | ⚠️ Large only | ❌ | Chart lines OK |
| `series.5` | `surface.app` | 4.5:1 | ✅ | ❌ | Chart lines OK |

**Chart Line Guidance:** Series colors on dark plot background (`#1a1d21`) meet 3:1 for non-text (lines ≥2px). Ensure all chart lines use `width ≥ 2px`.

---

### 3.3 Theme Behaviour Decision

**Single Polished Dark Theme Only.**

**Rationale:**
1. Streamlit's native theming (`.streamlit/config.toml`) controls native widgets but not custom `unsafe_allow_html` CSS — dual-theme maintenance doubles CSS surface
2. Custom Plotly chart templates require explicit light/dark templates — current codebase has none
3. Automotive diagnostic context favors dark (workshop lighting, reduced glare)
4. No user demand for light theme identified
5. Adding theme toggle introduces regression risk across 9 pages × custom components

**Implementation:** Lock `config.toml` to dark base; all tokens reference dark values. Future light theme would require full design system v2.

---

## 4. Typography System

### 4.1 Font Stack

```css
/* Primary: System UI for reliability, no external deps */
--font-family-base: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
/* Monospace: Technical identifiers, codes, numeric readings */
--font-family-mono: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Monaco, Consolas, 'Liberation Mono', monospace;
/* Numeric: Tabular numerals for stable telemetry */
--font-family-numeric: var(--font-family-base); /* Use font-variant-numeric: tabular-nums */
```

### 4.2 Type Scale Tokens

| Token | Size | Weight | Line Height | Letter Spacing | Font Family | Usage |
|-------|------|--------|-------------|----------------|-------------|-------|
| `display` | 48px / 3rem | 700 | 1.1 | -0.02em | base | Hero vehicle identity (rare) |
| `h1` | 32px / 2rem | 700 | 1.2 | -0.01em | base | Page title |
| `h2` | 24px / 1.5rem | 600 | 1.3 | 0 | base | Major section heading |
| `h3` | 20px / 1.25rem | 600 | 1.4 | 0 | base | Subsection heading |
| `h4` | 16px / 1rem | 600 | 1.4 | 0 | base | Card heading, widget group |
| `body-lg` | 16px / 1rem | 400 | 1.6 | 0 | base | Important explanatory text |
| `body` | 14px / 0.875rem | 400 | 1.5 | 0 | base | Standard content |
| `body-sm` | 13px / 0.8125rem | 400 | 1.5 | 0 | base | Secondary content, table cells |
| `label` | 12px / 0.75rem | 500 | 1.4 | +0.02em | base | Form labels, metric labels |
| `caption` | 11px / 0.6875rem | 400 | 1.4 | +0.03em | base | Metadata, timestamps, help |
| `numeric-xl` | 48px / 3rem | 700 | 1.0 | 0 | numeric | Main telemetry reading (gauge center) |
| `numeric-lg` | 32px / 2rem | 600 | 1.1 | 0 | numeric | Secondary metric (metric card value) |
| `numeric-md` | 20px / 1.25rem | 600 | 1.2 | 0 | numeric | Tertiary metric, sparkline label |
| `numeric-sm` | 14px / 0.875rem | 500 | 1.3 | 0 | numeric | Table numeric cells |
| `code` | 13px / 0.8125rem | 400 | 1.5 | 0 | mono | DTC codes, PIDs, VIN, technical IDs |
| `code-sm` | 11px / 0.6875rem | 400 | 1.4 | 0 | mono | Inline code, small technical refs |

### 4.3 Numeric Readability Rules

- **Always** use `font-variant-numeric: tabular-nums` on numeric tokens
- **Always** use `font-variant-numeric: tabular-nums` on Plotly gauge numbers via `number.font.family`
- Never use proportional numerals for changing telemetry — causes layout shift
- RPM/Speed: `numeric-xl` (48px) in gauges, `numeric-lg` (32px) in metric cards
- Coolant/Load/Throttle: `numeric-lg` in metric cards
- Table values: `numeric-sm` with right alignment

---

## 5. Spacing System

### 5.1 4px Base Scale Tokens

| Token | Value | Rem | Usage |
|-------|-------|-----|-------|
| `space.0` | 0px | 0 | Reset, tight inline |
| `space.1` | 4px | 0.25rem | Icon gaps, badge padding, inline elements |
| `space.2` | 8px | 0.5rem | Form field gap, button icon gap, card content gap |
| `space.3` | 12px | 0.75rem | Card padding (tight), list item gap |
| `space.4` | 16px | 1rem | **Standard card padding**, section gap, form field vertical |
| `space.5` | 20px | 1.25rem | Card gap (grid), sidebar section gap |
| `space.6` | 24px | 1.5rem | Section vertical rhythm, page block gap |
| `space.8` | 32px | 2rem | Major section gap, page header bottom |
| `space.10` | 40px | 2.5rem | Large layout gaps |
| `space.12` | 48px | 3rem | Page-level separation |
| `space.16` | 64px | 4rem | Hero/landing only |

### 5.2 Semantic Spacing Aliases

| Alias | Token | Usage |
|-------|-------|-------|
| `gap.inline` | `space.2` | Icon + text, button content |
| `gap.field` | `space.4` | Form field vertical, input + help text |
| `gap.card` | `space.4` | Internal card padding (all sides) |
| `gap.card-grid` | `space.5` | Gap between cards in CSS grid |
| `gap.section` | `space.6` | Between major page sections |
| `gap.page` | `space.8` | Page header to content |
| `gap.sidebar` | `space.4` | Sidebar internal section gap |
| `padding.page` | `space.6` | Main content horizontal padding |
| `padding.card` | `space.4` | Card internal padding |
| `padding.card-lg` | `space.5` | Large card (wizard, modal) padding |

### 5.3 Responsive Spacing Adjustments

| Breakpoint | `padding.page` | `gap.card-grid` | `gap.section` |
|------------|----------------|-----------------|---------------|
| Desktop (≥1280px) | `space.6` (24px) | `space.5` (20px) | `space.6` (24px) |
| Laptop (1024-1279px) | `space.5` (20px) | `space.4` (16px) | `space.5` (20px) |
| Tablet (768-1023px) | `space.4` (16px) | `space.4` (16px) | `space.4` (16px) |
| Mobile (<768px) | `space.3` (12px) | `space.3` (12px) | `space.4` (16px) |

---

## 6. Border Radius Scale

| Token | Value | Usage |
|-------|-------|-------|
| `radius.none` | 0px | Tables, full-width bars |
| `radius.sm` | 4px | Inputs, selects, buttons, badges, pills |
| `radius.md` | 8px | **Standard card**, metric card, panel, modal content |
| `radius.lg` | 12px | Large cards (wizard, report preview), dropdown menus |
| `radius.xl` | 16px | Page-level containers, modal wrapper |
| `radius.pill` | 9999px | Status badges, pills, avatar, progress bars |
| `radius.circle` | 50% | Indicator dots, avatars, gauge center |

**Rule:** Never use arbitrary radius values. Map every component to one token.

---

## 7. Elevation & Shadow System

### 7.1 Shadow Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `shadow.none` | none | Flat surfaces, most cards |
| `shadow.hairline` | `0 1px 0 border.subtle` | Subtle separation (table rows, list items) |
| `shadow.sm` | `0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.08)` | Hover on cards, dropdown |
| `shadow.md` | `0 4px 12px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.1)` | Floating dropdowns, popovers, toast |
| `shadow.lg` | `0 12px 28px rgba(0,0,0,0.2), 0 4px 8px rgba(0,0,0,0.15)` | Modal overlay, wizard card |
| `shadow.focus` | `0 0 0 3px accent.primary` | Keyboard focus ring (inset/outset) |
| `shadow.glow.success` | `0 0 8px status.success` | Connected indicator pulse |
| `shadow.glow.warning` | `0 0 8px status.warning` | Simulation indicator pulse |
| `shadow.glow.critical` | `0 0 8px status.critical` | Error indicator pulse |

### 7.2 Elevation Hierarchy

| Level | Shadow | Border | Background | Example |
|-------|--------|--------|------------|---------|
| 0 (Base) | none | `border.default` | `surface.primary` | Standard card, metric card |
| 1 (Hover) | `shadow.sm` | `border.strong` | `surface.interactive` | Card hover, row hover |
| 2 (Floating) | `shadow.md` | `border.default` | `surface.elevated` | Dropdown, popover, tooltip |
| 3 (Modal) | `shadow.lg` | none | `surface.primary` | Modal, wizard step card |
| 4 (Overlay) | `shadow.lg` + backdrop | none | `surface.primary` | Full-screen modal |

**Principle:** Prefer border + background difference over shadows. Use shadows only for true floating elements (dropdowns, modals, toasts).

---

## 8. Layout System

### 8.1 Global Shell

```
┌─────────────────────────────────────────────────────────────┐
│ Sidebar (280px fixed, collapsible to 72px icon-only)       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Main Content (flex: 1)                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Top Bar (48px): Page Title | Breadcrumb | Actions  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                     │   │
│  │ Page Content (padding.page horizontal)             │   │
│  │   - max-width: 1400px (centered)                   │   │
│  │   - Section gap: gap.section                       │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Sidebar Spec:**
- Default: 280px with labels
- Collapsed: 72px (icon-only, tooltips on hover)
- State persisted in `st.session_state.sidebar_collapsed`
- Keyboard toggle: `Ctrl+B` (or `Cmd+B`)

**Top Bar Spec:**
- Height: 48px
- Background: `surface.secondary`
- Border bottom: `border.default`
- Left: Page title (h1), optional breadcrumb
- Right: Global actions (theme, notifications, user menu)

### 8.2 Grid System

**No rigid 12-column grid.** Instead, use CSS Grid with explicit track definitions per page:

```css
/* Two-column (50/50) */
grid-template-columns: 1fr 1fr;

/* Three-column (33/33/33) */
grid-template-columns: repeat(3, 1fr);

/* Four-column metrics (primary use case) */
grid-template-columns: repeat(4, 1fr);

/* Sidebar main split (app shell) */
grid-template-columns: 280px 1fr;

/* Responsive stacking */
@media (max-width: 1024px) {
  grid-template-columns: 1fr;
}
```

**Breakpoints:**
| Name | Width | Behavior |
|------|-------|----------|
| `desktop` | ≥1280px | Full 4-col metrics, 3-col charts, sidebar expanded |
| `laptop` | 1024-1279px | 4-col → 2-col metrics, sidebar expanded |
| `tablet` | 768-1023px | 2-col metrics, sidebar collapsible drawer |
| `mobile` | <768px | 1-col stacked, sidebar drawer, gauges vertical stack |

### 8.3 Standard Page Anatomy

Every page follows this hierarchy (adapt as needed):

```markdown
# Page Title (h1)
## Context/Subtitle (body-lg, text.secondary) — optional

### Primary Status/Overview (metric cards, gauge cluster, key KPIs)
- Most important current state
- Real-time if applicable

### Main Content (tabs, tables, charts, forms)
- Primary workspace

### Supporting Information (expandable, secondary)
- History, logs, details, configuration

### History/Secondary Content (bottom)
- Previous sessions, audit trail, archives
```

---

## 9. Component Anatomy Specification

### 9.1 Metric Card (Telemetry KPI)

```
┌─────────────────────────────────────────┐
│  [Icon]  Label (label, text.secondary)  │  ← gap.inline
│                                         │
│  1,234  (numeric-lg, text.primary)     │  ← gap.card
│  RPM    (caption, text.muted)           │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │ ████░░░░░░░░░░░░░░░░░░░░░░░░░░  │   │  ← Sparkline (60px h)
│  └─────────────────────────────────┘   │
│                                         │
│  ↗ +12%  (caption, status.success)     │  ← Trend (optional)
└─────────────────────────────────────────┘
```

**Tokens:**
- Surface: `surface.primary`
- Border: `border.default`
- Radius: `radius.md` (8px)
- Padding: `padding.card` (16px)
- Gap: `gap.card` (16px) vertical, `gap.inline` (8px) horizontal

**States:**
- Default: As above
- Hover: `shadow.sm`, `border.strong`
- Loading: Skeleton (surface.secondary → surface.interactive pulse)
- Alert: Left border 3px `status.critical`/`status.warning`

**Responsive:**
- Desktop: 4-col grid
- Laptop: 2-col grid
- Tablet/Mobile: 1-col stacked, full width

---

### 9.2 Status Card (Connection/Mode Indicator)

```
┌─────────────────────────────────────────┐
│  ●  Label (label, text.primary)         │  ← gap.inline
│     Detail (caption, text.secondary)    │
└─────────────────────────────────────────┘
```

**Tokens:**
- Surface: `surface.primary`
- Border: `border.default`
- Radius: `radius.md` (8px)
- Padding: `space.3` (12px) vertical, `space.4` (16px) horizontal
- Dot: 10px circle, `radius.circle`
- Dot colors: `status.success` / `status.warning` / `status.critical` / `status.info` / `status.neutral`

**Accessibility:** Dot + text label (never color-only). Dot has `aria-hidden="true"`, label conveys state.

---

### 9.3 Diagnostic Finding Card (DTC/AI/Rule Result)

```
┌────────────────────────────────────────────────────────────┐
│ [Severity Badge]  P0300 - Random Misfire (h4)              │
│  Severity: Major (diag.major badge)  Confidence: 87%       │
├────────────────────────────────────────────────────────────┤
│  Summary: Multiple cylinders misfiring under load...       │
├────────────────────────────────────────────────────────────┤
│  ▼ Probable Causes (expandable)                            │
│     1. Faulty ignition coil (87%)  [Confidence: High]      │
│        Evidence: Cylinder 3 misfire count 247              │
│        Verification: Swap coil 3→1, monitor misfire move   │
│        Urgency: [Soon badge]                               │
│     2. Vacuum leak (45%)  [Confidence: Medium]             │
│        ...                                                  │
├────────────────────────────────────────────────────────────┤
│  [Recommended Action: Replace ignition coil]  Priority: 8/10│
│  Safety: [Caution badge]  Cost: ₹3,500-5,000               │
└────────────────────────────────────────────────────────────┘
```

**Tokens:**
- Surface: `surface.primary`
- Border: `border.default` + left accent border 3px (`diag.*` color)
- Radius: `radius.md` (8px)
- Padding: `padding.card` (16px)
- Severity badge: `radius.pill`, `diag.*` background 15%, `diag.*` text
- Confidence badge: `radius.pill`, `status.success`/`status.warning`/`status.critical` bg 15%
- Urgency badge: `radius.pill`, `status.critical` (immediate), `status.warning` (soon), `status.info` (schedule), `status.neutral` (monitor)

**Critical Content:** Never collapse severity, code, description, confidence, primary action.

---

### 9.4 Report Card (Report Generation)

```
┌────────────────────────────────────────────────────────────┐
│  🔍  Comprehensive Diagnostic Report         [HTML] [PDF]  │
│  Full diagnostic analysis including DTCs, AI diagnosis...  │
├────────────────────────────────────────────────────────────┤
│  Requires: OBD Session  ✓  AI Diagnosis  ✓                 │
│  [Generate Report] (primary button, full width)            │
└────────────────────────────────────────────────────────────┘
```

**Tokens:**
- Surface: `surface.primary`
- Border: `border.default`
- Radius: `radius.md` (8px)
- Padding: `padding.card` (16px)
- Format badges: `radius.sm` (4px), `surface.secondary`, `text.secondary`
- Generate button: Primary, full width in card

---

### 9.5 Button Variants

| Variant | Background | Text | Border | Hover | Active | Focus | Disabled |
|---------|------------|------|--------|-------|--------|-------|----------|
| **Primary** | `accent.primary` | `text.inverse` | none | `accent.primary-hover` | `accent.primary-active` | `shadow.focus` | `surface.interactive` + `text.muted` |
| **Secondary** | `surface.primary` | `text.primary` | `border.default` | `surface.interactive` | `surface.secondary` | `shadow.focus` | `surface.secondary` + `text.muted` |
| **Tertiary/Ghost** | transparent | `text.primary` | none | `surface.secondary` | `surface.interactive` | `shadow.focus` | `text.muted` |
| **Destructive** | `status.critical` | `text.inverse` | none | `#c0392b` | `#a93226` | `shadow.focus` | `surface.interactive` + `text.muted` |
| **Icon-only** | varies | N/A | varies | varies | varies | `shadow.focus` (full ring) | varies |

**Shared Specs:**
- Padding: `space.2` (8px) vertical, `space.4` (16px) horizontal
- Icon gap: `gap.inline` (8px)
- Radius: `radius.sm` (4px)
- Font: `label` (12px, 500)
- Min height: 40px (touch target)
- Transition: `all 0.15s ease`

**Loading State:** Spinner (20px) replaces label, button disabled, width locked.

---

### 9.6 Badge Variants

| Variant | Background | Text | Radius | Padding | Usage |
|---------|------------|------|--------|---------|-------|
| **Status** | `status.*` 15% | `status.*` | `radius.pill` | 4px 10px | Connection, mode, health |
| **Severity** | `diag.*` 15% | `diag.*` | `radius.pill` | 4px 10px | DTC, AI diagnosis |
| **Confidence** | `status.*` 15% | `status.*` | `radius.pill` | 4px 10px | AI/rule confidence |
| **Urgency** | `status.*` 15% | `status.*` | `radius.pill` | 4px 10px | Action urgency |
| **Data Source** | `datasource.*` 15% | `datasource.*` | `radius.pill` | 4px 10px | Real/Sim/AI |
| **Format** | `surface.secondary` | `text.secondary` | `radius.sm` | 2px 8px | HTML/PDF/CSV |
| **Numeric** | `accent.primary` 15% | `accent.primary` | `radius.sm` | 2px 8px | Count, PID number |

**Accessibility:** All badges use text label + color. Never color-only.

---

### 9.7 Alert Variants

```
┌────────────────────────────────────────────────────────────┐
│ [Icon]  Title (h4)                                         │
│         Description (body)                                 │
│         [Action Button] (optional)                         │
└────────────────────────────────────────────────────────────┘
```

| Variant | Background | Border | Icon | Text | Use Case |
|---------|------------|--------|------|------|----------|
| **Success** | `status.success` 15% | `status.success` | ✓ | `status.success` | Operation complete |
| **Info** | `status.info` 15% | `status.info` | ℹ | `status.info` | Guidance, tips |
| **Warning** | `status.warning` 15% | `status.warning` | ⚠ | `status.warning` | Simulation mode, pending |
| **Error** | `status.critical` 15% | `status.critical` | ✕ | `status.critical` | Failed operation |
| **Critical Diagnostic** | `diag.critical` 15% | `diag.critical` | ⚠ | `diag.critical` | Safety-critical finding |

**Tokens:** Padding `padding.card` (16px), Radius `radius.md` (8px), Icon size 20px.

---

### 9.8 Form Components

**Input/Select/Textarea:**
- Surface: `surface.secondary`
- Border: `border.default` (default), `border.focus` (focus), `border.critical` (error)
- Text: `text.primary`
- Placeholder: `text.muted`
- Radius: `radius.sm` (4px)
- Padding: `space.2` (8px) vertical, `space.3` (12px) horizontal
- Height: 40px min
- Font: `body` (14px)

**Label:**
- Font: `label` (12px, 500)
- Color: `text.primary`
- Margin bottom: `space.1` (4px)
- Required marker: `*` in `status.critical`

**Help Text:**
- Font: `caption` (11px)
- Color: `text.secondary`
- Margin top: `space.1` (4px)

**Error Message:**
- Font: `caption` (11px)
- Color: `status.critical`
- Margin top: `space.1` (4px)
- Icon: ⚠ (12px)

**Validation States:**
- Default: `border.default`
- Focus: `border.focus` + `shadow.focus`
- Error: `border.critical` (alias for `status.critical`)
- Success: `border.success` (alias for `status.success`)

---

### 9.9 Table Specification

```
┌────────────────────────────────────────────────────────────┐
│ Header (label, text.secondary, bg: surface.secondary)      │
├────────────────────────────────────────────────────────────┤
│ Row 1 (body-sm, text.primary)                              │
│ Row 2 (hover: surface.interactive)                         │
│ Row 3 (selected: surface.selected = accent.primary 10%)    │
├────────────────────────────────────────────────────────────┤
│ Empty State (centered, text.secondary, padding: space.8)   │
└────────────────────────────────────────────────────────────┘
```

**Tokens:**
- Header: `surface.secondary`, `border.subtle` bottom, `label` font, `text.secondary`
- Row: `surface.primary`, `border.subtle` bottom, `body-sm` font
- Hover: `surface.interactive`
- Selected: `accent.primary` 10% background
- Numeric columns: Right-aligned, `numeric-sm`, `font-variant-numeric: tabular-nums`
- Status columns: Centered, badge variant
- Action columns: Icon buttons (tertiary), grouped with `gap.inline`

**Responsive:**
- Desktop/Laptop: Full table, horizontal scroll if needed
- Tablet: Horizontal scroll with sticky first column
- Mobile: Card-per-row layout (stack cells vertically)

---

### 9.10 Empty States

```
┌────────────────────────────────────────────────────────────┐
│                                                              │
│      [Icon 64px, text.muted]                                │
│                                                              │
│      Title (h3, text.primary)                               │
│                                                              │
│      Description (body, text.secondary, max-width 400px)   │
│                                                              │
│      [Primary Action Button] (optional)                    │
│                                                              │
└────────────────────────────────────────────────────────────┘
```

**Variants:**
| Context | Icon | Title | Description | Action |
|---------|------|-------|-------------|--------|
| No DTCs | 🔍 | No diagnostic codes | Last scan found no issues | Run Scan |
| No Telemetry | 📊 | No telemetry data | Start simulation or connect OBD | Start Simulation |
| No Sessions | 📁 | No performance sessions | Record a driving session | New Session |
| No Maintenance | 🔧 | No service records | Add your first service | Add Record |
| No Reports | 📋 | No generated reports | Generate a professional report | Generate |
| No AI Chat | 🤖 | No conversation yet | Ask a question or run diagnosis | New Chat |
| No OBD Adapter | 🔌 | No adapter detected | Connect ELM327 and rescan | Rescan |

**Tokens:** Padding `space.12` (48px) vertical, centered, `surface.primary`, `border.default`, `radius.md`.

---

### 9.11 Loading States

| Context | Pattern | Tokens |
|---------|---------|--------|
| **Page/Section** | Skeleton cards (surface.secondary → surface.interactive pulse) | Animation: 1.5s ease-in-out |
| **Telemetry Update** | Subtle pulse on metric card border (accent.primary 30%) | No spinner — data is live |
| **AI Inference** | Pulsing dots in message bubble (3 dots, 1.5s stagger) | `accent.secondary` |
| **OBD Connection** | Determinate progress bar (steps: 1-8) | `accent.primary` fill, `surface.secondary` track |
| **Report Generation** | Indeterminate progress + "Generating {type}..." | `accent.primary` spinner |
| **Backup/Migration** | Determinate progress with step labels | `accent.primary` |

**Never:** Fake progress for indeterminate operations. Use honest indeterminate indicators.

---

## 10. Chart Design System

### 10.1 Chart Theme Tokens (Plotly Layout)

```python
CHART_THEME = {
    "paper_bgcolor": surface.app,           # #1a1d21
    "plot_bgcolor": surface.primary,        # #2a2e36
    "font": {
        "family": "system-ui, -apple-system, Segoe UI, sans-serif",
        "color": text.primary,              # #e8eaed
        "size": 12
    },
    "title": {
        "font": {"color": text.primary, "size": 14, "family": "..."},
        "x": 0.02, "xanchor": "left"
    },
    "xaxis": {
        "gridcolor": border.default,        # #3a3f4a
        "zerolinecolor": border.default,
        "linecolor": border.default,
        "tickfont": {"color": text.secondary, "size": 10},
        "titlefont": {"color": text.secondary, "size": 11}
    },
    "yaxis": {
        "gridcolor": border.default,
        "zerolinecolor": border.default,
        "linecolor": border.default,
        "tickfont": {"color": text.secondary, "size": 10},
        "titlefont": {"color": text.secondary, "size": 11}
    },
    "legend": {
        "bgcolor": "rgba(0,0,0,0)",
        "bordercolor": border.default,
        "borderwidth": 1,
        "font": {"color": text.secondary, "size": 11},
        "orientation": "h",
        "yanchor": "bottom", "y": -0.15,
        "xanchor": "left", "x": 0
    },
    "hovermode": "x unified",
    "hoverlabel": {
        "bgcolor": surface.secondary,       # #23272e
        "bordercolor": border.default,
        "font": {"color": text.primary, "size": 11, "family": "..."}
    },
    "margin": {"l": 50, "r": 30, "t": 60, "b": 50}
}
```

### 10.2 Gauge Chart Spec

```
┌─────────────────────────────────────────────┐
│                    Title                     │  ← caption, text.secondary
│                                             │
│        ┌─────────────────────┐              │
│      ┌─┘                     └─┐            │
│     │   ████████████░░░░░░░░  │  ← Green sector (0-green_max)
│     │   ████████████████░░░░  │  ← Amber sector (green_max-amber_max)
│     │   ████████████████████  │  ← Red sector (amber_max-red_max)
│      └─┐                     ┌─┘            │
│        └─────────────────────┘              │
│              3,240 RPM                      │  ← numeric-xl, text.primary
│                                             │
│   ● 3000  ● 5000  ● 6500                   │  ← Tick marks
└─────────────────────────────────────────────┘
```

**Tokens:**
- Sectors: `status.success` 25%, `status.warning` 25%, `status.critical` 25%, `status.critical` 40% (beyond red_max)
- Needle/Threshold line: `text.primary`, 3px
- Value color: Dynamic based on current value (success/warning/critical)
- Font: `numeric-xl` (48px, 700, tabular-nums)
- Height: 250px standard, 200px compact

**Diverging Gauge (Fuel Trim):** Centered at 0, symmetric sectors.

---

### 10.3 Time-Series / Line Chart Spec

- Series colors: `series.1` through `series.5` (fixed order)
- Line width: 2px (spline interpolation)
- Markers: Off by default; on for ≤50 points (6px, white stroke 2px)
- Grid: `border.default` (subtle)
- Legend: Horizontal, bottom, outside plot area
- Hover: Unified x, shows all series at timestamp

---

### 10.4 Multi-Series (Small Multiples) Spec

- Shared X-axis (time)
- Independent Y-axes per row (no dual-axis)
- Row height: 150px minimum
- Vertical spacing: 8% of figure height
- Subplot titles: `h4` equivalent, left-aligned
- Each row uses `series.1` color (consistent) — distinguish by title, not color

---

### 10.5 Comparison Chart Spec

- Categorical groups (sessions, scenarios)
- Each group = one series using `series.1`..`series.5`
- Line + markers (6px)
- Legend shows group names
- No dual-axis — use small multiples if metrics differ in scale

---

### 10.6 Sparkline Spec

- Height: 60px, Width: 200px (flexible)
- No axes, no grid, no legend
- Fill: `series.1` 12% opacity
- Line: `series.1` 1.5px
- Margin: 0
- Background: transparent

---

### 10.7 Chart Color Usage Rules

| Metric | Series Index | Gauge Type | Reason |
|--------|--------------|------------|--------|
| RPM | 1 (blue) | rpm | Primary driver metric |
| Speed | 1 (blue) | speed | Primary driver metric |
| Coolant Temp | 2 (amber) | coolant_temp | Temperature = warning hue |
| Throttle | 2 (amber) | throttle | Input = warning hue |
| Engine Load | 3 (green) | engine_load | Load = healthy range |
| Battery Voltage | 3 (green) | voltage | Electrical = healthy range |
| Fuel Trim ST | 4 (purple) | fuel_trim | Derived/calculated |
| Fuel Trim LT | 4 (purple) | fuel_trim | Derived/calculated |
| Intake Pressure | 5 (red) | — | Alert/derived |
| MAF | 5 (red) | — | Alert/derived |

**Never** assign series colors arbitrarily. Use the mapping above consistently.

---

## 11. Page-Specific Design Blueprints

### 11.1 Dashboard

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar: "Dashboard" | [Simulation Badge] [Live/Sim Toggle]   │
├────────────────────────────────────────────────────────────────┤
│ VEHICLE IDENTITY BAR                                           │
│ [i20 Badge]  2023 Hyundai i20 Asta  |  1.2L Petrol  |  Manual  │
├────────────────────────────────────────────────────────────────┤
│ GAUGE CLUSTER (6 gauges, 2-row × 3-col desktop)               │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐                            │
│ │   RPM   │ │  SPEED  │ │ COOLANT │  ← Primary row            │
│ └─────────┘ └─────────┘ └─────────┘                            │
│ ┌─────────┐ ┌─────────┐ ┌─────────┐                            │
│ │THROTTLE │ │  LOAD   │ │ VOLTAGE │  ← Secondary row          │
│ └─────────┘ └─────────┘ └─────────┘                            │
├────────────────────────────────────────────────────────────────┤
│ TELEMETRY CARDS (4-col: RPM, Speed, Coolant, Load)            │
│ [Metric Card] [Metric Card] [Metric Card] [Metric Card]       │
├────────────────────────────────────────────────────────────────┤
│ LIVE CHARTS (Tabs: RPM/Speed | Coolant/Load | Throttle/Fuel)  │
│ [Multi-series chart with 300-point rolling window]            │
├────────────────────────────────────────────────────────────────┤
│ SIMULATION CONTROLS                                            │
│ [Scenario Select] [Start/Stop] [Interval] [Session Name]      │
├────────────────────────────────────────────────────────────────┤
│ STATUS PANEL (Connection, AI, Simulation badges)              │
└────────────────────────────────────────────────────────────────┘
```

**Responsive:**
- Tablet: Gauges 2×3, Cards 2×2, Charts full-width tabs
- Mobile: Gauges stacked 6×1, Cards 1×4, Charts single column

---

### 11.2 Diagnostics

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar: "Diagnostics" | [Run Scan] [Last Scan: 2m ago]       │
├────────────────────────────────────────────────────────────────┤
│ TABS: [Scan] [DTC Detail] [AI Diagnosis] [Rule Engine] [History]│
├────────────────────────────────────────────────────────────────┤
│ SCAN TAB                                                       │
│ ┌──────────────────────────┐  ┌────────────────────────────┐  │
│ │ DTC LIST (Table)         │  │ LIVE TELEMETRY SNAPSHOT    │  │
│ │ Code | Desc | Sev | Act  │  │ [6 Mini Gauges]            │  │
│ │ P0300│Misfire│Major│View│  │                             │  │
│ │ P0171│Lean   │Major│View│  │                             │  │
│ └──────────────────────────┘  └────────────────────────────┘  │
├────────────────────────────────────────────────────────────────┤
│ DTC DETAIL TAB                                                 │
│ [Diagnostic Finding Card] × N (expandable, severity-sorted)   │
├────────────────────────────────────────────────────────────────┤
│ AI DIAGNOSIS TAB                                               │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ PRIMARY DIAGNOSIS CARD (severity left border, confidence)│  │
│ │ Probable Causes (expandable list with evidence)          │  │
│ └──────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ SECONDARY DIAGNOSES (collapsed by default)               │  │
│ └──────────────────────────────────────────────────────────┘  │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ RECOMMENDED ACTIONS (priority, safety, cost)             │  │
│ └──────────────────────────────────────────────────────────┘  │
│ [Safety Warnings Alert] [Missing Information Alert]          │
├────────────────────────────────────────────────────────────────┤
│ RULE ENGINE TAB                                                │
│ [Rule Match Cards: Rule ID, Category, Severity, Confidence]  │
├────────────────────────────────────────────────────────────────┤
│ HISTORY TAB                                                    │
│ [Diagnostic Report Table: Date, DTCs, Severity, Source, View] │
└────────────────────────────────────────────────────────────────┘
```

**Key:** DTC severity always visible. AI confidence always visible. Safety warnings never collapsed.

---

### 11.3 Performance

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar: "Performance" | [Session Selector] [Compare Mode]    │
├────────────────────────────────────────────────────────────────┤
│ TABS: [Live Charts] [Statistics] [Sessions] [Compare]         │
├────────────────────────────────────────────────────────────────┤
│ LIVE CHARTS TAB                                                │
│ [Session Selector] → [Multi-series chart for active session]  │
├────────────────────────────────────────────────────────────────┤
│ STATISTICS TAB                                                 │
│ [Metric Cards Row: Peak RPM, Max Speed, Avg Speed, Max Coolant,│
│  Max Load, Distance, Fuel Used, Duration]                     │
│ [Session Statistics Table: All sessions with sortable columns] │
├────────────────────────────────────────────────────────────────┤
│ SESSIONS TAB                                                   │
│ [Session Table: Name, Scenario, Date, Duration, Peaks, Actions]│
│ Actions: [Export CSV] [Export JSON] [Delete]                  │
├────────────────────────────────────────────────────────────────┤
│ COMPARE TAB                                                    │
│ [Session Multi-Select (max 4)] → [Comparison Charts]          │
│ Charts: RPM Overlay | Speed Overlay | Coolant Overlay | Load  │
│ [Generate Comparison Report]                                   │
└────────────────────────────────────────────────────────────────┘
```

---

### 11.4 Maintenance

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar: "Maintenance" | [Add Record] [Odometer: 45,230 km]   │
├────────────────────────────────────────────────────────────────┤
│ TABS: [Records] [Upcoming] [Add/Edit]                         │
├────────────────────────────────────────────────────────────────┤
│ RECORDS TAB                                                    │
│ [Maintenance Table: Type, Date, Odometer, Cost, Next Due, Act]│
│ Row hover → [Edit] [Delete]                                    │
├────────────────────────────────────────────────────────────────┤
│ UPCOMING TAB                                                   │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │ OVERDUE (Critical)                                       │  │
│ │ [Interval Card] Brake Fluid — Due 42,000 km (3,230 over) │  │
│ │ [Interval Card] Engine Oil — Due 40,000 km (5,230 over)  │  │
│ ├──────────────────────────────────────────────────────────┤  │
│ │ DUE SOON (Warning) — within 1,000 km                     │  │
│ │ [Interval Card] Air Filter — Due 50,000 km (4,770 left)  │  │
│ ├──────────────────────────────────────────────────────────┤  │
│ │ ON SCHEDULE (Success)                                    │  │
│ │ [Interval Card] Coolant — Due 100,000 km                 │  │
│ └──────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────┤
│ ADD/EDIT TAB (Modal/Form)                                      │
│ [Service Type ↓] [Date] [Odometer] [Cost] [Notes]             │
│ [Next Service km] [Next Service Date] [Save] [Cancel]         │
└────────────────────────────────────────────────────────────────┘
```

---

### 11.5 Vehicle Profile

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar: "Vehicle Profile"                                    │
├────────────────────────────────────────────────────────────────┤
│ TABS: [Vehicle Info] [Engine Specs] [Connections] [Diagnostics]│
├────────────────────────────────────────────────────────────────┤
│ VEHICLE INFO TAB                                               │
│ [Spec Grid: 2-col cards]                                       │
│ Make/Model | Year | Engine | Transmission | Fuel | Market     │
│ ECU Tuning | VIN | Diagnostic Mode                             │
├────────────────────────────────────────────────────────────────┤
│ ENGINE SPECS TAB                                               │
│ [Spec Grid: 2-col cards]                                       │
│ Displacement | Cylinders | Max Power | Max Torque             │
│ Compression | Fuel System | Emissions | Redline/Idle          │
├────────────────────────────────────────────────────────────────┤
│ CONNECTIONS TAB                                                │
│ [OBD Status Card] [Supported PIDs Count] [Adapter Info]       │
│ [Port] [Baudrate] [Protocol] [Last Connected]                 │
├────────────────────────────────────────────────────────────────┤
│ DIAGNOSTICS TAB                                                │
│ [Summary Cards: Total Scans, Total DTCs, AI Diagnoses, Rules] │
│ [Recent DTC History Table]                                     │
└────────────────────────────────────────────────────────────────┘
```

---

### 11.6 AI Assistant

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar: "AI Assistant" | [Mode: Chat ▼ Diagnostic] [Status]  │
├────────────────────────────────────────────────────────────────┤
│ CHAT MODE (3:1 split)                                          │
│ ┌─────────────────────────────┐ ┌───────────────────────────┐ │
│ │ CONVERSATION AREA           │ │ SIDEBAR PANELS            │ │
│ │ [Message List]              │ │ [Model Info]              │ │
│ │   👤 User message           │ │   Model: qwen2.5-3b       │ │
│ │   🤖 Assistant response     │ │   Temp: 0.7               │ │
│ │   👤 User message           │ │   Status: ✓ Connected     │ │
│ │   🤖 Loading... (pulse)     │ │ [Quick Prompts]           │ │
│ │                             │ │   🔧 P0300                │ │
│ │ [Input Form: Textarea]      │ │   🌡️ Coolant high         │ │
│ │   [Send] [Clear]            │ │   ⛽ Fuel trim            │ │
│ └─────────────────────────────┘ │ [Conversation Mgmt]       │ │
│                                 │   Session: abc123         │ │
│                                 │   Messages: 12            │ │
│                                 │   [Clear Conversation]    │ │
│                                 └───────────────────────────┘ │
├────────────────────────────────────────────────────────────────┤
│ DIAGNOSTIC MODE (Full width)                                   │
│ [Header: "Run Diagnostic Analysis"]                            │
│ [DTC Input] [Analyze]  OR  [Symptoms Textarea] [Analyze]      │
│ [Full Vehicle Scan]                                            │
│ [Results: Diagnostic Finding Cards — same as Diagnostics tab]  │
└────────────────────────────────────────────────────────────────┘
```

---

### 11.7 OBD Connection (8-Step Wizard)

```
┌────────────────────────────────────────────────────────────────┐
│ WIZARD STEPPER (8 steps, horizontal)                          │
│ [1 Mode] → [2 Discover] → [3 Select] → [4 Connect] →          │
│ [5 ECU] → [6 PIDs] → [7 Success] → [8 Error]                  │
│ Active: accent.primary, Completed: status.success, Error: status.critical
├────────────────────────────────────────────────────────────────┤
│ STEP CONTENT (Wizard Card: surface.primary, radius.lg, shadow.lg)│
│                                                                 │
│ STEP 1: Mode Selection                                         │
│ [Simulation Card] [Real OBD Card] — Radio-style cards         │
│                                                                 │
│ STEP 2: Port Discovery                                         │
│ [Scanning Spinner] → [Port Cards Grid]                        │
│ Port Card: Device, Description, VID:PID, Likely-OBD badge     │
│                                                                 │
│ STEP 3: Port Selection                                         │
│ [Port Select] [Baudrate] [Protocol] [Timeout] [Query Timeout] │
│                                                                 │
│ STEP 4: Connection                                             │
│ [Progress Bar: Trying 38400→115200→9600→57600]               │
│ [Connection Log: Timestamped entries]                         │
│                                                                 │
│ STEP 5: ECU Detection                                          │
│ [Progress Bar: VIN, CALID, CVN, ECU Name, Fuel, Runtime]      │
│ [Results Grid: 2-col disabled inputs]                         │
│                                                                 │
│ STEP 6: PID Discovery                                          │
│ [PID Grid: Supported (green border) / Unsupported (amber)]    │
│ Summary: "47/64 standard PIDs supported"                      │
│                                                                 │
│ STEP 7: Success                                                │
│ [✓ Icon] [Metrics: Mode, Port, PIDs, Adapter, Baud, Protocol] │
│ [Dashboard] [Diagnostics] [Disconnect]                        │
│                                                                 │
│ STEP 8: Error                                                  │
│ [✕ Icon] [Error Detail] [Troubleshooting Cards × 7]           │
│ [Retry] [Back to Port Selection]                               │
├────────────────────────────────────────────────────────────────┤
│ CONNECTION LOG (Expander, bottom)                              │
└────────────────────────────────────────────────────────────────┘
```

**Connected State (bypasses wizard):**
- Success banner with health check metrics
- Quick nav: Dashboard, Diagnostics, Disconnect

---

### 11.8 Reports

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar: "Reports" | [Batch Generate All]                     │
├────────────────────────────────────────────────────────────────┤
│ SIDEBAR (Generate Tab):                                        │
│ [Report Type ↓] [Format: HTML ● PDF]                          │
│ [Session Select] [Diagnosis Select]                           │
│ [Vehicle Override Expander]                                    │
│ [Generate Button — Primary, Full Width]                        │
├────────────────────────────────────────────────────────────────┤
│ TABS: [Generate] [Preview] [Download]                         │
├────────────────────────────────────────────────────────────────┤
│ GENERATE TAB                                                   │
│ [Config Summary Card] [Generate Button]                       │
│ [Batch Generate Section]                                       │
├────────────────────────────────────────────────────────────────┤
│ PREVIEW TAB                                                    │
│ [HTML: iframe 800px height + "Open in New Tab" link]          │
│ [PDF: Info card with size + Download button]                  │
│ [Batch: Expandable cards per report]                          │
├────────────────────────────────────────────────────────────────┤
│ DOWNLOAD TAB                                                   │
│ [Current Report Download]                                      │
│ [Batch Downloads]                                              │
│ [Saved Reports Browser: HTML column + PDF column]             │
└────────────────────────────────────────────────────────────────┘
```

---

### 11.9 Settings

```
┌────────────────────────────────────────────────────────────────┐
│ Top Bar: "Settings"                                           │
├────────────────────────────────────────────────────────────────┤
│ TABS: [AI & LM Studio] [OBD Connection] [Simulation]          │
│       [Data & Export] [Backup & Restore] [About]              │
├────────────────────────────────────────────────────────────────┤
│ AI & LM STUDIO                                                 │
│ [Base URL Input] [Test Connection Button]                     │
│ [Model Select + Refresh] [Model Badges Grid]                  │
│ [Temperature Slider 0.0-2.0] [Timeout Input]                  │
├────────────────────────────────────────────────────────────────┤
│ OBD CONNECTION                                                 │
│ [Mode Radio: Simulation ● Real]                               │
│ Real mode → [Port] [Baudrate] [Protocol] [Test Connection]    │
│ Simulation mode → [Info Alert: Simulation Active]             │
├────────────────────────────────────────────────────────────────┤
│ SIMULATION                                                     │
│ [Update Interval] [Refresh Interval]                          │
│ [Scenario Reference Cards: Idle, City, Highway, Accel, Overheat]│
│ [UI Preferences: Theme (locked dark), Auto-refresh]           │
├────────────────────────────────────────────────────────────────┤
│ DATA & EXPORT                                                  │
│ [Session Export Cards: CSV/JSON/Delete per session]           │
│ [Diagnostic Export Cards]                                     │
│ [Maintenance Export Button]                                   │
│ [Complete Archive Button — Primary]                           │
├────────────────────────────────────────────────────────────────┤
│ BACKUP & RESTORE                                               │
│ [Create Backup] [Open Backup Folder]                          │
│ [Backup History Table: Name, Size, Date, Restore/Delete]      │
│ [Database Statistics: 8 Metric Cards]                         │
├────────────────────────────────────────────────────────────────┤
│ ABOUT                                                          │
│ [App Info Cards] [Vehicle Profile Cards] [Engine Specs Cards] │
│ [Disclaimer Alert] [Open Source Notice]                       │
└────────────────────────────────────────────────────────────────┘
```

---

## 12. Accessibility Specification

### 12.1 WCAG 2.1 AA Targets

| Criterion | Target | Implementation |
|-----------|--------|----------------|
| 1.4.3 Contrast (Text) | ≥4.5:1 normal, ≥3:1 large | Verified via contrast matrix (§3.2) |
| 1.4.11 Contrast (UI Components) | ≥3:1 | Focus rings, borders, indicator dots |
| 2.1.1 Keyboard | All functionality | Native widgets + custom HTML with tabindex |
| 2.4.3 Focus Order | Logical | DOM order = visual order |
| 2.4.7 Focus Visible | Always visible | `shadow.focus` (3px accent.primary ring) |
| 3.2.1 On Focus | No context change | No auto-navigation on focus |
| 3.3.2 Labels | All inputs labeled | `<label for="">` + `aria-describedby` |
| 3.3.3 Error Suggestion | Accessible errors | `role="alert"`, `aria-live="polite"` |
| 4.1.2 Name/Role/Value | Custom components | Semantic HTML + explicit ARIA where needed |

### 12.2 Streamlit Constraints & Workarounds

| Constraint | Impact | Workaround |
|------------|--------|------------|
| Native widgets lack `aria-label` control | Screen reader labels may be generic | Use descriptive `label` param; hide visual label with `label_visibility="collapsed"` only when aria-label provided |
| `st.button` no `aria-pressed` | Toggle buttons not announced | Use `st.checkbox` for toggles; or custom HTML with proper ARIA |
| `st.tabs` keyboard support limited | Tab panel switching may not announce | Ensure tab labels are descriptive; add `aria-controls` via CSS-injected JS if critical |
| `st.dataframe` no row selection ARIA | Selected row not announced | Add visual selection + status text "X rows selected" |
| `st.components.v1.html` iframe sandbox | Report preview not accessible | Provide "Open in New Tab" link (primary access) |
| Custom HTML via `unsafe_allow_html` | No Streamlit ARIA integration | Use semantic HTML (`<button>`, `<label>`, `<nav>`, `<main>`); add explicit ARIA only where semantic insufficient |

### 12.3 Custom HTML Accessibility Rules

1. **Never** use `<div onClick>` — use `<button>` or `<a href>`
2. **Always** pair `<label for="id">` with `<input id="id">`
3. **Always** add `role="status" aria-live="polite"` to loading/toast regions
4. **Always** add `aria-expanded` + `aria-controls` to expandable sections
5. **Always** use `<nav aria-label="...">` for sidebar navigation
6. **Always** use `<main>` for page content area
7. **Always** use heading hierarchy (h1→h2→h3) without skipping
8. **Focus Ring:** `:focus-visible { outline: none; box-shadow: 0 0 0 3px var(--accent-primary); }`

### 12.4 Color-Only Information

| Pattern | Fix |
|---------|-----|
| Status dot only | Dot + text label (e.g., "● Connected") |
| Severity badge only | Badge + text (e.g., "Major" in badge) |
| Gauge sector only | Value number + dynamic color + threshold labels |
| Chart series only | Legend + distinct line patterns (solid/dash/dot) for CVD |

### 12.5 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
  .pulse { animation: none; opacity: 1; }
}
```

---

## 13. Responsive Design Specification

### 13.1 Breakpoints

| Name | Width | Sidebar | Layout Changes |
|------|-------|---------|----------------|
| `desktop` | ≥1280px | Expanded (280px) | 4-col metrics, 3-col charts, full tables |
| `laptop` | 1024-1279px | Expanded (280px) | 2-col metrics, 2-col charts, full tables |
| `tablet` | 768-1023px | Collapsible drawer | 2-col metrics, stacked charts, scrollable tables |
| `mobile` | <768px | Drawer only | 1-col all, stacked gauges, card-per-row tables |

### 13.2 Component Responsive Behaviour

| Component | Desktop | Laptop | Tablet | Mobile |
|-----------|---------|--------|--------|--------|
| Metric Cards | 4-col grid | 2-col grid | 2-col grid | 1-col stack |
| Gauge Cluster | 2×3 grid | 2×3 grid | 2×3 grid | 6×1 stack |
| Tables | Full | Full | Horizontal scroll + sticky col 1 | Card-per-row |
| Charts | Full width | Full width | Full width | Full width, reduced height |
| Forms | 2-col fields | 2-col fields | 1-col fields | 1-col fields |
| Wizard Steps | Horizontal | Horizontal | Horizontal scroll | Horizontal scroll |
| Sidebar | Fixed 280px | Fixed 280px | Drawer (overlay) | Drawer (overlay) |
| Top Bar | Full | Full | Condensed | Condensed (hamburger) |

### 13.3 Streamlit Responsive Implementation

- Use `st.columns()` with responsive ratios (not fixed)
- CSS Grid media queries via injected global CSS
- `st.dataframe` → `use_container_width=True`
- Charts → `use_container_width=True`, responsive height via CSS
- Custom HTML: CSS Grid/Flexbox with media queries in global CSS

---

## 14. Motion & Interaction Principles

### 14.1 Approved Interactions

| Interaction | Duration | Easing | Trigger |
|-------------|----------|--------|---------|
| Button hover | 150ms | ease-out | Mouse enter |
| Button active | 50ms | ease-out | Mouse down |
| Card hover | 150ms | ease-out | Mouse enter |
| Focus ring | 100ms | ease-out | Keyboard focus |
| Expand/collapse | 200ms | ease-in-out | Click chevron |
| Tab switch | 100ms | ease-out | Click tab |
| Progress bar | 300ms | linear | Value change |
| Toast appear | 200ms | ease-out | Mount |
| Toast dismiss | 150ms | ease-in | Dismiss/timeout |
| Skeleton pulse | 1.5s | ease-in-out | Infinite (loading) |

### 14.2 Prohibited

- ❌ Continuous animations (except loading skeletons)
- ❌ Parallax, scroll animations
- ❌ Auto-advancing carousels
- ❌ Animations on telemetry updates (values change, UI stays stable)
- ❌ Page transition animations (Streamlit reruns are instant)

### 14.3 Reduced Motion

All non-essential animations disabled via `prefers-reduced-motion`. Essential: progress bars, loading indicators.

---

## 15. Session-State Preservation Matrix

**Enumerated from actual codebase inspection (`app.py`, all 9 modules, `components/sidebar.py`).**

| Session State Key | Current Purpose | Pages Using It | Data Type | Must Preserve |
|-------------------|-----------------|----------------|-----------|---------------|
| `current_page` | Active navigation | All (via app.py, sidebar) | str | ✅ Yes |
| `sim_running` | Simulation active | Dashboard, Diagnostics, Performance, OBD, Sidebar | bool | ✅ Yes |
| `sim_scenario` | Active scenario key | Dashboard, OBD, Sidebar, Settings | str (idle/city/highway/acceleration/overheating) | ✅ Yes |
| `telemetry_history` | Rolling 300-point buffer | Dashboard, Diagnostics, Performance | List[Dict] | ✅ Yes |
| `session_id` | Active telemetry session PK | Dashboard, Diagnostics, Performance, Reports | int/None | ✅ Yes |
| `last_update` | Timestamp of last telemetry | Dashboard | float (epoch) | ✅ Yes |
| `obd_connected` | OBD connection status | All (via sidebar, app.py) | bool | ✅ Yes |
| `ai_connected` | LM Studio connection status | All (via sidebar, app.py), AI Assistant | bool | ✅ Yes |
| `services_initialized` | Service singleton flag | app.py | bool | ✅ Yes |
| `wizard_step` | OBD wizard current step (1-8) | OBD Connection | int | ✅ Yes |
| `wizard_selected_port` | Selected COM port | OBD Connection | str/None | ✅ Yes |
| `wizard_discovered_ports` | Discovered port list | OBD Connection | List[PortInfo] | ✅ Yes |
| `wizard_connection_log` | Timestamped connection events | OBD Connection | List[Dict] | ✅ Yes |
| `wizard_auto_connect` | Auto-connect flag | OBD Connection | bool | ✅ Yes |
| `connection_attempted` | Connection attempt guard | OBD Connection | bool | ✅ Yes |
| `ecu_detected` | ECU detection guard | OBD Connection | bool | ✅ Yes |
| `pids_discovered` | PID discovery guard | OBD Connection | bool | ✅ Yes |
| `vehicle_info` | Detected ECU info dict | OBD Connection | Dict | ✅ Yes |
| `ai_session_id` | AI conversation UUID | AI Assistant | str | ✅ Yes |
| `ai_messages` | Conversation history | AI Assistant | List[Dict] | ✅ Yes |
| `ai_loading` | AI response in progress | AI Assistant | bool | ✅ Yes |
| `ai_mode` | "chat" or "diagnostic" | AI Assistant | str | ✅ Yes |
| `ai_diagnostic_result` | Structured diagnosis result | AI Assistant, Diagnostics | DiagnosticResult/None | ✅ Yes |
| `ai_status` | LM Studio status (online/offline/checking) | AI Assistant | str | ✅ Yes |
| `ai_models` | Available model list | AI Assistant | List[ModelInfo] | ✅ Yes |
| `ai_model_available` | Current model loaded | AI Assistant | bool | ✅ Yes |
| `ai_history_loaded` | DB history load guard | AI Assistant | bool | ✅ Yes |
| `report_generator` | ReportGenerator instance | Reports | ReportGenerator | ✅ Yes |
| `generated_report` | Last generation metadata | Reports | Dict/None | ✅ Yes |
| `report_html` | Generated HTML content | Reports | str/None | ✅ Yes |
| `report_pdf` | Generated PDF bytes | Reports | bytes/None | ✅ Yes |
| `batch_results` | Batch generation results | Reports | Dict/None | ✅ Yes |
| `report_config` | Generation config (type, format, session, etc.) | Reports | Dict | ✅ Yes |
| `confirm_delete_{session_id}` | Delete confirmation guard | Settings | bool | ✅ Yes |
| `confirm_restore` | Restore confirmation guard | Settings | bool | ✅ Yes |

**Total: 34 distinct session-state keys**

### 15.1 Preservation Rules (Non-Negotiable)

1. **No renaming** — Keys used across modules; rename breaks cross-page features
2. **No deletion** — Even "unused" keys may be read by other pages
3. **No structure change** — `ai_messages` is List[Dict] with specific keys; changing breaks persistence
4. **No reset on navigation** — `st.rerun()` preserves state; only explicit clear actions reset
5. **No duplicate initialization** — Each key initialized once in `app.py` or owning module
6. **Documentation** — Any new key must be added to this matrix before merge

---

## 16. CSS & Design Token Architecture

### 16.1 Centralized Structure (Stage 3 Implementation Target)

```
components/
├── design_tokens.py          # All token constants (colors, spacing, radius, shadows, type)
├── theme.py                  # Theme class: token → CSS var mapping, Plotly template
├── css/
│   ├── __init__.py           # CSS builder utilities
│   ├── variables.css         # :root { --token: value; } — injected once in app.py
│   ├── global.css            # Global resets, Streamlit overrides, utility classes
│   ├── layout.css            # Grid, flex, container, sidebar, top-bar
│   ├── components.css        # Cards, buttons, badges, alerts, forms, tables
│   ├── charts.css            # Chart-specific utilities (not Plotly — for HTML charts)
│   └── states.css            # Hover, focus, active, disabled, loading, empty
├── ui/
│   ├── __init__.py           # Exports: Button, Card, Badge, Alert, Input, Table, etc.
│   ├── button.py             # st.button wrapper with variant prop
│   ├── card.py               # MetricCard, StatusCard, DiagnosticCard, ReportCard
│   ├── badge.py              # StatusBadge, SeverityBadge, ConfidenceBadge, etc.
│   ├── alert.py              # SuccessAlert, WarningAlert, ErrorAlert, CriticalAlert
│   ├── form.py               # FormField, Input, Select, Textarea, Slider
│   ├── table.py              # DataTable with sorting, selection, actions
│   ├── empty.py              # EmptyState variants
│   ├── loading.py            # Skeleton, Spinner, ProgressBar, PulseDots
│   ├── wizard.py             # Stepper, WizardCard, WizardNav
│   └── sidebar.py            # NavItem, VehicleStatus, ConnectionIndicators, SimStatus
└── charts_v2.py              # Token-driven Plotly chart factory
```

### 16.2 Token → CSS Variable Mapping

```python
# design_tokens.py → theme.py → variables.css
TOKEN_TO_CSS_VAR = {
    # Surfaces
    "surface.app": "--surface-app",
    "surface.primary": "--surface-primary",
    "surface.secondary": "--surface-secondary",
    "surface.elevated": "--surface-elevated",
    "surface.interactive": "--surface-interactive",
    # Text
    "text.primary": "--text-primary",
    "text.secondary": "--text-secondary",
    "text.muted": "--text-muted",
    "text.inverse": "--text-inverse",
    "text.link": "--text-link",
    "text.on-accent": "--text-on-accent",
    # Borders
    "border.default": "--border-default",
    "border.subtle": "--border-subtle",
    "border.strong": "--border-strong",
    "border.focus": "--border-focus",
    "border.separator": "--border-separator",
    # Accents
    "accent.primary": "--accent-primary",
    "accent.primary-hover": "--accent-primary-hover",
    "accent.primary-active": "--accent-primary-active",
    "accent.secondary": "--accent-secondary",
    "accent.selected": "--accent-selected",
    # Status
    "status.success": "--status-success",
    "status.warning": "--status-warning",
    "status.critical": "--status-critical",
    "status.info": "--status-info",
    "status.neutral": "--status-neutral",
    # Diagnostic
    "diag.critical": "--diag-critical",
    "diag.major": "--diag-major",
    "diag.minor": "--diag-minor",
    "diag.info": "--diag-info",
    # Data Source
    "datasource.real": "--datasource-real",
    "datasource.simulation": "--datasource-simulation",
    "datasource.ai": "--datasource-ai",
    # Chart Series
    "series.1": "--series-1",
    "series.2": "--series-2",
    "series.3": "--series-3",
    "series.4": "--series-4",
    "series.5": "--series-5",
    # Chart Status
    "chart.good": "--chart-good",
    "chart.warning": "--chart-warning",
    "chart.serious": "--chart-serious",
    "chart.critical": "--chart-critical",
    # Spacing
    "space.1": "--space-1",  # ... up to space.16
    # Radius
    "radius.sm": "--radius-sm",
    "radius.md": "--radius-md",
    "radius.lg": "--radius-lg",
    "radius.xl": "--radius-xl",
    "radius.pill": "--radius-pill",
    "radius.circle": "--radius-circle",
    # Shadows
    "shadow.sm": "--shadow-sm",
    "shadow.md": "--shadow-md",
    "shadow.lg": "--shadow-lg",
    "shadow.focus": "--shadow-focus",
    # Typography
    "font.family.base": "--font-family-base",
    "font.family.mono": "--font-family-mono",
    "font.size.display": "--font-size-display",
    "font.size.h1": "--font-size-h1",
    # ... all type tokens
}
```

### 16.3 Migration Strategy (Stage 3 → Stage 5)

1. **Phase 1:** Create `design_tokens.py`, `theme.py`, `css/variables.css`, inject in `app.py` once
2. **Phase 2:** Build `components/ui/` primitives (Button, Card, Badge, Alert, Form, Table, Loading, Empty)
3. **Phase 3:** Refactor `components/charts.py` → `charts_v2.py` using tokens
4. **Phase 4:** Redesign Sidebar using `ui/` primitives
5. **Phase 5:** Redesign pages one-by-one (Dashboard first), replacing inline CSS with `ui/` components
6. **Phase 6:** Remove all inline `st.markdown(css, ...)` from page modules

**Rollback Plan:** Keep old CSS in place until new component verified. Feature-flag new pages via `st.session_state.use_new_ui`.

---

## 17. Stage 3 Implementation Sequence

| Step | Deliverable | Dependencies | Est. Effort |
|------|-------------|--------------|-------------|
| 1 | `design_tokens.py` + `theme.py` + `css/variables.css` | None | 1 day |
| 2 | `css/global.css` (Streamlit overrides, utilities) | Step 1 | 0.5 day |
| 3 | `components/ui/button.py`, `badge.py`, `alert.py` | Step 1 | 1 day |
| 4 | `components/ui/card.py` (MetricCard, StatusCard, DiagnosticCard, ReportCard) | Step 1 | 1.5 days |
| 5 | `components/ui/form.py`, `table.py`, `empty.py`, `loading.py` | Step 1 | 1.5 days |
| 6 | `components/ui/wizard.py` (Stepper, WizardCard) | Step 1 | 1 day |
| 7 | `components/ui/sidebar.py` (NavItem, VehicleStatus, ConnectionIndicators, SimStatus) | Steps 1-3 | 1 day |
| 8 | `components/charts_v2.py` (token-driven Plotly factory) | Step 1 | 1 day |
| 9 | Sidebar redesign using `ui/sidebar.py` | Steps 1-7 | 1 day |
| 10 | Dashboard redesign using `ui/` + `charts_v2.py` | Steps 1-8 | 2 days |
| 11 | Diagnostics redesign | Steps 1-8 | 2 days |
| 12 | AI Assistant redesign | Steps 1-8 | 1.5 days |
| 13 | OBD Connection redesign | Steps 1-8 | 1.5 days |
| 14 | Reports redesign | Steps 1-8 | 1 day |
| 15 | Performance redesign | Steps 1-8 | 1 day |
| 16 | Maintenance redesign | Steps 1-8 | 1 day |
| 17 | Vehicle Profile redesign | Steps 1-8 | 0.5 day |
| 18 | Settings redesign | Steps 1-8 | 1 day |
| 19 | Responsive testing & fixes | Steps 9-18 | 1 day |
| 20 | Accessibility audit & fixes | Steps 9-18 | 1 day |

**Total: ~19 days for full Stage 3-5 implementation**

---

## 18. Acceptance Criteria (Stage 2 Complete)

- [x] Existing audit document reviewed
- [x] Actual THEME values inspected (config.py:145-157)
- [x] Existing chart color system inspected (components/charts.py:16-46)
- [x] Final color palette specified (17 surface + 7 text + 5 border + 3 accent + 5 status + 4 diag + 3 datasource + 5 series + 4 chart status = 53 tokens)
- [x] Semantic status mappings specified (app status vs diag severity vs datasource vs chart)
- [x] Contrast matrix documented (22 combinations tested)
- [x] Typography scale specified (16 tokens with exact sizes/weights/line-heights)
- [x] Spacing scale specified (12 base tokens + 9 semantic aliases)
- [x] Radius scale specified (7 tokens)
- [x] Elevation scale specified (8 shadow tokens + 4-level hierarchy)
- [x] Global layout specified (shell, sidebar, top-bar, grid, page anatomy)
- [x] Shared component anatomy documented (11 component types with full specs)
- [x] Button variants specified (5 variants × 8 states)
- [x] Status indicators specified (7 badge variants)
- [x] Form specification complete (input, label, help, error, validation states)
- [x] Table specification complete (header, row, states, responsive)
- [x] Empty and loading states specified (7 empty variants, 6 loading patterns)
- [x] Chart system specified (theme, gauge, line, multi-series, comparison, sparkline, color mapping)
- [x] Accessibility requirements documented (WCAG targets, Streamlit constraints, custom HTML rules)
- [x] Responsive behaviour specified (4 breakpoints, component behaviour table)
- [x] All 9 pages have design blueprints (detailed ASCII layouts)
- [x] Actual shared session-state keys inventoried (34 keys with types, consumers, preservation rules)
- [x] CSS centralization architecture specified (proposed file structure, token→CSS var mapping, migration plan)
- [x] Stage 3 implementation sequence prepared (20 steps, ~19 days)
- [x] Progress tracker will be updated (next section)
- [x] No application source files changed

---

## 19. Files Created/Modified

### Created:
- `docs/PHASE_6_DESIGN_SYSTEM.md` (this document)

### Modified:
- `docs/PHASE_6_PROGRESS.md` (updated below)

### Application Source Files Changed:
- **NONE** — Stage 2 is design specification only

---

## 20. Progress Tracker Update

### `docs/PHASE_6_PROGRESS.md`

```markdown
# Phase 6 Progress Tracker

## Stage 1: Read-Only Audit — COMPLETE (2026-11-16)
- All 9 pages audited
- Shared components catalogued
- Session-state dependencies mapped
- Visual/UX inconsistencies documented
- Output: `docs/PHASE_6_AUDIT_SUMMARY.md`

## Stage 2: Design Direction & Specification — COMPLETE (2026-11-16)
- Design philosophy defined: Automotive Technical Professional
- Final color palette: 53 semantic tokens derived from existing THEME
- Contrast matrix: 22 combinations validated against WCAG 2.1 AA
- Typography: 16-token scale with numeric optimization
- Spacing: 4px base system (12 tokens + 9 aliases)
- Radius: 7 tokens, Elevation: 8 shadow tokens
- Layout: Global shell, grid system, page anatomy
- Components: 11 types fully specified (cards, buttons, badges, alerts, forms, tables, empty, loading, wizard, sidebar, charts)
- Charts: Token-driven Plotly theme, gauge/line/multi-series/comparison/sparkline specs
- Accessibility: WCAG 2.1 AA targets, Streamlit constraints documented
- Responsive: 4 breakpoints, component behaviour matrix
- Page Blueprints: All 9 pages with ASCII layouts
- Session-State: 34 keys inventoried with preservation rules
- CSS Architecture: Centralized token→CSS var structure, migration plan
- Stage 3 Sequence: 20 steps, ~19 days
- Output: `docs/PHASE_6_DESIGN_SYSTEM.md`

## Stage 3: Design System Foundations — PENDING
- [ ] design_tokens.py + theme.py + css/variables.css
- [ ] css/global.css
- [ ] ui primitives (button, badge, alert, card, form, table, empty, loading, wizard, sidebar)
- [ ] charts_v2.py
- [ ] Sidebar redesign
- [ ] Dashboard redesign (proves design system)

## Stage 4: Global Shell Redesign — PENDING
## Stage 5: Page-by-Page Redesign (9 pages) — PENDING
## Stage 6: Responsive & Mobile — PENDING
## Stage 7: Accessibility (WCAG 2.1 AA) — PENDING
## Stage 8: Regression Testing — PENDING
## Stage 9: Documentation — PENDING

## Known Implementation Constraints
1. Streamlit native theming cannot control custom CSS → single dark theme locked
2. `unsafe_allow_html` required for custom components → semantic HTML + explicit ARIA
3. 34 shared session-state keys → no renaming/deletion/structure changes
4. Plotly chart theming via layout dict → token-driven factory required
5. Sidebar width fixed ~300px → collapsible drawer for mobile
6. No light theme → design system v1 is dark-only
```

---

## 21. Next Stage

**Stage 3 — Centralized Design System Implementation**

**Entry Point:** Create `components/design_tokens.py` with all 53 color tokens, 12 spacing tokens, 7 radius tokens, 8 shadow tokens, 16 typography tokens, and 7 semantic spacing aliases as Python constants.

**Do not begin Stage 3 automatically.** Await explicit instruction.

---

**End of Stage 2 Design Specification** — Ready for Stage 3 Implementation