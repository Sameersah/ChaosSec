"""Configuration management for ChaosSec."""

import base64
import json
import os
from dataclasses import dataclass
from typing import Optional

import boto3
from botocore.exceptions import ClientError


@dataclass
class AWSConfig:
    """AWS configuration settings."""

    region: str
    account_id: str
    bedrock_api_key: str


@dataclass
class SystemInitiativeConfig:
    """System Initiative API configuration."""

    api_url: str
    api_key: str
    workspace_id: Optional[str] = None


@dataclass
class VantaConfig:
    """Vanta MCP API configuration with OAuth2."""

    client_id: str
    client_secret: str
    api_url: str = "https://api.vanta.com"
    oauth_token_url: str = "https://api.vanta.com/oauth/token"


@dataclass
class ChaosSecConfig:
    """Main ChaosSec configuration."""

    aws: AWSConfig
    system_initiative: SystemInitiativeConfig
    vanta: VantaConfig
    safety_mode: bool = True
    log_level: str = "INFO"


def decode_bedrock_key(encoded_key: str) -> str:
    """Decode base64-encoded Bedrock API key.
    
    Args:
        encoded_key: Base64-encoded API key
        
    Returns:
        Decoded API key string
    """
    try:
        decoded_bytes = base64.b64decode(encoded_key)
        return decoded_bytes.decode('utf-8')
    except Exception as e:
        raise ValueError(f"Failed to decode Bedrock API key: {e}")


def load_secret_from_secrets_manager(secret_name: str, region: str) -> dict:
    """Load secret from AWS Secrets Manager.
    
    Args:
        secret_name: Name of the secret in Secrets Manager
        region: AWS region
        
    Returns:
        Dictionary containing secret values
    """
    client = boto3.client('secretsmanager', region_name=region)
    
    try:
        response = client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            return json.loads(response['SecretString'])
        else:
            return json.loads(base64.b64decode(response['SecretBinary']))
    except ClientError as e:
        raise RuntimeError(f"Failed to load secret {secret_name}: {e}")


def load_config() -> ChaosSecConfig:
    """Load ChaosSec configuration from environment variables and AWS Secrets Manager.
    
    Returns:
        ChaosSecConfig instance with all configuration loaded
    """
    # AWS Configuration
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    aws_account_id = os.getenv('AWS_ACCOUNT_ID', '')
    bedrock_key_encoded = os.getenv('BEDROCK_API_KEY', '')
    
    if not aws_account_id:
        raise ValueError("AWS_ACCOUNT_ID environment variable is required")
    
    # Bedrock uses AWS credentials, not a separate API key
    # The BEDROCK_API_KEY is not actually used by boto3
    bedrock_key = "bedrock-uses-aws-credentials"
    
    aws_config = AWSConfig(
        region=aws_region,
        account_id=aws_account_id,
        bedrock_api_key=bedrock_key
    )
    
    # System Initiative Configuration
    si_api_url = os.getenv('SYSTEM_INITIATIVE_API_URL', 'https://api.systeminit.com')
    si_api_key = os.getenv('SYSTEM_INITIATIVE_API_KEY', '')
    si_workspace_id = os.getenv('SYSTEM_INITIATIVE_WORKSPACE_ID')
    
    if not si_api_key:
        # Try loading from Secrets Manager
        try:
            secrets = load_secret_from_secrets_manager('chaossec/system-initiative', aws_region)
            si_api_key = secrets.get('api_key', '')
        except Exception:
            pass
    
    if not si_api_key:
        raise ValueError("System Initiative API key not found in environment or Secrets Manager")
    
    si_config = SystemInitiativeConfig(
        api_url=si_api_url,
        api_key=si_api_key,
        workspace_id=si_workspace_id
    )
    
    # Vanta Configuration (OAuth2)
    vanta_client_id = os.getenv('VANTA_CLIENT_ID', 'mock-client-id')
    vanta_client_secret = os.getenv('VANTA_CLIENT_SECRET', 'mock-client-secret')
    vanta_api_url = os.getenv('VANTA_API_URL', 'https://api.vanta.com')
    vanta_oauth_token_url = os.getenv('VANTA_OAUTH_TOKEN_URL', 'https://api.vanta.com/oauth/token')
    
    vanta_config = VantaConfig(
        client_id=vanta_client_id,
        client_secret=vanta_client_secret,
        api_url=vanta_api_url,
        oauth_token_url=vanta_oauth_token_url
    )
    
    # General Configuration
    safety_mode = os.getenv('CHAOSSEC_SAFETY_MODE', 'true').lower() == 'true'
    log_level = os.getenv('CHAOSSEC_LOG_LEVEL', 'INFO').upper()
    
    return ChaosSecConfig(
        aws=aws_config,
        system_initiative=si_config,
        vanta=vanta_config,
        safety_mode=safety_mode,
        log_level=log_level
    )


def validate_config(config: ChaosSecConfig) -> bool:
    """Validate that all required configuration is present.
    
    Args:
        config: ChaosSecConfig to validate
        
    Returns:
        True if valid
        
    Raises:
        ValueError if configuration is invalid
    """
    if not config.aws.region:
        raise ValueError("AWS region is required")
    
    if not config.aws.account_id:
        raise ValueError("AWS account ID is required")
    
    if not config.aws.bedrock_api_key:
        raise ValueError("Bedrock API key is required")
    
    if not config.system_initiative.api_key:
        raise ValueError("System Initiative API key is required")
    
    return True
