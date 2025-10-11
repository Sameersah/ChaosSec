#!/usr/bin/env python3
"""Demo script to run ChaosSec end-to-end scenario."""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from chaossec.orchestrator import ChaosSecOrchestrator
from chaossec.logger import generate_correlation_id


def print_banner():
    """Print ChaosSec banner."""
    print("="*70)
    print(" " * 20 + "🔐 ChaosSec Demo 🔐")
    print(" " * 10 + "Autonomous Chaos & Security Agent for AWS")
    print("="*70)
    print()


def print_step(step_num: int, step_name: str):
    """Print step header."""
    print(f"\n{'='*70}")
    print(f"  Step {step_num}: {step_name}")
    print(f"{'='*70}\n")


def main():
    """Run ChaosSec demo."""
    print_banner()
    
    # Load environment variables
    print("Loading environment configuration...")
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        'AWS_REGION',
        'AWS_ACCOUNT_ID',
        'BEDROCK_API_KEY',
        'SYSTEM_INITIATIVE_API_KEY'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set these in your .env file or environment.")
        print("See env.example for template.\n")
        return 1
    
    print("✅ Environment configuration loaded")
    print(f"   - AWS Region: {os.getenv('AWS_REGION')}")
    print(f"   - AWS Account: {os.getenv('AWS_ACCOUNT_ID')}")
    print(f"   - Safety Mode: {os.getenv('CHAOSSEC_SAFETY_MODE', 'true')}")
    print()
    
    # Generate correlation ID
    correlation_id = generate_correlation_id()
    print(f"🔗 Correlation ID: {correlation_id}\n")
    
    try:
        # Initialize orchestrator
        print("Initializing ChaosSec Orchestrator...")
        orchestrator = ChaosSecOrchestrator(correlation_id=correlation_id)
        print("✅ Orchestrator initialized\n")
        
        # Run the demo scenario
        print_step(1, "Demo Scenario: S3 Bucket Misconfiguration")
        print("Scenario Description:")
        print("  1. System Initiative creates digital twin of S3 bucket")
        print("  2. Semgrep scans IaC for security vulnerabilities")
        print("  3. AWS Bedrock AI decides next chaos test")
        print("  4. Agent simulates making S3 bucket public (SAFETY MODE)")
        print("  5. AWS Config detects non-compliance")
        print("  6. Evidence logged to Vanta for SOC2/ISO 27001")
        print("  7. Results stored for future learning\n")
        
        # Auto-start demo (no input required)
        print("\n🚀 Starting demo automatically...\n")
        
        # Run one iteration
        print("\n🚀 Starting ChaosSec autonomous loop...\n")
        
        project_root = str(Path(__file__).parent)
        result = orchestrator.run_chaossec_loop(
            max_iterations=1,
            project_root=project_root
        )
        
        # Print results
        print("\n" + "="*70)
        print("  📊 Demo Results")
        print("="*70 + "\n")
        
        print(f"Status: {result.get('status', 'unknown').upper()}")
        print(f"Correlation ID: {result.get('correlation_id')}")
        print(f"Safety Mode: {result.get('safety_mode')}")
        print(f"Iterations Completed: {result.get('total_iterations', 0)}\n")
        
        # Print iteration details
        if result.get('iterations'):
            iteration = result['iterations'][0]
            steps = iteration.get('steps', {})
            
            print("Step Results:")
            print(f"  1. Simulate: {steps.get('simulate', {}).get('status', 'N/A')}")
            if steps.get('simulate', {}).get('twin_id'):
                print(f"     Twin ID: {steps['simulate']['twin_id']}")
            
            print(f"  2. Scan: {steps.get('scan', {}).get('total_findings', 0)} findings")
            
            print(f"  3. Reason: AI recommended '{steps.get('reason', {}).get('chaos_type', 'N/A')}'")
            if steps.get('reason', {}).get('reasoning'):
                print(f"     Reasoning: {steps['reason']['reasoning']}")
            
            print(f"  4. Chaos: {steps.get('chaos', {}).get('action', 'N/A')}")
            print(f"     Applied: {steps.get('chaos', {}).get('applied', False)}")
            print(f"     Safety Mode: {steps.get('chaos', {}).get('safety_mode', True)}")
            
            print(f"  5. Monitor: Collected {len(steps.get('monitor', {}).get('metrics', []))} metrics")
            
            print(f"  6. Validate: {steps.get('validate', {}).get('outcome', 'N/A')}")
            print(f"     Test Passed: {steps.get('validate', {}).get('test_passed', False)}")
            
            print(f"  7. Report: {steps.get('report', {}).get('evidence_count', 0)} evidence items uploaded")
            
            print(f"  8. Learn: History stored ({steps.get('learn', {}).get('history_length', 0)} total entries)")
        
        # Print summary
        if result.get('summary'):
            print("\n📝 AI-Generated Summary:")
            print("   " + result['summary'].replace('\n', '\n   '))
        
        # Print evidence location
        print("\n📁 Evidence stored in: ./chaossec_evidence/")
        print("📜 Execution history: ./chaossec_history.json")
        
        print("\n" + "="*70)
        print(" " * 20 + "✅ Demo Completed Successfully!")
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

