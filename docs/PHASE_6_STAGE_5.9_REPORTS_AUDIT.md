# Phase 6 Stage 5.9: Reports Page - Read-Only Audit

**Date:** 2026-11-17  
**Status:** AUDIT COMPLETE

---

## 1. File Overview

**File:** `modules/reports.py`  
**Lines:** ~642  
**Custom CSS:** ~80 lines (in `inject_reports_css()`)

---

## 2. Current Architecture

### Main Page Structure (`render_reports_page()`)
| Section | Description |
|---------|-------------|
| **Sidebar Configuration** | Report type, output format, session selection, diagnosis selection, vehicle override |
| **Tab 1: Generate** | Single report generation with progress, batch generation for all 4 types |
| **Tab 2: Preview** | HTML preview of generated report |
| **Tab 3: Download** | Download HTML/PDF buttons, report metadata |
| **Saved Reports** | List of previously generated reports with load/delete actions |

### Standalone Page Functions
| Function | Purpose |
|----------|---------|
| `render_diagnostic_reports_page()` | Diagnostic-specific reports |
| `render_vehicle_health_reports_page()` | Vehicle health-specific reports |
| `render_performance_reports_page()` | Performance-specific reports |
| `render_maintenance_reports_page()` | Maintenance-specific reports |

### Session State Keys (Page-Specific)
| Key | Type | Purpose |
|-----|------|---------|
| `report_generator` | ReportGenerator | Singleton report generator instance |
| `generated_report` | ReportDataUnion | Current report data model |
| `report_html` | str | Rendered HTML output |
| `report_pdf` | bytes | Rendered PDF bytes |
| `report_config` | Dict | Current report configuration |
| `batch_results` | Dict | Batch generation results for all 4 types |

### Shared Session State Keys (34 total - must preserve)
- Navigation: `current_page`, `sidebar_collapsed`
- Dashboard: 5 keys
- Diagnostics: 11 keys
- Performance: 7 keys
- Maintenance: 6 keys
- Vehicle Profile: uses shared
- AI Assistant: 9 keys
- OBD Connection: 10 keys
- Reports: 6 page-specific (above)
- Settings: uses shared

---

## 3. Professional Reporting Engine (Must NOT Modify)

The engine is fully implemented and must be preserved exactly. The UI redesign should only touch `modules/reports.py`.

### Report Types (4) — `services/report_models.py`
| Type | Enum Value | Data Model |
|------|------------|------------|
| Diagnostic | `ReportType.DIAGNOSTIC` | `DiagnosticReportData` |
| Vehicle Health | `ReportType.VEHICLE_HEALTH` | `VehicleHealthReportData` |
| Performance | `ReportType.PERFORMANCE` | `PerformanceReportData` |
| Maintenance | `ReportType.MAINTENANCE` | `MaintenanceReportData` |

### Output Formats (2) — `services/report_models.py`
| Format | Enum Value | Renderer |
|--------|------------|----------|
| HTML | `ReportFormat.HTML` | `HTMLRenderer` (Jinja2 with `select_autoescape(["html", "xml"])`) |
| PDF | `ReportFormat.PDF` | `PDFRenderer` (ReportLab) |

### Data Source Tracking — `services/report_models.py:DataSource`
| Source | Enum Value | Description |
|--------|------------|-------------|
| Real | `DataSource.REAL` | Live OBD-II data |
| Simulation | `DataSource.SIMULATION` | Simulated/demo data |
| Mixed | `DataSource.MIXED` | Combination of real and simulated |
| Unknown | `DataSource.UNKNOWN` | Source indeterminate |

### Core Engine Files
| File | Lines | Purpose |
|------|-------|---------|
| `services/report_models.py` | 431 | Pydantic models for all 4 report types |
| `services/report_data_builder.py` | 1290 | `ReportDataBuilder` class - assembles report data from DB, DiagnosticEngine, RuleEngine, OBDService |
| `services/report_generator.py` | 470 | `ReportGenerator` class - orchestrates generation, dispatches by type, batch generation |
| `services/report_renderers/html_renderer.py` | 189 | `HTMLRenderer` - Jinja2 templates with autoescape |
| `services/report_renderers/pdf_renderer.py` | 1265 | `PDFRenderer` - ReportLab professional PDFs |
| `services/report_renderers/__init__.py` | 20 | Exports and convenience functions |

---

## 4. Data Flow (Preserve Exactly)

