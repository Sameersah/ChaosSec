# 🔧 System Initiative Configuration - Step by Step

## What is System Initiative?

System Initiative (SI) is a platform for creating **digital twins** of your infrastructure. ChaosSec uses it to:
- Simulate infrastructure changes before applying them
- Validate changes against guardrails
- Test chaos scenarios safely

---

## 📝 System Initiative Configuration Fields

```env
SYSTEM_INITIATIVE_API_URL=https://api.systeminit.com
SYSTEM_INITIATIVE_API_KEY=YOUR_SI_API_KEY_HERE
SYSTEM_INITIATIVE_WORKSPACE_ID=
```

### Field Explanations:

| Field | What It Is | Required? |
|-------|-----------|-----------|
| `SYSTEM_INITIATIVE_API_URL` | API endpoint URL | ✅ Yes (already set) |
| `SYSTEM_INITIATIVE_API_KEY` | Your authentication token | ✅ Yes (you need to get this) |
| `SYSTEM_INITIATIVE_WORKSPACE_ID` | Your workspace ID | ⚠️ Optional (can be empty) |

---

## 🚀 Option 1: Get Real System Initiative Credentials (Recommended)

### Step 1: Sign Up for System Initiative

1. **Go to**: https://www.systeminit.com
2. Click **Sign Up** or **Get Started**
3. Create an account with your email
4. Verify your email

### Step 2: Get Your API Key

1. **Log into System Initiative dashboard**
2. Go to **Settings** or **Profile** (top right)
3. Click **API Keys** or **Developer Settings**
4. Click **Create API Key** or **Generate Token**
5. **Copy the API key** (starts with `si_` or similar)
6. Paste it into your `.env`:
   ```env
   SYSTEM_INITIATIVE_API_KEY=si_your_actual_key_here
   ```

### Step 3: Get Your Workspace ID (Optional)

1. In System Initiative dashboard, go to **Workspaces**
2. Click on your workspace name
3. Look for **Workspace ID** in workspace settings
4. Copy it to `.env`:
   ```env
   SYSTEM_INITIATIVE_WORKSPACE_ID=ws_your_workspace_id
   ```

### Step 4: Verify API URL

The default URL should work:
```env
SYSTEM_INITIATIVE_API_URL=https://api.systeminit.com
```

If System Initiative gives you a different URL, use that instead.

---

## 🧪 Option 2: Use Mock Mode for Testing (Quick Start)

If you don't have System Initiative credentials yet or want to test quickly:

### Just use a placeholder:

```env
# System Initiative Configuration (Mock Mode)
SYSTEM_INITIATIVE_API_URL=https://api.systeminit.com
SYSTEM_INITIATIVE_API_KEY=mock-si-key-for-testing
SYSTEM_INITIATIVE_WORKSPACE_ID=mock-workspace
```

**ChaosSec will work** but System Initiative features will return mock responses.

---

## 🔍 How ChaosSec Uses System Initiative

### 1. **Digital Twin Creation**
ChaosSec creates a copy of your AWS infrastructure in System Initiative:
```python
# Creates digital twin of S3 buckets, EC2 instances, etc.
twin_id = system_initiative.create_digital_twin(aws_resources)
```

### 2. **Change Simulation**
Before making real AWS changes, ChaosSec simulates them:
```python
# Simulates: "What if I make this S3 bucket public?"
result = system_initiative.simulate_changeset(proposed_changes)
```

### 3. **Guardrail Validation**
Checks if changes violate security/compliance rules:
```python
# Validates: "Is this change safe?"
validation = system_initiative.validate_guardrails(changeset)
```

### 4. **Safe Rollback**
If something goes wrong, can rollback:
```python
# Undo the change
system_initiative.rollback_changeset(changeset_id)
```

---

## ✅ Complete Configuration Example

### For Real System Initiative:
```env
# System Initiative Configuration
SYSTEM_INITIATIVE_API_URL=https://api.systeminit.com
SYSTEM_INITIATIVE_API_KEY=si_abc123def456ghi789  # Your real key
SYSTEM_INITIATIVE_WORKSPACE_ID=ws_prod_12345     # Your workspace (optional)
```

### For Mock/Testing:
```env
# System Initiative Configuration (Mock Mode)
SYSTEM_INITIATIVE_API_URL=https://api.systeminit.com
SYSTEM_INITIATIVE_API_KEY=mock-si-key
SYSTEM_INITIATIVE_WORKSPACE_ID=
```

---

## 🧪 Test Your Configuration

After adding your System Initiative credentials:

```bash
cd /Users/sameer/Documents/hackathon/ChaosSec
source venv/bin/activate

# Test System Initiative connection
python -c "
from dotenv import load_dotenv
load_dotenv()
import os
print('✅ SI API URL:', os.getenv('SYSTEM_INITIATIVE_API_URL'))
print('✅ SI API Key:', os.getenv('SYSTEM_INITIATIVE_API_KEY')[:10] + '...')
print('✅ SI Workspace:', os.getenv('SYSTEM_INITIATIVE_WORKSPACE_ID') or 'Not set (OK)')
"
```

---

## 🆘 Troubleshooting

### "I don't have System Initiative account"
**Solution:** Use mock mode with placeholder values (see Option 2 above)

### "Where do I find the API key?"
**Solution:** 
1. Log into https://www.systeminit.com
2. Settings → API Keys → Generate
3. Copy the key

### "What if System Initiative is down?"
**Solution:** ChaosSec will fall back gracefully. In the code:
```python
# If SI API fails, ChaosSec continues but skips simulation
if not si_response:
    logger.warning("System Initiative unavailable, skipping simulation")
```

### "Do I need to pay for System Initiative?"
**Solution:** Check their website for pricing. Many services have free tiers for testing.

---

## 📋 Quick Decision Guide

### Choose Your Path:

```
Do you have System Initiative account?
│
├─ YES → Get API key from SI dashboard
│         → Add to SYSTEM_INITIATIVE_API_KEY
│         → Run demo with real simulation
│
└─ NO  → Option A: Sign up for System Initiative (10 min)
          Option B: Use mock mode for now:
                    SYSTEM_INITIATIVE_API_KEY=mock-si-key
```

---

## 🎯 Your Next Steps

1. **Decide:** Real System Initiative or Mock Mode?

2. **If Real:**
   - [ ] Sign up at https://www.systeminit.com
   - [ ] Get API key from dashboard
   - [ ] Add key to `.env`

3. **If Mock (Quick Start):**
   - [ ] Set `SYSTEM_INITIATIVE_API_KEY=mock-si-key`
   - [ ] ChaosSec will work with simulated responses

4. **Test:**
   ```bash
   python demo_run.py
   ```

---

## 💡 Recommendation

For your **hackathon MVP**, I recommend:

✅ **Use Mock Mode** to get started quickly:
```env
SYSTEM_INITIATIVE_API_KEY=mock-si-key-for-hackathon
```

This lets you:
- Run ChaosSec immediately
- See the full flow working
- Demo the concept
- Add real SI credentials later if needed

The mock mode still demonstrates the architecture and flow perfectly! 🚀

