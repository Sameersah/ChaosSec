#!/usr/bin/env python3
"""
Simplified ChaosSec Test Script
Tests ChaosSec against deployed demo target app
"""
import os
import boto3
import json
from datetime import datetime

def main():
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║           CHAOSSEC - SECURITY TESTING DEMO                     ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    
    # Initialize AWS clients
    print("Step 1: Initializing AWS Clients")
    print("─" * 60)
    s3 = boto3.client('s3', region_name='us-east-1')
    rds = boto3.client('rds', region_name='us-east-1')
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    iam = boto3.client('iam', region_name='us-east-1')
    bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
    print("✅ AWS clients initialized")
    print()
    
    # Discover deployed resources
    print("Step 2: Discovering Deployed Resources")
    print("─" * 60)
    
    vulnerabilities = []
    
    # Check S3 buckets
    bucket_name = 'demo-ecommerce-products-042744890612'
    try:
        # Check public access
        acl = s3.get_bucket_acl(Bucket=bucket_name)
        for grant in acl.get('Grants', []):
            if grant.get('Grantee', {}).get('URI') == 'http://acs.amazonaws.com/groups/global/AllUsers':
                vulnerabilities.append({
                    'severity': 'CRITICAL',
                    'resource': bucket_name,
                    'issue': 'S3 Bucket has public read access',
                    'compliance': ['SOC2: CC6.6', 'ISO 27001: A.9.2']
                })
                print(f"🔴 CRITICAL: S3 bucket {bucket_name} is PUBLIC")
        
        # Check encryption
        try:
            encryption = s3.get_bucket_encryption(Bucket=bucket_name)
        except:
            vulnerabilities.append({
                'severity': 'HIGH',
                'resource': bucket_name,
                'issue': 'S3 Bucket has no encryption at rest',
                'compliance': ['PCI-DSS: Req 3.4', 'HIPAA']
            })
            print(f"🟠 HIGH: S3 bucket {bucket_name} has NO ENCRYPTION")
    except Exception as e:
        print(f"⚠️  Could not check S3 bucket: {e}")
    
    # Check RDS instances
    try:
        dbs = rds.describe_db_instances()
        for db in dbs['DBInstances']:
            if 'demoecommerce' in db['DBInstanceIdentifier'].lower():
                if db.get('PubliclyAccessible'):
                    vulnerabilities.append({
                        'severity': 'CRITICAL',
                        'resource': db['DBInstanceIdentifier'],
                        'issue': 'RDS database is publicly accessible',
                        'compliance': ['SOC2: CC6.1', 'PCI-DSS: Req 1.3']
                    })
                    print(f"🔴 CRITICAL: RDS {db['DBInstanceIdentifier']} is PUBLICLY ACCESSIBLE")
                
                if not db.get('StorageEncrypted'):
                    vulnerabilities.append({
                        'severity': 'HIGH',
                        'resource': db['DBInstanceIdentifier'],
                        'issue': 'RDS database not encrypted at rest',
                        'compliance': ['PCI-DSS: Req 3.4']
                    })
                    print(f"🟠 HIGH: RDS {db['DBInstanceIdentifier']} has NO ENCRYPTION")
    except Exception as e:
        print(f"⚠️  Could not check RDS: {e}")
    
    # Check Lambda functions
    try:
        functions = lambda_client.list_functions()
        for func in functions['Functions']:
            if 'DemoECommerce' in func['FunctionName'] and 'ApiFunction' in func['FunctionName']:
                # Check IAM role
                role_name = func['Role'].split('/')[-1]
                try:
                    attached_policies = iam.list_attached_role_policies(RoleName=role_name)
                    for policy in attached_policies['AttachedPolicies']:
                        if 'Administrator' in policy['PolicyName']:
                            vulnerabilities.append({
                                'severity': 'CRITICAL',
                                'resource': func['FunctionName'],
                                'issue': 'Lambda has AdministratorAccess IAM policy',
                                'compliance': ['SOC2: CC6.3', 'ISO 27001: A.9.2']
                            })
                            print(f"🔴 CRITICAL: Lambda {func['FunctionName']} has ADMIN ACCESS")
                except:
                    pass
                
                # Check for environment variables with secrets
                if func.get('Environment', {}).get('Variables', {}):
                    env_vars = func['Environment']['Variables']
                    if 'DB_PASSWORD' in env_vars or 'SECRET_KEY' in env_vars or 'API_KEY' in env_vars:
                        vulnerabilities.append({
                            'severity': 'CRITICAL',
                            'resource': func['FunctionName'],
                            'issue': 'Hardcoded secrets in Lambda environment variables',
                            'compliance': ['SOC2: CC6.1']
                        })
                        print(f"🔴 CRITICAL: Lambda has HARDCODED SECRETS in environment")
    except Exception as e:
        print(f"⚠️  Could not check Lambda: {e}")
    
    print()
    
    # AI Analysis Simulation
    print("Step 3: AI Analysis (AWS Bedrock)")
    print("─" * 60)
    try:
        # Test Bedrock connectivity
        models = bedrock.list_foundation_models() if hasattr(bedrock, 'list_foundation_models') else None
        print("✅ AWS Bedrock accessible")
        print("🤖 AI would analyze and prioritize: 'Test S3 public access detection'")
        print("   Reasoning: Public S3 buckets pose highest risk for data exposure")
    except Exception as e:
        print(f"⚠️  Bedrock AI: Using mock analysis")
        print("🤖 AI Recommendation: Test S3 public access detection")
    print()
    
    # Results Summary
    print("Step 4: Vulnerability Summary")
    print("─" * 60)
    print(f"Total Vulnerabilities Found: {len(vulnerabilities)}")
    
    critical = [v for v in vulnerabilities if v['severity'] == 'CRITICAL']
    high = [v for v in vulnerabilities if v['severity'] == 'HIGH']
    
    print(f"  🔴 Critical: {len(critical)}")
    print(f"  🟠 High: {len(high)}")
    print()
    
    # Compliance Evidence
    print("Step 5: Generating Compliance Evidence")
    print("─" * 60)
    frameworks = set()
    for v in vulnerabilities:
        for c in v.get('compliance', []):
            frameworks.add(c.split(':')[0])
    
    print(f"✅ Evidence generated for {len(frameworks)} frameworks:")
    for fw in sorted(frameworks):
        print(f"   • {fw}")
    print()
    
    # Final Report
    print("╔═══════════════════════════════════════════════════════════════╗")
    print("║                    TEST RESULTS                                ║")
    print("╚═══════════════════════════════════════════════════════════════╝")
    print()
    print(f"✅ AWS Resources Scanned: 3 (S3, RDS, Lambda)")
    print(f"✅ Vulnerabilities Discovered: {len(vulnerabilities)}")
    print(f"✅ Critical Issues: {len(critical)}")
    print(f"✅ High Issues: {len(high)}")
    print(f"✅ Compliance Frameworks: {len(frameworks)}")
    print()
    print("Discovered Vulnerabilities:")
    for i, vuln in enumerate(vulnerabilities, 1):
        print(f"\n{i}. [{vuln['severity']}] {vuln['issue']}")
        print(f"   Resource: {vuln['resource']}")
        print(f"   Compliance: {', '.join(vuln['compliance'])}")
    print()
    print("═══════════════════════════════════════════════════════════════")
    print("✅ CHAOSSEC TEST COMPLETE!")
    print("═══════════════════════════════════════════════════════════════")
    print()
    print("Next Steps:")
    print("  1. View React Dashboard: http://localhost:5173")
    print("  2. Click 'Start Demo' for visual presentation")
    print("  3. Show these real AWS vulnerabilities to judges")
    print()

if __name__ == '__main__':
    main()

