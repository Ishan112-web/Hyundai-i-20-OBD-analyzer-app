"""
Page Component Responsive Tests - Charts, Tables, Forms, Reports
Phase 6 Stage 6: Component-Level Responsive Verification
"""

import pytest
from playwright.sync_api import Page, expect

from tests.browser.conftest import (
    VIEWPORT_NAMES,
    MAIN_PAGES,
    STANDALONE_PAGES,
    navigate_to_page,
    capture_screenshot,
    check_charts_in_bounds,
    check_table_scroll,
    check_forms_visible,
    check_touch_targets,
    check_responsive_grids,
    check_page_overflow,
    current_viewport,
)


# =============================================================================
# Chart Responsiveness Tests
# =============================================================================

class TestChartResponsiveness:
    """Test Plotly charts resize and stay within containers."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_dashboard_gauges_responsive(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test dashboard gauge charts."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"Dashboard gauge {i} overflows viewport on {viewport_name}: "
                f"chart={chart.get('chart_width')}, parent={chart.get('parent_width')}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_dashboard_live_chart_responsive(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test dashboard live multi-series chart."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        # Wait for live chart to render
        page.wait_for_timeout(2000)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"Dashboard live chart {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_performance_telemetry_charts(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test performance page telemetry charts."""
        navigate_to_page(page, base_url, "performance", standalone_urls)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"Performance chart {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_diagnostics_charts(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test diagnostics page charts."""
        navigate_to_page(page, base_url, "diagnostics", standalone_urls)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"Diagnostics chart {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_maintenance_charts(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test maintenance page charts."""
        navigate_to_page(page, base_url, "maintenance", standalone_urls)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"Maintenance chart {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_vehicle_profile_charts(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test vehicle profile page charts."""
        navigate_to_page(page, base_url, "vehicle_profile", standalone_urls)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"Vehicle profile chart {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_reports_page_charts(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test reports page charts."""
        navigate_to_page(page, base_url, "reports", standalone_urls)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"Reports chart {i} overflows on {viewport_name}"
            )


# =============================================================================
# Table Responsiveness Tests
# =============================================================================

