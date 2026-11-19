# Phase 6 Stage 6: Playwright Browser Automation Setup

**Date:** 2026-11-18  
**Status:** Implementation Guide

---

## 1. Project Environment Analysis

### Application Structure
- **Main App:** `app.py` — Streamlit application with 9 main pages via sidebar navigation
- **Standalone Reports:** 4 separate entry points in `modules/reports.py`:
  - `render_diagnostic_report_page()` — Diagnostic Report
  - `render_vehicle_health_report_page()` — Vehicle Health Report
  - `render_performance_report_page()` — Performance Report
  - `render_maintenance_report_page()` — Maintenance Report

### Navigation
- Main pages: `dashboard`, `diagnostics`, `performance`, `maintenance`, `reports`, `vehicle_profile`, `ai_assistant`, `obd_connection`, `settings`
- Navigation via `st.session_state.current_page` set by shell sidebar
- Each page renders via `page_renderers` dict in `app.py:main()`

### Database
- SQLite at `data/i20_garage.db` (configurable via `DATABASE_PATH` in `config.py`)
- `DatabaseService` singleton via `services.database.get_database()`
- Accepts custom `db_path` in constructor for test isolation

### External Services
- **OBD:** Simulation mode by default (`OBD_MODE=simulation`) — no hardware needed
- **AI:** LM Studio connection — fails gracefully if unavailable, returns `False` from `is_available()`
- **Simulation:** Built-in `SimulationEngine` — generates deterministic test data

### Startup
```powershell
# Main app
.\.venv\Scripts\Activate.ps1
python -m streamlit run app.py --server.headless=true --server.port=8501
```

---

## 2. Playwright Setup Architecture

### Dependency Management
Create `requirements-dev.txt` for development dependencies:

```text
# Browser Automation
playwright>=1.40.0
pytest-playwright>=0.4.0
```

### Installation (Windows PowerShell)
```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m playwright install chromium
```

### Test Structure
```text
tests/
    browser/
        conftest.py                 # Fixtures: app startup, browser, viewports, navigation
        test_responsive_matrix.py   # 13 pages × 7 viewports parametrized
        test_mobile_navigation.py   # Drawer open/close, page selection
        test_page_components.py     # Charts, tables, forms, reports preview
        fixtures/
            test_data.py            # Temporary database, mocked services
        utils/
            viewport.py             # Viewport definitions
            assertions.py           # Reusable responsive checks
            screenshots.py          # Screenshot capture & comparison
```

---

## 3. Application Test Isolation Strategy

### Database Isolation
- Create temporary SQLite database per test session
- Set `DATABASE_PATH` environment variable before importing services
- Use `DatabaseService(db_path=temp_path, run_migrations=True)`
- Clean up temp file after test session

### Service Mocking
- **OBD:** Already uses simulation mode by default — no mock needed
- **AI:** `AIService.check_connection()` returns `False` when LM Studio unavailable — acceptable for layout tests
- **Reports:** `ReportGenerator` uses database — works with test database

### Standalone Report Pages
Create test entry point scripts:
```python
# tests/browser/fixtures/standalone_diagnostic.py
import streamlit as st
from modules.reports import render_diagnostic_report_page
render_diagnostic_report_page()
```

Run on separate ports (8502-8505) during test session.

---

## 4. Viewport Definitions

| ID | Profile | Width | Height | Device Class |
|---|---|---:|---:|---|
| VP01 | Desktop | 1440 | 900 | Desktop |
| VP02 | Laptop | 1100 | 800 | Laptop |
| VP03 | Tablet | 900 | 768 | Tablet Landscape |
| VP04 | Tablet Portrait | 768 | 1024 | Tablet Portrait |
| VP05 | Mobile | 390 | 844 | Mobile (iPhone 12/13/14) |
| VP06 | Small Mobile | 360 | 800 | Mobile (Android) |
| VP07 | Minimum Mobile | 320 | 700 | Minimum (iPhone SE) |

---

## 5. Test Destinations (13 Total)

### Main App Pages (9) — accessed via sidebar navigation
1. `dashboard`
2. `diagnostics`
3. `performance`
4. `maintenance`
5. `vehicle_profile`
6. `ai_assistant`
7. `obd_connection`
8. `reports`
9. `settings`

### Standalone Reports (4) — separate Streamlit processes
10. `diagnostic_report` — `render_diagnostic_report_page()`
11. `vehicle_health_report` — `render_vehicle_health_report_page()`
12. `performance_report` — `render_performance_report_page()`
13. `maintenance_report` — `render_maintenance_report_page()`

---

## 6. Responsive Assertions Library

### Core Checks (Reusable Functions)

