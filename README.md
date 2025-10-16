# 🔐 ChaosSec: Autonomous Chaos & Security Agent
**Contributor** - Shruti Goyal (https://github.com/shrutiebony)
ChaosSec is an autonomous agent that continuously performs chaos testing and self-hardening on AWS infrastructure. It simulates security scenarios, detects vulnerabilities, and provides compliance evidence automatically.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ChaosSec Agent                          │
└─────────────────────────────────────────────────────────────────┘
           │
           ├──▶ AWS Layer (Lambda, FIS, CloudWatch, Config)
           ├──▶ System Initiative (Digital Twin & Simulation)
           ├──▶ Semgrep (Static Analysis & Vulnerability Scanning)
           ├──▶ Vanta MCP (Compliance Evidence Reporting)
           └──▶ AWS Bedrock (AI Reasoning with Claude)

┌─────────────────────────────────────────────────────────────────┐
│                      Execution Flow                             │
└─────────────────────────────────────────────────────────────────┘

1. System Initiative → Simulate AWS environment in digital twin
2. Semgrep → Scan IaC and code for security vulnerabilities  
3. Agent Brain (Bedrock) → Analyze history, decide next chaos test
4. AWS FIS → Inject controlled chaos (e.g., make S3 bucket public)
5. Monitor → CloudWatch metrics, Config compliance, CloudTrail audit
6. Validate → Check if security controls detected/blocked the issue
7. Report → Log evidence to Vanta (mapped to SOC2/ISO controls)
8. Learn → Store results for smarter future test selection
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- AWS Account with appropriate permissions
- AWS Bedrock access enabled
- Node.js 18+ (for AWS CDK)

### Installation

1. **Clone and setup environment:**
```bash
cd ChaosSec
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment variables:**
```bash
cp env.example .env
# Edit .env with your AWS credentials and Bedrock key
```

3. **Deploy infrastructure:**
```bash
cd infrastructure
npm install -g aws-cdk
cdk bootstrap  # First time only
cdk deploy
```

### Running the Demo

Run the end-to-end demo scenario (S3 bucket misconfiguration):

```bash
python demo_run.py
```

This will:
- Simulate an S3 bucket with public-read ACL
- Detect the vulnerability with Semgrep
- Use Bedrock to recommend a fix
- Validate the change in System Initiative
- Apply the fix (in safety mode, no real changes)
- Log evidence to Vanta

## 📁 Project Structure

```
ChaosSec/
├── src/
│   ├── chaossec/              # Core application modules
│   │   ├── config.py          # Configuration and secrets management
│   │   ├── logger.py          # Structured logging (CloudWatch + S3)
│   │   ├── aws_handler.py     # AWS FIS, CloudWatch, Config, CloudTrail
│   │   ├── semgrep_scan.py    # Security scanning
│   │   ├── system_initiative.py # Digital twin simulation
│   │   ├── vanta_integration.py # Compliance evidence reporting
│   │   ├── agent_brain.py     # AI reasoning with Bedrock
│   │   └── orchestrator.py    # Main execution loop
│   └── lambda_handlers/       # AWS Lambda entry points
├── infrastructure/            # AWS CDK infrastructure code
│   ├── app.py                # CDK app entry point
│   └── chaossec_stack.py     # Lambda, Step Functions, FIS, etc.
├── tests/                    # Unit and integration tests
├── demo_run.py              # End-to-end demo script
└── requirements.txt         # Python dependencies
```

## 🧪 Running Tests

```bash
pytest tests/ -v
```

## 🛡️ Safety Features

- **Safety Mode**: Set `CHAOSSEC_SAFETY_MODE=true` to prevent real AWS changes
- **Idempotent Operations**: All operations can be safely retried
- **Audit Logging**: Every action logged with correlation IDs
- **Rollback Support**: Changes can be reverted via System Initiative
- **Guardrails**: Validation before applying any infrastructure changes

## 🔧 Configuration

Key environment variables (see `env.example`):

- `AWS_REGION` - AWS region for deployment
- `AWS_ACCOUNT_ID` - Your AWS account ID
- `BEDROCK_API_KEY` - AWS Bedrock API key (base64 encoded)
- `SYSTEM_INITIATIVE_API_URL` - System Initiative API endpoint
- `SYSTEM_INITIATIVE_API_KEY` - SI authentication token
- `VANTA_API_KEY` - Vanta MCP API key (optional for MVP)
- `CHAOSSEC_SAFETY_MODE` - Set to `true` to prevent real AWS modifications

## 📊 Compliance Mapping

ChaosSec automatically maps chaos experiments to compliance controls:

- **SOC 2**: CC6.6 (Logical Access), CC7.2 (System Monitoring)
- **ISO 27001**: A.9.2 (Access Control), A.12.1 (Operational Procedures)
- **NIST**: SC-7 (Boundary Protection), SI-4 (Information System Monitoring)

## 🤝 Contributing

This is a prototype/MVP. Key areas for enhancement:
- Additional chaos experiment templates
- More sophisticated AI reasoning prompts
- Real-time dashboard for monitoring
- Multi-region chaos orchestration

## 📄 License

MIT License - See LICENSE file for details

## 🆘 Troubleshooting

**Issue: Bedrock API key invalid**
- Ensure the key is properly base64 encoded
- Check Bedrock service is enabled in your AWS account

**Issue: CDK deployment fails**
- Run `cdk bootstrap` first
- Ensure AWS credentials are configured (`aws configure`)

**Issue: FIS experiments not running**
- Check IAM permissions for FIS service role
- Verify FIS is available in your region

For more help, see the inline documentation in each module.

