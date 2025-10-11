"""Semgrep security scanning integration for ChaosSec."""

import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from .logger import ChaosSecLogger


class SemgrepScanner:
    """Semgrep security scanner for IaC and code analysis."""
    
    def __init__(self, logger: ChaosSecLogger):
        """Initialize Semgrep scanner.
        
        Args:
            logger: ChaosSec logger instance
        """
        self.logger = logger
    
    def scan_repository(
        self,
        repo_path: str,
        rules: Optional[List[str]] = None,
        config: Optional[str] = None
    ) -> Dict[str, Any]:
        """Scan a repository with Semgrep.
        
        Args:
            repo_path: Path to repository to scan
            rules: List of rule IDs or paths to custom rules
            config: Semgrep config (e.g., 'auto', 'p/security-audit', 'p/ci')
            
        Returns:
            Dictionary containing scan results
        """
        self.logger.info(f"Starting Semgrep scan on {repo_path}", extra={
            "repo_path": repo_path,
            "rules": rules,
            "config": config
        })
        
        # Build semgrep command
        cmd = ['semgrep', 'scan', '--json', '--quiet']
        
        if config:
            cmd.extend(['--config', config])
        elif rules:
            for rule in rules:
                cmd.extend(['--config', rule])
        else:
            # Default: use security-audit ruleset
            cmd.extend(['--config', 'p/security-audit'])
        
        cmd.append(repo_path)
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode != 0 and result.returncode != 1:  # 1 means findings found
                self.logger.error(f"Semgrep scan failed: {result.stderr}")
                return {
                    "status": "error",
                    "error": result.stderr,
                    "findings": []
                }
            
            # Parse JSON output
            scan_results = self.parse_semgrep_json(result.stdout)
            
            self.logger.audit(
                action="semgrep_scan_completed",
                resource=repo_path,
                outcome="success",
                details={
                    "finding_count": len(scan_results['findings']),
                    "severity_breakdown": scan_results['severity_breakdown']
                }
            )
            
            return scan_results
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Semgrep scan timed out for {repo_path}")
            return {
                "status": "timeout",
                "error": "Scan timed out after 300 seconds",
                "findings": []
            }
        except Exception as e:
            self.logger.error(f"Semgrep scan failed: {e}")
            return {
                "status": "error",
                "error": str(e),
                "findings": []
            }
    
    def parse_semgrep_json(self, json_output: str) -> Dict[str, Any]:
        """Parse Semgrep JSON output.
        
        Args:
            json_output: JSON string from Semgrep
            
        Returns:
            Parsed and structured findings
        """
        try:
            data = json.loads(json_output)
            
            findings = []
            severity_breakdown = {
                "ERROR": 0,
                "WARNING": 0,
                "INFO": 0
            }
            
            for result in data.get('results', []):
                severity = result.get('extra', {}).get('severity', 'INFO').upper()
                severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
                
                finding = {
                    "rule_id": result.get('check_id'),
                    "severity": severity,
                    "message": result.get('extra', {}).get('message', ''),
                    "file": result.get('path'),
                    "line": result.get('start', {}).get('line'),
                    "code": result.get('extra', {}).get('lines', ''),
                    "fix": result.get('extra', {}).get('fix'),
                    "metadata": result.get('extra', {}).get('metadata', {})
                }
                
                findings.append(finding)
            
            return {
                "status": "success",
                "findings": findings,
                "finding_count": len(findings),
                "severity_breakdown": severity_breakdown,
                "errors": data.get('errors', [])
            }
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Semgrep JSON: {e}")
            return {
                "status": "parse_error",
                "error": str(e),
                "findings": []
            }
    
    def scan_iac_directory(
        self,
        iac_path: str,
        include_terraform: bool = True,
        include_cloudformation: bool = True,
        include_kubernetes: bool = True
    ) -> Dict[str, Any]:
        """Scan Infrastructure as Code directory.
        
        Args:
            iac_path: Path to IaC directory
            include_terraform: Scan Terraform files
            include_cloudformation: Scan CloudFormation templates
            include_kubernetes: Scan Kubernetes manifests
            
        Returns:
            Scan results focused on IaC findings
        """
        self.logger.info(f"Scanning IaC directory: {iac_path}")
        
        # Build config for IaC scanning
        configs = []
        
        if include_terraform:
            configs.append('p/terraform')
        
        if include_cloudformation:
            configs.append('p/cloudformation')
        
        if include_kubernetes:
            configs.append('p/kubernetes')
        
        # Run multiple scans and merge results
        all_findings = []
        severity_breakdown = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        
        for config in configs:
            result = self.scan_repository(iac_path, config=config)
            
            if result['status'] == 'success':
                all_findings.extend(result['findings'])
                for severity, count in result['severity_breakdown'].items():
                    severity_breakdown[severity] = severity_breakdown.get(severity, 0) + count
        
        return {
            "status": "success",
            "findings": all_findings,
            "finding_count": len(all_findings),
            "severity_breakdown": severity_breakdown,
            "scanned_path": iac_path
        }
    
    def scan_self(self, project_root: str) -> Dict[str, Any]:
        """Scan the ChaosSec project itself for vulnerabilities.
        
        Args:
            project_root: Path to ChaosSec project root
            
        Returns:
            Self-scan results
        """
        self.logger.info("Performing self-scan of ChaosSec codebase")
        
        # Scan Python code
        python_scan = self.scan_repository(
            project_root,
            config='p/python'
        )
        
        # Scan IaC (CDK infrastructure)
        iac_path = Path(project_root) / 'infrastructure'
        iac_scan = {"findings": [], "finding_count": 0}
        
        if iac_path.exists():
            iac_scan = self.scan_iac_directory(str(iac_path))
        
        # Merge results
        all_findings = python_scan.get('findings', []) + iac_scan.get('findings', [])
        
        severity_breakdown = {"ERROR": 0, "WARNING": 0, "INFO": 0}
        for finding in all_findings:
            severity = finding.get('severity', 'INFO')
            severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
        
        result = {
            "status": "success",
            "self_scan": True,
            "findings": all_findings,
            "finding_count": len(all_findings),
            "severity_breakdown": severity_breakdown,
            "python_findings": len(python_scan.get('findings', [])),
            "iac_findings": len(iac_scan.get('findings', []))
        }
        
        self.logger.audit(
            action="chaossec_self_scan",
            resource=project_root,
            outcome="success",
            details={
                "finding_count": result['finding_count'],
                "severity_breakdown": severity_breakdown
            }
        )
        
        return result
    
    def generate_custom_rule(
        self,
        rule_id: str,
        pattern: str,
        message: str,
        severity: str = "WARNING",
        languages: Optional[List[str]] = None,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate a custom Semgrep rule.
        
        Args:
            rule_id: Unique rule identifier
            pattern: Semgrep pattern to match
            message: Message to display when rule matches
            severity: Severity level (ERROR, WARNING, INFO)
            languages: List of languages to apply rule to
            output_path: Path to save the rule file
            
        Returns:
            Generated rule dictionary
        """
        if not languages:
            languages = ["python"]
        
        rule = {
            "rules": [
                {
                    "id": rule_id,
                    "pattern": pattern,
                    "message": message,
                    "severity": severity,
                    "languages": languages
                }
            ]
        }
        
        if output_path:
            try:
                with open(output_path, 'w') as f:
                    json.dump(rule, f, indent=2)
                
                self.logger.info(f"Custom rule saved to {output_path}", extra={
                    "rule_id": rule_id
                })
            except Exception as e:
                self.logger.error(f"Failed to save custom rule: {e}")
        
        return rule
    
    def filter_findings_by_severity(
        self,
        findings: List[Dict[str, Any]],
        min_severity: str = "WARNING"
    ) -> List[Dict[str, Any]]:
        """Filter findings by minimum severity level.
        
        Args:
            findings: List of findings
            min_severity: Minimum severity to include (ERROR, WARNING, INFO)
            
        Returns:
            Filtered list of findings
        """
        severity_order = {"ERROR": 3, "WARNING": 2, "INFO": 1}
        min_level = severity_order.get(min_severity.upper(), 1)
        
        return [
            f for f in findings
            if severity_order.get(f.get('severity', 'INFO').upper(), 1) >= min_level
        ]
    
    def get_high_risk_findings(self, scan_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract high-risk findings from scan results.
        
        Args:
            scan_results: Complete scan results
            
        Returns:
            List of ERROR-level findings
        """
        findings = scan_results.get('findings', [])
        return self.filter_findings_by_severity(findings, min_severity="ERROR")

