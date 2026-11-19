#!/usr/bin/env python
"""
Responsive Test Runner - Runs all 91 viewport/page combinations
without pytest parametrization to avoid multiple app startups.
"""

import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

import pytest
from playwright.sync_api import sync_playwright, Page, BrowserContext

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# Configuration
# =============================================================================

@dataclass
class ViewportConfig:
    name: str
    width: int
    height: int
    is_mobile: bool = False
    has_touch: bool = False

VIEWPORTS: List[ViewportConfig] = [
    ViewportConfig("desktop", 1440, 900, is_mobile=False),
    ViewportConfig("laptop", 1100, 800, is_mobile=False),
    ViewportConfig("tablet", 900, 768, is_mobile=True, has_touch=True),
    ViewportConfig("tablet_portrait", 768, 1024, is_mobile=True, has_touch=True),
    ViewportConfig("mobile", 390, 844, is_mobile=True, has_touch=True),
    ViewportConfig("mobile_small", 360, 800, is_mobile=True, has_touch=True),
    ViewportConfig("mobile_minimum", 320, 700, is_mobile=True, has_touch=True),
]

VIEWPORT_NAMES = [v.name for v in VIEWPORTS]
VIEWPORT_MAP = {v.name: v for v in VIEWPORTS}

@dataclass
class PageDestination:
    key: str
    name: str
    url_path: str
    is_standalone: bool = False
    standalone_port: Optional[int] = None

MAIN_PAGES: List[PageDestination] = [
    PageDestination("dashboard", "Dashboard", "?page=dashboard"),
    PageDestination("diagnostics", "Diagnostics", "?page=diagnostics"),
    PageDestination("performance", "Performance", "?page=performance"),
    PageDestination("maintenance", "Maintenance", "?page=maintenance"),
    PageDestination("vehicle_profile", "Vehicle Profile", "?page=vehicle_profile"),
    PageDestination("ai_assistant", "AI Assistant", "?page=ai_assistant"),
    PageDestination("obd_connection", "OBD Connection", "?page=obd_connection"),
    PageDestination("reports", "Reports", "?page=reports"),
    PageDestination("settings", "Settings", "?page=settings"),
]

STANDALONE_PAGES: List[PageDestination] = [
    PageDestination("diagnostic_report", "Diagnostic Report", "", is_standalone=True, standalone_port=8502),
    PageDestination("vehicle_health_report", "Vehicle Health Report", "", is_standalone=True, standalone_port=8503),
    PageDestination("performance_report", "Performance Report", "", is_standalone=True, standalone_port=8504),
    PageDestination("maintenance_report", "Maintenance Report", "", is_standalone=True, standalone_port=8505),
]

ALL_PAGES = MAIN_PAGES + STANDALONE_PAGES

SCREENSHOT_DIR = PROJECT_ROOT / "artifacts" / "phase_6_stage_6" / "screenshots"


# =============================================================================
# App Manager
# =============================================================================

