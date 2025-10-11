# 🎯 Demo Strategy: Create Target Application for Testing

## ✅ Best Approach: Separate Demo Application

### **Strategy: Create a Vulnerable Demo Application**

Create a simple web application with **intentional security issues** that ChaosSec can discover and test.

---

## 🏗️ Demo Application Structure

### **Option 1: Simple E-Commerce App (Recommended)**

```
demo-target-app/
├── infrastructure/           # IaC with intentional security issues
│   ├── app.py               # CDK stack
│   ├── s3_bucket.py         # S3 with public access issue
│   ├── database.py          # RDS without encryption
│   ├── api.py               # Lambda with overly permissive IAM
│   └── network.py           # VPC with open security groups
├── application/             # Application code
│   ├── lambda_functions/    # API handlers
│   ├── static/              # Frontend files
│   └── config/              # Configuration files
└── README.md
```

### **Intentional Security Issues:**

1. **S3 Bucket Misconfiguration**
   - Public read access enabled
   - No encryption at rest
   - No versioning

2. **Overly Permissive IAM Roles**
   - Lambda with `s3:*` permissions
   - Admin access instead of least privilege

3. **Database Security**
   - RDS publicly accessible
   - No encryption at rest
   - Default security group

4. **Network Issues**
   - Security group allows 0.0.0.0/0
   - No VPC flow logs
   - Public subnets for private resources

5. **Application Code Issues**
   - Hardcoded secrets
   - SQL injection vulnerabilities
   - Missing input validation

---

## 🎬 Demo Flow

### **Step 1: Deploy Vulnerable Application**
```bash
cd demo-target-app/infrastructure
cdk deploy DemoECommerceStack
```

**This creates:**
- S3 bucket for product images (with public access)
- RDS database (publicly accessible)
- Lambda functions (overly permissive IAM)
- API Gateway endpoint
- VPC with insecure security groups

### **Step 2: ChaosSec Discovers and Tests**
```bash
cd ../../ChaosSec
python demo_run.py --target-app demo-target-app
```

**ChaosSec will:**
1. Scan IaC for security issues (Semgrep)
2. Discover deployed resources in AWS
3. AI analyzes and selects high-risk test
4. Tests S3 public access detection
5. Validates monitoring catches the issue
6. Generates compliance evidence
7. Provides remediation recommendations

---

## 📋 Demo Application: E-Commerce Store

### **Application Description:**
> "SimpleShop - A basic e-commerce platform with product catalog, shopping cart, and checkout."

### **Architecture:**
```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
┌──────▼──────────────────────────────────────┐
│         API Gateway                          │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────────────────────────────────┐
│    Lambda Functions                          │
│  - GetProducts()                             │
│  - CreateOrder()                             │
│  - ProcessPayment()                          │
└──────┬──────────────────────────────────────┘
       │
┌──────▼──────────┐     ┌──────────────────┐
│  RDS Database   │     │   S3 Bucket      │
│  (Products,     │     │  (Product Images)│
│   Orders)       │     │  [PUBLIC ACCESS] │
└─────────────────┘     └──────────────────┘
```

---

## 🚀 Implementation Plan

### **Create Demo Target Application**

#### **File 1: `demo-target-app/infrastructure/app.py`**
```python
#!/usr/bin/env python3
import aws_cdk as cdk
from vulnerable_ecommerce_stack import VulnerableECommerceStack

app = cdk.App()

VulnerableECommerceStack(
    app, 
    "DemoECommerceStack",
    description="Intentionally vulnerable e-commerce app for ChaosSec demo"
)

app.synth()
```

#### **File 2: `demo-target-app/infrastructure/vulnerable_ecommerce_stack.py`**
```python
from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_rds as rds,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_apigateway as apigw,
    RemovalPolicy,
    Duration
)
from constructs import Construct

class VulnerableECommerceStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        # ISSUE 1: S3 bucket with public access
        product_images_bucket = s3.Bucket(
            self, "ProductImagesBucket",
            bucket_name=f"demo-ecommerce-products-{self.account}",
            public_read_access=True,  # VULNERABILITY!
            block_public_access=s3.BlockPublicAccess(
                block_public_acls=False,
                block_public_policy=False,
                ignore_public_acls=False,
                restrict_public_buckets=False
            ),
            encryption=s3.BucketEncryption.UNENCRYPTED,  # VULNERABILITY!
            versioned=False,  # VULNERABILITY!
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # ISSUE 2: VPC with overly permissive security groups
        vpc = ec2.Vpc(
            self, "ECommerceVPC",
            max_azs=2,
            nat_gateways=0  # Cost saving for demo
        )
        
        # ISSUE 3: Security group allowing all traffic
        database_sg = ec2.SecurityGroup(
            self, "DatabaseSG",
            vpc=vpc,
            allow_all_outbound=True
        )
        database_sg.add_ingress_rule(
            ec2.Peer.any_ipv4(),  # VULNERABILITY!
            ec2.Port.tcp(5432),
            "Allow all inbound PostgreSQL"
        )
        
        # ISSUE 4: RDS database publicly accessible, no encryption
        database = rds.DatabaseInstance(
            self, "ECommerceDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            security_groups=[database_sg],
            publicly_accessible=True,  # VULNERABILITY!
            storage_encrypted=False,  # VULNERABILITY!
            removal_policy=RemovalPolicy.DESTROY,
            deletion_protection=False
        )
        
        # ISSUE 5: Lambda with overly permissive IAM role
        api_lambda_role = iam.Role(
            self, "ApiLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AdministratorAccess"  # VULNERABILITY!
                )
            ]
        )
        
        # Lambda function with security issues
        api_lambda = lambda_.Function(
            self, "ApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=lambda_.Code.from_inline("""
import json
import os

# VULNERABILITY: Hardcoded credentials
DB_PASSWORD = "SuperSecret123!"
API_KEY = "sk_live_1234567890abcdef"

def handler(event, context):
    # VULNERABILITY: No input validation
    user_input = event.get('queryStringParameters', {}).get('search', '')
    
    # VULNERABILITY: SQL injection possible
    query = f"SELECT * FROM products WHERE name LIKE '%{user_input}%'"
    
    return {
        'statusCode': 200,
        'body': json.dumps({'message': 'Success'})
    }
            """),
            role=api_lambda_role,
            timeout=Duration.seconds(30),
            environment={
                "DB_HOST": database.db_instance_endpoint_address,
                "S3_BUCKET": product_images_bucket.bucket_name,
                "SECRET_KEY": "hardcoded-secret-key-123"  # VULNERABILITY!
            }
        )
        
        # API Gateway
        api = apigw.RestApi(
            self, "ECommerceAPI",
            rest_api_name="Demo E-Commerce API",
            description="Intentionally vulnerable API for demo"
        )
        
        products = api.root.add_resource("products")
        products.add_method("GET", apigw.LambdaIntegration(api_lambda))
```

