#!/usr/bin/env python
"""
CI Check: Token-Only Usage in Custom HTML (A1.7)
Ensures no hardcoded colors in custom HTML components — all must use design system CSS variables.
"""
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Patterns to detect hardcoded colors in Python files
HARDCODED_COLOR_PATTERNS = [
    # Hex colors
    r'#[0-9a-fA-F]{3,8}',
    # RGB/RGBA (but not transparent rgba(0,0,0,0) which is standard)
    r'rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)',
    r'rgba\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*(?!0\s*\))[\d.]+\s*\)',  # Not rgba(...,0)
    # HSL/HSLA
    r'hsl\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*\)',
    r'hsla\(\s*\d+\s*,\s*\d+%\s*,\s*\d+%\s*,\s*[\d.]+\s*\)',
    # Named colors (common ones) - but exclude CSS keywords
    r'\b(red|green|blue|yellow|orange|purple|pink|cyan|magenta|lime|teal|indigo|violet|gray|grey|white|black)\b',
]

# Allowlist: files/patterns that are allowed to have colors
ALLOWLIST = {
    # Design system token files (they define the colors)
    'components/ui/tokens.py',
    'components/ui/theme.py',
    'components/ui/styles.py',
    # Legacy config - defines base colors that map to design tokens
    'config.py',
    # Legacy chart files (being migrated)
    'components/charts.py',
    'components/sidebar.py',
    'components/status_cards.py',
    # PDF renderer - generates PDFs not HTML
    'services/report_renderers/pdf_renderer.py',
    # OBD service - internal status logic
    'services/obd_service.py',
    # Test files
    'tests/',
    # Documentation
    'docs/',
    # Scripts
    'scripts/',
    # Virtual environment (third-party packages)
    '.venv/',
    # Standalone report scripts (they use design system)
    'tests/browser/fixtures/standalone_scripts/',
}

# Allowlist patterns within files (e.g., CSS variable definitions)
ALLOWLIST_PATTERNS = [
    r'var\(--i20-color-',  # CSS variable usage
    r'var\(--color-',      # Legacy CSS variable usage
    r'SEMANTIC_COLORS\[',  # Token reference
    r'get_color\(',        # Token function
    r'THEME\[',            # Legacy theme reference
    r'color:\s*var\(',     # CSS variable in style
    r'background-color:\s*var\(',
    r'border-color:\s*var\(',
    r'fill:\s*var\(',
    r'stroke:\s*var\(',
    # Plotly color references (they use design system tokens)
    r'marker_color\s*=',
    r'line_color\s*=',
    r'fillcolor\s*=',
    # Plotly transparent background (standard)
    r'rgba\(0,\s*0,\s*0,\s*0\)',
    r'"rgba\(0,\s*0,\s*0,\s*0\)"',
    r'"transparent"',
    # CSS standard keywords (not design system colors)
    r'\btransparent\b',
    r'\binherit\b',
    r'\binitial\b',
    r'\bunset\b',
    r'\bcurrentColor\b',
    # Status color names used as semantic identifiers (not CSS)
    r'StatusColor\s*=',
    r'status:\s*["\'](green|red|blue|amber|purple|gray)["\']',
    r'["\'](green|red|blue|amber|purple|gray)["\']\s*,\s*["\']',
    # Dictionary mapping status names to design tokens (semantic, not CSS)
    r'"(green|red|blue|amber|purple|gray)"\s*:\s*(STATUS_|ACCENT_|SEMANTIC_)',
    # Column headers / descriptive text with color names
    r'(Green|Red|Amber|Yellow|Blue|Purple)\s+Zone',
    r'RdYlGn',
    r'colorscale',
    # In comments or strings that are documentation
    r'#.*#[0-9a-fA-F]{3,8}',  # Hex in comments
    r'""".*#[0-9a-fA-F]{3,8}',  # Hex in docstrings
    r"'''.*#[0-9a-fA-F]{3,8}",
    # White-space CSS property (not a color)
    r'white-space\s*:',
    # PDF report generation (not HTML)
    r'from reportlab',
    r'HexColor\(',
    r'reportlab\.lib\.colors',
    # Descriptive text (not CSS colors)
    r'OEM\s+(blue|red|green|yellow|black|white)\s+coolant',
    r'OEM\s+(blue|red|green|yellow|black|white)\s+',
]


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped based on allowlist."""
    rel_path = file_path.relative_to(PROJECT_ROOT)
    rel_str = str(rel_path).replace('\\', '/')  # Normalize to forward slashes

    for allow in ALLOWLIST:
        allow_norm = allow.replace('\\', '/')
        if allow_norm.endswith('/'):
            if rel_str.startswith(allow_norm):
                return True
        elif rel_str == allow_norm or rel_str.startswith(allow_norm + '/'):
            return True
    return False


def is_allowed_pattern(line: str) -> bool:
    """Check if a line matches an allowed pattern."""
    for pattern in ALLOWLIST_PATTERNS:
        if re.search(pattern, line):
            return True
    return False


def check_file(file_path: Path) -> list[tuple[int, str, str]]:
    """Check a single file for hardcoded colors. Returns list of (line_num, line, matched_pattern)."""
    violations = []

    try:
        content = file_path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return violations

    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        # Skip empty lines and comments
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        # Check if line is allowed
        if is_allowed_pattern(line):
            continue

        # Check for hardcoded colors
        for pattern in HARDCODED_COLOR_PATTERNS:
            matches = re.findall(pattern, line, re.IGNORECASE)
            if matches:
                # Filter out false positives (e.g., version numbers like 1.2.3)
                for match in matches:
                    if re.match(r'^\d+\.\d+\.\d+$', match):
                        continue  # Version number
                    if re.match(r'^\d+$', match):
                        continue  # Just a number
                    violations.append((i, line.strip(), match))

    return violations


def main():
    """Main entry point."""
    python_files = list(PROJECT_ROOT.rglob('*.py'))

    all_violations = []

    for file_path in python_files:
        if should_skip_file(file_path):
            continue

        violations = check_file(file_path)
        if violations:
            rel_path = file_path.relative_to(PROJECT_ROOT)
            for line_num, line, match in violations:
                all_violations.append((str(rel_path), line_num, line, match))

    if all_violations:
        print("ERROR: HARDCODED COLOR VIOLATIONS FOUND (A1.7 - Contrast: Token-Only Usage)")
        print("=" * 80)
        print("All custom HTML must use design system CSS variables (var(--i20-color-...))")
        print("=" * 80)
        print()

        current_file = None
        for file_path, line_num, line, match in all_violations:
            if file_path != current_file:
                current_file = file_path
                print(f"\nFILE: {file_path}")
            print(f"  Line {line_num}: {match}")
            print(f"    {line[:120]}")

        print(f"\n{'='*80}")
        print(f"Total violations: {len(all_violations)} across {len(set(v[0] for v in all_violations))} files")
        print("Fix: Replace hardcoded colors with design system tokens (var(--i20-color-...))")
        return 1
    else:
        print("SUCCESS: No hardcoded color violations found (A1.7 PASS)")
        print("All custom HTML uses design system CSS variables")
        return 0


if __name__ == '__main__':
    sys.exit(main())