```
User Config (Sidebar) 
    → ReportGenerator.generate_report(type, format, session_id, diagnosis_id, vehicle_override)
        → ReportDataBuilder.build_*_report_data() [assembles from services]
            → DatabaseService, DiagnosticEngine, RuleEngine, OBDService
        → ReportDataUnion (Pydantic model)
    → HTMLRenderer.render_report() / PDFRenderer.render_report()
        → Jinja2 templates (autoescape=select_autoescape(["html", "xml"]))
        → HTML string / PDF bytes
    → Session State: generated_report, report_html, report_pdf, report_config, batch_results
    → UI: Preview tab (HTML), Download tab (buttons)
```

---

## 5. Backend Integrations (Must Preserve)

| Service | Methods Used |
|---------|--------------|
| `ReportGenerator` | `generate_report()`, `generate_all_reports()`, `get_available_sessions()`, `get_available_diagnoses()` |
| `HTMLRenderer` | `render_report()`, `save_report()` |
| `PDFRenderer` | `render_report()`, `render_report_bytes()` |
| `DatabaseService` | Via ReportDataBuilder |
| `DiagnosticEngine` | Via ReportDataBuilder |
| `RuleEngine` | Via ReportDataBuilder |
| `OBDService` | Via ReportDataBuilder |

---

## 6. Custom CSS Classes to Replace

### Report Cards & Layout
- `.report-card` → **card()** component
- `.report-card-header` → **card()** header pattern
- `.report-card-title` → Typography tokens
- `.report-meta-row` → Grid layout with tokens
- `.report-meta-label` / `.report-meta-value` → Label/value typography
- `.report-section` → **section_header()** or card sections

### Status & Badges
- `.status-badge` → **badge()** component
- `.status-normal` / `.status-attention` / `.status-critical` / `.status-insufficient` → **badge()** with variant
- `.data-source-badge` → **badge()** with DATASOURCE tokens
- `.severity-badge` → **badge()** with DIAG tokens

### Buttons & Forms
- `.report-button-row` → Flex layout with button components
- `.stButton > button[report-primary]` → **button_primary()**
- `.stSelectbox` / `.stRadio` → **selectbox()** / native with token styling

### Preview & Download
- `.report-preview-container` → **card()** with overflow
- `.report-download-btn` → **button_primary()** / **button_secondary()**

### Batch Generation
- `.batch-progress` → **spinner()** + progress text
- `.batch-item` → **card_simple()** with status badge
- `.batch-item.success` / `.batch-item.error` / `.batch-item.pending` → Badge variants

### Saved Reports
- `.saved-report-item` → **card_simple()** with action buttons
- `.saved-report-header` → Layout
- `.saved-report-meta` → Metadata grid

---

## 7. Design System Components to Use

| Component | Usage |
|-----------|-------|
| `page_header()` | Main page title with icon |
| `section_header()` | Section titles (Generate, Preview, Download, Saved Reports) |
| `card()` / `card_simple()` | All content containers |
| `button_primary()` | Generate, Download, Save actions |
| `button_secondary()` | Preview, Batch, secondary actions |
| `button_ghost()` | Cancel, Clear, Load actions |
| `button_danger()` | Delete saved reports |
| `badge()` | Report type, format, data source, severity, status |
| `alert()` | Success/error/warning/info messages |
| `selectbox()` | Report type, format, session, diagnosis selectors |
| `text_input()` | Vehicle override fields |
| `empty_state()` | No reports generated, no saved reports |
| `spinner()` / `skeleton_card()` | Generation loading states |
| `tabs()` / native st.tabs | 3-tab layout (Generate/Preview/Download) |

---

## 8. Design Tokens to Apply

