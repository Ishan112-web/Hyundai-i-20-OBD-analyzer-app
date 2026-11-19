"""
Playwright Browser Test Configuration for i20 AI Garage
Phase 6 Stage 6: Responsive Verification
"""

import os
import sys
from pathlib import Path
from typing import Generator, Dict, List, Optional
from dataclasses import dataclass

import pytest
from playwright.sync_api import Page, BrowserContext

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# =============================================================================
# Viewport Configuration
# =============================================================================

@dataclass
class ViewportConfig:
    name: str
    width: int
    height: int
    device_scale_factor: float = 1.0
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

# =============================================================================
# Page Destinations
# =============================================================================

@dataclass
class PageDestination:
    key: str
    name: str
    url_path: str  # For main app: query param or session state; for standalone: separate port
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
ALL_PAGE_KEYS = [p.key for p in ALL_PAGES]

# =============================================================================
# Test Application Manager
# =============================================================================

class TestAppManager:
    """Connects to pre-running Streamlit applications."""

    def __init__(self):
        self.base_url = "http://localhost:8501"
        self.standalone_urls = {
            "diagnostic_report": "http://localhost:8502",
            "vehicle_health_report": "http://localhost:8503",
            "performance_report": "http://localhost:8504",
            "maintenance_report": "http://localhost:8505",
        }

    def verify_apps_running(self) -> bool:
        """Verify all apps are running."""
        import requests

        # Check main app
        try:
            resp = requests.get(self.base_url, timeout=5)
            if resp.status_code != 200:
                return False
        except requests.exceptions.RequestException:
            return False

        # Check standalone apps
        for url in self.standalone_urls.values():
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code != 200:
                    return False
            except requests.exceptions.RequestException:
                return False

        return True

    def get_base_url(self) -> str:
        return self.base_url

    def get_standalone_urls(self) -> Dict[str, str]:
        return self.standalone_urls


# Global app manager instance
_app_manager: Optional[TestAppManager] = None


def get_app_manager() -> TestAppManager:
    global _app_manager
    if _app_manager is None:
        _app_manager = TestAppManager()
    return _app_manager


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture(scope="session")
def app_manager() -> Generator[TestAppManager, None, None]:
    """Session-scoped application manager - connects to pre-running apps."""
    manager = get_app_manager()

    # Verify apps are running
    if not manager.verify_apps_running():
        pytest.skip("Streamlit apps not running. Run tests/browser/start_apps.py first.")

    yield manager


@pytest.fixture(scope="session")
def base_url(app_manager: TestAppManager) -> str:
    """Base URL for main application."""
    return app_manager.get_base_url()


@pytest.fixture(scope="session")
def standalone_urls(app_manager: TestAppManager) -> Dict[str, str]:
    """URLs for standalone report pages."""
    return app_manager.get_standalone_urls()


