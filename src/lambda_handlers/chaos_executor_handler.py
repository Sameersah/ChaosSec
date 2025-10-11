"""Lambda handler for chaos execution."""

import json
import os
from typing import Any, Dict

from chaossec.aws_handler import AWSHandler
from chaossec.logger import create_logger


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for chaos execution.
    
    Args:
        event: Lambda event containing chaos parameters
        context: Lambda context
        
    Returns:
        Chaos execution result
    """
    print(f"Chaos executor handler invoked: {json.dumps(event)}")
    
    try:
        # Create logger
        logger = create_logger("chaossec.chaos-executor")
        
        # Initialize AWS handler
        aws_handler = AWSHandler(
            region=os.environ.get('AWS_REGION', 'us-east-1'),
            logger=logger
        )
        
        # Get chaos parameters
        chaos_type = event.get('chaos_type', 'make_s3_public')
        target = event.get('target_resource', 'chaossec-test-bucket')
        safety_mode = event.get('safety_mode', True)
        
        # Execute chaos based on type
        if 'public' in chaos_type.lower() or 's3' in chaos_type.lower():
            result = aws_handler.simulate_s3_bucket_misconfiguration(
                bucket_name=target,
                make_public=True,
                safety_mode=safety_mode
            )
        else:
            result = {
                "error": f"Chaos type '{chaos_type}' not implemented",
                "applied": False
            }
        
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in chaos executor: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

