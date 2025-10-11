# 🔑 AWS Credentials Explained

## Why You Need AWS Access Keys

The `AWS_ACCOUNT_ID` alone **cannot authenticate** with AWS. It's just an identifier.

To make API calls to AWS (FIS, CloudWatch, S3, Config, etc.), boto3 needs:

### Required AWS Credentials

```env
# Required for AWS API authentication
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG...

# Optional but recommended
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
```

## 🔍 What Each Does

| Credential | Purpose | Example |
|------------|---------|---------|
| `AWS_ACCESS_KEY_ID` | Public identifier for your AWS user/role | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | Secret key that proves identity | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |
| `AWS_ACCOUNT_ID` | Your AWS account number (for reference) | `123456789012` |
| `AWS_REGION` | Default region for AWS operations | `us-east-1` |

## 📝 How to Get AWS Access Keys

### Method 1: IAM User Access Keys (Recommended for Testing)

1. **Go to AWS Console** → IAM → Users
2. **Select your user** (or create a new one)
3. **Security credentials** tab
4. **Create access key** → Select "CLI" use case
5. **Download or copy:**
   - Access Key ID
   - Secret Access Key ⚠️ (shown only once!)

### Method 2: IAM Role (Recommended for Production/Lambda)

If running **on AWS infrastructure** (EC2, Lambda, ECS):
- Attach an IAM Role to your resource
- boto3 automatically uses the role credentials
- No need to set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY

### Method 3: AWS SSO / AWS CLI Profiles

If using AWS SSO or named profiles:
```env
AWS_PROFILE=your-profile-name
```

## ⚠️ Security Best Practices

### ✅ DO:
- Use IAM roles when running on AWS infrastructure
- Create IAM users with **minimum required permissions**
- Use AWS Secrets Manager for production credentials
- Rotate access keys regularly (every 90 days)
- Use different keys for dev/staging/production
- Add `.env` to `.gitignore` (already done)

### ❌ DON'T:
- Never commit access keys to Git
- Never share secret keys in Slack/email
- Don't use root account access keys
- Don't give overly broad permissions

## 🔐 Required IAM Permissions for ChaosSec

Your IAM user/role needs these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "fis:StartExperiment",
        "fis:GetExperiment",
        "fis:StopExperiment",
        "fis:ListExperiments"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:GetMetricStatistics",
        "cloudwatch:ListMetrics",
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "config:DescribeComplianceByResource",
        "config:GetComplianceDetailsByResource"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudtrail:LookupEvents"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketAcl",
        "s3:PutBucketAcl",
        "s3:GetPublicAccessBlock",
        "s3:PutPublicAccessBlock",
        "s3:DeletePublicAccessBlock",
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": [
        "arn:aws:s3:::chaossec-*",
        "arn:aws:s3:::chaossec-*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock-runtime:InvokeModel"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/chaossec*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:*:*:table/chaossec-*"
    }
  ]
}
```

## 🧪 Testing Your AWS Credentials

After adding credentials to `.env`, test them:

```bash
# Activate venv
source venv/bin/activate

# Test AWS credentials
python -c "import boto3; print('Region:', boto3.Session().region_name); print('Account ID:', boto3.client('sts').get_caller_identity()['Account'])"
```

Expected output:
```
Region: us-east-1
Account ID: 123456789012
```

If you get an error, your credentials are invalid or missing.

## 🎯 Quick Setup Checklist

- [ ] Created IAM user in AWS Console
- [ ] Downloaded Access Key ID and Secret Access Key
- [ ] Added both to `.env` file
- [ ] Added `.env` to `.gitignore` (already done)
- [ ] Tested credentials with boto3
- [ ] Verified user has required IAM permissions
- [ ] Never committed `.env` to Git

## 🆘 Troubleshooting

### Error: "Unable to locate credentials"
**Solution:** Add AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to `.env`

### Error: "An error occurred (UnauthorizedOperation)"
**Solution:** Your IAM user lacks required permissions. See IAM policy above.

### Error: "The security token included in the request is invalid"
**Solution:** Your secret access key is wrong or credentials expired

### Error: "Access Denied" for Bedrock
**Solution:** Enable Bedrock access in AWS Console → Bedrock → Model access

---

**Now you're ready!** Add your AWS access keys to `.env` and ChaosSec will authenticate properly with all AWS services. 🚀

