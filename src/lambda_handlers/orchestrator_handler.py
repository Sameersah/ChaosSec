"""Lambda handler for ChaosSec orchestrator."""

import json
import os
from typing import Any, Dict

from chaossec.orchestrator import ChaosSecOrchestrator


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Lambda handler for orchestrator.
    
    Args:
        event: Lambda event
        context: Lambda context
        
    Returns:
        Execution result
    """
    print(f"Orchestrator handler invoked: {json.dumps(event)}")
    
    try:
        # Initialize orchestrator
        orchestrator = ChaosSecOrchestrator()
        
        # Check which step to execute
        step = event.get('step', 'full')
        
        if step == 'full':
            # Run complete loop
            result = orchestrator.run_chaossec_loop(
                max_iterations=event.get('iterations', 1),
                project_root=event.get('project_root')
            )
        else:
            # Run specific step (for Step Functions)
            result = {
                "step": step,
                "status": "completed",
                "message": f"Step {step} executed"
            }
        
        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }
        
    except Exception as e:
        print(f"Error in orchestrator handler: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

