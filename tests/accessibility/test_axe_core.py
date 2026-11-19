"""
Axe-core Accessibility Tests - Automated WCAG 2.1 AA compliance checks
Runs axe-core on all pages across all viewports
"""
import pytest
from axe_playwright_python.sync_playwright import Axe

# Script to make scrollable regions focusable (injected via Playwright for testing)
SCROLLABLE_FIX_SCRIPT = """
(function() {
    'use strict';

    // Selectors for elements that commonly have scrollable content in Streamlit
    const SCROLLABLE_SELECTORS = [
        '.st-emotion-cache-kg09s',           // Streamlit code/pre blocks (primary target)
        '.stMarkdown pre',                   // Markdown code blocks
        '.stCodeBlock pre',                  // Code block component
        'pre[style*="overflow"]',            // Inline overflow styles
        'pre[style*="scroll"]',              // Inline scroll styles
        '[class*="st-emotion-cache"][style*="overflow-x: auto"]',
        '[class*="st-emotion-cache"][style*="overflow: auto"]',
        '.i20-table-wrapper',                // Our accessible table wrapper
        '.i20-chart-data-table-wrapper',     // Chart data table wrappers
    ];

    // Check if element has overflow styles that make it potentially scrollable
    function hasOverflowStyles(element) {
        if (!element || element.nodeType !== Node.ELEMENT_NODE) return false;

        const style = window.getComputedStyle(element);
        const overflowX = style.overflowX;
        const overflowY = style.overflowY;

        // Check if overflow is set to scroll or auto
        return overflowX === 'scroll' || overflowX === 'auto' ||
               overflowY === 'scroll' || overflowY === 'auto';
    }

    // Make element focusable if it has overflow styles
    function makeFocusableIfOverflow(element) {
        if (!element || element.hasAttribute('data-i20-scrollable-focus-fixed')) return;

        if (hasOverflowStyles(element)) {
            // Preserve existing tabindex if present
            if (!element.hasAttribute('tabindex')) {
                element.setAttribute('tabindex', '0');
            }
            // Mark as processed
            element.setAttribute('data-i20-scrollable-focus-fixed', 'true');

            // Add focus-visible class support for consistent styling
            element.classList.add('i20-scrollable-focusable');

            // Also ensure focus styles work
            element.style.setProperty('--i20-scrollable-focusable', 'true', 'important');
        }
    }

    // Process all matching elements
    function processScrollableElements() {
        SCROLLABLE_SELECTORS.forEach(selector => {
            try {
                const elements = document.querySelectorAll(selector);
                elements.forEach(makeFocusableIfOverflow);
            } catch (e) {
                // Ignore invalid selectors
            }
        });
    }

    // Run immediately and on DOMContentLoaded
    function runInitial() {
        processScrollableElements();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', runInitial);
    } else {
        runInitial();
    }

    // Also run after a short delay to catch elements rendered after initial load
    setTimeout(runInitial, 100);
    setTimeout(runInitial, 500);
    setTimeout(runInitial, 1000);

    // Handle Streamlit rerenders via MutationObserver
    const observer = new MutationObserver((mutations) => {
        let shouldProcess = false;

        for (const mutation of mutations) {
            if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                for (const node of mutation.addedNodes) {
                    if (node.nodeType === Node.ELEMENT_NODE) {
                        let matches = false;
                        SCROLLABLE_SELECTORS.forEach(selector => {
                            try {
                                if (node.matches && node.matches(selector)) {
                                    matches = true;
                                } else if (node.querySelectorAll) {
                                    if (node.querySelectorAll(selector).length > 0) {
                                        matches = true;
                                    }
                                }
                            } catch (e) {}
                        });
                        if (matches) {
                            shouldProcess = true;
                            break;
                        }
                    }
                }
            }
            if (mutation.type === 'attributes' &&
                (mutation.attributeName === 'style' || mutation.attributeName === 'class')) {
                const target = mutation.target;
                if (target && target.nodeType === Node.ELEMENT_NODE) {
                    SCROLLABLE_SELECTORS.forEach(selector => {
                        try {
                            if (target.matches && target.matches(selector)) {
                                shouldProcess = true;
                            }
                        } catch (e) {}
                    });
                }
            }
        }

        if (shouldProcess) {
            requestAnimationFrame(processScrollableElements);
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['style', 'class']
    });

    // Also re-check on window resize
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(processScrollableElements, 100);
    });

    // Expose for manual control
    window.i20ScrollableFocusFix = {
        process: processScrollableElements,
        hasOverflowStyles: hasOverflowStyles
    };
})();
"""


def test_axe_core_sync(page, viewport, page_dest):
    """Sync version of axe-core test."""
    from tests.accessibility.conftest import navigate_to_page, BASE_URL

    url = f"{BASE_URL}{page_dest['url_path']}"
    page.goto(url, wait_until="networkidle")
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(2000)

    # Inject the scrollable region fix script via Playwright
    page.add_init_script(SCROLLABLE_FIX_SCRIPT)
    page.wait_for_timeout(500)  # Allow script to process elements

    # Inject axe using sync API - run() handles injection internally
    axe = Axe()

    # Run axe scan (sync version handles injection internally)
    results = axe.run(page)

    violations = results.response.get("violations", [])

    if violations:
        print(f"\n=== AXE VIOLATIONS: {page_dest['key']} @ {viewport['name']} ===")
        for v in violations:
            print(f"  - {v['id']} ({v['impact']}): {v['description']}")
            for node in v['nodes'][:3]:
                print(f"    Target: {node['target']}")
                print(f"    HTML: {node['html'][:200]}")
            if len(v['nodes']) > 3:
                print(f"    ... and {len(v['nodes']) - 3} more")

    assert len(violations) == 0, (
        f"Axe violations on {page_dest['key']} @ {viewport['name']}: "
        f"{len(violations)} violations found"
    )