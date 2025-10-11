# 🆕 Create IAM User for ChaosSec - Step-by-Step Guide

## 📋 Prerequisites
- AWS Account access with administrator permissions
- Ability to create IAM users and policies

---

## 🚀 Step 1: Create IAM User

### 1.1 Go to IAM Console
1. Log into **AWS Console**: https://console.aws.amazon.com
2. Search for **IAM** in the top search bar
3. Click **IAM** to open the Identity and Access Management console

### 1.2 Create New User
1. Click **Users** in the left sidebar
2. Click **Create user** button (orange button, top right)
3. **User name**: `chaossec-agent` (or any name you prefer)
4. ⚠️ **DO NOT** check "Provide user access to AWS Management Console" (we only need API access)
5. Click **Next**

---

## 🔐 Step 2: Set Permissions

You have 3 options for permissions:

### Option A: Quick Start (Broad Permissions - Easiest)
**Good for: Testing and development**

1. Select **Attach policies directly**
2. Search and check these AWS managed policies:
   - `PowerUserAccess` (almost full access, good for testing)
   
3. Click **Next**

⚠️ **Note:** This gives broad permissions. For production, use Option C below.

### Option B: Service-Specific (Moderate Permissions - Recommended)
**Good for: Safer testing with specific services**

1. Select **Attach policies directly**
2. Search and check these AWS managed policies:
   - `CloudWatchReadOnlyAccess`
   - `CloudWatchLogsFullAccess`
   - `AWSConfigUserAccess`
   - `CloudTrailReadOnlyAccess`
   
3. Click **Create policy** (opens new tab)
4. Click **JSON** tab and paste this policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "fis:*",
        "bedrock:InvokeModel",
        "bedrock-runtime:InvokeModel",
        "s3:*",
        "dynamodb:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

5. Click **Next**
6. **Policy name**: `ChaosSec-CustomPolicy`
7. Click **Create policy**
8. Go back to the user creation tab
9. Click refresh button and select your new policy
10. Click **Next**

### Option C: Least Privilege (Most Secure - Best for Production)
**Good for: Production environments**

1. Select **Attach policies directly**
2. Click **Create policy** (opens new tab)
3. Click **JSON** tab
4. Copy the complete IAM policy from `AWS_CREDENTIALS_EXPLAINED.md`
5. Create policy named `ChaosSec-LeastPrivilege`
6. Go back and attach this policy
7. Click **Next**

---

## 🔑 Step 3: Create Access Keys

### 3.1 Review and Create User
1. Review the settings
2. Click **Create user**
3. You'll see "User created successfully"

### 3.2 Generate Access Keys
1. Click on the username you just created (e.g., `chaossec-agent`)
2. Click **Security credentials** tab
3. Scroll down to **Access keys** section
4. Click **Create access key** button

### 3.3 Select Use Case
1. Select **Command Line Interface (CLI)**
2. Check the box: ☑️ "I understand the above recommendation..."
3. Click **Next**

### 3.4 Add Description (Optional)
1. Description tag: `ChaosSec local development`
2. Click **Create access key**

### 3.5 ⚠️ SAVE YOUR KEYS NOW!
You'll see:
- **Access key ID**: `AKIA...` (starts with AKIA)
- **Secret access key**: Long random string

**CRITICAL:** The secret key is shown **ONLY ONCE**! 

**Choose one:**
- Click **Download .csv file** (recommended)
- Copy both values to a safe place immediately

---

## 📝 Step 4: Add Keys to Your .env File

1. Open your `.env` file in ChaosSec project:
```bash
cd /Users/sameer/Documents/hackathon/ChaosSec
nano .env  # or use your preferred editor
```

2. Add your credentials:
```env
AWS_ACCESS_KEY_ID=AKIA...your_access_key_here
AWS_SECRET_ACCESS_KEY=wJalr...your_secret_key_here
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012  # Your AWS account ID
```

3. Save and close the file

---

## ✅ Step 5: Test Your Credentials

### 5.1 Activate Virtual Environment
```bash
cd /Users/sameer/Documents/hackathon/ChaosSec
source venv/bin/activate
```

### 5.2 Test AWS Connection
```bash
python -c "import boto3; sts = boto3.client('sts'); identity = sts.get_caller_identity(); print(f'✅ Connected as: {identity[\"Arn\"]}'); print(f'Account ID: {identity[\"Account\"]}')"
```

**Expected output:**
```
✅ Connected as: arn:aws:iam::123456789012:user/chaossec-agent
Account ID: 123456789012
```

### 5.3 Test Bedrock Access
```bash
python -c "import boto3; bedrock = boto3.client('bedrock', region_name='us-east-1'); print('✅ Bedrock client created successfully')"
```

---

## 🎯 Quick Reference

### What You Need to Copy:

From AWS Console after creating user:
```
Access key ID: AKIA________________
Secret access key: ____________________________________
```

To `.env` file:
```env
AWS_ACCESS_KEY_ID=AKIA________________
AWS_SECRET_ACCESS_KEY=____________________________________
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=123456789012
```

---

## 🆘 Troubleshooting

### Error: "User already exists"
- Choose a different username or delete the existing user first

### Error: "You are not authorized to perform this operation"
- You need administrator access to create IAM users
- Ask your AWS account administrator for help

### Error: "Access Denied" when testing
- Your IAM policy might be too restrictive
- Try Option A (PowerUserAccess) first for testing

### Error: "Invalid credentials"
- Double-check you copied the keys correctly
- No extra spaces or newlines
- Secret key is case-sensitive

### Can't see "Create access key" button
- Make sure you're on the **Security credentials** tab
- You might have reached the 2-key limit (delete an old one)

### Error: "Bedrock access denied"
- Enable Bedrock in AWS Console:
  - Go to **AWS Bedrock** service
  - Click **Model access** in left sidebar
  - Click **Modify model access**
  - Enable **Anthropic Claude** models
  - Submit and wait for approval (~2 minutes)

---

## 🔒 Security Best Practices

After creating your user:

✅ **DO:**
- Download the .csv file and store it securely
- Add `.env` to `.gitignore` (already done)
- Delete access keys when done testing
- Use different keys for dev/staging/prod
- Rotate keys every 90 days

❌ **DON'T:**
- Don't share secret keys via email/Slack
- Don't commit keys to Git
- Don't use root account access keys
- Don't give overly broad permissions in production

---

## 📚 Additional Resources

- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [Creating IAM Users](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_users_create.html)
- [Managing Access Keys](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

---

## ✅ Checklist

- [ ]