### Colors
- `ACCENT_PRIMARY` (#00b4d8) — Primary actions, active states
- `STATUS_SUCCESS` (#2ecc71) — Completed, healthy, success
- `STATUS_WARNING` (#f39c12) — Pending, warnings, simulation
- `STATUS_CRITICAL` (#e74c3c) — Errors, failed, critical
- `STATUS_INFO` (#00b4d8) — Info, real data
- `STATUS_NEUTRAL` (#9aa3ad) — Disabled, unknown, secondary
- `DATASOURCE_REAL` / `DATASOURCE_SIMULATION` / `DATASOURCE_MIXED` / `DATASOURCE_UNKNOWN` — Source badges
- `DIAG_CRITICAL` / `DIAG_MAJOR` / `DIAG_MINOR` / `DIAG_INFO` — Severity badges
- `TEXT_PRIMARY` / `TEXT_SECONDARY` / `TEXT_MUTED` / `TEXT_ON_ACCENT` — Text hierarchy
- `SURFACE_PRIMARY` / `SURFACE_SECONDARY` / `SURFACE_INTERACTIVE` / `SURFACE_APP` — Backgrounds
- `BORDER_DEFAULT` / `BORDER_SUBTLE` / `BORDER_FOCUS` — Borders

### Spacing
- `SPACE_1` (4px) through `SPACE_6` (24px) — Consistent spacing
- `GAP_FIELD` / `GAP_INLINE` / `GAP_CARD_GRID` / `GAP_SECTION` — Semantic gaps

### Typography
- `FONT_SIZE_LABEL` (0.75rem) — Form labels, metadata
- `FONT_SIZE_BODY` (0.875rem) — Standard content
- `FONT_SIZE_BODY_SM` (0.8125rem) — Secondary content
- `FONT_SIZE_CAPTION` (0.6875rem) — Fine print, timestamps
- `FONT_SIZE_H1` / `FONT_SIZE_H2` / `FONT_SIZE_H3` — Headers
- `FONT_WEIGHT_LABEL` (500) / `FONT_WEIGHT_BODY` (400) — Weights
- `LETTER_SPACING_LABEL` / `LETTER_SPACING_CAPTION` — Uppercase tracking

### Radius
- `RADIUS_SM` (4px) — Inputs, badges
- `RADIUS_MD` (8px) — Standard cards
- `RADIUS_LG` (12px) — Elevated cards
- `RADIUS_PILL` — Badges, pills

### Shadows
- `SHADOW_SM` / `SHADOW_MD` / `SHADOW_LG` / `SHADOW_FOCUS` — Elevation

### Transitions
- `TRANSITION_FAST` (0.15s) — Hover, focus
- `TRANSITION_NORMAL` (0.2s) — Card transforms

---

## 9. Migration Strategy

### Phase 1: Setup & Imports
- Replace `inject_reports_css()` with `inject_global_css()` + `initialize_layout()`
- Import all needed components and tokens from `components.ui`
- Add `page_header()` at top of `render_reports_page()`

### Phase 2: Sidebar Configuration Redesign
- Replace sidebar controls with design system components
- Use `selectbox()` for report type, format, session, diagnosis
- Use `text_input()` for vehicle override
- Use `badge()` for current selection indicators

### Phase 3: Tab 1 - Generate Redesign
- Report type/format selector cards using `card()` + `badge()`
- Generate button using `button_primary()`
- Batch generation using `button_secondary()` with progress via `spinner()`
- Status alerts using `alert()`

### Phase 4: Tab 2 - Preview Redesign
- Preview container using `card()` with scrollable HTML
- Use `section_header()` for "Report Preview"

### Phase 5: Tab 3 - Download Redesign
- Download buttons using `button_primary()` (HTML) and `button_secondary()` (PDF)
- Report metadata using `card_simple()` with grid layout
- Use `badge()` for format, data source, type

### Phase 6: Saved Reports Redesign
- List using `card_simple()` for each saved report
- Action buttons using `button_ghost()` (Load) and `button_danger()` (Delete)
- Empty state using `empty_state()`

### Phase 7: Standalone Pages
- Apply same patterns to 4 standalone page functions
- Use `page_header()` and `section_header()`

### Phase 8: Remove Custom CSS
- Delete `inject_reports_css()` entirely
- Verify zero custom CSS remains

### Phase 9: Verification
- Run all 415 tests
- Manual verification of all 4 report types × 2 formats
- Check responsive behavior
- Verify no custom CSS remains

---

## 10. Risk Areas

1. **HTML Preview Security** - Jinja2 `select_autoescape(["html", "xml"])` must remain intact; no double-escaping
2. **PDF Generation** - ReportLab rendering via `render_report_bytes()` must work for Streamlit download buttons
3. **Batch Generation State** - `batch_results` session state structure must be preserved exactly
4. **Session/Session Selection** - `get_available_sessions()` and `get_available_diagnoses()` integration
5. **Report Data Models** - All 4 `ReportDataUnion` types must render correctly in preview
6. **Standalone Pages** - 4 additional page functions need same treatment

---

## 11. Success Criteria

- [ ] Zero custom CSS (remove `inject_reports_css()` entirely)
- [ ] 30+ design system component usages
- [ ] All 6 page-specific session state keys preserved
- [ ] All 34 shared session state keys preserved
- [ ] All backend integrations preserved (ReportGenerator, HTMLRenderer, PDFRenderer)
- [ ] All 4 report types functional (Diagnostic, Vehicle Health, Performance, Maintenance)
- [ ] Both output formats functional (HTML, PDF)
- [ ] Batch generation functional
- [ ] Saved reports functional (list, load, delete)
- [ ] 4 standalone pages redesigned
- [ ] 415/415 tests passing
- [ ] Responsive at all breakpoints
- [ ] Dark theme only (no light theme regression)
- [ ] WCAG 2.1 AA contrast
- [ ] Jinja2 autoescape preserved (no XSS regression)