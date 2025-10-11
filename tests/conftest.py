"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import Mock, MagicMock

from chaossec.logger import ChaosSecLogger


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=ChaosSecLogger)
    logger.correlation_id = "test-correlation-id"
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.audit = Mock()
    return logger


@pytest.fixture
def mock_boto3_client(monkeypatch):
    """Mock boto3 clients."""
    mock_client = MagicMock()
    
    def mock_boto3_client_factory(service_name, **kwargs):
        return mock_client
    
    import boto3
    monkeypatch.setattr(boto3, "client", mock_boto3_client_factory)
    
    return mock_client


@pytest.fixture
def sample_semgrep_results():
    """Sample Semgrep scan results."""
    return {
        "status": "success",
        "findings": [
            {
                "rule_id": "python.lang.security.audit.dangerous-system-call",
                "severity": "ERROR",
                "message": "Dangerous system call detected",
                "file": "test.py",
                "line": 10,
                "code": "os.system(user_input)"
            },
            {
                "rule_id": "aws.s3.public-bucket",
                "severity": "WARNING",
                "message": "S3 bucket configured with public access",
                "file": "infrastructure/s3.tf",
                "line": 5,
                "code": "acl = 'public-read'"
            }
        ],
        "finding_count": 2,
        "severity_breakdown": {
            "ERROR": 1,
            "WARNING": 1,
            "INFO": 0
        }
    }


@pytest.fixture
def sample_aws_resources():
    """Sample AWS resources for testing."""
    return [
        {
            "type": "aws_s3_bucket",
            "name": "test-bucket",
            "properties": {
                "bucket": "test-bucket",
                "acl": "private"
            }
        }
    ]


@pytest.fixture
def sample_chaos_result():
    """Sample chaos test result."""
    return {
        "bucket": "test-bucket",
        "action": "make_public",
        "applied": False,
        "safety_mode": True,
        "outcome": "success"
    }


@pytest.fixture
def sample_bedrock_response():
    """Sample AWS Bedrock response."""
    return {
        "target_resource": "s3-test-bucket",
        "chaos_type": "make_s3_public",
        "expected_outcome": "Security controls should detect",
        "validation_criteria": "Config rule violation detected",
        "compliance_control": "SOC2:CC6.6",
        "reasoning": "Testing S3 public access detection"
    }


@pytest.fixture
def mock_vanta_config():
    """Mock Vanta configuration with OAuth."""
    return {
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "api_url": "https://api.vanta.com",
        "oauth_token_url": "https://api.vanta.com/oauth/token"
    }

