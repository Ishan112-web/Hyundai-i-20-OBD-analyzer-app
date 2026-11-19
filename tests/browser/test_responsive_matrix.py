"""
Responsive Test Matrix - 13 pages × 7 viewports = 91 combinations
Phase 6 Stage 6: Full Responsive Verification
"""

import pytest
from playwright.sync_api import Page, expect

# Import test utilities from conftest
from tests.browser.conftest import (
    VIEWPORT_NAMES,
    MAIN_PAGES,
    STANDALONE_PAGES,
    ALL_PAGES,
    navigate_to_page,
    capture_screenshot,
    check_page_overflow,
    check_main_content_visible,
    check_responsive_grids,
    check_touch_targets,
    check_table_scroll,
    check_charts_in_bounds,
    check_forms_visible,
    check_mobile_navigation,
    collect_console_errors,
    collect_page_errors,
)


# =============================================================================
# Parametrization: 7 viewports × 13 pages = 91 test combinations
# =============================================================================

@pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
@pytest.mark.parametrize("page_dest", MAIN_PAGES + STANDALONE_PAGES, ids=lambda p: p.key)
class TestResponsiveMatrix:
    """Test responsive behavior across all pages and viewports."""

    def test_page_loads_without_errors(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify page loads without JavaScript/console errors."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        # Check for critical console errors (filter out known benign warnings)
        console_errors = collect_console_errors(page)
        page_errors = collect_page_errors(page)

        # Filter known benign errors
        critical_console_errors = [
            e for e in console_errors
            if e["type"] == "error"
            and "favicon" not in e["text"].lower()
            and "source map" not in e["text"].lower()
            and "devtools" not in e["text"].lower()
        ]

        critical_page_errors = [
            e for e in page_errors
            if "favicon" not in e["message"].lower()
        ]

        assert len(critical_console_errors) == 0, f"Console errors on {page_dest.key} @ {viewport_name}: {critical_console_errors}"
        assert len(critical_page_errors) == 0, f"Page errors on {page_dest.key} @ {viewport_name}: {critical_page_errors}"

    def test_no_horizontal_overflow(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify no unintended document-level horizontal overflow."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        overflow = check_page_overflow(page)

        assert overflow["pass"], (
            f"Horizontal overflow on {page_dest.key} @ {viewport_name}: "
            f"doc={overflow['doc_width']}px, viewport={overflow['viewport_width']}px, "
            f"overflow={overflow['overflow']}px"
        )

    def test_main_content_visible(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify main content area is visible and within viewport."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        content = check_main_content_visible(page)

        assert content["visible"], (
            f"Main content not visible on {page_dest.key} @ {viewport_name}: {content.get('reason', 'unknown')}"
        )

        if content.get("clipped"):
            # Warning only - content may be intentionally scrollable
            print(f"WARNING: Main content may be clipped on {page_dest.key} @ {viewport_name}")

    def test_responsive_grids(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify grid containers adapt to viewport."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        grids = check_responsive_grids(page)

        # At least one grid should exist on most pages
        # Grid children should not overflow viewport
        for i, grid in enumerate(grids):
            assert grid.get("children_in_bounds", True), (
                f"Grid {i} children overflow on {page_dest.key} @ {viewport_name}: "
                f"grid_width={grid.get('grid_width')}, overflows={grid.get('overflows_viewport')}"
            )
            if grid.get("overflows_viewport"):
                print(f"WARNING: Grid {i} overflows viewport on {page_dest.key} @ {viewport_name}")

    def test_touch_targets_mobile(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
        current_viewport,
    ):
        """Verify touch targets meet minimum size on mobile/tablet viewports."""
        if not current_viewport.has_touch:
            pytest.skip("Touch target test only for mobile/tablet viewports")

        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        targets = check_touch_targets(page, min_size=44)

        # Filter to visible interactive elements
        visible_targets = [t for t in targets if t["visible"]]

        failing_targets = [t for t in visible_targets if not t["pass"]]

        # Allow some failures for complex components (like selectboxes)
        # but flag if too many fail
        if len(visible_targets) > 0:
            fail_rate = len(failing_targets) / len(visible_targets)
            assert fail_rate < 0.3, (
                f"Touch target failure rate {fail_rate:.0%} on {page_dest.key} @ {viewport_name}: "
                f"{len(failing_targets)}/{len(visible_targets)} failing. "
                f"Examples: {failing_targets[:3]}"
            )

    def test_table_scroll_internal(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify tables use internal scroll without page overflow."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        tables = check_table_scroll(page)

        for i, table in enumerate(tables):
            if table.get("overflows_page"):
                assert False, (
                    f"Table {i} overflows page on {page_dest.key} @ {viewport_name}: "
                    f"table_width={table.get('table_width')}, content_width={table.get('content_width')}"
                )

            if table.get("has_horizontal_scroll"):
                # Good - table has internal scroll
                assert table.get("in_bounds"), (
                    f"Table {i} has scroll but overflows page on {page_dest.key} @ {viewport_name}"
                )

    def test_charts_in_bounds(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify Plotly charts stay within containers."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"Chart {i} overflows viewport on {page_dest.key} @ {viewport_name}: "
                f"chart_width={chart.get('chart_width')}, parent_width={chart.get('parent_width')}"
            )

            if chart.get("overflows_parent"):
                print(f"WARNING: Chart {i} may overflow parent on {page_dest.key} @ {viewport_name}")

    def test_forms_visible(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify form inputs are visible and accessible."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        forms = check_forms_visible(page)

        for i, form in enumerate(forms):
            if not form.get("visible"):
                print(f"WARNING: Form input {i} not visible on {page_dest.key} @ {viewport_name}: {form}")

            if not form.get("in_viewport"):
                assert False, (
                    f"Form input {i} outside viewport on {page_dest.key} @ {viewport_name}: {form}"
                )

    def test_capture_screenshot(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Capture baseline screenshot for visual regression."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        path = capture_screenshot(page, page_dest.key, viewport_name)

        assert path.exists(), f"Screenshot not created: {path}"
        assert path.stat().st_size > 1000, f"Screenshot too small: {path}"


# =============================================================================
# Mobile Navigation Specific Tests
# =============================================================================

@pytest.mark.parametrize("viewport_name", ["mobile", "mobile_small", "mobile_minimum", "tablet", "tablet_portrait"])
class TestMobileNavigation:
    """Test mobile navigation drawer behavior on touch viewports."""

    def test_mobile_nav_drawer_exists(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify mobile navigation drawer and toggle exist on mobile."""
        # Test on dashboard page
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        nav = check_mobile_navigation(page)

        # On mobile, should have drawer and toggle
        assert nav["has_drawer"], f"No sidebar drawer found on {viewport_name}"
        assert nav["has_toggle"], f"No mobile menu toggle found on {viewport_name}"
        assert nav["toggle_visible"], f"Mobile menu toggle not visible on {viewport_name}"

    def test_mobile_nav_drawer_opens(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify mobile navigation drawer can be opened."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        # Find and click the menu toggle
        toggle = page.locator('button[aria-label*="menu" i], button[aria-label*="Menu" i], .i20-top-bar-mobile-menu').first

        if toggle.count() > 0:
            toggle.click()
            page.wait_for_timeout(300)

            nav = check_mobile_navigation(page)
            assert nav["drawer_visible"], f"Drawer did not open on {viewport_name}"

    def test_mobile_nav_page_selection(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Verify page selection works from mobile drawer."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        # Open drawer
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

                # Verify navigation occurred
                assert "diagnostics" in page.url.lower() or page.locator("h1:has-text('Diagnostics'), h2:has-text('Diagnostics')").count() > 0


# =============================================================================
# Standalone Report Pages Tests
# =============================================================================

@pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
@pytest.mark.parametrize("page_dest", STANDALONE_PAGES, ids=lambda p: p.key)
class TestStandaloneReports:
    """Test standalone report pages specifically."""

    def test_report_page_loads(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify standalone report page loads."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        # Check page has content
        expect(page.locator("body")).not_to_be_empty()

    def test_report_no_overflow(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Verify no overflow on report pages."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        overflow = check_page_overflow(page)
        assert overflow["pass"], (
            f"Report page overflow on {page_dest.key} @ {viewport_name}: "
            f"overflow={overflow['overflow']}px"
        )

    def test_report_screenshot(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Capture report page screenshot."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        path = capture_screenshot(page, page_dest.key, viewport_name)
        assert path.exists()


# =============================================================================
# Specific Page Component Tests
# =============================================================================

class TestDashboardComponents:
    """Test dashboard-specific responsive components."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_gauges_responsive(self, page: Page, base_url: str, standalone_urls: dict, viewport_name: str):
        """Verify dashboard gauges adapt to viewport."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        # Check for gauge charts
        gauges = page.locator(".js-plotly-plot, [data-testid*='gauge'], .plotly-graph-div")
        gauge_count = gauges.count()

        # Dashboard should have 4 primary gauges
        if gauge_count > 0:
            for i in range(min(gauge_count, 6)):
                gauge = gauges.nth(i)
                bbox = gauge.bounding_box()
                if bbox:
                    assert bbox["width"] > 0 and bbox["height"] > 0
                    assert bbox["right"] <= page.evaluate("window.innerWidth")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_telemetry_cards_grid(self, page: Page, base_url: str, standalone_urls: dict, viewport_name: str):
        """Verify telemetry cards use responsive grid."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        # Look for telemetry card grid
        cards = page.locator(".i20-grid, [style*='auto-fit'], [style*='auto-fill']").first
        if cards.count() > 0:
            bbox = cards.bounding_box()
            if bbox:
                assert bbox["right"] <= page.evaluate("window.innerWidth")


class TestDiagnosticsComponents:
    """Test diagnostics-specific responsive components."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_dtc_table_scroll(self, page: Page, base_url: str, standalone_urls: dict, viewport_name: str):
        """Verify DTC table has internal scroll on mobile."""
        navigate_to_page(page, base_url, "diagnostics", standalone_urls)

        tables = page.locator("table, .stTable, .i20-table-wrapper")
        for i in range(tables.count()):
            table = tables.nth(i)
            bbox = table.bounding_box()
            if bbox:
                scroll_width = table.evaluate("el => el.scrollWidth")
                client_width = table.evaluate("el => el.clientWidth")

                if scroll_width > client_width:
                    # Table has horizontal content - should not overflow page
                    assert bbox["right"] <= page.evaluate("window.innerWidth"), (
                        f"DTC table overflows page on {viewport_name}"
                    )


class TestPerformanceComponents:
    """Test performance-specific responsive components."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_telemetry_charts_responsive(self, page: Page, base_url: str, standalone_urls: dict, viewport_name: str):
        """Verify performance telemetry charts resize properly."""
        navigate_to_page(page, base_url, "performance", standalone_urls)

        charts = page.locator(".js-plotly-plot, .plotly-graph-div")
        for i in range(charts.count()):
            chart = charts.nth(i)
            bbox = chart.bounding_box()
            if bbox:
                assert bbox["right"] <= page.evaluate("window.innerWidth"), (
                    f"Performance chart {i} overflows on {viewport_name}"
                )


class TestSettingsComponents:
    """Test settings page responsive components."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_settings_tabs_responsive(self, page: Page, base_url: str, standalone_urls: dict, viewport_name: str):
        """Verify settings tabs work on mobile."""
        navigate_to_page(page, base_url, "settings", standalone_urls)

        # Check tabs are accessible
        tabs = page.locator('[role="tab"], button[aria-selected], .stTabs [role="tab"]')
        tab_count = tabs.count()

        if tab_count > 0:
            # On mobile, tabs should not overflow
            for i in range(tab_count):
                tab = tabs.nth(i)
                bbox = tab.bounding_box()
                if bbox:
                    assert bbox["right"] <= page.evaluate("window.innerWidth") + 10, (
                        f"Settings tab {i} overflows on {viewport_name}"
                    )


class TestOBDWizardComponents:
    """Test OBD Connection wizard responsive components."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_wizard_steps_responsive(self, page: Page, base_url: str, standalone_urls: dict, viewport_name: str):
        """Verify OBD wizard steps adapt to viewport."""
        navigate_to_page(page, base_url, "obd_connection", standalone_urls)

        # Check wizard container
        wizard = page.locator(".i20-wizard, [data-testid*='wizard'], .wizard")
        if wizard.count() > 0:
            bbox = wizard.bounding_box()
            if bbox:
                assert bbox["right"] <= page.evaluate("window.innerWidth"), (
                    f"OBD wizard overflows on {viewport_name}"
                )


# =============================================================================
# Regression: Run Full Test Suite
# =============================================================================

def test_full_regression_suite():
    """Placeholder for running the full 415-test regression suite."""
    # This will be run separately via: python -m pytest tests/ -v
    pass