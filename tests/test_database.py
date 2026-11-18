"""
i20 AI Garage - Database Tests
"""

import pytest
import tempfile
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.database import DatabaseService


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = Path(f.name)

    db = DatabaseService(db_path, run_migrations=False)
    yield db

    # Cleanup
    if db_path.exists():
        db_path.unlink()


def test_database_initialization(temp_db):
    """Test database initializes with all tables."""
    stats = temp_db.get_database_stats()

    assert "vehicle_profile" in stats
    assert "telemetry_sessions" in stats
    assert "telemetry_records" in stats
    assert "diagnostic_reports" in stats
    assert "maintenance_records" in stats
    assert "ai_conversations" in stats
    assert "settings" in stats
    assert stats["db_size_bytes"] > 0


def test_vehicle_profile(temp_db):
    """Test vehicle profile CRUD operations."""
    # Get default profile
    profile = temp_db.get_vehicle_profile()
    assert profile is not None
    assert profile["make"] == "Hyundai"
    assert profile["model"] == "i20 Asta"
    assert profile["year"] == 2023

    # Update profile
    result = temp_db.update_vehicle_profile(make="Test Make", model="Test Model")
    assert result is True

    # Verify update
    profile = temp_db.get_vehicle_profile()
    assert profile["make"] == "Test Make"
    assert profile["model"] == "Test Model"


def test_telemetry_session(temp_db):
    """Test telemetry session lifecycle."""
    # Create session
    session_id = temp_db.create_telemetry_session("Test Session", "idle")
    assert session_id > 0

    # Get active session
    session = temp_db.get_active_session()
    assert session is not None
    assert session["id"] == session_id
    assert session["is_active"] == 1

    # Add telemetry records
    for i in range(5):
        data = {
            "rpm": 1000 + i * 100,
            "speed_kmh": i * 10,
            "coolant_temp_c": 90.0,
            "throttle_pos_pct": 10.0 + i * 2,
            "engine_load_pct": 20.0 + i * 5,
            "is_simulated": True
        }
        result = temp_db.add_telemetry_record(session_id, data)
        assert result is True

    # End session
    result = temp_db.end_telemetry_session(session_id, "Test notes")
    assert result is True

    # Verify session ended
    session = temp_db.get_active_session()
    assert session is None or session["id"] != session_id

    # Get session records
    records = temp_db.get_session_records(session_id)
    assert len(records) == 5
    assert records[0]["rpm"] == 1000
    assert records[-1]["rpm"] == 1400


def test_session_statistics(temp_db):
    """Test session statistics calculation."""
    session_id = temp_db.create_telemetry_session("Stats Test", "highway")

    # Add records with known values
    test_data = [
        {"rpm": 2000, "speed_kmh": 80, "coolant_temp_c": 90, "throttle_pos_pct": 30, "engine_load_pct": 40},
        {"rpm": 3000, "speed_kmh": 100, "coolant_temp_c": 92, "throttle_pos_pct": 40, "engine_load_pct": 50},
        {"rpm": 3500, "speed_kmh": 110, "coolant_temp_c": 94, "throttle_pos_pct": 45, "engine_load_pct": 55},
        {"rpm": 2500, "speed_kmh": 90, "coolant_temp_c": 91, "throttle_pos_pct": 35, "engine_load_pct": 45},
    ]

    for data in test_data:
        data["is_simulated"] = True
        temp_db.add_telemetry_record(session_id, data)

    temp_db.end_telemetry_session(session_id)

    # Check statistics
    sessions = temp_db.get_telemetry_sessions(limit=1)
    session = sessions[0]

    assert session["peak_rpm"] == 3500
    assert session["max_speed"] == 110
    assert abs(session["avg_speed"] - 95.0) < 0.1
    assert session["max_coolant_temp"] == 94
    assert session["max_engine_load"] == 55


def test_diagnostic_reports(temp_db):
    """Test diagnostic report storage."""
    codes = [
        {"code": "P0300", "description": "Random Misfire", "severity": "major"},
        {"code": "P0171", "description": "System Too Lean", "severity": "major"},
    ]

    report_id = temp_db.save_diagnostic_report(
        session_id=None,
        dtc_count=2,
        codes=codes,
        summary="Two codes found",
        is_demo=True
    )
    assert report_id > 0

    reports = temp_db.get_diagnostic_reports(limit=10)
    assert len(reports) == 1
    assert reports[0]["dtc_count"] == 2
    assert len(reports[0]["codes"]) == 2
    assert reports[0]["codes"][0]["code"] == "P0300"