class AppManager:
    def __init__(self):
        self.main_process: Optional[subprocess.Popen] = None
        self.standalone_processes: Dict[int, subprocess.Popen] = {}
        self.temp_db_path: Optional[Path] = None
        self.base_url = "http://localhost:8501"
        self.standalone_urls = {
            "diagnostic_report": "http://localhost:8502",
            "vehicle_health_report": "http://localhost:8503",
            "performance_report": "http://localhost:8504",
            "maintenance_report": "http://localhost:8505",
        }

    def create_temp_database(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="i20_test_"))
        db_path = temp_dir / "test_i20_garage.db"
        self.temp_db_path = db_path
        return db_path

    def start_all_apps(self):
        """Start all Streamlit apps."""
        if not self.temp_db_path:
            self.create_temp_database()

        # Create standalone scripts
        scripts_dir = PROJECT_ROOT / "tests" / "browser" / "fixtures" / "standalone_scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)

        STANDALONE_SCRIPTS = {
            "diagnostic_report": "from modules.reports import render_diagnostic_report_page\nrender_diagnostic_report_page()",
            "vehicle_health_report": "from modules.reports import render_vehicle_health_report_page\nrender_vehicle_health_report_page()",
            "performance_report": "from modules.reports import render_performance_report_page\nrender_performance_report_page()",
            "maintenance_report": "from modules.reports import render_maintenance_report_page\nrender_maintenance_report_page()",
        }

        for key, content in STANDALONE_SCRIPTS.items():
            script_path = scripts_dir / f"{key}.py"
            full_content = f"import streamlit as st\n{content}"
            script_path.write_text(full_content)

        # Start main app
        print(f"Starting main app on port 8501...")
        self.main_process = self._start_streamlit(PROJECT_ROOT / "app.py", 8501, self.temp_db_path)
        self._wait_for_app("http://localhost:8501")
        print("Main app ready!")

        # Start standalone apps
        for key, port in self.standalone_urls.items():
            port_num = port.split(":")[-1]
            print(f"Starting {key} on port {port_num}...")
            script_path = scripts_dir / f"{key}.py"
            self.standalone_processes[port_num] = self._start_streamlit(script_path, int(port_num), self.temp_db_path)
            self._wait_for_app(f"http://localhost:{port_num}")
            print(f"{key} ready!")

        print("\nAll apps started successfully!")

    def _start_streamlit(self, script_path: Path, port: int, db_path: Path) -> subprocess.Popen:
        env = os.environ.copy()
        env["DATABASE_PATH"] = str(db_path)
        env["OBD_MODE"] = "simulation"
        env["STREAMLIT_SERVER_HEADLESS"] = "true"
        env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

        cmd = [
            sys.executable, "-m", "streamlit", "run", str(script_path),
            f"--server.port={port}",
            "--server.address=localhost",
            "--server.headless=true",
        ]

        # Use DEVNULL to avoid pipe buffer issues
        return subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def _wait_for_app(self, url: str, timeout: int = 120):
        import requests
        start = time.time()
        while time.time() - start < timeout:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    time.sleep(3)
                    return
            except requests.exceptions.RequestException:
                pass
            time.sleep(2)
        raise TimeoutError(f"Streamlit app at {url} did not start within {timeout}s")

    def stop_all(self):
        if self.main_process:
            self.main_process.terminate()
            try:
                self.main_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.main_process.kill()

        for proc in self.standalone_processes.values():
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        if self.temp_db_path and self.temp_db_path.exists():
            try:
                self.temp_db_path.unlink()
                self.temp_db_path.parent.rmdir()
            except Exception:
                pass


# =============================================================================
# Responsive Checks
# =============================================================================

def check_page_overflow(page: Page) -> dict:
    return page.evaluate("""
        () => {
            const docWidth = document.documentElement.scrollWidth;
            const viewportWidth = window.innerWidth;
            const overflow = docWidth - viewportWidth;
            return { doc_width: docWidth, viewport_width: viewportWidth, overflow: overflow, pass: overflow <= 1 };
        }
    """)

def check_main_content_visible(page: Page) -> dict:
    return page.evaluate("""
        () => {
            const main = document.querySelector('main#main-content, .i20-page-container, [data-testid="stMain"], .main');
            if (!main) return { visible: false, reason: "Main content not found" };
            const rect = main.getBoundingClientRect();
            const style = window.getComputedStyle(main);
            return { visible: rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden', bbox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height }, clipped: rect.right > window.innerWidth || rect.bottom > window.innerHeight };
        }
    """)

def check_responsive_grids(page: Page) -> list:
    return page.evaluate("""
        () => {
            const grids = document.querySelectorAll('[style*="auto-fit"], [style*="auto-fill"], .i20-grid, .stHorizontalBlock');
            return Array.from(grids).map(grid => {
                const rect = grid.getBoundingClientRect();
                const children = Array.from(grid.children);
                const childRects = children.map(c => c.getBoundingClientRect());
                return { grid_width: rect.width, grid_height: rect.height, child_count: children.length, children_in_bounds: childRects.every(c => c.left >= rect.left - 1 && c.right <= rect.right + 1), overflows_viewport: rect.right > window.innerWidth };
            });
        }
    """)

def check_touch_targets(page: Page, min_size: int = 44) -> list:
    return page.evaluate(f"""
        () => {{
            const interactive = document.querySelectorAll('button, a, input, select, textarea, [role="button"], .stButton button, .stSelectbox, .stTextInput input, .stCheckbox');
            return Array.from(interactive).map(el => {{
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                const isVisible = rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                return {{ tag: el.tagName.toLowerCase(), class: el.className, width: Math.round(rect.width), height: Math.round(rect.height), pass: isVisible && rect.width >= {min_size} && rect.height >= {min_size}, visible: isVisible }};
            }});
        }}
    """)

