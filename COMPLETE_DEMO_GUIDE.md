# 🎬 Complete ChaosSec Demo Guide

## 🎯 Demo Strategy: Test a Vulnerable Target Application

### **Setup Overview:**

1. **ChaosSec** → The security testing agent (in `/ChaosSec`)
2. **Demo Target App** → Vulnerable e-commerce app to test (in `/demo-target-app`)

---

## 🚀 Complete Demo Flow

### **Phase 1: Deploy Target Application (5 minutes)**

#### **Step 1: Navigate to target app**
```bash
cd /Users/sameer/Documents/hackathon/demo-target-app/infrastructure
```

#### **Step 2: Setup environment**
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### **Step 3: Bootstrap CDK (first time only)**
```bash
cdk bootstrap aws://042744890612/us-east-1
```

#### **Step 4: Deploy vulnerable application**
```bash
cdk deploy DemoECommerceStack
```

**Expected output:**
```
✅  DemoECommerceStack

Outputs:
DemoECommerceStack.ApiEndpoint = https://abc123.execute-api.us-east-1.amazonaws.com/prod/
DemoECommerceStack.S3BucketName = demo-ecommerce-products-042744890612
DemoECommerceStack.DatabaseEndpoint = demo-db.abc123.us-east-1.rds.amazonaws.com

Deployment time: ~3-5 minutes
```

---

### **Phase 2: Run ChaosSec Against Target (2 minutes)**

#### **Step 1: Navigate to ChaosSec**
```bash
cd /Users/sameer/Documents/hackathon/ChaosSec
source venv/bin/activate
```

#### **Step 2: Configure target**
```bash
# Copy .env if not done
cp env.example .env

# Ensure AWS credentials are set
cat .env | grep AWS
```

#### **Step 3: Run ChaosSec demo**
```bash
python demo_run.py
```

**ChaosSec will:**
1. **Discover** deployed resources in your AWS account
2. **Scan** infrastructure code with Semgrep
3. **Analyze** with AI (AWS Bedrock)
4. **Test** security controls (simulated)
5. **Validate** monitoring capabilities
6. **Report** compliance evidence
7. **Recommend** remediation steps

---

### **Phase 3: Show Results (2 minutes)**

#### **Demo Output:**
```
🔐 ChaosSec Security Testing 🔐
================================

Target: AWS Account 042744890612
Correlation ID: abc123-def456

Step 1: ✅ IaC Scan Complete
   Found 8 security vulnerabilities:
   - S3 bucket public access
   - RDS publicly accessible
   - Hardcoded credentials in Lambda
   - Overly permissive IAM (AdministratorAccess)
   - Security group allows 0.0.0.0/0
   - No encryption at rest
   - No input validation
   - Missing authentication

Step 2: ✅ AI Risk Analysis (AWS Bedrock)
   AI Recommendation: "Test S3 public access detection"
   Priority: CRITICAL
   Reasoning: "Public S3 buckets are highest risk for data exposure"

Step 3: ✅ Chaos Test: S3 Public Access
   Mode: Simulation (safety mode)
   Result: Validated detection capabilities

Step 4: ✅ Monitoring Validation
   AWS Config: Would detect non-compliance
   CloudTrail: Would log API calls
   CloudWatch: Would trigger alarms

Step 5: ✅ Compliance Evidence Generated
   SOC2: CC6.6 (Access Control)
   ISO 27001: A.9.2 (Access Control)
   NIST: SC-7 (Boundary Protection)

Step 6: ✅ Remediation Recommendations
   1. Enable S3 Block Public Access
   2. Encrypt S3 bucket at rest (AES-256)
   3. Replace AdministratorAccess with least privilege
   4. Restrict security groups to specific IPs
   5. Move RDS to private subnet
   6. Enable RDS encryption at rest
   7. Remove hardcoded credentials, use Secrets Manager
   8. Add API authentication (Cognito or IAM)

📊 Security Posture: HIGH RISK
🔧 Critical Issues: 3
🔧 High Issues: 5
📁 Evidence: ./chaossec_evidence/2024-10-10/
```

---

## 🎤 Demo Script for Judges

### **Opening (30 seconds):**
> "I've built ChaosSec - an autonomous AI agent that continuously tests AWS security. Let me show you how it works by deploying a vulnerable e-commerce application and watching ChaosSec discover and test the security issues."

### **Phase 1: Deploy Target (1 minute):**
> "First, I'm deploying a simple e-commerce app with common security misconfigurations - public S3 buckets, weak IAM policies, hardcoded secrets. These are issues we see every day in production."

```bash
cd demo-target-app/infrastructure
cdk deploy
```

### **Phase 2: Run ChaosSec (2 minutes):**
> "Now watch ChaosSec work. It scans the infrastructure code, discovers 8 security vulnerabilities, uses AWS Bedrock AI to prioritize which issue to test first, then validates that our monitoring would catch it."

```bash
cd ../../ChaosSec
python demo_run.py
```