#### **File 3: `demo-target-app/README.md`**
```markdown
# Demo E-Commerce Application

## ⚠️ WARNING: Intentionally Vulnerable Application

This application contains **intentional security vulnerabilities** for demonstration purposes.

**DO NOT use in production or with real data.**

## Purpose

This demo application serves as a target for ChaosSec to test and validate security controls.

## Intentional Vulnerabilities

1. **S3 Bucket**: Public read access, no encryption
2. **RDS Database**: Publicly accessible, no encryption at rest
3. **IAM Roles**: Overly permissive (AdministratorAccess)
4. **Security Groups**: Open to 0.0.0.0/0
5. **Application Code**: Hardcoded secrets, SQL injection

## Deployment

```bash
cd infrastructure
pip install -r requirements.txt
cdk deploy
```

## Cleanup

```bash
cdk destroy
```
```

---

## 🎬 Updated Demo Flow

### **Complete Demo Script:**

#### **Opening (30 seconds):**
> "I've deployed a simple e-commerce application with several common security misconfigurations. Let me show you how ChaosSec automatically discovers and tests these issues."

#### **Step 1: Show Target Application**
```bash
cd demo-target-app
ls -la infrastructure/
cat infrastructure/vulnerable_ecommerce_stack.py | grep "VULNERABILITY"
```

#### **Step 2: Deploy Target Application**
```bash
cd infrastructure
cdk deploy DemoECommerceStack
```

#### **Step 3: Run ChaosSec Against Target**
```bash
cd ../../ChaosSec
python demo_run.py --target-app ../demo-target-app
```

#### **Step 4: Show Results**
```
🔐 ChaosSec Security Testing 🔐
================================

Target: Demo E-Commerce Application
AWS Account: 042744890612

Step 1: ✅ IaC Scan - Found 8 security issues
   - S3 bucket public access
   - RDS publicly accessible
   - Hardcoded credentials
   - Overly permissive IAM

Step 2: ✅ AI selected critical test: "s3_public_access"

Step 3: ✅ Chaos test: Validated S3 public access detection

Step 4: ✅ Generated compliance evidence

Step 5: ✅ Remediation recommendations provided

📊 Security Posture: HIGH RISK
🔧 Recommendations: 8 critical fixes needed
```

---

## 🎤 Demo Talking Points

### **Opening:**
> "ChaosSec works by testing real applications. I've created a simple e-commerce app with common security misconfigurations. Watch ChaosSec discover these issues, test if monitoring would catch them, and provide remediation guidance."

### **Key Points:**
1. **Real Application**: Not testing itself, testing a real target app
2. **Common Issues**: S3 public access, weak IAM, hardcoded secrets
3. **AI-Driven**: Bedrock AI prioritizes which issues to test
4. **Actionable**: Provides specific remediation steps
5. **Continuous**: Can run daily to catch new issues

### **Closing:**
> "ChaosSec found 8 security issues, validated that monitoring would detect critical ones, and provided remediation guidance - all automatically. This is chaos engineering for security."

---

## 🚀 Implementation Steps

1. **Create demo target application directory**
2. **Implement vulnerable infrastructure**
3. **Update ChaosSec to accept target app parameter**
4. **Deploy target application**
5. **Run ChaosSec against target**
6. **Show results and remediation**

---

## 🎯 Benefits of This Approach

✅ **Realistic**: Tests a real application, not itself
✅ **Educational**: Shows common security issues
✅ **Impressive**: Discovers 8+ issues automatically
✅ **Safe**: Intentional vulnerabilities in isolated app
✅ **Scalable**: Can add more complex scenarios
✅ **Reusable**: Target app can be used for other demos

---

## 🚀 Next Steps

Let me create the demo target application for you!