def check_table_scroll(page: Page) -> list:
    return page.evaluate("""
        () => {
            const tables = document.querySelectorAll('table, .i20-table-wrapper, .stTable');
            return Array.from(tables).map(table => {
                const rect = table.getBoundingClientRect();
                const scrollWidth = table.scrollWidth;
                const clientWidth = table.clientWidth;
                const hasHorizontalScroll = scrollWidth > clientWidth;
                return { has_horizontal_scroll: hasHorizontalScroll, table_width: Math.round(clientWidth), content_width: Math.round(scrollWidth), overflows_page: rect.right > window.innerWidth, in_bounds: rect.right <= window.innerWidth };
            });
        }
    """)

def check_charts_in_bounds(page: Page) -> list:
    return page.evaluate("""
        () => {
            const charts = document.querySelectorAll('.js-plotly-plot, .plotly-graph-div, [data-testid="stPlotlyChart"]');
            return Array.from(charts).map(chart => {
                const rect = chart.getBoundingClientRect();
                const parent = chart.parentElement;
                const parentRect = parent ? parent.getBoundingClientRect() : null;
                return { chart_width: Math.round(rect.width), chart_height: Math.round(rect.height), parent_width: parentRect ? Math.round(parentRect.width) : null, overflows_parent: parentRect && rect.right > parentRect.right, overflows_viewport: rect.right > window.innerWidth };
            });
        }
    """)

def check_forms_visible(page: Page) -> list:
    return page.evaluate("""
        () => {
            const forms = document.querySelectorAll('form, .stForm, .i20-field');
            return Array.from(forms).map(form => {
                const inputs = form.querySelectorAll('input, select, textarea');
                return Array.from(inputs).map(input => {
                    const rect = input.getBoundingClientRect();
                    const label = form.querySelector(`label[for="${input.id}"]`) || input.closest('label');
                    return { type: input.type || input.tagName.toLowerCase(), width: Math.round(rect.width), height: Math.round(rect.height), has_label: !!label, visible: rect.width > 0 && rect.height > 0, in_viewport: rect.right <= window.innerWidth && rect.bottom <= window.innerHeight };
                });
            }).flat();
        }
    """)

def check_mobile_navigation(page: Page) -> dict:
    return page.evaluate("""
        () => {
            const drawer = document.querySelector('.i20-sidebar-drawer, [data-testid="stSidebar"]');
            const toggle = document.querySelector('.i20-top-bar-mobile-menu, button[aria-label*="menu" i], button[aria-label*="Menu" i]');
            const backdrop = document.querySelector('.i20-sidebar-backdrop');
            return { has_drawer: !!drawer, has_toggle: !!toggle, has_backdrop: !!backdrop, drawer_visible: drawer ? window.getComputedStyle(drawer).display !== 'none' : false, toggle_visible: toggle ? window.getComputedStyle(toggle).display !== 'none' : false };
        }
    """)

def collect_console_errors(page: Page) -> list:
    return getattr(page, 'console_errors', [])

def collect_page_errors(page: Page) -> list:
    return getattr(page, 'page_errors', [])

def capture_screenshot(page: Page, page_key: str, viewport_name: str, suffix: str = "") -> Path:
    viewport_dir = SCREENSHOT_DIR / viewport_name
    viewport_dir.mkdir(parents=True, exist_ok=True)
    suffix_str = f"_{suffix}" if suffix else ""
    path = viewport_dir / f"{page_key}{suffix_str}.png"
    page.wait_for_timeout(1000)
    page.screenshot(path=path, full_page=True)
    return path


# =============================================================================
# Navigation
# =============================================================================

def navigate_to_page(page: Page, base_url: str, standalone_urls: dict, page_dest: PageDestination) -> str:
    if page_dest.is_standalone:
        url = standalone_urls.get(page_dest.key, f"http://localhost:{page_dest.standalone_port}")
        page.goto(url, wait_until="networkidle")
    else:
        url = f"{base_url}{page_dest.url_path}"
        page.goto(url, wait_until="networkidle")
        if "page=" in page_dest.url_path:
            sidebar_item = page.locator(f"button:has-text('{page_dest.name}'), [data-page='{page_dest.key}']").first
            if sidebar_item.count() > 0:
                sidebar_item.click()
                page.wait_for_timeout(500)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    return page.url


