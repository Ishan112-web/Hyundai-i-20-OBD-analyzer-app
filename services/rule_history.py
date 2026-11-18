"""
i20 AI Garage - Rule History Store

Persistence layer for rule evaluation history.
Stores evaluation results and findings in SQLite database.
"""

import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

from .database import DatabaseService
from .rule_models import (
    RuleEvaluationResult, RuleFinding, RuleHistoryEntry, RuleSeverity,
    RuleStatus, DataSource, RuleType
)

logger = logging.getLogger(__name__)


class RuleHistoryStore:
    """Database-backed storage for rule evaluation history."""

    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self._init_tables()

    def _init_tables(self) -> None:
        """Initialize database tables for rule history."""
        with self.db_service.get_connection() as conn:
            cursor = conn.cursor()

            # Rule evaluations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rule_evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_id TEXT UNIQUE NOT NULL,
                    timestamp TEXT NOT NULL,
                    vehicle_id TEXT,
                    diagnostic_session_id TEXT,
                    rules_evaluated INTEGER DEFAULT 0,
                    rules_skipped INTEGER DEFAULT 0,
                    rules_failed INTEGER DEFAULT 0,
                    findings_count INTEGER DEFAULT 0,
                    critical_findings INTEGER DEFAULT 0,
                    high_findings INTEGER DEFAULT 0,
                    medium_findings INTEGER DEFAULT 0,
                    low_findings INTEGER DEFAULT 0,
                    data_quality TEXT,
                    data_source TEXT,
                    execution_duration_ms REAL,
                    evaluation_json TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Rule findings table (individual findings)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rule_findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    evaluation_id TEXT NOT NULL,
                    finding_id TEXT UNIQUE NOT NULL,
                    rule_id TEXT NOT NULL,
                    rule_name TEXT,
                    rule_type TEXT,
                    timestamp TEXT NOT NULL,
                    severity TEXT,
                    priority INTEGER,
                    confidence REAL,
                    status TEXT,
                    summary TEXT,
                    explanation TEXT,
                    observed_values TEXT,
                    expected_values TEXT,
                    evidence TEXT,
                    missing_data TEXT,
                    recommended_checks TEXT,
                    recommended_actions TEXT,
                    safety_notes TEXT,
                    data_source TEXT,
                    diagnostic_session_id TEXT,
                    rule_source TEXT,
                    dtc_hints TEXT,
                    evaluation_duration_ms REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (evaluation_id) REFERENCES rule_evaluations(evaluation_id)
                )
            """)

            # Rule trigger history (for cooldown tracking)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rule_triggers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rule_id TEXT NOT NULL,
                    finding_id TEXT,
                    timestamp TEXT NOT NULL,
                    severity TEXT,
                    confidence REAL,
                    matched BOOLEAN,
                    vehicle_id TEXT,
                    diagnostic_session_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Create indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_eval_timestamp
                ON rule_evaluations(timestamp)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_eval_session
                ON rule_evaluations(diagnostic_session_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_findings_eval
                ON rule_findings(evaluation_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_findings_rule
                ON rule_findings(rule_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_findings_severity
                ON rule_findings(severity)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_triggers_rule
                ON rule_triggers(rule_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_rule_triggers_timestamp
                ON rule_triggers(timestamp)
            """)

            conn.commit()
            logger.debug("Rule history tables initialized")

    def save_evaluation(self,
                       result: RuleEvaluationResult,
                       diagnostic_session_id: Optional[str] = None) -> bool:
        """
        Save a complete rule evaluation result.

        Args:
            result: RuleEvaluationResult to save
            diagnostic_session_id: Optional session ID for grouping

        Returns:
            True if saved successfully
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()

                # Count findings by severity
                severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "informational": 0}
                for finding in result.findings:
                    severity_counts[finding.severity.value] = severity_counts.get(finding.severity.value, 0) + 1

                # Insert evaluation record
                cursor.execute("""
                    INSERT OR REPLACE INTO rule_evaluations (
                        evaluation_id, timestamp, vehicle_id, diagnostic_session_id,
                        rules_evaluated, rules_skipped, rules_failed, findings_count,
                        critical_findings, high_findings, medium_findings, low_findings,
                        data_quality, data_source, execution_duration_ms, evaluation_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.evaluation_id,
                    result.timestamp.isoformat(),
                    None,  # vehicle_id - would come from vehicle profile
                    diagnostic_session_id or result.diagnostic_session_id,
                    result.rules_evaluated,
                    result.rules_skipped,
                    result.rules_failed,
                    len(result.findings),
                    severity_counts["critical"],
                    severity_counts["high"],
                    severity_counts["medium"],
                    severity_counts["low"] + severity_counts["informational"],
                    result.data_quality,
                    result.data_source.value,
                    result.execution_duration_ms,
                    json.dumps(self._evaluation_to_dict(result))
                ))

                # Insert individual findings
                for finding in result.findings:
                    self._save_finding(cursor, finding, result.evaluation_id)

                conn.commit()
                logger.debug(f"Saved evaluation {result.evaluation_id} with {len(result.findings)} findings")
                return True

        except Exception as e:
            logger.error(f"Failed to save rule evaluation: {e}")
            return False

    def _save_finding(self, cursor: sqlite3.Cursor,
                     finding: RuleFinding, evaluation_id: str) -> None:
        """Save a single finding."""
        cursor.execute("""
            INSERT OR REPLACE INTO rule_findings (
                evaluation_id, finding_id, rule_id, rule_name, rule_type,
                timestamp, severity, priority, confidence, status,
                summary, explanation, observed_values, expected_values,
                evidence, missing_data, recommended_checks, recommended_actions,
                safety_notes, data_source, diagnostic_session_id,
                rule_source, dtc_hints, evaluation_duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            evaluation_id,
            finding.finding_id,
            finding.rule_id,
            finding.rule_name,
            finding.rule_type.value,
            finding.timestamp.isoformat(),
            finding.severity.value,
            finding.priority,
            finding.confidence,
            finding.status.value,
            finding.summary,
            finding.explanation,
            json.dumps(finding.observed_values),
            json.dumps(finding.expected_values),
            json.dumps(finding.evidence),
            json.dumps(finding.missing_data),
            json.dumps(finding.recommended_checks),
            json.dumps(finding.recommended_actions),
            json.dumps(finding.safety_notes),
            finding.data_source.value,
            finding.diagnostic_session_id,
            finding.rule_source,
            json.dumps(finding.dtc_hints),
            finding.evaluation_duration_ms
        ))

        # Also save to triggers for cooldown tracking
        cursor.execute("""
            INSERT INTO rule_triggers (
                rule_id, finding_id, timestamp, severity, confidence,
                matched, vehicle_id, diagnostic_session_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding.rule_id,
            finding.finding_id,
            finding.timestamp.isoformat(),
            finding.severity.value,
            finding.confidence,
            finding.status == RuleStatus.TRIGGERED,
            None,  # vehicle_id
            finding.diagnostic_session_id
        ))

    def _evaluation_to_dict(self, result: RuleEvaluationResult) -> Dict:
        """Convert evaluation to dict for JSON storage."""
        return {
            "evaluation_id": result.evaluation_id,
            "timestamp": result.timestamp.isoformat(),
            "rules_evaluated": result.rules_evaluated,
            "rules_skipped": result.rules_skipped,
            "rules_failed": result.rules_failed,
            "findings_count": len(result.findings),
            "data_quality": result.data_quality,
            "data_source": result.data_source.value,
            "execution_duration_ms": result.execution_duration_ms,
            "finding_ids": [f.finding_id for f in result.findings],
            "evaluation_errors": result.evaluation_errors
        }

    def get_history(self,
                   limit: int = 100,
                   rule_id: Optional[str] = None,
                   severity: Optional[RuleSeverity] = None,
                   start_time: Optional[datetime] = None,
                   end_time: Optional[datetime] = None,
                   diagnostic_session_id: Optional[str] = None) -> List[Dict]:
        """
        Get rule evaluation history.

        Args:
            limit: Maximum records to return
            rule_id: Filter by rule ID
            severity: Filter by severity
            start_time: Filter by start time
            end_time: Filter by end time
            diagnostic_session_id: Filter by session

        Returns:
            List of evaluation records
        """
        query = "SELECT * FROM rule_evaluations WHERE 1=1"
        params = []

        if rule_id:
            query += " AND evaluation_json LIKE ?"
            params.append(f"%\"rule_id\": \"{rule_id}\"%")

        if severity:
            # Need to join with findings for severity filter
            query = """
                SELECT DISTINCT e.* FROM rule_evaluations e
                JOIN rule_findings f ON e.evaluation_id = f.evaluation_id
                WHERE f.severity = ?
            """
            params = [severity.value]

            if rule_id:
                query += " AND f.rule_id = ?"
                params.append(rule_id)

        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat())

        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat())

        if diagnostic_session_id:
            query += " AND diagnostic_session_id = ?"
            params.append(diagnostic_session_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            with self.db_service.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get rule history: {e}")
            return []

    def get_findings_for_rule(self,
                             rule_id: str,
                             limit: int = 50) -> List[Dict]:
        """Get finding history for a specific rule."""
        try:
            with self.db_service.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM rule_findings
                    WHERE rule_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (rule_id, limit))
                rows = cursor.fetchall()

                return [self._row_to_finding_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get findings for rule {rule_id}: {e}")
            return []

    def get_findings_for_evaluation(self, evaluation_id: str) -> List[Dict]:
        """Get all findings for a specific evaluation."""
        try:
            with self.db_service.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM rule_findings
                    WHERE evaluation_id = ?
                    ORDER BY priority ASC, severity DESC
                """, (evaluation_id,))
                rows = cursor.fetchall()

                return [self._row_to_finding_dict(row) for row in rows]

        except Exception as e:
            logger.error(f"Failed to get findings for evaluation {evaluation_id}: {e}")
            return []

    def _row_to_finding_dict(self, row: sqlite3.Row) -> Dict:
        """Convert database row to finding dictionary."""
        return {
            "id": row["id"],
            "evaluation_id": row["evaluation_id"],
            "finding_id": row["finding_id"],
            "rule_id": row["rule_id"],
            "rule_name": row["rule_name"],
            "rule_type": row["rule_type"],
            "timestamp": row["timestamp"],
            "severity": row["severity"],
            "priority": row["priority"],
            "confidence": row["confidence"],
            "status": row["status"],
            "summary": row["summary"],
            "explanation": row["explanation"],
            "observed_values": json.loads(row["observed_values"]) if row["observed_values"] else {},
            "expected_values": json.loads(row["expected_values"]) if row["expected_values"] else {},
            "evidence": json.loads(row["evidence"]) if row["evidence"] else [],
            "missing_data": json.loads(row["missing_data"]) if row["missing_data"] else [],
            "recommended_checks": json.loads(row["recommended_checks"]) if row["recommended_checks"] else [],
            "recommended_actions": json.loads(row["recommended_actions"]) if row["recommended_actions"] else [],
            "safety_notes": json.loads(row["safety_notes"]) if row["safety_notes"] else [],
            "data_source": row["data_source"],
            "diagnostic_session_id": row["diagnostic_session_id"],
            "rule_source": row["rule_source"],
            "dtc_hints": json.loads(row["dtc_hints"]) if row["dtc_hints"] else [],
            "evaluation_duration_ms": row["evaluation_duration_ms"],
            "created_at": row["created_at"]
        }

    def get_recent_triggers(self,
                           rule_id: str,
                           since: datetime) -> List[Dict]:
        """Get recent triggers for a rule (for cooldown checking)."""
        try:
            with self.db_service.get_connection() as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM rule_triggers
                    WHERE rule_id = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                """, (rule_id, since.isoformat()))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get recent triggers: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get rule history statistics."""
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()

                stats = {}

                # Total evaluations
                cursor.execute("SELECT COUNT(*) FROM rule_evaluations")
                stats["total_evaluations"] = cursor.fetchone()[0]

                # Total findings
                cursor.execute("SELECT COUNT(*) FROM rule_findings")
                stats["total_findings"] = cursor.fetchone()[0]

                # Findings by severity
                cursor.execute("""
                    SELECT severity, COUNT(*) FROM rule_findings
                    GROUP BY severity
                """)
                stats["findings_by_severity"] = dict(cursor.fetchall())

                # Findings by rule type
                cursor.execute("""
                    SELECT rule_type, COUNT(*) FROM rule_findings
                    GROUP BY rule_type
                """)
                stats["findings_by_type"] = dict(cursor.fetchall())

                # Most triggered rules
                cursor.execute("""
                    SELECT rule_id, rule_name, COUNT(*) as count
                    FROM rule_findings
                    WHERE status = 'triggered'
                    GROUP BY rule_id, rule_name
                    ORDER BY count DESC
                    LIMIT 10
                """)
                stats["top_triggered_rules"] = [
                    {"rule_id": r[0], "rule_name": r[1], "count": r[2]}
                    for r in cursor.fetchall()
                ]

                # Recent activity (last 24h)
                cursor.execute("""
                    SELECT COUNT(*) FROM rule_evaluations
                    WHERE timestamp >= datetime('now', '-1 day')
                """)
                stats["evaluations_last_24h"] = cursor.fetchone()[0]

                cursor.execute("""
                    SELECT COUNT(*) FROM rule_findings
                    WHERE timestamp >= datetime('now', '-1 day')
                """)
                stats["findings_last_24h"] = cursor.fetchone()[0]

                return stats

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

    def cleanup_old_records(self, days_to_keep: int = 30) -> int:
        """
        Clean up old history records.

        Args:
            days_to_keep: Number of days of history to retain

        Returns:
            Number of records deleted
        """
        try:
            with self.db_service.get_connection() as conn:
                cursor = conn.cursor()

                # Delete old findings first (foreign key)
                cursor.execute("""
                    DELETE FROM rule_findings
                    WHERE timestamp < datetime('now', ?)
                """, (f'-{days_to_keep} days',))
                findings_deleted = cursor.rowcount

                # Delete old evaluations
                cursor.execute("""
                    DELETE FROM rule_evaluations
                    WHERE timestamp < datetime('now', ?)
                """, (f'-{days_to_keep} days',))
                evals_deleted = cursor.rowcount

                # Delete old triggers
                cursor.execute("""
                    DELETE FROM rule_triggers
                    WHERE timestamp < datetime('now', ?)
                """, (f'-{days_to_keep} days',))
                triggers_deleted = cursor.rowcount

                conn.commit()

                total = findings_deleted + evals_deleted + triggers_deleted
                logger.info(f"Cleaned up {total} old rule history records")
                return total

        except Exception as e:
            logger.error(f"Failed to cleanup old records: {e}")
            return 0


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "RuleHistoryStore",
]