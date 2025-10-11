"""Lambda handler for evidence reporting."""

import json
import os
from typing import Any, Dict

from chaossec.vanta_integration import VantaClient
from chaossec.logger import create_logger


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Vanta evidence reporting.
    
    Args:
        event: Lambda event containing evidence data
        context: Lambda context
        
    Returns:
        Report submission result
    """
    print(f"Reporter handler invoked: {json.dumps(event)}")
    
    try:
        # Create logger
        logger = create_logger("chaossec.reporter")
        
        # Initialize Vanta client
        vanta_client = VantaClient(
            client_id=os.environ.get('VANTA_CLIENT_ID', 'mock-client-id'),
            client_secret=os.environ.get('VANTA_CLIENT_SECRET', 'mock-secret'),
            api_url=os.environ.get('VANTA_API_URL', 'https://api.vanta.com'),
            oauth_token_url=os.environ.get('VANTA_OAUTH_TOKEN_URL', 'https://api.vanta.com/oauth/token'),
            logger=logger,
            mock_mode=True
        )
        
        # Create evidence package
        evidence_package = vanta_client.create_evidence_package(
            chaos_experiment_id=event.get('experiment_id', 'unknown'),
            semgrep_results=event.get('semgrep_results', {}),
            aws_metrics=event.get('aws_metrics', []),
            outcome=event.get('outcome', 'unknown')
        )
        
        # Upload evidence
        upload_results = vanta_client.upload_evidence_package(evidence_package)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "package_id": evidence_package['package_id'],
                "evidence_count": len(upload_results),
                "results": upload_results
            })
        }
        
    except Exception as e:
        print(f"Error in reporter: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

