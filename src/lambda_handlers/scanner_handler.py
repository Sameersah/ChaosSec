"""Lambda handler for security scanning."""

import json
import os
from typing import Any, Dict

from chaossec.semgrep_scan import SemgrepScanner
from chaossec.logger import create_logger


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for Semgrep scanning.
    
    Args:
        event: Lambda event containing scan parameters
        context: Lambda context
        
    Returns:
        Scan results
    """
    print(f"Scanner handler invoked: {json.dumps(event)}")
    
    try:
        # Create logger
        logger = create_logger("chaossec.scanner")
        
        # Initialize scanner
        scanner = SemgrepScanner(logger)
        
        # Get scan parameters
        repo_path = event.get('repo_path', '/tmp/scan')
        scan_type = event.get('scan_type', 'iac')
        
        # Execute scan
        if scan_type == 'iac':
            result = scanner.scan_iac_directory(repo_path)
        else:
            result = scanner.scan_repository(repo_path)
        
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in scanner: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "error": str(e),
                "findings": []
            })
        }