# =============================================================================
# Test Runner
# =============================================================================

def run_tests():
    app_manager = AppManager()
    results = {
        "passed": 0,
        "failed": 0,
        "errors": [],
        "screenshots": []
    }

    try:
        # Start all apps
        app_manager.start_all_apps()

        # Run Playwright tests
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for page_dest in ALL_PAGES:
                print(f"\n{'='*60}")
                print(f"Testing page: {page_dest.key} ({page_dest.name})")
                print(f"{'='*60}")

                for vp in VIEWPORTS:
                    print(f"\n  Viewport: {vp.name} ({vp.width}x{vp.height})")

                    context = browser.new_context(
                        viewport={"width": vp.width, "height": vp.height},
                        is_mobile=vp.is_mobile,
                        has_touch=vp.has_touch,
                    )

                    pw_page = context.new_page()
                    pw_page.console_errors = []
                    pw_page.page_errors = []

                    def handle_console(msg):
                        if msg.type in ("error", "warning"):
                            pw_page.console_errors.append({"type": msg.type, "text": msg.text})

                    def handle_page_error(exc):
                        pw_page.page_errors.append({"message": str(exc)})

                    pw_page.on("console", handle_console)
                    pw_page.on("pageerror", handle_page_error)

                    try:
                        # Navigate
                        navigate_to_page(pw_page, app_manager.base_url, app_manager.standalone_urls, page_dest)

                        # Check console errors
                        console_errors = collect_console_errors(pw_page)
                        critical_errors = [e for e in console_errors if e["type"] == "error" and "favicon" not in e["text"].lower() and "source map" not in e["text"].lower()]
                        if critical_errors:
                            raise AssertionError(f"Console errors: {critical_errors}")

                        # Check overflow
                        overflow = check_page_overflow(pw_page)
                        if not overflow["pass"]:
                            raise AssertionError(f"Horizontal overflow: {overflow['overflow']}px")

                        # Check main content
                        content = check_main_content_visible(pw_page)
                        if not content["visible"]:
                            raise AssertionError(f"Main content not visible: {content.get('reason')}")

                        # Check responsive grids
                        grids = check_responsive_grids(pw_page)
                        for i, grid in enumerate(grids):
                            if not grid.get("children_in_bounds", True):
                                raise AssertionError(f"Grid {i} children overflow viewport")

                        # Check touch targets (mobile only)
                        if vp.has_touch:
                            targets = check_touch_targets(pw_page, 44)
                            visible = [t for t in targets if t["visible"]]
                            failing = [t for t in visible if not t["pass"]]
                            if len(visible) > 0:
                                fail_rate = len(failing) / len(visible)
                                if fail_rate >= 0.3:
                                    raise AssertionError(f"Touch target failure rate {fail_rate:.0%}: {len(failing)}/{len(visible)}")

                        # Check table scroll
                        tables = check_table_scroll(pw_page)
                        for i, table in enumerate(tables):
                            if table.get("overflows_page"):
                                raise AssertionError(f"Table {i} overflows page")

                        # Check charts
                        charts = check_charts_in_bounds(pw_page)
                        for i, chart in enumerate(charts):
                            if chart.get("overflows_viewport"):
                                raise AssertionError(f"Chart {i} overflows viewport")

                        # Check forms
                        forms = check_forms_visible(pw_page)
                        for i, form in enumerate(forms):
                            if not form.get("in_viewport"):
                                raise AssertionError(f"Form {i} outside viewport")

                        # Capture screenshot
                        screenshot_path = capture_screenshot(pw_page, page_dest.key, vp.name)
                        results["screenshots"].append(str(screenshot_path))
                        print(f"    [OK] Screenshot saved: {screenshot_path}")

                        results["passed"] += 1
                        print(f"    [PASS] PASSED")

                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(f"{page_dest.key} @ {vp.name}: {e}")
                        print(f"    [FAIL] FAILED: {e}")
                    finally:
                        pw_page.close()
                        context.close()

            browser.close()

    finally:
        print("\nStopping all apps...")
        app_manager.stop_all()

    # Print summary
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Screenshots: {len(results['screenshots'])}")

    if results["errors"]:
        print(f"\nFAILURES:")
        for err in results["errors"]:
            print(f"  - {err}")

    return results


if __name__ == "__main__":
    run_tests()