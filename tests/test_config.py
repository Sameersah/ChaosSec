"""Tests for config module."""

import os
import pytest
from unittest.mock import patch, MagicMock

from chaossec.config import (
    decode_bedrock_key,
    load_config,
    validate_config,
    ChaosSecConfig,
    AWSConfig
)


def test_decode_bedrock_key():
    """Test Bedrock key decoding."""
    # Base64 encoded "test-key"
    encoded = "dGVzdC1rZXk="
    decoded = decode_bedrock_key(encoded)
    assert decoded == "test-key"


def test_decode_bedrock_key_invalid():
    """Test invalid Bedrock key."""
    with pytest.raises(ValueError):
        decode_bedrock_key("invalid!!!base64")


@patch.dict(os.environ, {
    'AWS_REGION': 'us-east-1',
    'AWS_ACCOUNT_ID': '123456789',
    'BEDROCK_API_KEY': 'dGVzdC1rZXk=',
    'SYSTEM_INITIATIVE_API_KEY': 'si-test-key',
    'CHAOSSEC_SAFETY_MODE': 'true'
})
def test_load_config():
    """Test config loading from environment."""
    config = load_config()
    
    assert config.aws.region == 'us-east-1'
    assert config.aws.account_id == '123456789'
    assert config.aws.bedrock_api_key == 'test-key'
    assert config.safety_mode is True


def test_validate_config():
    """Test config validation."""
    config = ChaosSecConfig(
        aws=AWSConfig(
            region='us-east-1',
            account_id='123',
            bedrock_api_key='key'
        ),
        system_initiative=MagicMock(api_key='si-key'),
        vanta=MagicMock(api_key='vanta-key')
    )
    
    assert validate_config(config) is True


def test_validate_config_missing_region():
    """Test validation with missing region."""
    config = ChaosSecConfig(
        aws=AWSConfig(
            region='',
            account_id='123',
            bedrock_api_key='key'
        ),
        system_initiative=MagicMock(api_key='si-key'),
        vanta=MagicMock(api_key='vanta-key')
    )
    
    with pytest.raises(ValueError, match="AWS region is required"):
        validate_config(config)

