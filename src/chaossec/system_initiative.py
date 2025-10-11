"""System Initiative API integration for digital twin simulation."""

import json
from typing import Any, Dict, List, Optional

import httpx

from .logger import ChaosSecLogger


class SystemInitiativeClient:
    """Client for System Initiative API interactions."""
    
    def __init__(
        self,
        api_url: str,
        api_key: str,
        workspace_id: Optional[str],
        logger: ChaosSecLogger,
        timeout: int = 30
    ):
        """Initialize System Initiative client.
        
        Args:
            api_url: Base API URL for System Initiative
            api_key: API authentication key
            workspace_id: Workspace identifier
            logger: ChaosSec logger instance
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.workspace_id = workspace_id
        self.logger = logger
        self.timeout = timeout
        
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request to System Initiative API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            data: Request body data
            params: Query parameters
            
        Returns:
            API response data
        """
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        self.logger.debug(f"SI API Request: {method} {url}")
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=data,
                    params=params
                )
                
                response.raise_for_status()
                
                return response.json() if response.content else {}
                
        except httpx.HTTPStatusError as e:
            self.logger.error(f"SI API HTTP error: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"System Initiative API error: {e}")
        except httpx.RequestError as e:
            self.logger.error(f"SI API request error: {e}")
            raise RuntimeError(f"Failed to connect to System Initiative: {e}")
        except Exception as e:
            self.logger.error(f"SI API unexpected error: {e}")
            raise
    
    def create_digital_twin(
        self,
        aws_resources: List[Dict[str, Any]],
        name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a digital twin of AWS resources in System Initiative.
        
        Args:
            aws_resources: List of AWS resource definitions
            name: Optional name for the digital twin
            
        Returns:
            Digital twin creation result with twin_id
        """
        self.logger.info(f"Creating digital twin with {len(aws_resources)} resources")
        
        payload = {
            'workspace_id': self.workspace_id,
            'name': name or f"chaossec-twin-{self.logger.correlation_id}",
            'resources': aws_resources,
            'provider': 'aws',
            'sync_mode': 'full'
        }
        
        try:
            result = self._make_request('POST', '/api/v1/twins', data=payload)
            
            twin_id = result.get('twin_id') or result.get('id')
            
            self.logger.audit(
                action="digital_twin_created",
                resource=twin_id,
                outcome="success",
                details={'resource_count': len(aws_resources)}
            )
            
            return {
                'twin_id': twin_id,
                'status': result.get('status', 'created'),
                'resource_count': len(aws_resources),
                'workspace_id': self.workspace_id
            }
            
        except Exception as e:
            self.logger.error(f"Failed to create digital twin: {e}")
            return {
                'twin_id': None,
                'status': 'error',
                'error': str(e)
            }
    
    def get_digital_twin(self, twin_id: str) -> Dict[str, Any]:
        """Get digital twin details.
        
        Args:
            twin_id: Digital twin identifier
            
        Returns:
            Digital twin details
        """
        self.logger.debug(f"Fetching digital twin: {twin_id}")
        
        try:
            return self._make_request('GET', f'/api/v1/twins/{twin_id}')
        except Exception as e:
            self.logger.error(f"Failed to fetch digital twin: {e}")
            return {'error': str(e)}
    
    def simulate_changeset(
        self,
        twin_id: str,
        proposed_changes: List[Dict[str, Any]],
        validation_rules: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Simulate proposed infrastructure changes.
        
        Args:
            twin_id: Digital twin identifier
            proposed_changes: List of proposed changes to simulate
            validation_rules: Optional list of validation rule IDs
            
        Returns:
            Simulation results with impact analysis
        """
        self.logger.info(f"Simulating {len(proposed_changes)} changes on twin {twin_id}")
        
        payload = {
            'twin_id': twin_id,
            'changes': proposed_changes,
            'validation_rules': validation_rules or ['security', 'compliance', 'cost'],
            'simulation_mode': 'full',
            'include_impact_analysis': True
        }
        
        try:
            result = self._make_request('POST', '/api/v1/simulations', data=payload)
            
            simulation_id = result.get('simulation_id') or result.get('id')
            status = result.get('status', 'unknown')
            
            self.logger.audit(
                action="changeset_simulated",
                resource=twin_id,
                outcome="success",
                details={
                    'simulation_id': simulation_id,
                    'change_count': len(proposed_changes)
                }
            )
            
            return {
                'simulation_id': simulation_id,
                'status': status,
                'twin_id': twin_id,
                'impact': result.get('impact', {}),
                'validation_results': result.get('validation_results', []),
                'safe_to_apply': result.get('safe_to_apply', False)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to simulate changeset: {e}")
            return {
                'simulation_id': None,
                'status': 'error',
                'error': str(e),
                'safe_to_apply': False
            }
    
    def get_simulation_results(self, simulation_id: str) -> Dict[str, Any]:
        """Get simulation results.
        
        Args:
            simulation_id: Simulation identifier
            
        Returns:
            Detailed simulation results
        """
        self.logger.debug(f"Fetching simulation results: {simulation_id}")
        
        try:
            return self._make_request('GET', f'/api/v1/simulations/{simulation_id}')
        except Exception as e:
            self.logger.error(f"Failed to fetch simulation results: {e}")
            return {'error': str(e)}
    
    def validate_guardrails(
        self,
        twin_id: str,
        changeset_id: str,
        guardrails: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Validate changeset against guardrails.
        
        Args:
            twin_id: Digital twin identifier
            changeset_id: Changeset to validate
            guardrails: List of guardrail IDs to check
            
        Returns:
            Validation results
        """
        self.logger.info(f"Validating changeset {changeset_id} against guardrails")
        
        payload = {
            'twin_id': twin_id,
            'changeset_id': changeset_id,
            'guardrails': guardrails or ['security', 'compliance', 'best-practices']
        }
        
        try:
            result = self._make_request('POST', '/api/v1/validations', data=payload)
            
            passed = result.get('passed', False)
            violations = result.get('violations', [])
            
            self.logger.audit(
                action="guardrails_validated",
                resource=changeset_id,
                outcome="passed" if passed else "failed",
                details={
                    'violation_count': len(violations),
                    'guardrails_checked': len(guardrails) if guardrails else 3
                }
            )
            
            return {
                'passed': passed,
                'violations': violations,
                'warnings': result.get('warnings', []),
                'changeset_id': changeset_id,
                'safe_to_apply': passed and len(violations) == 0
            }
            
        except Exception as e:
            self.logger.error(f"Failed to validate guardrails: {e}")
            return {
                'passed': False,
                'error': str(e),
                'safe_to_apply': False
            }
    
    def apply_changeset(
        self,
        twin_id: str,
        changeset_id: str,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """Apply validated changeset to real infrastructure.
        
        Args:
            twin_id: Digital twin identifier
            changeset_id: Changeset to apply
            auto_approve: Whether to auto-approve without manual review
            
        Returns:
            Application results
        """
        self.logger.warning(f"Applying changeset {changeset_id} to real infrastructure")
        
        payload = {
            'twin_id': twin_id,
            'changeset_id': changeset_id,
            'auto_approve': auto_approve,
            'apply_mode': 'safe'  # Always use safe mode
        }
        
        try:
            result = self._make_request('POST', f'/api/v1/changesets/{changeset_id}/apply', data=payload)
            
            status = result.get('status', 'unknown')
            
            self.logger.audit(
                action="changeset_applied",
                resource=changeset_id,
                outcome=status,
                details={'twin_id': twin_id}
            )
            
            return {
                'changeset_id': changeset_id,
                'status': status,
                'applied': status == 'success',
                'details': result.get('details', {})
            }
            
        except Exception as e:
            self.logger.error(f"Failed to apply changeset: {e}")
            return {
                'changeset_id': changeset_id,
                'status': 'error',
                'applied': False,
                'error': str(e)
            }
    
    def rollback_changeset(self, changeset_id: str) -> Dict[str, Any]:
        """Rollback an applied changeset.
        
        Args:
            changeset_id: Changeset to rollback
            
        Returns:
            Rollback results
        """
        self.logger.warning(f"Rolling back changeset {changeset_id}")
        
        try:
            result = self._make_request('POST', f'/api/v1/changesets/{changeset_id}/rollback')
            
            self.logger.audit(
                action="changeset_rolled_back",
                resource=changeset_id,
                outcome="success",
                details=result
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to rollback changeset: {e}")
            return {'error': str(e)}
    
    def sync_from_aws(
        self,
        twin_id: str,
        resource_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Sync digital twin state from actual AWS resources.
        
        Args:
            twin_id: Digital twin identifier
            resource_types: Optional list of resource types to sync
            
        Returns:
            Sync results
        """
        self.logger.info(f"Syncing digital twin {twin_id} from AWS")
        
        payload = {
            'twin_id': twin_id,
            'source': 'aws',
            'resource_types': resource_types or ['all'],
            'sync_mode': 'incremental'
        }
        
        try:
            result = self._make_request('POST', f'/api/v1/twins/{twin_id}/sync', data=payload)
            
            synced_count = result.get('synced_resource_count', 0)
            
            self.logger.audit(
                action="digital_twin_synced",
                resource=twin_id,
                outcome="success",
                details={'synced_resources': synced_count}
            )
            
            return {
                'twin_id': twin_id,
                'status': 'synced',
                'synced_resource_count': synced_count,
                'changes_detected': result.get('changes_detected', [])
            }
            
        except Exception as e:
            self.logger.error(f"Failed to sync digital twin: {e}")
            return {
                'twin_id': twin_id,
                'status': 'error',
                'error': str(e)
            }
    
    def delete_digital_twin(self, twin_id: str) -> Dict[str, Any]:
        """Delete a digital twin.
        
        Args:
            twin_id: Digital twin identifier
            
        Returns:
            Deletion result
        """
        self.logger.info(f"Deleting digital twin {twin_id}")
        
        try:
            result = self._make_request('DELETE', f'/api/v1/twins/{twin_id}')
            
            self.logger.audit(
                action="digital_twin_deleted",
                resource=twin_id,
                outcome="success",
                details=result
            )
            
            return {'twin_id': twin_id, 'status': 'deleted'}
            
        except Exception as e:
            self.logger.error(f"Failed to delete digital twin: {e}")
            return {'twin_id': twin_id, 'status': 'error', 'error': str(e)}