class TestTableResponsiveness:
    """Test tables have internal scroll without page overflow."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_diagnostics_dtc_table(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test DTC table on diagnostics page."""
        navigate_to_page(page, base_url, "diagnostics", standalone_urls)

        tables = check_table_scroll(page)

        for i, table in enumerate(tables):
            if table.get("has_horizontal_scroll"):
                assert table.get("in_bounds"), (
                    f"DTC table {i} overflows page on {viewport_name}: "
                    f"table={table.get('table_width')}, content={table.get('content_width')}"
                )
            assert not table.get("overflows_page"), (
                f"DTC table {i} overflows page on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_performance_sessions_table(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test sessions table on performance page."""
        navigate_to_page(page, base_url, "performance", standalone_urls)

        # Click Sessions tab if needed
        sessions_tab = page.locator('button:has-text("Sessions"), [role="tab"]:has-text("Sessions")').first
        if sessions_tab.count() > 0:
            sessions_tab.click()
            page.wait_for_timeout(500)

        tables = check_table_scroll(page)

        for i, table in enumerate(tables):
            assert not table.get("overflows_page"), (
                f"Performance sessions table {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_maintenance_records_table(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test maintenance records table."""
        navigate_to_page(page, base_url, "maintenance", standalone_urls)

        tables = check_table_scroll(page)

        for i, table in enumerate(tables):
            assert not table.get("overflows_page"), (
                f"Maintenance table {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_settings_data_tables(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test settings page data tables (backup history, etc.)."""
        navigate_to_page(page, base_url, "settings", standalone_urls)

        # Go to Backup tab
        backup_tab = page.locator('button:has-text("Backup"), [role="tab"]:has-text("Backup")').first
        if backup_tab.count() > 0:
            backup_tab.click()
            page.wait_for_timeout(500)

        tables = check_table_scroll(page)

        for i, table in enumerate(tables):
            assert not table.get("overflows_page"), (
                f"Settings table {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_vehicle_profile_dtc_table(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test DTC table on vehicle profile page."""
        navigate_to_page(page, base_url, "vehicle_profile", standalone_urls)

        # Go to Diagnostics tab
        diag_tab = page.locator('button:has-text("Diagnostics"), [role="tab"]:has-text("Diagnostics")').first
        if diag_tab.count() > 0:
            diag_tab.click()
            page.wait_for_timeout(500)

        tables = check_table_scroll(page)

        for i, table in enumerate(tables):
            assert not table.get("overflows_page"), (
                f"Vehicle profile DTC table {i} overflows on {viewport_name}"
            )


# =============================================================================
# Form Responsiveness Tests
# =============================================================================

class TestFormResponsiveness:
    """Test forms are usable and visible at all viewports."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_settings_forms(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test settings page forms."""
        navigate_to_page(page, base_url, "settings", standalone_urls)

        forms = check_forms_visible(page)

        for i, form in enumerate(forms):
            assert form.get("visible"), f"Settings form {i} not visible on {viewport_name}"
            assert form.get("in_viewport"), f"Settings form {i} outside viewport on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_vehicle_profile_forms(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test vehicle profile edit forms."""
        navigate_to_page(page, base_url, "vehicle_profile", standalone_urls)

        # Click edit if needed
        edit_btn = page.locator('button:has-text("Edit"), button:has-text("Edit Vehicle")').first
        if edit_btn.count() > 0:
            edit_btn.click()
            page.wait_for_timeout(500)

        forms = check_forms_visible(page)

        for i, form in enumerate(forms):
            assert form.get("visible"), f"Vehicle profile form {i} not visible on {viewport_name}"
            assert form.get("in_viewport"), f"Vehicle profile form {i} outside viewport on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_maintenance_add_form(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test maintenance add/edit form."""
        navigate_to_page(page, base_url, "maintenance", standalone_urls)

        # Click Add/Edit tab
        add_tab = page.locator('button:has-text("Add"), [role="tab"]:has-text("Add")').first
        if add_tab.count() > 0:
            add_tab.click()
            page.wait_for_timeout(500)

        forms = check_forms_visible(page)

        for i, form in enumerate(forms):
            assert form.get("visible"), f"Maintenance form {i} not visible on {viewport_name}"
            assert form.get("in_viewport"), f"Maintenance form {i} outside viewport on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_obd_connection_forms(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test OBD connection wizard forms."""
        navigate_to_page(page, base_url, "obd_connection", standalone_urls)

        forms = check_forms_visible(page)

        for i, form in enumerate(forms):
            assert form.get("visible"), f"OBD form {i} not visible on {viewport_name}"
            assert form.get("in_viewport"), f"OBD form {i} outside viewport on {viewport_name}"

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_ai_assistant_chat_form(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test AI Assistant chat input form."""
        navigate_to_page(page, base_url, "ai_assistant", standalone_urls)

        forms = check_forms_visible(page)

        # Find chat input
        chat_input = page.locator("textarea[placeholder*='chat' i], textarea[placeholder*='message' i], .stChatInput textarea").first

        if chat_input.count() > 0:
            bbox = chat_input.bounding_box()
            if bbox:
                assert bbox["right"] <= page.evaluate("window.innerWidth"), (
                    f"Chat input overflows on {viewport_name}"
                )
                assert bbox["height"] >= 44, f"Chat input too small on {viewport_name}"


# =============================================================================
# Grid/Layout Responsiveness Tests
# =============================================================================

class TestGridResponsiveness:
    """Test responsive grid layouts."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_dashboard_telemetry_grid(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        current_viewport,
    ):
        """Test dashboard telemetry cards grid."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)

        grids = check_responsive_grids(page)

        for i, grid in enumerate(grids):
            if grid.get("child_count", 0) > 4:  # Telemetry grid should have 10 cards
                assert grid.get("children_in_bounds"), (
                    f"Telemetry grid {i} children overflow on {viewport_name}"
                )
                assert not grid.get("overflows_viewport"), (
                    f"Telemetry grid {i} overflows viewport on {viewport_name}"
                )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_vehicle_profile_info_grid(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test vehicle profile info grid."""
        navigate_to_page(page, base_url, "vehicle_profile", standalone_urls)

        grids = check_responsive_grids(page)

        for i, grid in enumerate(grids):
            assert grid.get("children_in_bounds", True), (
                f"Vehicle profile grid {i} children overflow on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_obd_pid_grid(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test OBD PID discovery grid."""
        navigate_to_page(page, base_url, "obd_connection", standalone_urls)

        grids = check_responsive_grids(page)

        for i, grid in enumerate(grids):
            if grid.get("child_count", 0) > 5:  # PID grid has many items
                assert grid.get("children_in_bounds"), (
                    f"OBD PID grid {i} children overflow on {viewport_name}"
                )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_reports_type_grid(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Test reports page report type cards grid."""
        navigate_to_page(page, base_url, "reports", standalone_urls)

        grids = check_responsive_grids(page)

        for i, grid in enumerate(grids):
            assert grid.get("children_in_bounds", True), (
                f"Reports grid {i} children overflow on {viewport_name}"
            )


# =============================================================================
# Standalone Report Pages Component Tests
# =============================================================================

class TestStandaloneReportComponents:
    """Test components on standalone report pages."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    @pytest.mark.parametrize("page_dest", STANDALONE_PAGES, ids=lambda p: p.key)
    def test_report_page_charts(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Test charts on standalone report pages."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        charts = check_charts_in_bounds(page)

        for i, chart in enumerate(charts):
            assert not chart.get("overflows_viewport"), (
                f"{page_dest.key} chart {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    @pytest.mark.parametrize("page_dest", STANDALONE_PAGES, ids=lambda p: p.key)
    def test_report_page_tables(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Test tables on standalone report pages."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        tables = check_table_scroll(page)

        for i, table in enumerate(tables):
            assert not table.get("overflows_page"), (
                f"{page_dest.key} table {i} overflows on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    @pytest.mark.parametrize("page_dest", STANDALONE_PAGES, ids=lambda p: p.key)
    def test_report_page_forms(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Test forms on standalone report pages."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        forms = check_forms_visible(page)

        for i, form in enumerate(forms):
            assert form.get("in_viewport"), (
                f"{page_dest.key} form {i} outside viewport on {viewport_name}"
            )

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    @pytest.mark.parametrize("page_dest", STANDALONE_PAGES, ids=lambda p: p.key)
    def test_report_page_no_overflow(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Test no overflow on standalone report pages."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        overflow = check_page_overflow(page)
        assert overflow["pass"], (
            f"{page_dest.key} page overflow on {viewport_name}: {overflow['overflow']}px"
        )


# =============================================================================
# Touch Target Tests
# =============================================================================

class TestTouchTargets:
    """Test touch target sizes on mobile viewports."""

    MOBILE_VIEWPORTS = ["mobile", "mobile_small", "mobile_minimum", "tablet", "tablet_portrait"]

    @pytest.mark.parametrize("viewport_name", MOBILE_VIEWPORTS)
    @pytest.mark.parametrize("page_dest", MAIN_PAGES[:5], ids=lambda p: p.key)  # Sample pages
    def test_page_touch_targets(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
        current_viewport,
    ):
        """Test touch targets on main pages."""
        if not current_viewport.has_touch:
            pytest.skip("Touch test only for touch viewports")

        navigate_to_page(page, base_url, page_dest.key, standalone_urls)

        targets = check_touch_targets(page, min_size=44)
        visible_targets = [t for t in targets if t["visible"]]
        failing = [t for t in visible_targets if not t["pass"]]

        if len(visible_targets) > 0:
            fail_rate = len(failing) / len(visible_targets)
            # Allow up to 30% failure for complex components
            assert fail_rate < 0.3, (
                f"Touch target failure rate {fail_rate:.0%} on {page_dest.key} @ {viewport_name}: "
                f"{len(failing)}/{len(visible_targets)} failing"
            )


# =============================================================================
# Screenshot Baselines
# =============================================================================

class TestScreenshotBaselines:
    """Capture screenshots for visual regression baselines."""

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_dashboard_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture dashboard screenshots."""
        navigate_to_page(page, base_url, "dashboard", standalone_urls)
        capture_screenshot(page, "dashboard", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_diagnostics_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture diagnostics screenshots."""
        navigate_to_page(page, base_url, "diagnostics", standalone_urls)
        capture_screenshot(page, "diagnostics", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_performance_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture performance screenshots."""
        navigate_to_page(page, base_url, "performance", standalone_urls)
        capture_screenshot(page, "performance", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_maintenance_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture maintenance screenshots."""
        navigate_to_page(page, base_url, "maintenance", standalone_urls)
        capture_screenshot(page, "maintenance", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_vehicle_profile_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture vehicle profile screenshots."""
        navigate_to_page(page, base_url, "vehicle_profile", standalone_urls)
        capture_screenshot(page, "vehicle_profile", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_ai_assistant_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture AI assistant screenshots."""
        navigate_to_page(page, base_url, "ai_assistant", standalone_urls)
        capture_screenshot(page, "ai_assistant", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_obd_connection_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture OBD connection screenshots."""
        navigate_to_page(page, base_url, "obd_connection", standalone_urls)
        capture_screenshot(page, "obd_connection", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_reports_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture reports page screenshots."""
        navigate_to_page(page, base_url, "reports", standalone_urls)
        capture_screenshot(page, "reports", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    def test_capture_settings_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
    ):
        """Capture settings screenshots."""
        navigate_to_page(page, base_url, "settings", standalone_urls)
        capture_screenshot(page, "settings", viewport_name, "full")

    @pytest.mark.parametrize("viewport_name", VIEWPORT_NAMES)
    @pytest.mark.parametrize("page_dest", STANDALONE_PAGES, ids=lambda p: p.key)
    def test_capture_standalone_report_screenshots(
        self,
        page: Page,
        base_url: str,
        standalone_urls: dict,
        viewport_name: str,
        page_dest,
    ):
        """Capture standalone report screenshots."""
        navigate_to_page(page, base_url, page_dest.key, standalone_urls)
        capture_screenshot(page, page_dest.key, viewport_name, "full")