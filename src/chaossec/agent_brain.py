"""AI reasoning engine for ChaosSec using AWS Bedrock."""

import json
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

from .logger import ChaosSecLogger


class AgentBrain:
    """AI-powered decision engine for chaos test selection and analysis."""
    
    def __init__(
        self,
        region: str,
        bedrock_api_key: str,
        logger: ChaosSecLogger,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    ):
        """Initialize Agent Brain.
        
        Args:
            region: AWS region
            bedrock_api_key: Decoded Bedrock API key
            logger: ChaosSec logger instance
            model_id: Bedrock model ID to use
        """
        self.region = region
        self.bedrock_api_key = bedrock_api_key
        self.logger = logger
        self.model_id = model_id
        
        # Initialize Bedrock client
        self.bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=region
        )
    
    def analyze_history(
        self,
        past_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze historical chaos test results.
        
        Args:
            past_results: List of previous chaos test results
            
        Returns:
            Analysis summary
        """
        self.logger.info(f"Analyzing {len(past_results)} historical results")
        
        if not past_results:
            return {
                "total_tests": 0,
                "success_rate": 0.0,
                "common_failures": [],
                "recommendations": ["No historical data available - start with basic S3 tests"]
            }
        
        total = len(past_results)
        successful = sum(1 for r in past_results if r.get('outcome') == 'success')
        failed = sum(1 for r in past_results if r.get('outcome') == 'failure')
        
        # Analyze failure patterns
        failure_types: Dict[str, int] = {}
        for result in past_results:
            if result.get('outcome') == 'failure':
                failure_type = result.get('failure_type', 'unknown')
                failure_types[failure_type] = failure_types.get(failure_type, 0) + 1
        
        common_failures = sorted(
            failure_types.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        analysis = {
            "total_tests": total,
            "successful_tests": successful,
            "failed_tests": failed,
            "success_rate": successful / total if total > 0 else 0.0,
            "common_failures": [{"type": f[0], "count": f[1]} for f in common_failures],
            "most_recent": past_results[-1] if past_results else None
        }
        
        self.logger.debug(f"History analysis: {analysis['success_rate']:.1%} success rate")
        
        return analysis
    
    def reason_next_chaos(
        self,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use AI to decide the next chaos test to run.
        
        Args:
            context: Context including history, semgrep findings, current state
            
        Returns:
            AI recommendation for next chaos test
        """
        self.logger.info("Reasoning about next chaos test using AWS Bedrock")
        
        # Build the reasoning prompt
        prompt = self._build_reasoning_prompt(context)
        
        try:
            # Call AWS Bedrock
            response = self._call_bedrock(prompt)
            
            # Parse the AI response
            recommendation = self._parse_bedrock_response(response)
            
            self.logger.audit(
                action="ai_chaos_decision",
                resource="bedrock",
                outcome="success",
                details={
                    "recommended_test": recommendation.get('target_resource'),
                    "chaos_type": recommendation.get('chaos_type')
                }
            )
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Failed to get AI recommendation: {e}")
            
            # Fallback to basic recommendation
            return self._fallback_recommendation(context)
    
    def _build_reasoning_prompt(self, context: Dict[str, Any]) -> str:
        """Build the AI reasoning prompt.
        
        Args:
            context: Context data
            
        Returns:
            Formatted prompt string
        """
        history_summary = context.get('history_analysis', {})
        semgrep_findings = context.get('semgrep_findings', [])
        previous_tests = context.get('previous_tests', [])
        
        # Format previous results
        prev_tests_str = ""
        if previous_tests:
            prev_tests_str = "\n".join([
                f"- {t.get('target')}: {t.get('chaos_type')} → {t.get('outcome')}"
                for t in previous_tests[-5:]  # Last 5 tests
            ])
        else:
            prev_tests_str = "No previous tests"
        
        # Format Semgrep findings
        semgrep_str = ""
        if semgrep_findings:
            high_risk = [f for f in semgrep_findings if f.get('severity') == 'ERROR']
            if high_risk:
                semgrep_str = f"Found {len(high_risk)} high-risk security findings:\n"
                for finding in high_risk[:3]:
                    semgrep_str += f"- {finding.get('rule_id')}: {finding.get('message')}\n"
            else:
                semgrep_str = f"Found {len(semgrep_findings)} security findings (no critical issues)"
        else:
            semgrep_str = "No security findings from Semgrep"
        
        prompt = f"""You are ChaosSec, an autonomous AWS security agent that performs intelligent chaos testing.

Your goal is to analyze past chaos experiments and current security findings to decide the next chaos test that will most improve infrastructure resilience while minimizing disruption.

## Historical Performance
- Total tests run: {history_summary.get('total_tests', 0)}
- Success rate: {history_summary.get('success_rate', 0):.1%}
- Recent tests:
{prev_tests_str}

## Current Security Findings (Semgrep)
{semgrep_str}

## Your Task
Decide the next chaos test to run. Consider:
1. Tests that haven't been run recently
2. Areas with security vulnerabilities (from Semgrep)
3. Critical AWS services (S3, IAM, EC2)
4. Compliance requirements (SOC2, ISO 27001)

Respond ONLY with a valid JSON object in this exact format:
{{
  "target_resource": "AWS resource identifier or type (e.g., 's3-bucket-chaossec-test')",
  "chaos_type": "Type of chaos to inject (e.g., 'make_s3_public', 'stop_ec2', 'network_latency')",
  "expected_outcome": "What should happen (e.g., 'Security controls should detect and block')",
  "validation_criteria": "How to verify success (e.g., 'CloudWatch alarm triggers, Config detects non-compliance')",
  "compliance_control": "Relevant control (e.g., 'SOC2:CC6.6 - Access Control')",
  "reasoning": "Brief explanation of why this test was chosen"
}}

Respond with JSON only, no other text."""

        return prompt
    
    def _call_bedrock(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call AWS Bedrock with the prompt.
        
        Args:
            prompt: Prompt to send to Bedrock
            max_tokens: Maximum tokens in response
            
        Returns:
            Model response text
        """
        try:
            # Format request for Claude 3
            body = json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "top_p": 0.9
            })
            
            response = self.bedrock_runtime.invoke_model(
                modelId=self.model_id,
                body=body,
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            
            # Extract text from Claude 3 response
            content = response_body.get('content', [])
            if content and len(content) > 0:
                return content[0].get('text', '')
            
            return response_body.get('completion', '')
            
        except ClientError as e:
            self.logger.error(f"Bedrock API error: {e}")
            raise RuntimeError(f"Failed to call Bedrock: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error calling Bedrock: {e}")
            raise
    
    def _parse_bedrock_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON response from Bedrock.
        
        Args:
            response: Raw response text
            
        Returns:
            Parsed recommendation dictionary
        """
        try:
            # Extract JSON from response (handle markdown code blocks)
            response = response.strip()
            if response.startswith('```'):
                # Remove markdown code blocks
                lines = response.split('\n')
                response = '\n'.join(lines[1:-1]) if len(lines) > 2 else response
            
            recommendation = json.loads(response)
            
            # Validate required fields
            required_fields = ['target_resource', 'chaos_type', 'expected_outcome', 
                             'validation_criteria', 'compliance_control']
            
            for field in required_fields:
                if field not in recommendation:
                    self.logger.warning(f"Missing field in AI response: {field}")
                    recommendation[field] = "Not specified"
            
            return recommendation
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse Bedrock JSON response: {e}")
            self.logger.debug(f"Raw response: {response}")
            
            # Return fallback
            return {
                "target_resource": "s3-bucket-default",
                "chaos_type": "make_s3_public",
                "expected_outcome": "Detection by security controls",
                "validation_criteria": "Config compliance check fails",
                "compliance_control": "SOC2:CC6.6",
                "reasoning": "Fallback due to parse error",
                "error": str(e)
            }
    
    def _fallback_recommendation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide fallback recommendation when AI fails.
        
        Args:
            context: Context data
            
        Returns:
            Basic recommendation
        """
        self.logger.warning("Using fallback recommendation")
        
        # Simple logic: Start with S3 public access test
        return {
            "target_resource": "s3-chaossec-test-bucket",
            "chaos_type": "make_s3_public",
            "expected_outcome": "AWS Config should detect non-compliance, security alerts should fire",
            "validation_criteria": "Config rule violation detected, CloudWatch alarm triggered",
            "compliance_control": "SOC2:CC6.6 - Logical Access Controls",
            "reasoning": "Starting with fundamental S3 security test (fallback logic)",
            "fallback": True
        }
    
    def generate_report_summary(
        self,
        results: Dict[str, Any],
        for_humans: bool = True
    ) -> str:
        """Generate human-readable summary of results using AI.
        
        Args:
            results: Chaos test results to summarize
            for_humans: Whether to generate human-friendly text
            
        Returns:
            Summary text
        """
        self.logger.info("Generating report summary")
        
        if not for_humans:
            return json.dumps(results, indent=2)
        
        prompt = f"""Summarize these chaos engineering test results in a clear, executive-friendly format:

## Test Results
{json.dumps(results, indent=2)}

Create a brief summary (3-4 sentences) that includes:
1. What was tested
2. The outcome
3. Key findings
4. Next steps or recommendations

Write in professional but accessible language. Focus on impact and actionability."""
        
        try:
            summary = self._call_bedrock(prompt, max_tokens=500)
            
            self.logger.audit(
                action="report_summary_generated",
                resource="bedrock",
                outcome="success",
                details={"length": len(summary)}
            )
            
            return summary.strip()
            
        except Exception as e:
            self.logger.error(f"Failed to generate summary: {e}")
            
            # Fallback summary
            return f"""Chaos Test Summary:
            
Tested: {results.get('test_type', 'Unknown')} on {results.get('target_resource', 'Unknown')}
Outcome: {results.get('outcome', 'Unknown')}
Findings: {results.get('finding_count', 0)} security findings detected
Status: {'Passed' if results.get('outcome') == 'success' else 'Needs attention'}

The system has completed automated chaos testing. Review detailed logs for full analysis."""
    
    def evaluate_risk_score(
        self,
        semgrep_findings: List[Dict[str, Any]],
        config_compliance: List[Dict[str, Any]],
        previous_failures: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Evaluate overall risk score for the infrastructure.
        
        Args:
            semgrep_findings: Security scan findings
            config_compliance: Config compliance results
            previous_failures: Recent test failures
            
        Returns:
            Risk assessment with score and details
        """
        # Simple risk scoring algorithm
        risk_score = 0
        risk_factors = []
        
        # Semgrep findings
        critical_findings = sum(1 for f in semgrep_findings if f.get('severity') == 'ERROR')
        if critical_findings > 0:
            risk_score += critical_findings * 10
            risk_factors.append(f"{critical_findings} critical security findings")
        
        # Config compliance
        non_compliant = sum(1 for c in config_compliance if c.get('compliance_type') != 'COMPLIANT')
        if non_compliant > 0:
            risk_score += non_compliant * 5
            risk_factors.append(f"{non_compliant} non-compliant resources")
        
        # Previous failures
        recent_failures = len([f for f in previous_failures if f.get('outcome') == 'failure'])
        if recent_failures > 0:
            risk_score += recent_failures * 3
            risk_factors.append(f"{recent_failures} recent test failures")
        
        # Normalize score (0-100)
        risk_score = min(risk_score, 100)
        
        # Determine risk level
        if risk_score >= 70:
            risk_level = "HIGH"
        elif risk_score >= 40:
            risk_level = "MEDIUM"
        elif risk_score >= 20:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "recommendation": self._get_risk_recommendation(risk_level)
        }
    
    def _get_risk_recommendation(self, risk_level: str) -> str:
        """Get recommendation based on risk level.
        
        Args:
            risk_level: Current risk level
            
        Returns:
            Recommendation text
        """
        recommendations = {
            "HIGH": "Immediate action required. Address critical findings before continuing chaos tests.",
            "MEDIUM": "Schedule remediation for identified issues. Continue monitored chaos testing.",
            "LOW": "Minor issues detected. Continue normal chaos testing cycles.",
            "MINIMAL": "Infrastructure appears healthy. Proceed with advanced chaos scenarios."
        }
        
        return recommendations.get(risk_level, "Review findings and continue testing.")