def test_maintenance_records(temp_db):
    """Test maintenance record CRUD operations."""
    # Add record
    record_id = temp_db.add_maintenance_record(
        service_type="engine_oil",
        description="Oil change",
        service_date="2024-01-15",
        odometer_km=15000,
        cost=2500.0,
        notes="Used 5W-30 synthetic",
        next_service_km=25000,
        next_service_date="2024-07-15"
    )
    assert record_id > 0

    # Get records
    records = temp_db.get_maintenance_records()
    assert len(records) == 1
    assert records[0]["service_type"] == "engine_oil"
    assert records[0]["odometer_km"] == 15000
    assert records[0]["cost"] == 2500.0

    # Update record
    result = temp_db.update_maintenance_record(record_id, cost=3000.0, notes="Updated note")
    assert result is True

    records = temp_db.get_maintenance_records()
    assert records[0]["cost"] == 3000.0
    assert records[0]["notes"] == "Updated note"

    # Delete record
    result = temp_db.delete_maintenance_record(record_id)
    assert result is True

    records = temp_db.get_maintenance_records()
    assert len(records) == 0


def test_upcoming_maintenance(temp_db):
    """Test upcoming maintenance query."""
    # Add records with different next service intervals
    temp_db.add_maintenance_record("engine_oil", "Oil change", "2024-01-01", 10000, next_service_km=20000)
    temp_db.add_maintenance_record("brake_fluid", "Brake fluid", "2024-01-01", 10000, next_service_km=15000)
    temp_db.add_maintenance_record("coolant", "Coolant", "2024-01-01", 10000, next_service_km=50000)

    # Current odometer at 14500 - brake fluid due soon (within 1000km)
    upcoming = temp_db.get_upcoming_maintenance(14500)
    assert len(upcoming) == 1
    assert upcoming[0]["service_type"] == "brake_fluid"

    # Current odometer at 19500 - BOTH brake fluid (overdue) AND oil (due soon)
    # Query uses current_odometer + 1000 = 20500, so both 15000 and 20000 qualify
    upcoming = temp_db.get_upcoming_maintenance(19500)
    assert len(upcoming) == 2
    service_types = [u["service_type"] for u in upcoming]
    assert "brake_fluid" in service_types
    assert "engine_oil" in service_types


def test_ai_conversations(temp_db):
    """Test AI conversation storage."""
    session_id = "test_session_123"

    # Add messages
    temp_db.add_ai_message(session_id, "user", "Hello", "qwen2.5-3b-instruct", 10)
    temp_db.add_ai_message(session_id, "assistant", "Hi there!", "qwen2.5-3b-instruct", 20)

    # Get conversation
    history = temp_db.get_ai_conversation(session_id)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "Hello"
    assert history[1]["role"] == "assistant"
    assert history[1]["content"] == "Hi there!"
    assert history[0]["tokens_used"] == 10
    assert history[1]["tokens_used"] == 20

    # Clear conversation
    result = temp_db.clear_ai_conversation(session_id)
    assert result is True

    history = temp_db.get_ai_conversation(session_id)
    assert len(history) == 0


def test_settings(temp_db):
    """Test settings storage."""
    # Set setting
    result = temp_db.set_setting("test_key", "test_value", "Test description")
    assert result is True

    # Get setting
    value = temp_db.get_setting("test_key")
    assert value == "test_value"

    # Get non-existent setting with default
    value = temp_db.get_setting("nonexistent", "default_value")
    assert value == "default_value"

    # Update setting
    result = temp_db.set_setting("test_key", "updated_value")
    assert result is True

    value = temp_db.get_setting("test_key")
    assert value == "updated_value"


def test_csv_export(temp_db):
    """Test CSV export functionality."""
    import csv

    session_id = temp_db.create_telemetry_session("Export Test", "city")

    for i in range(3):
        data = {
            "rpm": 1500 + i * 200,
            "speed_kmh": 30 + i * 10,
            "coolant_temp_c": 90.0,
            "throttle_pos_pct": 20.0,
            "engine_load_pct": 30.0,
            "is_simulated": True
        }
        temp_db.add_telemetry_record(session_id, data)

    temp_db.end_telemetry_session(session_id)

    # Export to CSV
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        csv_path = Path(f.name)

    try:
        result = temp_db.export_session_csv(session_id, csv_path)
        assert result is True
        assert csv_path.exists()

        # Verify CSV content
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3
        assert rows[0]["rpm"] == "1500.0"
        assert rows[2]["rpm"] == "1900.0"
    finally:
        if csv_path.exists():
            csv_path.unlink()


def test_database_backup(temp_db):
    """Test database backup functionality."""
    # Add some data
    temp_db.add_maintenance_record("test", "Test", "2024-01-01", 10000)

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        backup_path = Path(f.name)

    try:
        result = temp_db.backup_database(backup_path)
        assert result is True
        assert backup_path.exists()
        assert backup_path.stat().st_size > 0

        # Verify backup can be opened (disable migrations for backup)
        backup_db = DatabaseService(backup_path, run_migrations=False)
        records = backup_db.get_maintenance_records()
        assert len(records) == 1
    finally:
        if backup_path.exists():
            backup_path.unlink(missing_ok=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])