@pytest.fixture(scope="function")
def browser_context_args(browser_context_args: dict, viewport_name: str) -> dict:
    """Configure browser context for each viewport."""
    vp = VIEWPORT_MAP[viewport_name]
    return {
        **browser_context_args,
        "viewport": {"width": vp.width, "height": vp.height},
        "device_scale_factor": vp.device_scale_factor,
        "is_mobile": vp.is_mobile,
        "has_touch": vp.has_touch,
    }


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Create a new page for each test."""
    page = context.new_page()

    # Collect console errors
    page.console_errors = []
    page.page_errors = []

    def handle_console(msg):
        if msg.type in ("error", "warning"):
            page.console_errors.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
            })

    def handle_page_error(exc):
        page.page_errors.append({
            "message": str(exc),
            "stack": exc.stack if hasattr(exc, 'stack') else None,
        })

    page.on("console", handle_console)
    page.on("pageerror", handle_page_error)

    yield page

    page.close()


@pytest.fixture(scope="function")
def viewport_name(request) -> str:
    """Get viewport name from parametrization."""
    return request.param if hasattr(request, 'param') else "desktop"


@pytest.fixture
def current_viewport(viewport_name: str) -> ViewportConfig:
    """Get current viewport configuration."""
    return VIEWPORT_MAP[viewport_name]


# =============================================================================
# Navigation Helpers
# =============================================================================

def navigate_to_page(page: Page, base_url: str, page_key: str, standalone_urls: Dict[str, str] = None) -> str:
    """Navigate to a specific page and wait for it to load."""
    page_dest = next((p for p in ALL_PAGES if p.key == page_key), None)
    if not page_dest:
        raise ValueError(f"Unknown page: {page_key}")

    if page_dest.is_standalone:
        url = standalone_urls.get(page_key, f"http://localhost:{page_dest.standalone_port}")
        page.goto(url, wait_until="networkidle")
    else:
        # For main app, we need to set the page via session state or URL
        # Streamlit uses session state for navigation, so we may need to use the sidebar
        url = f"{base_url}{page_dest.url_path}"
        page.goto(url, wait_until="networkidle")

        # If using session state navigation, click the sidebar item
        if "page=" in page_dest.url_path:
            # Try to click the navigation item in sidebar
            sidebar_item = page.locator(f"button:has-text('{page_dest.name}'), [data-page='{page_key}']").first
            if sidebar_item.count() > 0:
                sidebar_item.click()
                page.wait_for_timeout(500)

    # Wait for page to stabilize
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)  # Allow Streamlit to fully render

    return page.url


# =============================================================================
# Screenshot Utilities
# =============================================================================

SCREENSHOT_DIR = PROJECT_ROOT / "artifacts" / "phase_6_stage_6" / "screenshots"

def get_screenshot_path(page_key: str, viewport_name: str, suffix: str = "") -> Path:
    """Generate screenshot file path."""
    viewport_dir = SCREENSHOT_DIR / viewport_name
    viewport_dir.mkdir(parents=True, exist_ok=True)
    suffix_str = f"_{suffix}" if suffix else ""
    return viewport_dir / f"{page_key}{suffix_str}.png"


def capture_screenshot(page: Page, page_key: str, viewport_name: str, suffix: str = "") -> Path:
    """Capture a full-page screenshot."""
    path = get_screenshot_path(page_key, viewport_name, suffix)

    # Wait for fonts and charts to render
    page.wait_for_timeout(1000)

    page.screenshot(path=path, full_page=True)
    return path


# =============================================================================
# Responsive Assertions
# =============================================================================

def check_page_overflow(page: Page) -> dict:
    """Detect unintended document-level horizontal overflow."""
    result = page.evaluate("""
        () => {
            const docWidth = document.documentElement.scrollWidth;
            const viewportWidth = window.innerWidth;
            const overflow = docWidth - viewportWidth;
            return {
                doc_width: docWidth,
                viewport_width: viewportWidth,
                overflow: overflow,
                pass: overflow <= 1
            };
        }
    """)
    return result


def check_main_content_visible(page: Page) -> dict:
    """Verify main content area is visible and not obscured."""
    result = page.evaluate("""
        () => {
            const main = document.querySelector('main#main-content, .i20-page-container, [data-testid="stMain"], .main');
            if (!main) return { visible: false, reason: "Main content not found" };
            const rect = main.getBoundingClientRect();
            const style = window.getComputedStyle(main);
            return {
                visible: rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden',
                bbox: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                clipped: rect.right > window.innerWidth || rect.bottom > window.innerHeight
            };
        }
    """)
    return result


def check_responsive_grids(page: Page) -> list:
    """Verify grid containers adapt to viewport."""
    return page.evaluate("""
        () => {
            const grids = document.querySelectorAll('[style*="auto-fit"], [style*="auto-fill"], .i20-grid, .stHorizontalBlock');
            return Array.from(grids).map(grid => {
                const rect = grid.getBoundingClientRect();
                const children = Array.from(grid.children);
                const childRects = children.map(c => c.getBoundingClientRect());
                return {
                    grid_width: rect.width,
                    grid_height: rect.height,
                    child_count: children.length,
                    children_in_bounds: childRects.every(c => c.left >= rect.left - 1 && c.right <= rect.right + 1),
                    overflows_viewport: rect.right > window.innerWidth
                };
            });
        }
    """)


def check_touch_targets(page: Page, min_size: int = 44) -> list:
    """Check interactive elements meet minimum touch target size."""
    return page.evaluate(f"""
        () => {{
            const interactive = document.querySelectorAll('button, a, input, select, textarea, [role="button"], .stButton button, .stSelectbox, .stTextInput input, .stCheckbox');
            return Array.from(interactive).map(el => {{
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                const isVisible = rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
                return {{
                    tag: el.tagName.toLowerCase(),
                    class: el.className,
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    pass: isVisible && rect.width >= {min_size} && rect.height >= {min_size},
                    visible: isVisible
                }};
            }});
        }}
    """)


def check_table_scroll(page: Page) -> list:
    """Verify tables have internal horizontal scroll without page overflow."""
    return page.evaluate("""
        () => {
            const tables = document.querySelectorAll('table, .i20-table-wrapper, .stTable');
            return Array.from(tables).map(table => {
                const rect = table.getBoundingClientRect();
                const scrollWidth = table.scrollWidth;
                const clientWidth = table.clientWidth;
                const hasHorizontalScroll = scrollWidth > clientWidth;
                return {
                    has_horizontal_scroll: hasHorizontalScroll,
                    table_width: Math.round(clientWidth),
                    content_width: Math.round(scrollWidth),
                    overflows_page: rect.right > window.innerWidth,
                    in_bounds: rect.right <= window.innerWidth
                };
            });
        }
    """)


def check_charts_in_bounds(page: Page) -> list:
    """Verify Plotly charts stay within containers."""
    return page.evaluate("""
        () => {
            const charts = document.querySelectorAll('.js-plotly-plot, .plotly-graph-div, [data-testid="stPlotlyChart"]');
            return Array.from(charts).map(chart => {
                const rect = chart.getBoundingClientRect();
                const parent = chart.parentElement;
                const parentRect = parent ? parent.getBoundingClientRect() : null;
                return {
                    chart_width: Math.round(rect.width),
                    chart_height: Math.round(rect.height),
                    parent_width: parentRect ? Math.round(parentRect.width) : null,
                    overflows_parent: parentRect && rect.right > parentRect.right,
                    overflows_viewport: rect.right > window.innerWidth
                };
            });
        }
    """)


def check_forms_visible(page: Page) -> list:
    """Verify form inputs and labels are visible and accessible."""
    return page.evaluate("""
        () => {
            const forms = document.querySelectorAll('form, .stForm, .i20-field');
            return Array.from(forms).map(form => {
                const inputs = form.querySelectorAll('input, select, textarea');
                return Array.from(inputs).map(input => {
                    const rect = input.getBoundingClientRect();
                    const label = form.querySelector(`label[for="${input.id}"]`) || input.closest('label');
                    return {
                        type: input.type || input.tagName.toLowerCase(),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        has_label: !!label,
                        visible: rect.width > 0 && rect.height > 0,
                        in_viewport: rect.right <= window.innerWidth && rect.bottom <= window.innerHeight
                    };
                });
            }).flat();
        }
    """)


def check_mobile_navigation(page: Page) -> dict:
    """Verify mobile navigation drawer behavior."""
    return page.evaluate("""
        () => {
            const drawer = document.querySelector('.i20-sidebar-drawer, [data-testid="stSidebar"]');
            const toggle = document.querySelector('.i20-top-bar-mobile-menu, button[aria-label*="menu" i], button[aria-label*="Menu" i]');
            const backdrop = document.querySelector('.i20-sidebar-backdrop');

            return {
                has_drawer: !!drawer,
                has_toggle: !!toggle,
                has_backdrop: !!backdrop,
                drawer_visible: drawer ? window.getComputedStyle(drawer).display !== 'none' : false,
                toggle_visible: toggle ? window.getComputedStyle(toggle).display !== 'none' : false
            };
        }
    """)


def collect_console_errors(page: Page) -> list:
    """Collect browser console errors."""
    return getattr(page, 'console_errors', [])


def collect_page_errors(page: Page) -> list:
    """Collect page JavaScript errors."""
    return getattr(page, 'page_errors', [])


# =============================================================================
# Pytest Configuration
# =============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "viewport: mark test as viewport-specific")
    config.addinivalue_line("markers", "standalone: mark test for standalone report pages")
    config.addinivalue_line("markers", "main: mark test for main app pages")
    config.addinivalue_line("markers", "slow: mark test as slow")


# Make viewport configs available to tests
pytest.VIEWPORTS = VIEWPORTS
pytest.VIEWPORT_NAMES = VIEWPORT_NAMES
pytest.ALL_PAGES = ALL_PAGES
pytest.MAIN_PAGES = MAIN_PAGES
pytest.STANDALONE_PAGES = STANDALONE_PAGES