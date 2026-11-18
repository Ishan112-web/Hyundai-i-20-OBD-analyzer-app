"""
i20 AI Garage - Rule History Tests

Tests for the rule history persistence layer.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json

from services.rule_history import RuleHistoryStore
from services.rule_models import (
    RuleEvaluationResult, RuleFinding, RuleHistoryEntry,
    RuleType, RuleSeverity, RuleStatus, DataSource
)
from services.database import DatabaseService


class MockDatabaseService:
    """Mock database service for testing."""

    def __init__(self):
        self.conn = None
        self._init_db()

    def _init_db(self):
        import sqlite3
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self.conn.row_factory = sqlite3.Row

    def get_connection(self):
        class MockConnection:
            def __init__(self, conn):
                self.conn = conn

            def __enter__(self):
                return self.conn

            def __exit__(self, *args):
                pass

        return MockConnection(self.conn)

    def close(self):
        if self.conn:
            self.conn.close()


class TestRuleHistoryStore:
    """Test RuleHistoryStore class."""

    def setup_method(self):
        self.mock_db = MockDatabaseService()
        self.store = RuleHistoryStore(self.mock_db)

    def teardown_method(self):
        self.mock_db.close()

    def test_init_tables(self):
        """Test table initialization."""
        # Tables should be created in setup
        with self.mock_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            assert "rule_evaluations" in tables
            assert "rule_findings" in tables
            assert "rule_triggers" in tables

    def test_save_evaluation(self):
        """Test saving a complete evaluation."""
        findings = [
            RuleFinding(
                rule_id="RULE_1",
                rule_name="Rule 1",
                rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH,
                priority=2,
                confidence=0.9,
                status=RuleStatus.TRIGGERED,
                summary="Test finding",
                explanation="Test explanation",
                observed_values={"sensor_a": 100.0},
                evidence=["Evidence 1"],
                data_source=DataSource.SIMULATION
            )
        ]

        result = RuleEvaluationResult(
            evaluation_id="eval_test_123",
            timestamp=datetime.now(),
            rules_evaluated=5,
            rules_skipped=1,
            rules_failed=0,
            findings=findings,
            data_source=DataSource.SIMULATION,
            execution_duration_ms=15.5,
            diagnostic_session_id="diag_session_123"
        )

        success = self.store.save_evaluation(result, "diag_session_123")
        assert success is True

        # Verify in database
        with self.mock_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rule_evaluations WHERE evaluation_id = ?", ("eval_test_123",))
            row = cursor.fetchone()

            assert row is not None
            assert row["evaluation_id"] == "eval_test_123"
            assert row["rules_evaluated"] == 5
            assert row["findings_count"] == 1
            assert row["critical_findings"] == 0
            assert row["high_findings"] == 1
            assert row["diagnostic_session_id"] == "diag_session_123"

            # Check finding
            cursor.execute("SELECT * FROM rule_findings WHERE evaluation_id = ?", ("eval_test_123",))
            finding_row = cursor.fetchone()

            assert finding_row is not None
            assert finding_row["rule_id"] == "RULE_1"
            assert finding_row["severity"] == "high"
            assert finding_row["confidence"] == 0.9

    def test_save_evaluation_multiple_findings(self):
        """Test saving evaluation with multiple findings of different severities."""
        findings = [
            RuleFinding(
                rule_id="CRITICAL_RULE", rule_name="Critical", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.CRITICAL, priority=1, confidence=0.95,
                status=RuleStatus.TRIGGERED, summary="", explanation="",
                data_source=DataSource.SIMULATION
            ),
            RuleFinding(
                rule_id="HIGH_RULE", rule_name="High", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                status=RuleStatus.TRIGGERED, summary="", explanation="",
                data_source=DataSource.SIMULATION
            ),
            RuleFinding(
                rule_id="MEDIUM_RULE", rule_name="Medium", rule_type=RuleType.TREND,
                severity=RuleSeverity.MEDIUM, priority=5, confidence=0.8,
                status=RuleStatus.TRIGGERED, summary="", explanation="",
                data_source=DataSource.SIMULATION
            ),
            RuleFinding(
                rule_id="LOW_RULE", rule_name="Low", rule_type=RuleType.CORRELATION,
                severity=RuleSeverity.LOW, priority=8, confidence=0.7,
                status=RuleStatus.TRIGGERED, summary="", explanation="",
                data_source=DataSource.SIMULATION
            ),
            RuleFinding(
                rule_id="INFO_RULE", rule_name="Info", rule_type=RuleType.COMPOSITE,
                severity=RuleSeverity.INFORMATIONAL, priority=10, confidence=0.6,
                status=RuleStatus.TRIGGERED, summary="", explanation="",
                data_source=DataSource.SIMULATION
            )
        ]

        result = RuleEvaluationResult(
            evaluation_id="eval_multi",
            timestamp=datetime.now(),
            rules_evaluated=10,
            findings=findings,
            data_source=DataSource.SIMULATION
        )

        self.store.save_evaluation(result)

        with self.mock_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM rule_evaluations WHERE evaluation_id = ?", ("eval_multi",))
            row = cursor.fetchone()

            assert row["critical_findings"] == 1
            assert row["high_findings"] == 1
            assert row["medium_findings"] == 1
            assert row["low_findings"] == 2  # low + informational

    def test_get_history(self):
        """Test retrieving evaluation history."""
        # Save a few evaluations
        for i in range(3):
            findings = [
                RuleFinding(
                    rule_id=f"RULE_{i}", rule_name=f"Rule {i}", rule_type=RuleType.THRESHOLD,
                    severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                    status=RuleStatus.TRIGGERED, summary="", explanation="",
                    data_source=DataSource.SIMULATION
                )
            ]

            result = RuleEvaluationResult(
                evaluation_id=f"eval_{i}",
                timestamp=datetime.now() - timedelta(hours=i),
                rules_evaluated=5,
                findings=findings,
                data_source=DataSource.SIMULATION
            )

            self.store.save_evaluation(result)

        history = self.store.get_history(limit=10)

        assert len(history) == 3
        # Should be ordered by timestamp DESC (newest first)
        assert history[0]["evaluation_id"] == "eval_0"
        assert history[1]["evaluation_id"] == "eval_1"
        assert history[2]["evaluation_id"] == "eval_2"

    def test_get_history_with_filters(self):
        """Test history retrieval with filters."""
        # Save evaluations with different sessions
        for session_id in ["session_1", "session_2"]:
            for i in range(2):
                findings = [
                    RuleFinding(
                        rule_id=f"RULE_{session_id}_{i}", rule_name=f"Rule",
                        rule_type=RuleType.THRESHOLD, severity=RuleSeverity.HIGH,
                        priority=2, confidence=0.9, status=RuleStatus.TRIGGERED,
                        summary="", explanation="", data_source=DataSource.SIMULATION
                    )
                ]

                result = RuleEvaluationResult(
                    evaluation_id=f"eval_{session_id}_{i}",
                    timestamp=datetime.now(),
                    rules_evaluated=5,
                    findings=findings,
                    data_source=DataSource.SIMULATION,
                    diagnostic_session_id=session_id
                )

                self.store.save_evaluation(result, session_id)

        # Filter by session
        history = self.store.get_history(diagnostic_session_id="session_1")
        assert len(history) == 2
        assert all(h["diagnostic_session_id"] == "session_1" for h in history)

    def test_get_findings_for_rule(self):
        """Test retrieving findings for a specific rule."""
        for i in range(3):
            findings = [
                RuleFinding(
                    rule_id="TARGET_RULE", rule_name="Target Rule", rule_type=RuleType.THRESHOLD,
                    severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                    status=RuleStatus.TRIGGERED, summary="", explanation="",
                    data_source=DataSource.SIMULATION
                ),
                RuleFinding(
                    rule_id=f"OTHER_RULE_{i}", rule_name=f"Other {i}", rule_type=RuleType.THRESHOLD,
                    severity=RuleSeverity.MEDIUM, priority=5, confidence=0.8,
                    status=RuleStatus.TRIGGERED, summary="", explanation="",
                    data_source=DataSource.SIMULATION
                )
            ]

            result = RuleEvaluationResult(
                evaluation_id=f"eval_{i}",
                timestamp=datetime.now() - timedelta(hours=i),
                rules_evaluated=5,
                findings=findings,
                data_source=DataSource.SIMULATION
            )

            self.store.save_evaluation(result)

        findings = self.store.get_findings_for_rule("TARGET_RULE", limit=10)

        assert len(findings) == 3
        assert all(f["rule_id"] == "TARGET_RULE" for f in findings)
        # Should be ordered by timestamp DESC
        assert findings[0]["evaluation_id"] == "eval_0"

    def test_get_findings_for_evaluation(self):
        """Test retrieving all findings for an evaluation."""
        findings = [
            RuleFinding(
                rule_id=f"RULE_{i}", rule_name=f"Rule {i}", rule_type=RuleType.THRESHOLD,
                severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                status=RuleStatus.TRIGGERED, summary="", explanation="",
                data_source=DataSource.SIMULATION
            )
            for i in range(3)
        ]

        result = RuleEvaluationResult(
            evaluation_id="eval_findings_test",
            timestamp=datetime.now(),
            rules_evaluated=5,
            findings=findings,
            data_source=DataSource.SIMULATION
        )

        self.store.save_evaluation(result)

        retrieved = self.store.get_findings_for_evaluation("eval_findings_test")

        assert len(retrieved) == 3
        assert all(f["evaluation_id"] == "eval_findings_test" for f in retrieved)

    def test_get_recent_triggers(self):
        """Test retrieving recent triggers for cooldown checking."""
        # Save triggers at different times
        old_time = datetime.now() - timedelta(hours=2)
        recent_time = datetime.now() - timedelta(minutes=30)

        # Direct insert for testing
        with self.mock_db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO rule_triggers (rule_id, finding_id, timestamp, severity, confidence, matched, vehicle_id, diagnostic_session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("TEST_RULE", "find_old", old_time.isoformat(), "high", 0.9, 1, None, "session_1"))
            cursor.execute("""
                INSERT INTO rule_triggers (rule_id, finding_id, timestamp, severity, confidence, matched, vehicle_id, diagnostic_session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, ("TEST_RULE", "find_recent", recent_time.isoformat(), "high", 0.9, 1, None, "session_1"))
            conn.commit()

        # Get triggers from last hour
        since = datetime.now() - timedelta(hours=1)
        triggers = self.store.get_recent_triggers("TEST_RULE", since)

        assert len(triggers) == 1
        assert triggers[0]["finding_id"] == "find_recent"

    def test_get_statistics(self):
        """Test statistics retrieval."""
        # Save some evaluations
        for i in range(5):
            findings = [
                RuleFinding(
                    rule_id=f"RULE_{i}", rule_name=f"Rule {i}", rule_type=RuleType.THRESHOLD,
                    severity=RuleSeverity.HIGH if i < 2 else RuleSeverity.MEDIUM,
                    priority=2, confidence=0.9,
                    status=RuleStatus.TRIGGERED, summary="", explanation="",
                    data_source=DataSource.SIMULATION
                )
            ]

            result = RuleEvaluationResult(
                evaluation_id=f"eval_stat_{i}",
                timestamp=datetime.now() - timedelta(hours=i),
                rules_evaluated=5,
                findings=findings,
                data_source=DataSource.SIMULATION
            )

            self.store.save_evaluation(result)

        stats = self.store.get_statistics()

        assert stats["total_evaluations"] == 5
        assert stats["total_findings"] == 5
        assert stats["findings_by_severity"]["high"] == 2
        assert stats["findings_by_severity"]["medium"] == 3
        assert stats["findings_by_type"]["threshold"] == 5
        assert len(stats["top_triggered_rules"]) == 5
        assert stats["evaluations_last_24h"] == 5

    def test_cleanup_old_records(self):
        """Test cleaning up old records."""
        # Save old and new evaluations
        old_time = datetime.now() - timedelta(days=45)
        new_time = datetime.now() - timedelta(days=5)

        for ts, suffix in [(old_time, "old"), (new_time, "new")]:
            findings = [
                RuleFinding(
                    rule_id=f"RULE_{suffix}", rule_name=f"Rule {suffix}", rule_type=RuleType.THRESHOLD,
                    severity=RuleSeverity.HIGH, priority=2, confidence=0.9,
                    status=RuleStatus.TRIGGERED, summary="", explanation="",
                    data_source=DataSource.SIMULATION
                )
            ]

            result = RuleEvaluationResult(
                evaluation_id=f"eval_{suffix}",
                timestamp=ts,
                rules_evaluated=5,
                findings=findings,
                data_source=DataSource.SIMULATION
            )

            self.store.save_evaluation(result)

        # Cleanup keeping 30 days
        deleted = self.store.cleanup_old_records(days_to_keep=30)

        # Should have deleted old records
        assert deleted > 0

        # Verify new records remain
        history = self.store.get_history(limit=10)
        assert len(history) == 1
        assert history[0]["evaluation_id"] == "eval_new"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])