### **Phase 3: Show Results (2 minutes):**
> "Look at what ChaosSec found: 8 vulnerabilities including public S3 buckets, overly permissive IAM, and hardcoded secrets. The AI prioritized testing the S3 public access issue because it's the highest risk. It validated that AWS Config would detect it, CloudTrail would log it, and generated compliance evidence for SOC2 and ISO 27001 audits."

**Show evidence files:**
```bash
ls -la chaossec_evidence/
cat chaossec_history.json
```

### **Closing (30 seconds):**
> "This is chaos engineering for security. ChaosSec continuously validates that your security controls actually work, not just that they exist. It's like having a security engineer testing your infrastructure 24/7, getting smarter over time using AI."

---

## 🎯 Key Demo Highlights

### **1. Real Application Testing**
- ✅ Tests a real vulnerable application, not itself
- ✅ Discovers actual security issues
- ✅ Works with any AWS infrastructure

### **2. AI-Driven Prioritization**
- ✅ AWS Bedrock analyzes risk
- ✅ Intelligent test selection
- ✅ Explains reasoning

### **3. Safe Chaos Testing**
- ✅ Safety mode prevents real damage
- ✅ Simulates security incidents
- ✅ Validates detection capabilities

### **4. Automated Compliance**
- ✅ Generates SOC2 evidence
- ✅ ISO 27001 control mapping
- ✅ NIST framework alignment

### **5. Actionable Recommendations**
- ✅ Specific remediation steps
- ✅ Priority-based fixes
- ✅ Best practice guidance

---

## 📊 What ChaosSec Discovers

### **In the Demo Target App:**

1. **S3 Bucket Issues:**
   - ✗ Public read access enabled
   - ✗ No encryption at rest
   - ✗ No versioning

2. **RDS Database Issues:**
   - ✗ Publicly accessible
   - ✗ No encryption at rest
   - ✗ Security group allows 0.0.0.0/0

3. **IAM Permission Issues:**
   - ✗ Lambda with AdministratorAccess
   - ✗ Overly permissive policies

4. **Application Code Issues:**
   - ✗ Hardcoded credentials
   - ✗ SQL injection vulnerability
   - ✗ No input validation

5. **API Security Issues:**
   - ✗ No authentication
   - ✗ No rate limiting

**Total: 8+ vulnerabilities discovered automatically**

---

## 🧹 Cleanup After Demo

### **Important: Destroy resources to avoid AWS charges**

```bash
cd /Users/sameer/Documents/hackathon/demo-target-app/infrastructure
cdk destroy DemoECommerceStack
```

Confirm with `y` when prompted.

**Cost if left running:** ~$0.50/day for RDS

---

## 🎯 Success Criteria

### **Technical Success:**
- [ ] Target app deploys successfully
- [ ] ChaosSec discovers 8+ vulnerabilities
- [ ] AI provides clear reasoning
- [ ] Evidence files generated
- [ ] Safety mode prevents real changes

### **Demo Success:**
- [ ] Clear explanation of each phase
- [ ] Emphasis on AI decision-making
- [ ] Highlight of safety features
- [ ] Showcase of compliance value
- [ ] Illustration of scalability

---

## 💡 Backup Demo (If Deployment Fails)

### **If AWS deployment has issues:**

1. **Run ChaosSec in mock mode:**
```bash
cd /Users/sameer/Documents/hackathon/ChaosSec
python demo_run.py --mock-mode
```

2. **Show IaC scanning:**
```bash
# Scan the vulnerable infrastructure code
python -c "
from src.chaossec.semgrep_scan import SemgrepScanner
from src.chaossec.logger import create_logger

logger = create_logger('demo')
scanner = SemgrepScanner(logger)
result = scanner.scan_iac_directory('../demo-target-app/infrastructure/')
print(f'Found {result[\"finding_count\"]} issues')
"
```

3. **Show AI reasoning:**
```bash
# Show AI analysis capability
python -c "
from src.chaossec.agent_brain import AgentBrain
from src.chaossec.logger import create_logger

logger = create_logger('demo')
brain = AgentBrain('us-east-1', 'your-key', logger)
# Demo AI capabilities
"
```

---

## 🚀 You're Ready!

### **Quick Checklist:**

- [ ] AWS credentials configured (042744890612)
- [ ] Both directories ready (`ChaosSec` and `demo-target-app`)
- [ ] Virtual environments created
- [ ] Dependencies installed
- [ ] Demo script practiced

### **Run the demo:**

```bash
# 1. Deploy target
cd /Users/sameer/Documents/hackathon/demo-target-app/infrastructure
source .venv/bin/activate
cdk deploy

# 2. Run ChaosSec
cd /Users/sameer/Documents/hackathon/ChaosSec
source venv/bin/activate
python demo_run.py

# 3. Show results
ls -la chaossec_evidence/
cat chaossec_history.json

# 4. Cleanup
cd ../demo-target-app/infrastructure
cdk destroy
```

**Time: ~10 minutes total**

---

## 🏆 You've Got This!

Your demo shows:
- ✅ AI-driven security testing
- ✅ Real vulnerability discovery
- ✅ Automated compliance
- ✅ Safe chaos engineering
- ✅ Production-ready architecture

**Go win that hackathon!** 🚀
