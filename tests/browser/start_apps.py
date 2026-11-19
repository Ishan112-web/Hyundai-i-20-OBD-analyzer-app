#!/usr/bin/env python
"""
Start all Streamlit apps for browser testing.
Run this before running pytest tests.
"""

import os
import sys
import time
import subprocess
import tempfile
from pathlib import Path
import requests

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ports for apps
MAIN_PORT = 8501
STANDALONE_PORTS = {
    "diagnostic_report": 8502,
    "vehicle_health_report": 8503,
    "performance_report": 8504,
    "maintenance_report": 8505,
}

processes = {}
temp_db_path = None


def create_temp_database() -> Path:
    """Create a temporary database for testing."""
    temp_dir = Path(tempfile.mkdtemp(prefix="i20_test_"))
    db_path = temp_dir / "test_i20_garage.db"
    return db_path


def start_app(script_path: Path, port: int, db_path: Path) -> subprocess.Popen:
    """Start a Streamlit app."""
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

    proc = subprocess.Popen(
        cmd,
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def wait_for_app(url: str, timeout: int = 120):
    """Wait for Streamlit app to be ready."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                time.sleep(3)  # Extra time for JS hydration
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False


def main():
    global temp_db_path, processes

    # Create temp database
    temp_db_path = create_temp_database()
    print(f"Created temp database: {temp_db_path}")

    # Create standalone scripts directory
    scripts_dir = PROJECT_ROOT / "tests" / "browser" / "fixtures" / "standalone_scripts"
    scripts_dir.mkdir(parents=True, exist_ok=True)

    # Standalone scripts content
    STANDALONE_SCRIPTS = {
        "diagnostic_report": "from modules.reports import render_diagnostic_report_page\nrender_diagnostic_report_page()",
        "vehicle_health_report": "from modules.reports import render_vehicle_health_report_page\nrender_vehicle_health_report_page()",
        "performance_report": "from modules.reports import render_performance_report_page\nrender_performance_report_page()",
        "maintenance_report": "from modules.reports import render_maintenance_report_page\nrender_maintenance_report_page()",
    }

    # Write standalone scripts
    for key, content in STANDALONE_SCRIPTS.items():
        script_path = scripts_dir / f"{key}.py"
        full_content = f"import streamlit as st\n{content}"
        script_path.write_text(full_content)

    # Start main app
    print(f"Starting main app on port {MAIN_PORT}...")
    main_proc = start_app(PROJECT_ROOT / "app.py", MAIN_PORT, temp_db_path)
    processes[MAIN_PORT] = main_proc

    if not wait_for_app(f"http://localhost:{MAIN_PORT}"):
        print(f"ERROR: Main app failed to start on port {MAIN_PORT}")
        return False
    print(f"Main app ready at http://localhost:{MAIN_PORT}")

    # Start standalone apps
    for key, port in STANDALONE_PORTS.items():
        print(f"Starting {key} on port {port}...")
        script_path = scripts_dir / f"{key}.py"
        proc = start_app(script_path, port, temp_db_path)
        processes[port] = proc

        if not wait_for_app(f"http://localhost:{port}"):
            print(f"ERROR: {key} failed to start on port {port}")
            return False
        print(f"{key} ready at http://localhost:{port}")

    print("\nAll apps started successfully!")
    print("Press Ctrl+C to stop all apps.")

    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping all apps...")
        for port, proc in processes.items():
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        # Clean up temp database
        if temp_db_path and temp_db_path.exists():
            temp_db_path.unlink()
            temp_db_path.parent.rmdir()
        print("All apps stopped.")


if __name__ == "__main__":
    main()