"""
Single page axe-core test for quick verification
"""
import asyncio
from playwright.async_api import async_playwright
from axe_playwright_python.async_playwright import Axe


async def test_dashboard_desktop():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Navigate to dashboard
        await page.goto("http://localhost:8501?page=dashboard", wait_until="networkidle")
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(2000)

        # Inject axe - async version handles injection internally in run()
        axe = Axe()

        # Run axe scan
        results = await axe.run(page)

        violations = results.response.get("violations", [])

        if violations:
            print(f"\n=== AXE VIOLATIONS: dashboard @ desktop ===")
            for v in violations:
                print(f"  - {v['id']} ({v['impact']}): {v['description']}")
                for node in v['nodes'][:3]:
                    print(f"    Target: {node['target']}")
                    print(f"    HTML: {node['html'][:200]}")
                if len(v['nodes']) > 3:
                    print(f"    ... and {len(v['nodes']) - 3} more")
        else:
            print("PASS: No axe violations found!")

        await browser.close()
        return len(violations) == 0


if __name__ == "__main__":
    result = asyncio.run(test_dashboard_desktop())
    print(f"\nTest {'PASSED' if result else 'FAILED'}")
    exit(0 if result else 1)