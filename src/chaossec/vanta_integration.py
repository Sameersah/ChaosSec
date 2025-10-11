"""Vanta MCP API integration for compliance evidence reporting."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from .logger import ChaosSecLogger


class VantaClient:
    """Client for Vanta MCP API (Mock implementation for MVP)."""
    
    # Compliance control mappings
    CONTROL_MAPPINGS = {
        "s3_public_access": {
            "soc2": ["CC6.6", "CC7.2"],
            "iso27001": ["A.9.2", "A.12.1.2"],
            "nist": ["SC-7", "SI-4"]
        },
        "fis_chaos_test": {
            "soc2": ["CC7.2", "CC9.1"],
            "iso27001": ["A.12.1", "A.17.1"],
            "nist": ["CP-4", "SI-4"]
        },
        "iac_scan": {
            "soc2": ["CC8.1", "CC7.2"],
            "iso27001": ["A.12.1.2", "A.14.2.8"],
            "nist": ["CM-2", "RA-5"]
        },
        "infrastructure_monitoring": {
            "soc2": ["CC7.2", "CC7.3"],
            "iso27001": ["A.12.4", "A.16.1"],
            "nist": ["SI-4", "AU-6"]
        }
    }
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        api_url: str,
        logger: ChaosSecLogger,
        oauth_token_url: Optional[str] = None,
        mock_mode: bool = True,
        storage_path: Optional[str] = None
    ):
        """Initialize Vanta client with OAuth2 authentication.
        
        Args:
            client_id: Vanta OAuth2 client ID
            client_secret: Vanta OAuth2 client secret
            api_url: Vanta API base URL
            logger: ChaosSec logger instance
            oauth_token_url: OAuth token endpoint URL
            mock_mode: Whether to use mock mode (default True for MVP)
            storage_path: Path to store evidence locally
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = api_url.rstrip('/')
        self.oauth_token_url = oauth_token_url or f"{self.api_url}/oauth/token"
        self.logger = logger
        self.mock_mode = mock_mode
        
        # OAuth token management
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # Setup local storage for evidence
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path.cwd() / 'chaossec_evidence'
        
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        if mock_mode:
            self.logger.info("Vanta client initialized in MOCK MODE")
    
    def _get_access_token(self) -> str:
        """Get OAuth2 access token (with caching and auto-refresh).
        
        Returns:
            Valid access token
            
        Raises:
            RuntimeError: If token acquisition fails
        """
        # Check if we have a valid cached token
        if self.access_token and self.token_expires_at:
            if datetime.utcnow() < self.token_expires_at:
                return self.access_token
        
        # Request new token using client credentials flow
        self.logger.info("Requesting new Vanta OAuth access token")
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    self.oauth_token_url,
                    data={
                        'grant_type': 'client_credentials',
                        'client_id': self.client_id,
                        'client_secret': self.client_secret,
                        'scope': 'evidence:write compliance:read'  # Adjust scopes as needed
                    },
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded'
                    }
                )
                
                response.raise_for_status()
                token_data = response.json()
                
                self.access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)  # Default 1 hour
                
                # Set expiry with 5-minute buffer
                self.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in - 300)
                
                self.logger.info("Successfully obtained Vanta access token")
                return self.access_token
                
        except httpx.HTTPError as e:
            self.logger.error(f"Failed to get Vanta OAuth token: {e}")
            raise RuntimeError(f"Vanta OAuth authentication failed: {e}")
    
    def _make_api_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make authenticated API request to Vanta.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            data: Request payload
            
        Returns:
            API response data
        """
        if self.mock_mode:
            self.logger.debug("Mock mode: Skipping real API call")
            return {"status": "mock_success"}
        
        # Get valid access token
        access_token = self._get_access_token()
        
        url = f"{self.api_url}/{endpoint.lstrip('/')}"
        
        try:
            with httpx.Client() as client:
                response = client.request(
                    method=method,
                    url=url,
                    json=data,
                    headers={
                        'Authorization': f'Bearer {access_token}',
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    },
                    timeout=30.0
                )
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
        except httpx.HTTPError as e:
            self.logger.error(f"Vanta API request failed: {e}")
            raise RuntimeError(f"Vanta API error: {e}")
    
    def upload_evidence(
        self,
        control_id: str,
        test_result: str,
        details: Dict[str, Any],
        timestamp: Optional[datetime] = None,
        framework: str = "soc2"
    ) -> Dict[str, Any]:
        """Upload compliance evidence to Vanta.
        
        Args:
            control_id: Control identifier (e.g., CC7.2)
            test_result: Result of the test (pass, fail, warning)
            details: Additional evidence details
            timestamp: Evidence timestamp (default: now)
            framework: Compliance framework (soc2, iso27001, nist)
            
        Returns:
            Evidence upload result
        """
        if not timestamp:
            timestamp = datetime.utcnow()
        
        evidence = {
            "control_id": control_id,
            "framework": framework,
            "test_result": test_result,
            "timestamp": timestamp.isoformat(),
            "correlation_id": self.logger.correlation_id,
            "details": details,
            "source": "chaossec-agent"
        }
        
        self.logger.info(f"Uploading evidence for control {control_id}", extra={
            "control_id": control_id,
            "framework": framework,
            "result": test_result
        })
        
        if self.mock_mode:
            # Mock mode: Save locally
            result = self._save_evidence_locally(evidence)
            
            self.logger.audit(
                action="vanta_evidence_uploaded",
                resource=control_id,
                outcome="success_mock",
                details={"mock_mode": True, "file": result.get('file_path')}
            )
            
            return {
                "evidence_id": f"mock-{self.logger.correlation_id}-{int(timestamp.timestamp())}",
                "status": "uploaded_mock",
                "control_id": control_id,
                "framework": framework,
                "mock_mode": True,
                "stored_locally": True,
                "file_path": result.get('file_path')
            }
        else:
            # Real mode: Make actual API call with OAuth
            try:
                api_response = self._make_api_request(
                    method='POST',
                    endpoint='/v1/evidence',
                    data=evidence
                )
                
                evidence_id = api_response.get('id') or api_response.get('evidence_id')
                
                self.logger.audit(
                    action="vanta_evidence_uploaded",
                    resource=control_id,
                    outcome="success",
                    details={"evidence_id": evidence_id}
                )
                
                return {
                    "evidence_id": evidence_id,
                    "status": "uploaded",
                    "control_id": control_id,
                    "framework": framework,
                    "mock_mode": False
                }
                
            except Exception as e:
                self.logger.error(f"Failed to upload evidence to Vanta: {e}")
                # Fallback to local storage on API failure
                local_result = self._save_evidence_locally(evidence)
                return {
                    "evidence_id": None,
                    "status": "error_saved_locally",
                    "error": str(e),
                    "local_backup": local_result.get('file_path')
                }
    
    def _save_evidence_locally(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Save evidence to local storage.
        
        Args:
            evidence: Evidence dictionary
            
        Returns:
            Save result with file path
        """
        try:
            # Organize by date and control
            date_dir = self.storage_path / evidence['timestamp'][:10]  # YYYY-MM-DD
            date_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"{evidence['control_id']}_{evidence['correlation_id'][:8]}.json"
            file_path = date_dir / filename
            
            with open(file_path, 'w') as f:
                json.dump(evidence, f, indent=2)
            
            self.logger.debug(f"Evidence saved to {file_path}")
            
            return {
                "status": "saved",
                "file_path": str(file_path)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to save evidence locally: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def get_unverified_controls(
        self,
        framework: str = "soc2",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get list of controls that need verification/evidence.
        
        Args:
            framework: Compliance framework
            limit: Maximum number of controls to return
            
        Returns:
            List of unverified controls
        """
        self.logger.info(f"Fetching unverified controls for {framework}")
        
        if self.mock_mode:
            # Mock: Return sample unverified controls
            mock_controls = [
                {
                    "control_id": "CC7.2",
                    "framework": "soc2",
                    "title": "System Monitoring",
                    "description": "The entity monitors system components and the operation of those components",
                    "last_tested": None,
                    "status": "needs_evidence"
                },
                {
                    "control_id": "CC6.6",
                    "framework": "soc2",
                    "title": "Logical and Physical Access Controls",
                    "description": "The entity implements logical access security measures",
                    "last_tested": None,
                    "status": "needs_evidence"
                },
                {
                    "control_id": "CC9.1",
                    "framework": "soc2",
                    "title": "Risk Mitigation",
                    "description": "The entity identifies, selects, and develops risk mitigation activities",
                    "last_tested": None,
                    "status": "needs_evidence"
                }
            ]
            
            return mock_controls[:limit]
        else:
            # Real mode: Query Vanta API
            try:
                response = self._make_api_request(
                    method='GET',
                    endpoint=f'/v1/controls?framework={framework}&status=needs_evidence&limit={limit}'
                )
                
                controls = response.get('controls', [])
                return controls
                
            except Exception as e:
                self.logger.error(f"Failed to fetch unverified controls: {e}")
                return []
    
    def map_chaos_to_control(
        self,
        chaos_type: str,
        framework: str = "soc2"
    ) -> List[str]:
        """Map a chaos test type to relevant compliance controls.
        
        Args:
            chaos_type: Type of chaos test
            framework: Compliance framework
            
        Returns:
            List of relevant control IDs
        """
        controls = self.CONTROL_MAPPINGS.get(chaos_type, {}).get(framework, [])
        
        self.logger.debug(f"Mapped {chaos_type} to controls: {controls}")
        
        return controls
    
    def create_evidence_package(
        self,
        chaos_experiment_id: str,
        semgrep_results: Dict[str, Any],
        aws_metrics: List[Dict[str, Any]],
        outcome: str
    ) -> Dict[str, Any]:
        """Create a comprehensive evidence package for multiple controls.
        
        Args:
            chaos_experiment_id: FIS experiment ID
            semgrep_results: Semgrep scan results
            aws_metrics: CloudWatch metrics
            outcome: Overall outcome of the test
            
        Returns:
            Evidence package ready for upload
        """
        package = {
            "package_id": f"pkg-{self.logger.correlation_id}",
            "timestamp": datetime.utcnow().isoformat(),
            "chaos_experiment_id": chaos_experiment_id,
            "outcome": outcome,
            "evidence_items": []
        }
        
        # Create evidence for chaos testing control
        chaos_controls = self.map_chaos_to_control("fis_chaos_test")
        for control in chaos_controls:
            package["evidence_items"].append({
                "control_id": control,
                "framework": "soc2",
                "test_type": "chaos_engineering",
                "result": outcome,
                "details": {
                    "experiment_id": chaos_experiment_id,
                    "metrics": aws_metrics
                }
            })
        
        # Create evidence for IaC scanning control
        if semgrep_results:
            iac_controls = self.map_chaos_to_control("iac_scan")
            for control in iac_controls:
                package["evidence_items"].append({
                    "control_id": control,
                    "framework": "soc2",
                    "test_type": "static_analysis",
                    "result": "pass" if semgrep_results.get('finding_count', 0) == 0 else "findings_detected",
                    "details": {
                        "findings": semgrep_results.get('finding_count', 0),
                        "severity_breakdown": semgrep_results.get('severity_breakdown', {})
                    }
                })
        
        # Create evidence for monitoring control
        monitoring_controls = self.map_chaos_to_control("infrastructure_monitoring")
        for control in monitoring_controls:
            package["evidence_items"].append({
                "control_id": control,
                "framework": "soc2",
                "test_type": "continuous_monitoring",
                "result": "operational",
                "details": {
                    "metrics_collected": len(aws_metrics),
                    "monitoring_active": True
                }
            })
        
        self.logger.info(f"Created evidence package with {len(package['evidence_items'])} items")
        
        return package
    
    def upload_evidence_package(self, package: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Upload a complete evidence package.
        
        Args:
            package: Evidence package from create_evidence_package
            
        Returns:
            List of upload results for each evidence item
        """
        results = []
        
        for item in package.get("evidence_items", []):
            result = self.upload_evidence(
                control_id=item["control_id"],
                test_result=item["result"],
                details=item["details"],
                framework=item.get("framework", "soc2")
            )
            results.append(result)
        
        self.logger.audit(
            action="evidence_package_uploaded",
            resource=package["package_id"],
            outcome="success",
            details={
                "item_count": len(results),
                "package_id": package["package_id"]
            }
        )
        
        return results
    
    def get_evidence_summary(self) -> Dict[str, Any]:
        """Get summary of all evidence stored locally.
        
        Returns:
            Evidence summary statistics
        """
        if not self.storage_path.exists():
            return {
                "total_evidence": 0,
                "by_control": {},
                "by_date": {}
            }
        
        total = 0
        by_control: Dict[str, int] = {}
        by_date: Dict[str, int] = {}
        
        for date_dir in self.storage_path.iterdir():
            if date_dir.is_dir():
                date_str = date_dir.name
                by_date[date_str] = 0
                
                for evidence_file in date_dir.glob("*.json"):
                    total += 1
                    by_date[date_str] += 1
                    
                    # Extract control ID from filename
                    control_id = evidence_file.stem.split('_')[0]
                    by_control[control_id] = by_control.get(control_id, 0) + 1
        
        return {
            "total_evidence": total,
            "by_control": by_control,
            "by_date": by_date,
            "storage_path": str(self.storage_path)
        }

