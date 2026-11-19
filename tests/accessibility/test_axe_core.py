"""
Axe-core Accessibility Tests - Automated WCAG 2.1 AA compliance checks
Runs axe-core on all pages across all viewports
"""
import pytest
from axe_playwright_python.sync_playwright import Axe


def test_axe_core_sync(page, viewport, page_dest):
    """Sync version of axe-core test."""
    from tests.accessibility.conftest import navigate_to_page, BASE_URL, print_console_errors

    url = f"{BASE_URL}{page_dest['url_path']}"
    page.goto(url, wait_until="networkidle")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Inject axe using sync API - run() handles injection internally
    axe = Axe()

    # Run axe scan (sync version handles injection internally)
    results = axe.run(page)

    violations = results.response.get("violations", [])

    if violations:
        test_name = f"{page_dest['key']} @ {viewport['name']}"
        print(f"\n=== AXE VIOLATIONS: {test_name} ===")
        for v in violations:
            print(f"  - {v['id']} ({v['impact']}): {v['description']}")
            for node in v['nodes'][:3]:
                print(f"    Target: {node['target']}")
                print(f"    HTML: {node['html'][:200]}")
            if len(v['nodes']) > 3:
                print(f"    ... and {len(v['nodes']) - 3} more")
        # Print console errors for debugging
        print_console_errors(page, test_name)

    assert len(violations) == 0, (
        f"Axe violations on {page_dest['key']} @ {viewport['name']}: "
        f"{len(violations)} violations found"
    )