"""Tests for semgrep scanner."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from chaossec.semgrep_scan import SemgrepScanner


def test_parse_semgrep_json(mock_logger, sample_semgrep_results):
    """Test parsing Semgrep JSON output."""
    scanner = SemgrepScanner(mock_logger)
    
    semgrep_output = json.dumps({
        "results": [
            {
                "check_id": "test-rule",
                "path": "test.py",
                "start": {"line": 10},
                "extra": {
                    "severity": "ERROR",
                    "message": "Test finding",
                    "lines": "test code"
                }
            }
        ]
    })
    
    result = scanner.parse_semgrep_json(semgrep_output)
    
    assert result['status'] == 'success'
    assert result['finding_count'] == 1
    assert result['findings'][0]['severity'] == 'ERROR'


def test_filter_findings_by_severity(mock_logger):
    """Test filtering findings by severity."""
    scanner = SemgrepScanner(mock_logger)
    
    findings = [
        {"severity": "ERROR", "message": "Critical"},
        {"severity": "WARNING", "message": "Medium"},
        {"severity": "INFO", "message": "Low"}
    ]
    
    filtered = scanner.filter_findings_by_severity(findings, min_severity="WARNING")
    
    assert len(filtered) == 2
    assert all(f['severity'] in ['ERROR', 'WARNING'] for f in filtered)


def test_get_high_risk_findings(mock_logger):
    """Test extracting high-risk findings."""
    scanner = SemgrepScanner(mock_logger)
    
    scan_results = {
        "findings": [
            {"severity": "ERROR", "message": "Critical 1"},
            {"severity": "ERROR", "message": "Critical 2"},
            {"severity": "WARNING", "message": "Warning 1"}
        ]
    }
    
    high_risk = scanner.get_high_risk_findings(scan_results)
    
    assert len(high_risk) == 2
    assert all(f['severity'] == 'ERROR' for f in high_risk)


def test_generate_custom_rule(mock_logger):
    """Test generating custom Semgrep rule."""
    scanner = SemgrepScanner(mock_logger)
    
    rule = scanner.generate_custom_rule(
        rule_id="test-rule",
        pattern="os.system(...)",
        message="Test rule",
        severity="ERROR",
        languages=["python"]
    )
    
    assert "rules" in rule
    assert rule["rules"][0]["id"] == "test-rule"
    assert rule["rules"][0]["severity"] == "ERROR"

