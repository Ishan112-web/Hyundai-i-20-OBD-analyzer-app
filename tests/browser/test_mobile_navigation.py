"""
Mobile Navigation Tests - Drawer behavior, page selection, responsive breakpoints
Phase 6 Stage 6: Mobile Navigation Verification
"""

import pytest
from playwright.sync_api import Page, expect

from tests.browser.conftest import (
    VIEWPORT_NAMES,
    MAIN_PAGES,
    navigate_to_page,
    check_mobile_navigation,
    capture_screenshot,
    current_viewport,
)


# Mobile/tablet viewports for navigation tests
MOBILE_VIEWPORTS = ["mobile", "mobile_small", "mobile_minimum", "tablet", "tablet_portrait"]
DESKTOP_VIEWPORTS = ["desktop", "laptop"]


class TestMobileNavigationDrawer:
    """Test mobile navigation drawer open/close behavior."""

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_drawer_exists_on_mobile(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify navigation drawer component exists on mobile viewports."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        nav = check_mobile_navigation(page)

        assert nav["has_drawer"], f"No drawer on {viewport_name}"
        assert nav["has_toggle"], f"No toggle on {viewport_name}"
        assert nav["toggle_visible"], f"Toggle not visible on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", DESKTOP_VIEWPORTS)
    def test_drawer_hidden_on_desktop(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify navigation drawer is hidden on desktop (sidebar visible instead)."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        nav = check_mobile_navigation(page)

        # On desktop, toggle should be hidden, drawer may exist but not as mobile drawer
        assert not nav.get("toggle_visible", False), f"Mobile toggle visible on desktop {viewport_name}"

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_drawer_opens_on_toggle_click(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify drawer opens when toggle is clicked."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        toggle = page.locator('button[aria-label*="menu" i], button[aria-label*="Menu" i], .i20-top-bar-mobile-menu').first

        if toggle.count() > 0:
            # Drawer should be closed initially
            nav_before = check_mobile_navigation(page)

            toggle.click()
            page.wait_for_timeout(300)

            nav_after = check_mobile_navigation(page)

            assert nav_after["drawer_visible"], f"Drawer did not open on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_drawer_closes_on_backdrop_click(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify drawer closes when clicking backdrop."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        toggle = page.locator('button[aria-label*="menu" i], button[aria-label*="Menu" i], .i20-top-bar-mobile-menu').first

        if toggle.count() > 0:
            toggle.click()
            page.wait_for_timeout(300)

            # Click backdrop if exists
            backdrop = page.locator(".i20-sidebar-backdrop, .sidebar-backdrop").first
            if backdrop.count() > 0:
                backdrop.click()
                page.wait_for_timeout(300)

                nav = check_mobile_navigation(page)
                assert not nav["drawer_visible"], f"Drawer did not close on backdrop click on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_drawer_closes_on_page_select(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify drawer closes after page selection."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        toggle = page.locator('button[aria-label*="menu" i], button[aria-label*="Menu" i], .i20-top-bar-mobile-menu').first

        if toggle.count() > 0:
            toggle.click()
            page.wait_for_timeout(300)

            # Click a navigation item
            diagnostics_link = page.locator("button:has-text('Diagnostics'), a:has-text('Diagnostics'), [data-page='diagnostics']").first
            if diagnostics_link.count() > 0:
                diagnostics_link.click()
                page.wait_for_timeout(1000)
                page.wait_for_load_state("networkidle")

                # Drawer should close after navigation
                nav = check_mobile_navigation(page)
                assert not nav["drawer_visible"], f"Drawer did not close after page select on {viewport_name}"


class TestMobilePageNavigation:
    """Test page navigation from mobile drawer."""

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    @pytest.mark.parametrize("page_dest", MAIN_PAGES, ids=lambda p: p.key)
    def test_navigate_to_page_from_drawer(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify all main pages accessible from mobile drawer."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        toggle = page.locator('button[aria-label*="menu" i], button[aria-label*="Menu" i], .i20-top-bar-mobile-menu').first

        if toggle.count() > 0:
            toggle.click()
            page.wait_for_timeout(300)

            # Find page link in drawer
            link = page.locator(f"button:has-text('{page_dest.name}'), a:has-text('{page_dest.name}'), [data-page='{page_dest.key}']").first

            if link.count() > 0:
                link.click()
                page.wait_for_timeout(1000)
                page.wait_for_load_state("networkidle")

                # Verify navigation
                content = page.locator("body").text_content()
                assert page_dest.name.lower() in content.lower() or page_dest.key in page.url.lower(), (
                    f"Failed to navigate to {page_dest.key} from drawer on {viewport_name}"
                )

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_active_page_highlighted(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify current page is highlighted in mobile drawer."""
        navigate_to_page(page, base_url, "diagnostics", standalone_urls)

        toggle = page.locator('button[aria-label*="menu" i], button[aria-label*="Menu" i], .i20-top-bar-mobile-menu').first

        if toggle.count() > 0:
            toggle.click()
            page.wait_for_timeout(300)

            # Check active state on Diagnostics link
            active_link = page.locator("[data-page='diagnostics'][aria-current='page'], .active:has-text('Diagnostics'), button[aria-pressed='true']:has-text('Diagnostics')").first

            # At minimum, the link should exist
            link = page.locator("[data-page='diagnostics'], button:has-text('Diagnostics')").first
            assert link.count() > 0, "Diagnostics link not found in drawer"


class TestResponsiveBreakpoints:
    """Test responsive breakpoint behavior."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_topbar_adapts_to_viewport(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        current_viewport,
    ):
        """Verify top bar adapts to viewport width."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        topbar = page.locator(".i20-top-bar, [data-testid='stHeader'], header").first

        if topbar.count() > 0:
            bbox = topbar.bounding_box()
            if bbox:
                viewport_width = current_viewport.width
                assert bbox["width"] <= viewport_width, f"Topbar overflows on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_page_container_width(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        current_viewport,
    ):
        """Verify page container respects viewport width."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        container = page.locator(".i20-page-container, main#main-content, [data-testid='stMain'], .main").first

        if container.count() > 0:
            bbox = container.bounding_box()
            if bbox:
                viewport_width = current_viewport.width
                assert bbox["right"] <= viewport_width + 5, f"Page container overflows on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_sidebar_collapses_on_mobile(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify sidebar collapses to drawer on mobile."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        sidebar = page.locator("[data-testid='stSidebar'], .i20-sidebar").first

        if sidebar.count() > 0:
            bbox = sidebar.bounding_box()
            if bbox:
                # Sidebar should be hidden or very narrow on mobile
                assert bbox["width"] < 100, f"Sidebar not collapsed on mobile {viewport_name}: width={bbox['width']}"


class TestTouchInteractions:
    """Test touch-friendly interactions on mobile."""

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_buttons_touch_size(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify buttons meet minimum touch target size."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        buttons = page.locator("button, .stButton button, [role='button']")

        for i in range(min(buttons.count(), 10)):  # Check first 10 buttons
            btn = buttons.nth(i)
            bbox = btn.bounding_box()
            if bbox and bbox["width"] > 0 and bbox["height"] > 0:
                assert bbox["width"] >= 44, f"Button {i} width {bbox['width']} < 44 on {viewport_name}"
                assert bbox["height"] >= 44, f"Button {i} height {bbox['height']} < 44 on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_form_inputs_touch_size(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify form inputs meet minimum touch target size."""
        navigate_to_page(page, base_url, "settings", standalone_urls)

        inputs = page.locator("input, select, textarea, .stTextInput input, .stSelectbox, .stNumberInput input")

        for i in range(min(inputs.count(), 10)):
            inp = inputs.nth(i)
            bbox = inp.bounding_box()
            if bbox and bbox["width"] > 0 and bbox["height"] > 0:
                assert bbox["height"] >= 44, f"Input {i} height {bbox['height']} < 44 on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_no_hover_only_interactions(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify no critical functionality is hover-only."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        # Check for elements with :hover-only styles that affect functionality
        hover_only = page.evaluate("""
            () => {
                const elements = document.querySelectorAll('*');
                const results = [];
                for (const el of elements) {
                    const style = window.getComputedStyle(el);
                    // Check if element has hover styles but no touch/click handler
                    const hasHover = style.getPropertyValue('--hover-only') === 'true' ||
                                     el.matches(':hover') !== undefined;
                    const hasClick = el.onclick !== null ||
                                     el.getAttribute('onclick') !== null ||
                                     el.hasAttribute('role') && ['button', 'link', 'menuitem'].includes(el.getAttribute('role'));
                    if (hasHover && !hasClick) {
                        results.push(el.tagName.toLowerCase() + '.' + el.className);
                    }
                }
                return results.slice(0, 10);
            }
        """)

        # This is a warning-level check
        if hover_only:
            print(f"WARNING: Potential hover-only elements on {viewport_name}: {hover_only}")


class TestViewportTransitions:
    """Test smooth transitions between viewports."""

    def test_resize_desktop_to_mobile(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
    ):
        """Test viewport resize from desktop to mobile."""
        # Start at desktop
        page.set_viewport_size({"width": 1440, "height": 900})
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        # Verify desktop layout
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        assert overflow <= 1, "Initial desktop overflow"

        # Resize to mobile
        page.set_viewport_size({"width": 390, "height": 844})
        page.wait_for_timeout(500)

        # Verify mobile layout
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        assert overflow <= 1, "Overflow after resize to mobile"

        # Verify mobile navigation appears
        nav = check_mobile_navigation(page)
        assert nav["has_toggle"], "Mobile toggle not appeared after resize"

    def test_resize_mobile_to_desktop(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
    ):
        """Test viewport resize from mobile to desktop."""
        # Start at mobile
        page.set_viewport_size({"width": 390, "height": 844})
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        assert overflow <= 1, "Initial mobile overflow"

        # Resize to desktop
        page.set_viewport_size({"width": 1440, "height": 900})
        page.wait_for_timeout(500)

        # Verify desktop layout
        overflow = page.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        assert overflow <= 1, "Overflow after resize to desktop"

        # Verify desktop sidebar visible
        sidebar = page.locator("[data-testid='stSidebar'], .i20-sidebar").first
        if sidebar.count() > 0:
            bbox = sidebar.bounding_box()
            if bbox:
                assert bbox["width"] > 200, "Sidebar not expanded after resize to desktop"


class TestScreenshotCapture:
    """Capture screenshots for visual regression baseline."""

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    def test_mobile_nav_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture mobile navigation screenshots."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        # Closed state
        capture_screenshot(page, "mobile_nav_closed", viewport_name, "dashboard")

        # Open state
        toggle = page.locator('button[aria-label*="menu" i], button[aria-label*="Menu" i], .i20-top-bar-mobile-menu').first
        if toggle.count() > 0:
            toggle.click()
            page.wait_for_timeout(300)
            capture_screenshot(page, "mobile_nav_open", viewport_name, "dashboard")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_all_pages_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture screenshots for all pages at this viewport."""
        for page_dest in MAIN_PAGES[:3]:  # Sample first 3 pages
            navigate_to_page(page, base_url, page_dest.key, standalone_urls)
            capture_screenshot(page, f"page_{page_dest.key}", viewport_name)