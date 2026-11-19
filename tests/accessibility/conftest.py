"""
Accessibility Test Configuration - Playwright fixtures and viewport configs
"""
import pytest
from playwright.sync_api import sync_playwright, Page, BrowserContext, Browser
from typing import Generator, Dict, Any
from dataclasses import dataclass

# Viewport configurations matching Stage 6
VIEWPORTS = [
    {"name": "desktop", "width": 1440, "height": 900, "is_mobile": False},
    {"name": "laptop", "width": 1100, "height": 800, "is_mobile": False},
    {"name": "tablet", "width": 900, "height": 768, "is_mobile": True, "has_touch": True},
    {"name": "tablet_portrait", "width": 768, "height": 1024, "is_mobile": True, "has_touch": True},
    {"name": "mobile", "width": 390, "height": 844, "is_mobile": True, "has_touch": True},
    {"name": "mobile_small", "width": 360, "height": 800, "is_mobile": True, "has_touch": True},
    {"name": "mobile_minimum", "width": 320, "height": 700, "is_mobile": True, "has_touch": True},
]

# Main pages (use query param for navigation)
MAIN_PAGES = [
    {"key": "dashboard", "name": "Dashboard", "url_path": "?page=dashboard"},
    {"key": "diagnostics", "name": "Diagnostics", "url_path": "?page=diagnostics"},
    {"key": "performance", "name": "Performance", "url_path": "?page=performance"},
    {"key": "maintenance", "name": "Maintenance", "url_path": "?page=maintenance"},
    {"key": "vehicle_profile", "name": "Vehicle Profile", "url_path": "?page=vehicle_profile"},
    {"key": "ai_assistant", "name": "AI Assistant", "url_path": "?page=ai_assistant"},
    {"key": "obd_connection", "name": "OBD Connection", "url_path": "?page=obd_connection"},
    {"key": "reports", "name": "Reports", "url_path": "?page=reports"},
    {"key": "settings", "name": "Settings", "url_path": "?page=settings"},
]

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="session")
def browser() -> Generator[Browser, None, None]:
    """Session-scoped browser fixture."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


@pytest.fixture(scope="function")
def context(browser: Browser, viewport: Dict[str, Any]) -> Generator[BrowserContext, None, None]:
    """Function-scoped context with specific viewport."""
    context = browser.new_context(
        viewport={"width": viewport["width"], "height": viewport["height"]},
        is_mobile=viewport.get("is_mobile", False),
        has_touch=viewport.get("has_touch", False),
    )
    yield context
    context.close()


@pytest.fixture(scope="function")
def page(context: BrowserContext) -> Generator[Page, None, None]:
    """Function-scoped page fixture."""
    page = context.new_page()
    page.console_errors = []
    page.page_errors = []

    def handle_console(msg):
        if msg.type in ("error", "warning"):
            page.console_errors.append({"type": msg.type, "text": msg.text})

    def handle_page_error(exc):
        page.page_errors.append({"message": str(exc)})

    page.on("console", handle_console)
    page.on("pageerror", handle_page_error)

    yield page
    page.close()


@pytest.fixture(params=VIEWPORTS)
def viewport(request) -> Dict[str, Any]:
    """Parameterized viewport fixture."""
    return request.param


@pytest.fixture(params=MAIN_PAGES)
def page_dest(request) -> Dict[str, Any]:
    """Parameterized page destination fixture."""
    return request.param


def navigate_to_page(page: Page, page_dest: Dict[str, Any]) -> str:
    """Navigate to a page and wait for load."""
    url = f"{BASE_URL}{page_dest['url_path']}"
    page.goto(url, wait_until="networkidle")
    # Click sidebar item if present
    if "page=" in page_dest["url_path"]:
        sidebar_item = page.locator(f"button:has-text('{page_dest['name']}'), [data-page='{page_dest['key']}']").first
        if sidebar_item.count() > 0:
            sidebar_item.click()
            page.wait_for_timeout(500)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    return page.url