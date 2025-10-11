"""AWS service handlers for ChaosSec (FIS, CloudWatch, Config, CloudTrail)."""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from .logger import ChaosSecLogger


class AWSHandler:
    """Handler for AWS service interactions."""
    
    def __init__(self, region: str, logger: ChaosSecLogger):
        """Initialize AWS handler.
        
        Args:
            region: AWS region
            logger: ChaosSec logger instance
        """
        self.region = region
        self.logger = logger
        
        # Initialize AWS clients
        self.fis_client = boto3.client('fis', region_name=region)
        self.cloudwatch_client = boto3.client('cloudwatch', region_name=region)
        self.config_client = boto3.client('config', region_name=region)
        self.cloudtrail_client = boto3.client('cloudtrail', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
    
    def trigger_fis_experiment(
        self,
        template_id: str,
        target_resources: Optional[Dict[str, List[str]]] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Trigger an AWS FIS experiment.
        
        Args:
            template_id: FIS experiment template ID
            target_resources: Target resources for the experiment
            tags: Tags for the experiment
            
        Returns:
            Experiment execution details
        """
        self.logger.info(f"Triggering FIS experiment: {template_id}", extra={
            "template_id": template_id,
            "targets": target_resources
        })
        
        try:
            params = {
                'experimentTemplateId': template_id,
                'clientToken': f"{self.logger.correlation_id}-{int(time.time())}"
            }
            
            if tags:
                params['tags'] = tags
            
            response = self.fis_client.start_experiment(**params)
            
            experiment_id = response['experiment']['id']
            
            self.logger.audit(
                action="fis_experiment_started",
                resource=template_id,
                outcome="success",
                details={"experiment_id": experiment_id}
            )
            
            return {
                "experiment_id": experiment_id,
                "state": response['experiment']['state']['status'],
                "start_time": response['experiment']['startTime'].isoformat() if 'startTime' in response['experiment'] else None,
                "template_id": template_id
            }
            
        except ClientError as e:
            self.logger.error(f"Failed to start FIS experiment: {e}", extra={
                "template_id": template_id,
                "error": str(e)
            })
            raise
    
    def monitor_fis_experiment(
        self,
        experiment_id: str,
        max_wait_seconds: int = 600,
        poll_interval: int = 10
    ) -> Dict[str, Any]:
        """Monitor a running FIS experiment.
        
        Args:
            experiment_id: FIS experiment ID to monitor
            max_wait_seconds: Maximum time to wait for completion
            poll_interval: Seconds between polls
            
        Returns:
            Final experiment state and results
        """
        self.logger.info(f"Monitoring FIS experiment: {experiment_id}")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait_seconds:
            try:
                response = self.fis_client.get_experiment(id=experiment_id)
                experiment = response['experiment']
                state = experiment['state']['status']
                
                self.logger.debug(f"Experiment {experiment_id} state: {state}")
                
                if state in ['completed', 'stopped', 'failed']:
                    result = {
                        "experiment_id": experiment_id,
                        "state": state,
                        "start_time": experiment.get('startTime', '').isoformat() if experiment.get('startTime') else None,
                        "end_time": experiment.get('endTime', '').isoformat() if experiment.get('endTime') else None,
                        "stop_reason": experiment['state'].get('reason'),
                        "actions": experiment.get('actions', {})
                    }
                    
                    self.logger.audit(
                        action="fis_experiment_completed",
                        resource=experiment_id,
                        outcome=state,
                        details=result
                    )
                    
                    return result
                
                time.sleep(poll_interval)
                
            except ClientError as e:
                self.logger.error(f"Error monitoring experiment: {e}")
                raise
        
        # Timeout
        self.logger.warning(f"Experiment {experiment_id} monitoring timed out")
        return {
            "experiment_id": experiment_id,
            "state": "timeout",
            "error": "Monitoring timeout exceeded"
        }
    
    def get_cloudwatch_metrics(
        self,
        namespace: str,
        metric_name: str,
        dimensions: Optional[List[Dict[str, str]]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        period: int = 300,
        statistic: str = 'Average'
    ) -> List[Dict[str, Any]]:
        """Fetch CloudWatch metrics.
        
        Args:
            namespace: CloudWatch namespace
            metric_name: Metric name
            dimensions: Metric dimensions
            start_time: Start time for metrics (default: 1 hour ago)
            end_time: End time for metrics (default: now)
            period: Period in seconds
            statistic: Statistic type (Average, Sum, Maximum, etc.)
            
        Returns:
            List of metric datapoints
        """
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.utcnow()
        
        self.logger.debug(f"Fetching CloudWatch metrics: {namespace}/{metric_name}")
        
        try:
            params = {
                'Namespace': namespace,
                'MetricName': metric_name,
                'StartTime': start_time,
                'EndTime': end_time,
                'Period': period,
                'Statistics': [statistic]
            }
            
            if dimensions:
                params['Dimensions'] = dimensions
            
            response = self.cloudwatch_client.get_metric_statistics(**params)
            
            datapoints = sorted(
                response['Datapoints'],
                key=lambda x: x['Timestamp']
            )
            
            return [{
                "timestamp": dp['Timestamp'].isoformat(),
                "value": dp.get(statistic),
                "unit": dp.get('Unit')
            } for dp in datapoints]
            
        except ClientError as e:
            self.logger.error(f"Failed to fetch CloudWatch metrics: {e}")
            return []
    
    def get_config_compliance(
        self,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get AWS Config compliance status.
        
        Args:
            resource_type: AWS resource type (e.g., AWS::S3::Bucket)
            resource_id: Specific resource ID
            
        Returns:
            List of compliance results
        """
        self.logger.debug(f"Fetching Config compliance for {resource_type}:{resource_id}")
        
        try:
            if resource_id and resource_type:
                response = self.config_client.get_compliance_details_by_resource(
                    ResourceType=resource_type,
                    ResourceId=resource_id
                )
                
                results = response.get('EvaluationResults', [])
            else:
                response = self.config_client.describe_compliance_by_resource(
                    ResourceType=resource_type if resource_type else ''
                )
                results = response.get('ComplianceByResources', [])
            
            compliance_data = []
            for result in results:
                if 'EvaluationResultIdentifier' in result:
                    # Detailed compliance result
                    compliance_data.append({
                        "resource_type": result['EvaluationResultIdentifier'].get('EvaluationResultQualifier', {}).get('ResourceType'),
                        "resource_id": result['EvaluationResultIdentifier'].get('EvaluationResultQualifier', {}).get('ResourceId'),
                        "compliance_type": result.get('ComplianceType'),
                        "config_rule": result['EvaluationResultIdentifier'].get('EvaluationResultQualifier', {}).get('ConfigRuleName'),
                        "result_recorded_time": result.get('ResultRecordedTime', '').isoformat() if result.get('ResultRecordedTime') else None
                    })
                elif 'Compliance' in result:
                    # Summary compliance result
                    compliance_data.append({
                        "resource_type": result.get('ResourceType'),
                        "resource_id": result.get('ResourceId'),
                        "compliance_type": result['Compliance'].get('ComplianceType'),
                        "compliance_contributor_count": result['Compliance'].get('ComplianceContributorCount', {})
                    })
            
            return compliance_data
            
        except ClientError as e:
            self.logger.error(f"Failed to fetch Config compliance: {e}")
            return []
    
    def get_cloudtrail_events(
        self,
        resource_name: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """Get CloudTrail audit events.
        
        Args:
            resource_name: Filter by resource name
            start_time: Start time (default: 1 hour ago)
            end_time: End time (default: now)
            max_results: Maximum number of events to return
            
        Returns:
            List of CloudTrail events
        """
        if not start_time:
            start_time = datetime.utcnow() - timedelta(hours=1)
        if not end_time:
            end_time = datetime.utcnow()
        
        self.logger.debug(f"Fetching CloudTrail events for {resource_name}")
        
        try:
            params = {
                'StartTime': start_time,
                'EndTime': end_time,
                'MaxResults': max_results
            }
            
            if resource_name:
                params['LookupAttributes'] = [
                    {
                        'AttributeKey': 'ResourceName',
                        'AttributeValue': resource_name
                    }
                ]
            
            response = self.cloudtrail_client.lookup_events(**params)
            
            events = []
            for event in response.get('Events', []):
                events.append({
                    "event_id": event.get('EventId'),
                    "event_name": event.get('EventName'),
                    "event_time": event.get('EventTime', '').isoformat() if event.get('EventTime') else None,
                    "username": event.get('Username'),
                    "resources": event.get('Resources', []),
                    "cloud_trail_event": event.get('CloudTrailEvent')
                })
            
            return events
            
        except ClientError as e:
            self.logger.error(f"Failed to fetch CloudTrail events: {e}")
            return []
    
    def simulate_s3_bucket_misconfiguration(
        self,
        bucket_name: str,
        make_public: bool = True,
        safety_mode: bool = True
    ) -> Dict[str, Any]:
        """Simulate S3 bucket misconfiguration for chaos testing.
        
        Args:
            bucket_name: S3 bucket name
            make_public: Whether to make bucket public (chaos) or fix it
            safety_mode: If True, only simulate without making changes
            
        Returns:
            Result of the simulation/change
        """
        self.logger.info(f"Simulating S3 misconfiguration for {bucket_name}", extra={
            "bucket": bucket_name,
            "make_public": make_public,
            "safety_mode": safety_mode
        })
        
        if safety_mode:
            self.logger.warning("SAFETY MODE: Simulating S3 change without applying")
            return {
                "bucket": bucket_name,
                "action": "make_public" if make_public else "fix_public",
                "applied": False,
                "safety_mode": True,
                "simulated_outcome": "success"
            }
        
        try:
            if make_public:
                # Remove public access block (DANGER: Only for chaos testing)
                self.s3_client.delete_public_access_block(Bucket=bucket_name)
                
                # Apply public ACL
                self.s3_client.put_bucket_acl(
                    Bucket=bucket_name,
                    ACL='public-read'
                )
                
                action = "made_public"
            else:
                # Fix: Re-enable public access block
                self.s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
                
                # Apply private ACL
                self.s3_client.put_bucket_acl(
                    Bucket=bucket_name,
                    ACL='private'
                )
                
                action = "fixed_public"
            
            self.logger.audit(
                action=f"s3_bucket_{action}",
                resource=bucket_name,
                outcome="success",
                details={"make_public": make_public}
            )
            
            return {
                "bucket": bucket_name,
                "action": action,
                "applied": True,
                "safety_mode": False,
                "outcome": "success"
            }
            
        except ClientError as e:
            self.logger.error(f"Failed to modify S3 bucket: {e}")
            return {
                "bucket": bucket_name,
                "action": "make_public" if make_public else "fix_public",
                "applied": False,
                "error": str(e),
                "outcome": "failure"
            }

