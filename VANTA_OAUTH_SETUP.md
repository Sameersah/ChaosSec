# 🔐 Vanta OAuth2 Authentication Setup

## ✅ What Changed

ChaosSec now uses **OAuth2 authentication** with Vanta instead of simple API keys. This is the proper way to authenticate with Vanta's API.

## 🤔 Why OAuth2?

Vanta uses OAuth 2.0 Client Credentials flow for API authentication, which provides:
- ✅ Automatic token refresh
- ✅ Better security (tokens expire)
- ✅ Industry standard authentication
- ✅ Granular permission scopes

## 📝 Configuration Required

In your `.env` file, add your Vanta OAuth credentials:

```env
# Vanta Configuration (OAuth2 Authentication)
VANTA_CLIENT_ID=your_vanta_client_id_here
VANTA_CLIENT_SECRET=your_vanta_client_secret_here
VANTA_API_URL=https://api.vanta.com
VANTA_OAUTH_TOKEN_URL=https://api.vanta.com/oauth/token
```

## 🔑 How to Get Your Vanta Credentials

1. Log into your **Vanta dashboard**
2. Go to **Settings** → **API** → **OAuth Applications**
3. Create a new OAuth application (or use existing one)
4. Copy your:
   - **Client ID** 
   - **Client Secret** ⚠️ (keep this secret!)
5. Paste them into your `.env` file

## ⚙️ How It Works

The updated `VantaClient` now handles OAuth2 automatically:

### 1. **Automatic Token Management**
- Requests an access token using your Client ID and Secret
- Caches the token with expiration tracking
- Auto-refreshes when token expires (with 5-minute safety buffer)

### 2. **Secure API Calls**
- All API requests use `Bearer {access_token}` authentication
- Tokens are obtained via OAuth2 Client Credentials flow
- Requested scopes: `evidence:write compliance:read`

### 3. **Error Handling**
- Falls back to local storage if API calls fail
- Logs all authentication attempts for debugging
- Provides clear error messages

## 📦 Code Changes Made

### 1. `env.example` - Updated configuration template
```diff
- VANTA_API_KEY=mock-vanta-key
+ VANTA_CLIENT_ID=YOUR_VANTA_CLIENT_ID_HERE
+ VANTA_CLIENT_SECRET=YOUR_VANTA_CLIENT_SECRET_HERE
+ VANTA_OAUTH_TOKEN_URL=https://api.vanta.com/oauth/token
```

### 2. `vanta_integration.py` - Added OAuth2 support
**New Methods:**
- `_get_access_token()` - Handles OAuth token acquisition with caching
- `_make_api_request()` - Makes authenticated API calls with Bearer token
- Token caching with automatic refresh on expiry
- Updated `upload_evidence()` to use real OAuth API calls (when not in mock mode)
- Updated `get_unverified_controls()` to use real OAuth API calls

**OAuth Token Flow:**
```python
1. Check if cached token is still valid
2. If expired or missing:
   - POST to /oauth/token with client_credentials
   - Cache new token + expiration time
3. Use token in Authorization: Bearer {token} header
```

### 3. `config.py` - Updated configuration dataclass
```python
@dataclass
class VantaConfig:
    client_id: str
    client_secret: str
    api_url: str
    oauth_token_url: str
```

### 4. `orchestrator.py` - Updated client initialization
```python
self.vanta_client = VantaClient(
    client_id=config.vanta.client_id,
    client_secret=config.vanta.client_secret,
    api_url=config.vanta.api_url,
    oauth_token_url=config.vanta.oauth_token_url,
    logger=self.logger,
    mock_mode=True  # Set to False for real API
)
```

## 🧪 Testing OAuth Integration

### Mock Mode (Default)
By default, ChaosSec runs in **mock mode** - no real API calls are made. Evidence is stored locally.

```python
# In orchestrator or config
mock_mode=True  # Evidence saved locally, no OAuth calls
```

### Real Mode (Production)
To enable real Vanta API calls:

```python
# Set in orchestrator.py or via environment variable
mock_mode=False  # Uses real OAuth authentication
```

Or add to `.env`:
```env
CHAOSSEC_VANTA_MOCK_MODE=false
```

## 🔍 Debugging OAuth

If you have issues connecting to Vanta:

1. **Check your credentials:**
   ```bash
   echo $VANTA_CLIENT_ID
   echo $VANTA_CLIENT_SECRET  # Should show your secret
   ```

2. **Enable debug logging:**
   ```env
   CHAOSSEC_LOG_LEVEL=DEBUG
   ```

3. **Check logs for OAuth errors:**
   - Look for `"Requesting new Vanta OAuth access token"`
   - Check for HTTP error codes (401 = bad credentials, 403 = insufficient permissions)

4. **Test OAuth manually:**
   ```bash
   curl -X POST https://api.vanta.com/oauth/token \
     -d "grant_type=client_credentials" \
     -d "client_id=YOUR_CLIENT_ID" \
     -d "client_secret=YOUR_CLIENT_SECRET" \
     -d "scope=evidence:write compliance:read"
   ```

## 🎯 Next Steps

1. ✅ Add your Vanta Client ID and Secret to `.env`
2. ✅ Test in mock mode first: `python demo_run.py`
3. ✅ When ready, set `mock_mode=False` in orchestrator
4. ✅ Run a real chaos test and verify evidence uploads to Vanta

## 📚 Additional Resources

- [Vanta API Documentation](https://developer.vanta.com)
- [OAuth 2.0 Client Credentials Flow](https://oauth.net/2/grant-types/client-credentials/)
- ChaosSec README for full setup instructions

