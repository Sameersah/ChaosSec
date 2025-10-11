"""Main orchestrator for ChaosSec autonomous chaos and security testing."""

import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import boto3

from .agent_brain import AgentBrain
from .aws_handler import AWSHandler
from .config import ChaosSecConfig, load_config, validate_config
from .logger import ChaosSecLogger, create_logger, generate_correlation_id
from .semgrep_scan import SemgrepScanner
from .system_initiative import SystemInitiativeClient
from .vanta_integration import VantaClient


class ChaosSecOrchestrator:
    """Main orchestrator for the ChaosSec autonomous agent."""
    
    def __init__(self, config: Optional[ChaosSecConfig] = None, correlation_id: Optional[str] = None):
        """Initialize ChaosSec orchestrator.
        
        Args:
            config: ChaosSec configuration (loads from env if not provided)
            correlation_id: Correlation ID for this run
        """
        # Load configuration
        if config is None:
            config = load_config()
        
        validate_config(config)
        self.config = config
        
        # Generate correlation ID
        self.correlation_id = correlation_id or generate_correlation_id()
        
        # Initialize logger
        self.logger = create_logger(
            name="chaossec.orchestrator",
            config={
                "log_level": config.log_level,
                "region": config.aws.region,
                "log_group": "/aws/chaossec",
                "s3_bucket": None  # Will be set after infrastructure is ready
            },
            correlation_id=self.correlation_id
        )
        
        self.logger.info(f"Initializing ChaosSec Orchestrator (Safety Mode: {config.safety_mode})")
        
        # Initialize components
        self.aws_handler = AWSHandler(config.aws.region, self.logger)
        self.semgrep_scanner = SemgrepScanner(self.logger)
        self.system_initiative = SystemInitiativeClient(
            api_url=config.system_initiative.api_url,
            api_key=config.system_initiative.api_key,
            workspace_id=config.system_initiative.workspace_id,
            logger=self.logger
        )
        self.vanta_client = VantaClient(
            client_id=config.vanta.client_id,
            client_secret=config.vanta.client_secret,
            api_url=config.vanta.api_url,
            oauth_token_url=config.vanta.oauth_token_url,
            logger=self.logger,
            mock_mode=True  # Set to False when you want to use real Vanta API
        )
        self.agent_brain = AgentBrain(
            region=config.aws.region,
            bedrock_api_key=config.aws.bedrock_api_key,
            logger=self.logger
        )
        
        # Runtime state
        self.current_twin_id: Optional[str] = None
        self.execution_history: List[Dict[str, Any]] = []
        
        self.logger.audit(
            action="orchestrator_initialized",
            resource="chaossec",
            outcome="success",
            details={
                "correlation_id": self.correlation_id,
                "safety_mode": config.safety_mode
            }
        )
    
    def run_chaossec_loop(
        self,
        max_iterations: int = 1,
        project_root: Optional[str] = None
    ) -> Dict[str, Any]:
        """Run the complete ChaosSec loop.
        
        Args:
            max_iterations: Number of chaos cycles to run
            project_root: Path to project root for self-scanning
            
        Returns:
            Overall execution summary
        """
        self.logger.info(f"Starting ChaosSec loop: {max_iterations} iterations")
        
        loop_results = {
            "started_at": datetime.utcnow().isoformat(),
            "correlation_id": self.correlation_id,
            "iterations": [],
            "safety_mode": self.config.safety_mode
        }
        
        try:
            for iteration in range(max_iterations):
                self.logger.info(f"=== ChaosSec Iteration {iteration + 1}/{max_iterations} ===")
                
                iteration_result = self._run_single_iteration(project_root)
                loop_results["iterations"].append(iteration_result)
                
                # Sleep between iterations (except last one)
                if iteration < max_iterations - 1:
                    self.logger.info("Waiting before next iteration...")
                    time.sleep(5)
            
            loop_results["completed_at"] = datetime.utcnow().isoformat()
            loop_results["status"] = "completed"
            loop_results["total_iterations"] = len(loop_results["iterations"])
            
            # Generate final summary
            summary = self.agent_brain.generate_report_summary(loop_results)
            loop_results["summary"] = summary
            
            self.logger.info(f"ChaosSec loop completed: {len(loop_results['iterations'])} iterations")
            
            return loop_results
            
        except Exception as e:
            self.logger.error(f"ChaosSec loop failed: {e}")
            loop_results["status"] = "error"
            loop_results["error"] = str(e)
            return loop_results
    
    def _run_single_iteration(self, project_root: Optional[str]) -> Dict[str, Any]:
        """Run a single iteration of the ChaosSec loop.
        
        Args:
            project_root: Path to project root
            
        Returns:
            Iteration results
        """
        iteration_result = {
            "iteration_id": f"iter-{int(time.time())}",
            "started_at": datetime.utcnow().isoformat(),
            "steps": {}
        }
        
        try:
            # Step 1: Simulate environment with System Initiative
            self.logger.info("Step 1: Creating digital twin in System Initiative")
            simulation_result = self._step_simulate()
            iteration_result["steps"]["simulate"] = simulation_result
            
            # Step 2: Run Semgrep scans
            self.logger.info("Step 2: Running Semgrep security scans")
            scan_result = self._step_scan(project_root)
            iteration_result["steps"]["scan"] = scan_result
            
            # Step 3: AI reasoning for next chaos test
            self.logger.info("Step 3: AI agent deciding next chaos test")
            reasoning_result = self._step_reason(scan_result)
            iteration_result["steps"]["reason"] = reasoning_result
            
            # Step 4: Inject chaos via AWS FIS
            self.logger.info("Step 4: Injecting chaos")
            chaos_result = self._step_inject_chaos(reasoning_result)
            iteration_result["steps"]["chaos"] = chaos_result
            
            # Step 5: Monitor and collect results
            self.logger.info("Step 5: Monitoring chaos experiment")
            monitoring_result = self._step_monitor(chaos_result)
            iteration_result["steps"]["monitor"] = monitoring_result
            
            # Step 6: Validate outcomes
            self.logger.info("Step 6: Validating outcomes")
            validation_result = self._step_validate(monitoring_result, reasoning_result)
            iteration_result["steps"]["validate"] = validation_result
            
            # Step 7: Report to Vanta
            self.logger.info("Step 7: Reporting evidence to Vanta")
            report_result = self._step_report(
                chaos_result, 
                scan_result, 
                monitoring_result, 
                validation_result
            )
            iteration_result["steps"]["report"] = report_result
            
            # Step 8: Learn and store results
            self.logger.info("Step 8: Storing results for learning")
            learn_result = self._step_learn(iteration_result)
            iteration_result["steps"]["learn"] = learn_result
            
            iteration_result["completed_at"] = datetime.utcnow().isoformat()
            iteration_result["status"] = "success"
            
            return iteration_result
            
        except Exception as e:
            self.logger.error(f"Iteration failed: {e}")
            iteration_result["status"] = "error"
            iteration_result["error"] = str(e)
            iteration_result["completed_at"] = datetime.utcnow().isoformat()
            return iteration_result
    
    def _step_simulate(self) -> Dict[str, Any]:
        """Step 1: Simulate infrastructure with System Initiative."""
        # Define AWS resources to simulate (simplified for MVP)
        aws_resources = [
            {
                "type": "aws_s3_bucket",
                "name": "chaossec-test-bucket",
                "properties": {
                    "bucket": "chaossec-test-bucket",
                    "acl": "private",
                    "versioning": {"enabled": True}
                }
            },
            {
                "type": "aws_s3_bucket_public_access_block",
                "name": "chaossec-test-bucket-block",
                "properties": {
                    "bucket": "chaossec-test-bucket",
                    "block_public_acls": True,
                    "block_public_policy": True,
                    "ignore_public_acls": True,
                    "restrict_public_buckets": True
                }
            }
        ]
        
        twin_result = self.system_initiative.create_digital_twin(aws_resources)
        
        if twin_result.get('twin_id'):
            self.current_twin_id = twin_result['twin_id']
        
        return twin_result
    
    def _step_scan(self, project_root: Optional[str]) -> Dict[str, Any]:
        """Step 2: Run Semgrep scans."""
        scan_results = {
            "self_scan": None,
            "iac_scan": None,
            "combined_findings": []
        }
        
        # Scan ChaosSec itself
        if project_root:
            self_scan = self.semgrep_scanner.scan_self(project_root)
            scan_results["self_scan"] = self_scan
            scan_results["combined_findings"].extend(self_scan.get('findings', []))
        
        # Scan IaC if infrastructure exists
        if project_root:
            iac_path = Path(project_root) / 'infrastructure'
            if iac_path.exists():
                iac_scan = self.semgrep_scanner.scan_iac_directory(str(iac_path))
                scan_results["iac_scan"] = iac_scan
                scan_results["combined_findings"].extend(iac_scan.get('findings', []))
        
        scan_results["total_findings"] = len(scan_results["combined_findings"])
        
        return scan_results
    
    def _step_reason(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 3: Use AI to reason about next chaos test."""
        # Analyze history
        history_analysis = self.agent_brain.analyze_history(self.execution_history)
        
        # Build context for AI reasoning
        context = {
            "history_analysis": history_analysis,
            "semgrep_findings": scan_result.get('combined_findings', []),
            "previous_tests": self.execution_history[-5:] if self.execution_history else []
        }
        
        # Get AI recommendation
        recommendation = self.agent_brain.reason_next_chaos(context)
        
        return recommendation
    
    def _step_inject_chaos(self, reasoning_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 4: Inject chaos based on AI recommendation."""
        chaos_type = reasoning_result.get('chaos_type', 'make_s3_public')
        target = reasoning_result.get('target_resource', 'chaossec-test-bucket')
        
        # For MVP, we only implement S3 public access chaos
        if 'public' in chaos_type.lower() or 's3' in chaos_type.lower():
            result = self.aws_handler.simulate_s3_bucket_misconfiguration(
                bucket_name=target,
                make_public=True,
                safety_mode=self.config.safety_mode
            )
            
            result["chaos_type"] = chaos_type
            result["reasoning"] = reasoning_result.get('reasoning', '')
            
            return result
        else:
            self.logger.warning(f"Chaos type '{chaos_type}' not yet implemented, using S3 fallback")
            return {
                "chaos_type": "make_s3_public",
                "target": target,
                "applied": False,
                "safety_mode": self.config.safety_mode,
                "note": "Fallback to S3 test"
            }
    
    def _step_monitor(self, chaos_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 5: Monitor the chaos experiment."""
        target = chaos_result.get('bucket') or chaos_result.get('target', 'unknown')
        
        # Get CloudWatch metrics
        metrics = self.aws_handler.get_cloudwatch_metrics(
            namespace='AWS/S3',
            metric_name='NumberOfObjects',
            dimensions=[{'Name': 'BucketName', 'Value': target}]
        )
        
        # Get Config compliance
        compliance = self.aws_handler.get_config_compliance(
            resource_type='AWS::S3::Bucket',
            resource_id=target
        )
        
        # Get CloudTrail events
        events = self.aws_handler.get_cloudtrail_events(
            resource_name=target
        )
        
        return {
            "target": target,
            "metrics": metrics,
            "compliance": compliance,
            "events": events,
            "monitored_at": datetime.utcnow().isoformat()
        }
    
    def _step_validate(
        self,
        monitoring_result: Dict[str, Any],
        reasoning_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 6: Validate chaos test outcomes."""
        expected_outcome = reasoning_result.get('expected_outcome', '')
        validation_criteria = reasoning_result.get('validation_criteria', '')
        
        compliance_data = monitoring_result.get('compliance', [])
        
        # Check if non-compliance was detected (for S3 public access test)
        non_compliant_detected = any(
            c.get('compliance_type') == 'NON_COMPLIANT' 
            for c in compliance_data
        )
        
        # Determine if test passed
        if self.config.safety_mode:
            test_passed = True  # In safety mode, we just simulate
            outcome = "success_simulated"
        else:
            test_passed = non_compliant_detected  # Real test should trigger detection
            outcome = "success" if test_passed else "failure"
        
        return {
            "outcome": outcome,
            "test_passed": test_passed,
            "expected_outcome": expected_outcome,
            "validation_criteria": validation_criteria,
            "non_compliant_detected": non_compliant_detected,
            "compliance_count": len(compliance_data),
            "validated_at": datetime.utcnow().isoformat()
        }
    
    def _step_report(
        self,
        chaos_result: Dict[str, Any],
        scan_result: Dict[str, Any],
        monitoring_result: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Step 7: Report evidence to Vanta."""
        # Create evidence package
        evidence_package = self.vanta_client.create_evidence_package(
            chaos_experiment_id=self.correlation_id,
            semgrep_results=scan_result,
            aws_metrics=monitoring_result.get('metrics', []),
            outcome=validation_result.get('outcome', 'unknown')
        )
        
        # Upload package
        upload_results = self.vanta_client.upload_evidence_package(evidence_package)
        
        return {
            "package_id": evidence_package['package_id'],
            "evidence_count": len(upload_results),
            "upload_results": upload_results,
            "reported_at": datetime.utcnow().isoformat()
        }
    
    def _step_learn(self, iteration_result: Dict[str, Any]) -> Dict[str, Any]:
        """Step 8: Store results for future learning."""
        # Extract key information for history
        history_entry = {
            "iteration_id": iteration_result.get('iteration_id'),
            "timestamp": iteration_result.get('started_at'),
            "target": iteration_result.get('steps', {}).get('reason', {}).get('target_resource'),
            "chaos_type": iteration_result.get('steps', {}).get('reason', {}).get('chaos_type'),
            "outcome": iteration_result.get('steps', {}).get('validate', {}).get('outcome'),
            "test_passed": iteration_result.get('steps', {}).get('validate', {}).get('test_passed'),
            "findings_count": iteration_result.get('steps', {}).get('scan', {}).get('total_findings', 0)
        }
        
        self.execution_history.append(history_entry)
        
        # Save to file for persistence
        history_file = Path.cwd() / 'chaossec_history.json'
        try:
            with open(history_file, 'w') as f:
                json.dump(self.execution_history, f, indent=2)
            
            self.logger.info(f"Execution history saved to {history_file}")
        except Exception as e:
            self.logger.error(f"Failed to save history: {e}")
        
        return {
            "stored": True,
            "history_length": len(self.execution_history),
            "history_file": str(history_file)
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of orchestrator state.
        
        Returns:
            Current state summary
        """
        return {
            "correlation_id": self.correlation_id,
            "safety_mode": self.config.safety_mode,
            "current_twin_id": self.current_twin_id,
            "execution_count": len(self.execution_history),
            "recent_history": self.execution_history[-5:] if self.execution_history else []
        }

