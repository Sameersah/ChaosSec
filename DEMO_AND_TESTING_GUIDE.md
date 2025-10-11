# 🚀 ChaosSec Demo & Testing Guide

## 🎯 Quick Demo Overview

ChaosSec will demonstrate **autonomous chaos testing** with this flow:

```
1. 🤖 AI Brain decides what to test
2. 🔍 Semgrep scans for vulnerabilities  
3. 🏗️ System Initiative simulates changes
4. 💥 ChaosSec injects controlled chaos (S3 bucket → public)
5. 📊 Monitors if security controls detect it
6. 📋 Reports evidence to Vanta for compliance
7. 🧠 Learns for smarter future tests
```

---

## 🛠️ Setup Checklist

Before running the demo, ensure you have:

### ✅ Required Setup (5 minutes)

1. **Environment Setup:**
   ```bash
   # Run setup script
   ./scripts/setup.sh
   
   # Copy and configure environment
   cp env.example .env
   ```

2. **Configure .env with your credentials:**
   ```env
   # AWS Credentials
   AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID_HERE
   AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY_HERE
   AWS_ACCOUNT_ID=YOUR_AWS_ACCOUNT_ID_HERE
   
   # AWS Bedrock (uses AWS credentials)
   BEDROCK_API_KEY=bedrock-uses-aws-credentials
   
   # System Initiative (use mock for now)
   SYSTEM_INITIATIVE_API_KEY=mock-si-token-for-demo
   
   # Vanta (you already have these)
   VANTA_CLIENT_ID=vci_fa438e8425d88cdf9dadf7ed7ac30b4710cdbbcbbfc5661c
   VANTA_CLIENT_SECRET=vcs_40e77b_f7772b5d6d3e62c19a10b64c0b40186623a9c10c78470717a5ab8c6992dfeee1
   ```

3. **Activate Virtual Environment:**
   ```bash
   source venv/bin/activate
   ```

---

## 🎬 Demo Options

### 🟢 Option 1: Interactive Demo (Recommended)

**Perfect for presentations and live demos**

```bash
python demo_run.py
```

**What happens:**
- Beautiful CLI interface with progress bars
- Step-by-step execution display
- Real AWS Bedrock AI reasoning
- S3 bucket misconfiguration scenario
- Evidence generation and storage
- AI-generated summary at the end

**Demo Flow:**
```
🔐 ChaosSec Demo 🔐
==================

Step 1: Creating digital twin in System Initiative
Step 2: Running Semgrep security scans  
Step 3: AI agent deciding next chaos test
Step 4: Injecting chaos (S3 bucket → public)
Step 5: Monitoring chaos experiment
Step 6: Validating outcomes
Step 7: Reporting evidence to Vanta
Step 8: Storing results for learning

📊 Demo Results
===============
Status: SUCCESS
Correlation ID: abc123-def456
Safety Mode: true
Iterations Completed: 1

Step Results:
  1. Simulate: created
     Twin ID: twin_12345
  2. Scan: 3 findings
  3. Reason: AI recommended 'make_s3_public'
     Reasoning: Testing S3 public access detection
  4. Chaos: make_public
     Applied: false (safety mode)
  5. Monitor: Collected 5 metrics
  6. Validate: success_simulated
     Test Passed: true
  7. Report: 4 evidence items uploaded
  8. Learn: History stored (1 total entries)

📝 AI-Generated Summary:
ChaosSec successfully completed an autonomous security test targeting S3 bucket 
public access controls. The AI agent intelligently selected this test based on 
historical patterns and current infrastructure state. All safety measures were 
active, preventing real infrastructure changes while still demonstrating the 
complete chaos engineering workflow.

📁 Evidence stored in: ./chaossec_evidence/
📜 Execution history: ./chaossec_history.json

✅ Demo Completed Successfully!
```

---

### 🔵 Option 2: Test Individual Components

**Good for debugging and understanding each piece**

#### Test AWS Bedrock AI Brain:
```bash
python -c "
from src.chaossec.agent_brain import AgentBrain
from src.chaossec.logger import create_logger

logger = create_logger('test')
brain = AgentBrain('us-east-1', 'your-bedrock-key', logger)

# Test AI reasoning
context = {'history_analysis': {}, 'semgrep_findings': [], 'previous_tests': []}
result = brain.reason_next_chaos(context)
print('🤖 AI Recommendation:', result)
"
```

#### Test Semgrep Scanning:
```bash
python -c "
from src.chaossec.semgrep_scan import SemgrepScanner
from src.chaossec.logger import create_logger

logger = create_logger('test')
scanner = SemgrepScanner(logger)

# Scan ChaosSec itself
result = scanner.scan_self('.')
print('🔍 Scan Results:', result['finding_count'], 'findings')
"
```

#### Test Vanta Integration:
```bash
python -c "
from src.chaossec.vanta_integration import VantaClient
from src.chaossec.logger import create_logger

logger = create_logger('test')
vanta = VantaClient('mock-id', 'mock-secret', 'https://api.vanta.com', logger)

# Test evidence upload
result = vanta.upload_evidence('CC6.6', 'pass', {'test': 'demo'})
print('📋 Evidence Upload:', result)
"
```

