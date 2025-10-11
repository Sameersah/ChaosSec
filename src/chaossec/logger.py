"""Structured logging for ChaosSec with CloudWatch and S3 support."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError


class ChaosSecLogger:
    """Centralized logger for ChaosSec with structured logging and audit trails."""
    
    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        region: str = "us-east-1",
        log_group: str = "/aws/chaossec",
        s3_bucket: Optional[str] = None,
        correlation_id: Optional[str] = None
    ):
        """Initialize ChaosSec logger.
        
        Args:
            name: Logger name
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            region: AWS region for CloudWatch
            log_group: CloudWatch log group name
            s3_bucket: S3 bucket for long-term log storage
            correlation_id: Correlation ID for tracking related operations
        """
        self.name = name
        self.region = region
        self.log_group = log_group
        self.s3_bucket = s3_bucket
        self.correlation_id = correlation_id or str(uuid.uuid4())
        
        # Setup Python logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(console_handler)
        
        # AWS Clients
        self.cloudwatch_client = boto3.client('logs', region_name=region)
        self.s3_client = boto3.client('s3', region_name=region) if s3_bucket else None
        
        # Ensure log group and stream exist
        self._ensure_log_group()
        self.log_stream = f"{name}-{datetime.utcnow().strftime('%Y%m%d')}"
        self._ensure_log_stream()
    
    def _ensure_log_group(self) -> None:
        """Ensure CloudWatch log group exists."""
        try:
            self.cloudwatch_client.create_log_group(logGroupName=self.log_group)
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            pass
        except Exception as e:
            self.logger.warning(f"Failed to create log group: {e}")
    
    def _ensure_log_stream(self) -> None:
        """Ensure CloudWatch log stream exists."""
        try:
            self.cloudwatch_client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self.log_stream
            )
        except self.cloudwatch_client.exceptions.ResourceAlreadyExistsException:
            pass
        except Exception as e:
            self.logger.warning(f"Failed to create log stream: {e}")
    
    def _create_log_entry(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create structured log entry.
        
        Args:
            level: Log level
            message: Log message
            extra: Additional structured data
            
        Returns:
            Structured log entry dictionary
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": self.correlation_id,
            "logger": self.name,
            "level": level,
            "message": message,
        }
        
        if extra:
            entry["extra"] = extra
        
        return entry
    
    def _send_to_cloudwatch(self, log_entry: Dict[str, Any]) -> None:
        """Send log entry to CloudWatch.
        
        Args:
            log_entry: Structured log entry
        """
        try:
            self.cloudwatch_client.put_log_events(
                logGroupName=self.log_group,
                logStreamName=self.log_stream,
                logEvents=[
                    {
                        'timestamp': int(datetime.utcnow().timestamp() * 1000),
                        'message': json.dumps(log_entry)
                    }
                ]
            )
        except Exception as e:
            self.logger.warning(f"Failed to send log to CloudWatch: {e}")
    
    def _send_to_s3(self, log_entry: Dict[str, Any]) -> None:
        """Send log entry to S3 for long-term storage.
        
        Args:
            log_entry: Structured log entry
        """
        if not self.s3_client or not self.s3_bucket:
            return
        
        try:
            date_prefix = datetime.utcnow().strftime('%Y/%m/%d')
            key = f"logs/{date_prefix}/{self.correlation_id}/{uuid.uuid4()}.json"
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(log_entry),
                ContentType='application/json'
            )
        except Exception as e:
            self.logger.warning(f"Failed to send log to S3: {e}")
    
    def log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        send_to_cloud: bool = True
    ) -> None:
        """Log a message with structured data.
        
        Args:
            level: Log level
            message: Log message
            extra: Additional structured data
            send_to_cloud: Whether to send to CloudWatch/S3
        """
        # Local logging
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        if extra:
            log_method(f"{message} | {json.dumps(extra)}")
        else:
            log_method(message)
        
        # Cloud logging
        if send_to_cloud:
            log_entry = self._create_log_entry(level, message, extra)
            self._send_to_cloudwatch(log_entry)
            self._send_to_s3(log_entry)
    
    def info(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log INFO level message."""
        self.log("INFO", message, extra)
    
    def debug(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log DEBUG level message."""
        self.log("DEBUG", message, extra)
    
    def warning(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log WARNING level message."""
        self.log("WARNING", message, extra)
    
    def error(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log ERROR level message."""
        self.log("ERROR", message, extra)
    
    def critical(self, message: str, extra: Optional[Dict[str, Any]] = None) -> None:
        """Log CRITICAL level message."""
        self.log("CRITICAL", message, extra)
    
    def audit(
        self,
        action: str,
        resource: str,
        outcome: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log audit trail entry.
        
        Args:
            action: Action performed (e.g., "chaos_injection", "config_change")
            resource: Resource affected
            outcome: Outcome of the action (success, failure, etc.)
            details: Additional details
        """
        audit_data = {
            "audit": True,
            "action": action,
            "resource": resource,
            "outcome": outcome,
        }
        
        if details:
            audit_data.update(details)
        
        self.info(f"AUDIT: {action} on {resource} - {outcome}", extra=audit_data)


def create_logger(
    name: str,
    config: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None
) -> ChaosSecLogger:
    """Factory function to create a ChaosSec logger.
    
    Args:
        name: Logger name
        config: Configuration dictionary
        correlation_id: Correlation ID for tracking
        
    Returns:
        Configured ChaosSec logger
    """
    config = config or {}
    
    return ChaosSecLogger(
        name=name,
        log_level=config.get('log_level', 'INFO'),
        region=config.get('region', 'us-east-1'),
        log_group=config.get('log_group', '/aws/chaossec'),
        s3_bucket=config.get('s3_bucket'),
        correlation_id=correlation_id
    )


def generate_correlation_id() -> str:
    """Generate a new correlation ID.
    
    Returns:
        UUID string for correlation tracking
    """
    return str(uuid.uuid4())