```python
# tests/browser/utils/assertions.py

def check_page_overflow(page):
    """Detect unintended document-level horizontal overflow."""
    doc_width = page.evaluate("document.documentElement.scrollWidth")
    viewport_width = page.evaluate("window.innerWidth")
    overflow = doc_width - viewport_width
    return {
        "doc_width": doc_width,
        "viewport_width": viewport_width,
        "overflow": overflow,
        "pass": overflow <= 1  # Allow 1px rounding
    }

def check_main_content_visible(page):
    """Verify main content area is visible and not obscured."""
    main = page.locator("main#main-content, .i20-page-container, [data-testid='stMain']")
    return {
        "visible": main.is_visible(),
        "bbox": main.bounding_box() if main.count() > 0 else None
    }

def check_responsive_grid(page, selector=".i20-grid, [style*='auto-fit']"):
    """Verify grid containers adapt to viewport."""
    grids = page.locator(selector)
    results = []
    for grid in grids.element_handles():
        bbox = grid.bounding_box()
        children = grid.query_selector_all(":scope > *")
        results.append({
            "grid_width": bbox["width"] if bbox else 0,
            "child_count": len(children),
            "children_in_viewport": all(
                0 <= c.bounding_box()["x"] < bbox["width"] for c in children if c.bounding_box()
            ) if bbox else False
        })
    return results

def check_touch_targets(page, min_size=44):
    """Check interactive elements meet minimum touch target size."""
    interactive = page.locator("button, a, input, select, [role='button'], .stButton button")
    results = []
    for el in interactive.element_handles():
        bbox = el.bounding_box()
        if bbox:
            results.append({
                "tag": el.evaluate("el => el.tagName.toLowerCase()"),
                "width": bbox["width"],
                "height": bbox["height"],
                "pass": bbox["width"] >= min_size and bbox["height"] >= min_size
            })
    return results

def check_table_scroll(page):
    """Verify tables have internal horizontal scroll without page overflow."""
    tables = page.locator("table, .i20-table-wrapper")
    results = []
    for table in tables.element_handles():
        bbox = table.bounding_box()
        scroll_width = table.evaluate("el => el.scrollWidth")
        client_width = table.evaluate("el => el.clientWidth")
        results.append({
            "has_horizontal_scroll": scroll_width > client_width,
            "table_width": client_width,
            "content_width": scroll_width,
            "overflow_expands_page": bbox and bbox["width"] > page.evaluate("window.innerWidth")
        })
    return results

def check_charts_in_bounds(page):
    """Verify Plotly charts stay within containers."""
    charts = page.locator(".js-plotly-plot, .plotly-graph-div")
    results = []
    for chart in charts.element_handles():
        bbox = chart.bounding_box()
        parent = chart.evaluate_handle("el => el.parentElement")
        parent_bbox = parent.bounding_box() if parent else None
        results.append({
            "chart_width": bbox["width"] if bbox else 0,
            "parent_width": parent_bbox["width"] if parent_bbox else 0,
            "overflows_parent": bbox and parent_bbox and bbox["width"] > parent_bbox["width"]
        })
    return results

def check_console_errors(page):
    """Collect browser console errors."""
    return page.evaluate("() => window.__playwright_errors || []")
```

---

## 7. Test Execution Commands

### Run All Browser Tests
```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest tests/browser/ -v --tb=short
```

### Run Specific Viewport
```powershell
python -m pytest tests/browser/test_responsive_matrix.py -k "viewport_desktop" -v
```

### Run with Screenshots
```powershell
python -m pytest tests/browser/ -v --screenshots=on
```

### Update Visual Baselines
```powershell
python -m pytest tests/browser/ -v --update-snapshots
```

---

## 8. Screenshot & Visual Regression

### Structure
```text
artifacts/
    phase_6_stage_6/
        screenshots/
            desktop/
            laptop/
            tablet/
            tablet_portrait/
            mobile/
            mobile_small/
            mobile_minimum/
        baseline/              # Committed reference images
        diff/                  # Failure diffs
        manifest.json          # Screenshot manifest
```

### Screenshot Naming
`{page}_{viewport}_{timestamp}.png` → normalized to `{page}_{viewport}.png` for baseline

### Comparison Strategy
- Pixel-perfect comparison with 0.1% tolerance
- Mask dynamic regions: timestamps, telemetry values, session IDs
- Fail on layout changes, not content changes

---

## 9. Console Error Collection

```python
# In conftest.py - page fixture
page.on("console", lambda msg: collect_console_error(msg))
page.on("pageerror", lambda exc: collect_page_error(exc))
```

Filter out:
- Streamlit development warnings
- Source map loading failures
- Favicon 404s

Flag as test failure:
- Uncaught JavaScript exceptions
- Failed resource loads (CSS, JS, images)
- Plotly rendering errors
- WebSocket connection failures

---

## 10. Limitations & Known Gaps

| Limitation | Impact | Mitigation |
|---|---|---|
| Standalone pages need separate Streamlit processes | 4 additional ports | Launch subprocesses in fixture setup |
| Streamlit WebSocket reconnection on viewport resize | May cause reruns | Set viewport before navigation, wait for stability |
| Dynamic telemetry data | Screenshot flakiness | Mask telemetry values, use simulation mode |
| LM Studio unavailable | AI status shows disconnected | Expected — test layout only |
| No real OBD hardware | OBD page shows simulation | Expected — test layout only |

---

## 11. Next Steps

1. Create `requirements-dev.txt`
2. Install Playwright + Chromium
3. Create `tests/browser/conftest.py` with fixtures
4. Implement viewport parametrization
5. Create test entry points for standalone reports
6. Write responsive assertion library
7. Execute 91-combination matrix
8. Capture screenshots
9. Fix verified defects
10. Run full regression (415 tests)
11. Document results

---

*Setup document created 2026-11-18 — Ready for implementation*