---

### 🟡 Option 3: Unit Tests

**For developers and validation**

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_orchestrator.py -v

# Run with coverage
pytest tests/ --cov=src/chaossec
```

---

## 🎤 Demo Script for Presentations

### 🎯 **Opening (30 seconds)**
> "Let me show you ChaosSec - an autonomous agent that continuously tests your AWS infrastructure security. It uses AI to decide what to test, injects controlled chaos, and reports compliance evidence automatically."

### 🔧 **Setup (1 minute)**
> "First, let me show you it's configured with real AWS credentials, Bedrock for AI reasoning, and Vanta for compliance reporting. Notice it's in safety mode - no real infrastructure changes."

### 🚀 **Run Demo (2-3 minutes)**
```bash
python demo_run.py
```

**Narrate as it runs:**
> "Watch as ChaosSec creates a digital twin, scans for vulnerabilities, uses AI to decide the next test, simulates chaos, monitors the results, and reports compliance evidence. All autonomously!"

### 📊 **Show Results (1 minute)**
> "Look at the results - AI chose to test S3 public access detection, simulated making a bucket public, verified security controls would catch it, and logged evidence for SOC2 compliance."

### 🎯 **Key Points to Highlight**
- ✅ **Autonomous**: No human intervention needed
- ✅ **AI-Driven**: Bedrock decides what to test next
- ✅ **Safe**: Safety mode prevents real changes
- ✅ **Compliant**: Evidence logged for audits
- ✅ **Learning**: Gets smarter over time

---

## 🔍 What to Show in the Demo

### 1. **Configuration**
```bash
cat .env | grep -E "(BEDROCK|VANTA|AWS)" | head -5
```
Show real credentials are configured.

### 2. **Safety Mode**
```bash
grep "CHAOSSEC_SAFETY_MODE" .env
```
Emphasize no real infrastructure changes.

### 3. **AI Reasoning**
Point out the AI's explanation:
> "Testing S3 public access detection based on infrastructure analysis"

### 4. **Evidence Generation**
```bash
ls -la chaossec_evidence/
cat chaossec_history.json
```
Show compliance evidence is stored.

### 5. **Scalability**
```bash
# Show infrastructure code
ls infrastructure/
```
"This can deploy to AWS with Lambda, Step Functions, and run continuously."

---

## 🎬 Demo Variations

### **Quick Demo (2 minutes):**
Focus on the AI decision-making and safety features.

### **Technical Demo (5 minutes):**
Show code, configuration, and detailed results.

### **Business Demo (3 minutes):**
Emphasize compliance, automation, and cost savings.

### **Architecture Demo (4 minutes):**
Show the complete AWS infrastructure and Step Functions workflow.

---

## 🛡️ Safety Features to Highlight

1. **Safety Mode**: `CHAOSSEC_SAFETY_MODE=true`
2. **Correlation IDs**: Every action is tracked
3. **Audit Logging**: Complete trail in CloudWatch
4. **Rollback Capability**: Can undo any change
5. **Validation**: All changes tested before applying

---

## 📈 Demo Success Metrics

**What makes a great demo:**
- ✅ Runs without errors
- ✅ Shows AI reasoning clearly
- ✅ Demonstrates safety features
- ✅ Shows compliance evidence
- ✅ Explains business value

**Red flags to avoid:**
- ❌ Long loading times
- ❌ Error messages
- ❌ Missing credentials
- ❌ Unclear AI decisions

---

## 🆘 Troubleshooting Demo Issues

### **"Module not found" errors:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```

### **"AWS credentials invalid":**
```bash
python -c "import boto3; print(boto3.client('sts').get_caller_identity())"
```

### **"Bedrock access denied":**
Enable Bedrock in AWS Console → Bedrock → Model access

### **"Semgrep not found":**
```bash
pip install semgrep
```

### **Demo runs but shows errors:**
Check logs in `./chaossec_evidence/` for details.

---

## 🎯 Demo Checklist

**Before Demo:**
- [ ] All credentials configured
- [ ] Virtual environment activated
- [ ] Test run completed successfully
- [ ] Evidence files generated
- [ ] Safety mode confirmed

**During Demo:**
- [ ] Explain each step clearly
- [ ] Highlight AI decision-making
- [ ] Show safety features
- [ ] Point out compliance evidence
- [ ] Emphasize automation

**After Demo:**
- [ ] Show generated evidence files
- [ ] Explain business value
- [ ] Discuss scalability
- [ ] Answer questions about architecture

---

## 🚀 Ready to Demo!

You now have everything you need for a compelling ChaosSec demonstration. The system will showcase autonomous security testing, AI-driven decision making, and compliance automation - all while keeping your infrastructure safe.

**Start with:**
```bash
python demo_run.py
```

**And watch the magic happen!** ✨
