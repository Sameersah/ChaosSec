"""Tests for agent brain module."""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock

from chaossec.agent_brain import AgentBrain


def test_analyze_history_empty(mock_logger):
    """Test analyzing empty history."""
    brain = AgentBrain(
        region='us-east-1',
        bedrock_api_key='test-key',
        logger=mock_logger
    )
    
    analysis = brain.analyze_history([])
    
    assert analysis['total_tests'] == 0
    assert analysis['success_rate'] == 0.0


def test_analyze_history_with_data(mock_logger):
    """Test analyzing history with data."""
    brain = AgentBrain(
        region='us-east-1',
        bedrock_api_key='test-key',
        logger=mock_logger
    )
    
    past_results = [
        {"outcome": "success", "test": "test1"},
        {"outcome": "failure", "test": "test2", "failure_type": "timeout"},
        {"outcome": "success", "test": "test3"}
    ]
    
    analysis = brain.analyze_history(past_results)
    
    assert analysis['total_tests'] == 3
    assert analysis['successful_tests'] == 2
    assert analysis['failed_tests'] == 1
    assert analysis['success_rate'] == pytest.approx(0.666, rel=0.01)


def test_evaluate_risk_score(mock_logger):
    """Test risk score evaluation."""
    brain = AgentBrain(
        region='us-east-1',
        bedrock_api_key='test-key',
        logger=mock_logger
    )
    
    semgrep_findings = [
        {"severity": "ERROR"},
        {"severity": "ERROR"},
        {"severity": "WARNING"}
    ]
    
    config_compliance = [
        {"compliance_type": "NON_COMPLIANT"},
        {"compliance_type": "COMPLIANT"}
    ]
    
    previous_failures = [
        {"outcome": "failure"}
    ]
    
    risk = brain.evaluate_risk_score(
        semgrep_findings,
        config_compliance,
        previous_failures
    )
    
    assert risk['risk_score'] > 0
    assert risk['risk_level'] in ['MINIMAL', 'LOW', 'MEDIUM', 'HIGH']
    assert len(risk['risk_factors']) > 0


def test_fallback_recommendation(mock_logger):
    """Test fallback recommendation."""
    brain = AgentBrain(
        region='us-east-1',
        bedrock_api_key='test-key',
        logger=mock_logger
    )
    
    recommendation = brain._fallback_recommendation({})
    
    assert 'target_resource' in recommendation
    assert 'chaos_type' in recommendation
    assert recommendation['fallback'] is True


@patch('chaossec.agent_brain.boto3')
def test_parse_bedrock_response(mock_boto3, mock_logger, sample_bedrock_response):
    """Test parsing Bedrock response."""
    brain = AgentBrain(
        region='us-east-1',
        bedrock_api_key='test-key',
        logger=mock_logger
    )
    
    response_json = json.dumps(sample_bedrock_response)
    parsed = brain._parse_bedrock_response(response_json)
    
    assert parsed['target_resource'] == sample_bedrock_response['target_resource']
    assert parsed['chaos_type'] == sample_bedrock_response['chaos_type']

