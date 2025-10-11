"""Tests for orchestrator module."""

import pytest
from unittest.mock import patch, MagicMock

from chaossec.orchestrator import ChaosSecOrchestrator


@patch('chaossec.orchestrator.load_config')
@patch('chaossec.orchestrator.create_logger')
def test_orchestrator_initialization(mock_logger, mock_config):
    """Test orchestrator initialization."""
    mock_config.return_value = MagicMock(
        safety_mode=True,
        log_level='INFO',
        aws=MagicMock(region='us-east-1', bedrock_api_key='test'),
        system_initiative=MagicMock(api_url='http://test', api_key='test', workspace_id=None),
        vanta=MagicMock(api_key='test', api_url='http://test')
    )
    mock_logger.return_value = MagicMock()
    
    orchestrator = ChaosSecOrchestrator()
    
    assert orchestrator.config.safety_mode is True
    assert orchestrator.correlation_id is not None
    assert len(orchestrator.execution_history) == 0


@patch('chaossec.orchestrator.load_config')
@patch('chaossec.orchestrator.create_logger')
def test_orchestrator_single_iteration(mock_logger, mock_config, mock_boto3_client):
    """Test running a single orchestrator iteration."""
    # Setup mocks
    mock_config.return_value = MagicMock(
        safety_mode=True,
        log_level='INFO',
        aws=MagicMock(region='us-east-1', bedrock_api_key='test'),
        system_initiative=MagicMock(api_url='http://test', api_key='test', workspace_id=None),
        vanta=MagicMock(api_key='test', api_url='http://test')
    )
    
    mock_logger_instance = MagicMock()
    mock_logger_instance.correlation_id = 'test-id'
    mock_logger.return_value = mock_logger_instance
    
    orchestrator = ChaosSecOrchestrator()
    
    # Mock all the steps
    with patch.object(orchestrator, '_step_simulate', return_value={"twin_id": "test-twin"}):
        with patch.object(orchestrator, '_step_scan', return_value={"total_findings": 0}):
            with patch.object(orchestrator, '_step_reason', return_value={"chaos_type": "test"}):
                with patch.object(orchestrator, '_step_inject_chaos', return_value={"applied": False}):
                    with patch.object(orchestrator, '_step_monitor', return_value={"metrics": []}):
                        with patch.object(orchestrator, '_step_validate', return_value={"outcome": "success"}):
                            with patch.object(orchestrator, '_step_report', return_value={"evidence_count": 1}):
                                with patch.object(orchestrator, '_step_learn', return_value={"stored": True}):
                                    result = orchestrator._run_single_iteration(None)
    
    assert result['status'] == 'success'
    assert 'steps' in result


@patch('chaossec.orchestrator.load_config')
@patch('chaossec.orchestrator.create_logger')
def test_orchestrator_get_summary(mock_logger, mock_config):
    """Test getting orchestrator summary."""
    mock_config.return_value = MagicMock(
        safety_mode=True,
        log_level='INFO',
        aws=MagicMock(region='us-east-1', bedrock_api_key='test'),
        system_initiative=MagicMock(api_url='http://test', api_key='test', workspace_id=None),
        vanta=MagicMock(api_key='test', api_url='http://test')
    )
    mock_logger.return_value = MagicMock()
    
    orchestrator = ChaosSecOrchestrator()
    summary = orchestrator.get_summary()
    
    assert 'correlation_id' in summary
    assert 'safety_mode' in summary
    assert summary['execution_count'] == 0

