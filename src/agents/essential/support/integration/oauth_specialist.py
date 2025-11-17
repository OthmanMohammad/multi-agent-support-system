"""
OAuth Specialist Agent - Handles OAuth authentication flows.

This agent specializes in OAuth 2.0 setup, troubleshooting authentication flows,
token refresh, scope management, and common OAuth implementation issues.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("oauth_specialist", tier="essential", category="integration")
class OAuthSpecialist(BaseAgent):
    """
    OAuth Specialist - Expert in OAuth 2.0 authentication flows.

    Handles:
    - OAuth setup and configuration
    - Authorization flow troubleshooting
    - Token refresh implementation
    - Scope and permission issues
    - Callback and redirect errors
    """

    # OAuth-related keywords for detection
    OAUTH_TOPICS = {
        "setup": ["setup oauth", "configure oauth", "register app", "create oauth", "oauth setup"],
        "callback_error": ["callback", "redirect", "redirect_uri", "callback error", "state mismatch"],
        "token_refresh": ["refresh token", "token expired", "renew token", "token refresh"],
        "scope_error": ["scope", "permission", "access denied", "insufficient privileges"],
        "grant_flow": ["authorization code", "grant type", "oauth flow", "authentication flow"],
        "pkce": ["pkce", "code challenge", "code verifier"],
    }

    # Common OAuth error codes
    ERROR_CODES = {
        "redirect_uri_mismatch": "Redirect URI doesn't match registered URI",
        "invalid_scope": "Requested scope is not authorized",
        "access_denied": "User denied authorization",
        "invalid_grant": "Authorization code is invalid or expired",
        "unauthorized_client": "Client is not authorized for this grant type",
        "unsupported_grant_type": "Grant type not supported",
    }

    def __init__(self):
        config = AgentConfig(
            name="oauth_specialist",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE
            ],
            kb_category="integration",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process OAuth-related requests.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with OAuth guidance
        """
        self.logger.info("oauth_specialist_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        self.logger.debug(
            "oauth_processing_details",
            message_preview=message[:100],
            turn_count=state["turn_count"]
        )

        # Detect OAuth topic
        topic = self._detect_oauth_topic(message)

        # Extract error code if present
        error_code = self._extract_error_code(message)

        self.logger.info(
            "oauth_topic_detected",
            topic=topic,
            error_code=error_code
        )

        # Search knowledge base for OAuth documentation
        kb_results = await self.search_knowledge_base(
            message,
            category="integration",
            limit=2
        )
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info(
                "kb_articles_found",
                count=len(kb_results)
            )

        # Generate OAuth guidance
        response = self._generate_oauth_guide(topic, error_code, kb_results)

        state["agent_response"] = response
        state["oauth_topic"] = topic
        state["error_code"] = error_code
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "oauth_processing_completed",
            status="resolved",
            topic=topic
        )

        return state

    def _detect_oauth_topic(self, message: str) -> str:
        """
        Detect which OAuth topic the user is asking about.

        Args:
            message: User's message

        Returns:
            OAuth topic identifier
        """
        message_lower = message.lower()

        # Check for specific topics
        for topic, keywords in self.OAUTH_TOPICS.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic

        # Default to general setup
        return "setup"

    def _extract_error_code(self, message: str) -> Optional[str]:
        """
        Extract OAuth error code from message if present.

        Args:
            message: User's message

        Returns:
            Error code if found, None otherwise
        """
        message_lower = message.lower()

        for error_code in self.ERROR_CODES.keys():
            if error_code.replace("_", " ") in message_lower or error_code in message_lower:
                return error_code

        return None

    def _generate_oauth_guide(
        self,
        topic: str,
        error_code: Optional[str],
        kb_results: list
    ) -> str:
        """
        Generate OAuth guidance based on topic and error.

        Args:
            topic: OAuth topic
            error_code: Error code if applicable
            kb_results: Knowledge base search results

        Returns:
            Formatted OAuth guide
        """
        # If specific error code, provide targeted fix
        if error_code:
            guide = self._guide_error_fix(error_code)
        else:
            # Otherwise, provide topic-based guide
            guides = {
                "setup": self._guide_oauth_setup(),
                "callback_error": self._guide_callback_errors(),
                "token_refresh": self._guide_token_refresh(),
                "scope_error": self._guide_scope_management(),
                "grant_flow": self._guide_authorization_flow(),
                "pkce": self._guide_pkce(),
            }
            guide = guides.get(topic, guides["setup"])

        # Add KB context if available
        if kb_results:
            kb_context = "\n\n**📚 Related documentation:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"
            guide += kb_context

        return guide

    def _guide_oauth_setup(self) -> str:
        """Complete OAuth 2.0 setup guide"""
        return """**🔐 OAuth 2.0 Setup Guide**

Set up OAuth 2.0 authentication in 4 steps.

**Step 1: Register your OAuth application**

1. Navigate to **Settings > Developer > OAuth Apps**
2. Click **"Create OAuth App"**
3. Fill in application details:
   - **App name:** Your application name
   - **Redirect URI:** `https://your-app.com/oauth/callback`
   - **Scopes:** Select required permissions (read, write, admin)
   - **App description:** (optional)

4. **Save credentials securely:**
```plaintext
Client ID: abc123def456ghi789
Client Secret: xyz789abc123def456ghi789  ⚠️ Keep secret!
```

**Step 2: Implement authorization flow**

```python
from flask import Flask, request, redirect
import requests

app = Flask(__name__)

# Your OAuth credentials (use environment variables in production)
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "<YOUR_CLIENT_ID_HERE>")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "<YOUR_CLIENT_SECRET_HERE>")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "https://your-app.com/oauth/callback")

# Step 2a: Redirect user to authorize
@app.route('/login')
def login():
    # Generate random state for CSRF protection
    state = generate_random_state()
    save_state_to_session(state)

    auth_url = (
        "https://api.example.com/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=read+write&"
        f"response_type=code&"
        f"state={state}"
    )

    return redirect(auth_url)

# Step 2b: Handle callback
@app.route('/oauth/callback')
def callback():
    # Verify state (CSRF protection)
    state = request.args.get('state')
    if state != get_state_from_session():
        return "Invalid state", 400

    # Exchange authorization code for access token
    code = request.args.get('code')

    token_response = requests.post(
        'https://api.example.com/oauth/token',
        data={
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI
        }
    )

    tokens = token_response.json()
    # tokens = {
    #     "access_token": "access_token_here",
    #     "refresh_token": "refresh_token_here",
    #     "expires_in": 3600,
    #     "token_type": "Bearer"
    # }

    # Store tokens securely
    save_tokens_to_database(tokens)

    return "Successfully authenticated!"
```

**Step 3: Use access token in API requests**

```python
import requests

def make_api_call(access_token):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.get(
        'https://api.example.com/v1/customer',
        headers=headers
    )

    return response.json()
```

**Step 4: Implement token refresh**

```python
def refresh_access_token(refresh_token):
    response = requests.post(
        'https://api.example.com/oauth/token',
        data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
    )

    return response.json()['access_token']
```

**Security best practices:**
✅ Always use HTTPS for redirect URIs
✅ Implement state parameter (CSRF protection)
✅ Store client secret securely (env vars, secrets manager)
✅ Never expose client secret in frontend code
✅ Use PKCE for mobile/SPA applications
✅ Rotate refresh tokens periodically

**OAuth endpoints:**
- Authorize: `https://api.example.com/oauth/authorize`
- Token: `https://api.example.com/oauth/token`
- Revoke: `https://api.example.com/oauth/revoke`

**Available scopes:**
- `read` - Read customer data
- `write` - Create/update resources
- `admin` - Full administrative access

**Need help with a specific step?** Let me know!"""

    def _guide_callback_errors(self) -> str:
        """Guide for OAuth callback/redirect errors"""
        return """**🔄 OAuth Callback & Redirect Errors**

Troubleshooting common OAuth callback issues.

**Common Error: redirect_uri_mismatch**

**Problem:** The redirect URI doesn't match what you registered.

**Solution:**
1. Check registered URI in **Settings > OAuth Apps > Your App**
2. **Must match EXACTLY** (including protocol, port, path):

```plaintext
❌ Registered: https://app.com/callback
   Actual:     https://app.com/oauth/callback

❌ Registered: https://app.com/callback
   Actual:     http://app.com/callback  (http vs https!)

❌ Registered: https://app.com/callback
   Actual:     https://app.com:3000/callback  (port!)

✅ Both:       https://app.com/callback  (perfect match!)
```

3. **Update registered URI** to match your actual callback URL
4. For development, register multiple URIs:
   - Production: `https://app.com/callback`
   - Staging: `https://staging.app.com/callback`
   - Local: `http://localhost:3000/callback`

**Common Error: state parameter mismatch**

**Problem:** State parameter doesn't match (CSRF attack prevention).

**Solution:**
```python
# Step 1: Generate and store state before redirect
import secrets

def initiate_oauth():
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state  # Store in session

    return redirect(
        f"https://api.example.com/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"state={state}&"
        "..."
    )

# Step 2: Verify state in callback
@app.route('/callback')
def callback():
    returned_state = request.args.get('state')
    stored_state = session.get('oauth_state')

    if not returned_state or returned_state != stored_state:
        return "Invalid state - possible CSRF attack", 400

    # Clear used state
    session.pop('oauth_state', None)

    # Continue with token exchange...
```

**Common Error: access_denied**

**Problem:** User clicked "Deny" on authorization screen.

**Solution:**
```python
@app.route('/callback')
def callback():
    # Check if user denied
    error = request.args.get('error')
    if error == 'access_denied':
        return '''
<h1>Authorization Denied</h1>
<p>You must authorize the app to continue.</p>
<a href="/login">Try Again</a>
        '''

    # Continue normal flow...
```

**Common Error: invalid_grant (authorization code issues)**

**Causes:**
- Authorization code already used (can only use once!)
- Authorization code expired (valid for 10 minutes)
- Authorization code from different client_id

**Solution:**
```python
def exchange_code_for_token(code):
    try:
        response = requests.post(
            'https://api.example.com/oauth/token',
            data={
                'grant_type': 'authorization_code',
                'code': code,  # Use code only once!
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'redirect_uri': REDIRECT_URI
            }
        )

        if response.status_code != 200:
            error = response.json()
            if error.get('error') == 'invalid_grant':
                # Code expired or already used
                return redirect('/login')  # Restart flow

        return response.json()

    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        return redirect('/login')
```

**Debugging callback issues:**

```python
@app.route('/callback')
def callback():
    # Log all callback parameters
    logger.info(f"Callback params: {request.args}")
    logger.info(f"Stored state: {session.get('oauth_state')}")

    # Check for errors
    if 'error' in request.args:
        error = request.args.get('error')
        error_desc = request.args.get('error_description')
        logger.error(f"OAuth error: {error} - {error_desc}")
        return f"OAuth error: {error_desc}", 400

    # Continue...
```

**Test your callback:**
1. Use OAuth Playground: Settings > OAuth Apps > Test Flow
2. Check browser network tab for redirect URL
3. Verify all parameters are present (code, state)

**Still having issues?** Share the exact error message and I'll help debug!"""

    def _guide_token_refresh(self) -> str:
        """Guide for token refresh implementation"""
        return """**🔄 OAuth Token Refresh Guide**

Access tokens expire. Here's how to refresh them seamlessly.

**Understanding token lifecycle:**
```plaintext
Initial authorization:
├─ access_token  (expires in 1 hour)
└─ refresh_token (long-lived, doesn't expire)

After 1 hour:
├─ access_token expires ❌
└─ Use refresh_token to get new access_token ✅
```

**Implementation: Token refresh**

```python
import requests
from datetime import datetime, timedelta

class TokenManager:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None

    def refresh_access_token(self):
        \"\"\"Refresh the access token using refresh token\"\"\"
        response = requests.post(
            'https://api.example.com/oauth/token',
            data={
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
        )

        if response.status_code == 200:
            data = response.json()
            self.access_token = data['access_token']
            # Some APIs also return new refresh token
            if 'refresh_token' in data:
                self.refresh_token = data['refresh_token']
            # Calculate expiration
            self.expires_at = datetime.now() + timedelta(
                seconds=data['expires_in']
            )
            return self.access_token
        else:
            raise Exception(f"Token refresh failed: {response.json()}")

    def get_valid_token(self):
        \"\"\"Get a valid access token (refresh if expired)\"\"\"
        # Check if token exists
        if not self.access_token:
            raise Exception("No access token - user needs to authorize")

        # Check if token expired
        if datetime.now() >= self.expires_at:
            self.refresh_access_token()

        return self.access_token
```

**Auto-refresh pattern (recommended):**

```python
class APIClient:
    def __init__(self, token_manager):
        self.token_manager = token_manager

    def make_api_call(self, url, method='GET', **kwargs):
        \"\"\"Make API call with automatic token refresh\"\"\"
        # Get valid token (auto-refreshes if needed)
        token = self.token_manager.get_valid_token()

        headers = kwargs.get('headers', {})
        headers['Authorization'] = f'Bearer {token}'
        kwargs['headers'] = headers

        # Make request
        response = requests.request(method, url, **kwargs)

        # If token expired mid-flight, refresh and retry
        if response.status_code == 401:
            token = self.token_manager.refresh_access_token()
            headers['Authorization'] = f'Bearer {token}'
            response = requests.request(method, url, **kwargs)

        return response

# Usage
client = APIClient(token_manager)
response = client.make_api_call('https://api.example.com/customers')
```

**Proactive refresh (best practice):**

```python
def get_valid_token(self):
    \"\"\"Get token, refresh proactively before expiry\"\"\"
    if not self.access_token:
        raise Exception("No token")

    # Refresh 5 minutes before expiry (safer)
    buffer = timedelta(minutes=5)
    if datetime.now() >= (self.expires_at - buffer):
        self.refresh_access_token()

    return self.access_token
```

**Handle refresh token expiration:**

```python
def refresh_access_token(self):
    try:
        response = requests.post(...)

        if response.status_code == 200:
            # Success
            return response.json()['access_token']

        elif response.status_code == 400:
            error = response.json().get('error')
            if error == 'invalid_grant':
                # Refresh token expired/revoked
                # User needs to re-authorize
                self.clear_tokens()
                raise Exception("Re-authorization required")

    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise
```

**Store tokens securely:**

```python
# ❌ BAD - Plain text in database
db.save({
    'access_token': token,
    'refresh_token': refresh
})

# ✅ GOOD - Encrypted storage
from cryptography.fernet import Fernet

cipher = Fernet(ENCRYPTION_KEY)

db.save({
    'access_token': cipher.encrypt(token.encode()),
    'refresh_token': cipher.encrypt(refresh.encode())
})
```

**Best practices:**
✅ Refresh proactively (before expiration)
✅ Store tokens encrypted
✅ Handle refresh failures gracefully
✅ Clear tokens on logout
✅ Rotate refresh tokens when possible
✅ Set short expiry for access tokens (1 hour)

**Background token refresh (async):**

```python
import asyncio

async def refresh_tokens_periodically():
    \"\"\"Background task to refresh tokens\"\"\"
    while True:
        try:
            # Refresh 50 minutes before expiry
            await asyncio.sleep(50 * 60)
            await token_manager.refresh_access_token()
        except Exception as e:
            logger.error(f"Background refresh failed: {e}")

# Start background task
asyncio.create_task(refresh_tokens_periodically())
```

**Testing token refresh:**
1. Reduce token TTL in dev: Settings > OAuth Apps > Token TTL (5 minutes)
2. Wait for expiration and test refresh
3. Verify new token works

**Token refresh failing?** Check:
- Refresh token stored correctly
- Client ID/secret are correct
- Refresh token not revoked/expired
- Network connectivity to token endpoint"""

    def _guide_scope_management(self) -> str:
        """Guide for OAuth scopes and permissions"""
        return """**🔑 OAuth Scopes & Permissions**

Managing OAuth scopes and access levels.

**Available scopes:**

**Read access:**
- `customers:read` - Read customer data
- `products:read` - Read product catalog
- `analytics:read` - Read analytics data

**Write access:**
- `customers:write` - Create/update customers
- `products:write` - Manage products
- `subscriptions:write` - Manage subscriptions

**Administrative:**
- `webhooks:manage` - Configure webhooks
- `api_keys:manage` - Manage API keys
- `account:admin` - Full account access

**Request specific scopes:**

```python
# Request multiple scopes (space-separated)
auth_url = (
    "https://api.example.com/oauth/authorize?"
    f"client_id={CLIENT_ID}&"
    f"scope=customers:read customers:write analytics:read&"
    "..."
)
```

**Check granted scopes:**

```python
# Token response includes granted scopes
token_response = {
    "access_token": "...",
    "refresh_token": "...",
    "scope": "customers:read customers:write",  # What was granted
    "expires_in": 3600
}

# User may grant fewer scopes than requested!
granted_scopes = token_response['scope'].split(' ')
if 'customers:write' not in granted_scopes:
    # Handle read-only access
    show_read_only_ui()
```

**Verify scope before API call:**

```python
def create_customer(access_token, customer_data):
    # Check if token has required scope
    token_info = get_token_info(access_token)

    if 'customers:write' not in token_info['scopes']:
        raise PermissionError("Insufficient scope: customers:write required")

    # Make API call
    response = requests.post(
        'https://api.example.com/customers',
        headers={'Authorization': f'Bearer {access_token}'},
        json=customer_data
    )
    return response
```

**Handle insufficient scope errors:**

```python
def make_api_call(url, access_token):
    response = requests.get(
        url,
        headers={'Authorization': f'Bearer {access_token}'}
    )

    if response.status_code == 403:
        error = response.json()
        if error.get('error') == 'insufficient_scope':
            # Need to re-authorize with additional scopes
            required_scope = error.get('required_scope')
            return f"Please re-authorize with scope: {required_scope}"

    return response.json()
```

**Request additional scopes (incremental auth):**

```python
# User already authorized with 'read' scope
# Now need 'write' scope
def request_additional_scope():
    current_scopes = "customers:read"
    additional_scope = "customers:write"

    # Request combined scopes
    all_scopes = f"{current_scopes} {additional_scope}"

    auth_url = (
        "https://api.example.com/oauth/authorize?"
        f"client_id={CLIENT_ID}&"
        f"scope={all_scopes}&"
        "..."
    )

    return redirect(auth_url)
```

**Best practices:**
✅ Request minimum required scopes
✅ Request additional scopes when needed (incremental)
✅ Display scope descriptions to users
✅ Handle scope denials gracefully
✅ Check scopes before API calls
✅ Store granted scopes with tokens

**Scope descriptions for users:**

```python
SCOPE_DESCRIPTIONS = {
    'customers:read': 'View your customer data',
    'customers:write': 'Create and update customer records',
    'analytics:read': 'Access your usage analytics',
    'account:admin': 'Full administrative access to your account'
}

# Show to user during authorization
def show_authorization_screen(requested_scopes):
    for scope in requested_scopes:
        print(f"• {SCOPE_DESCRIPTIONS[scope]}")
```

**Scope error handling:**

```python
@app.route('/callback')
def callback():
    error = request.args.get('error')

    if error == 'access_denied':
        # User denied all scopes
        return "Authorization required to continue"

    # Check which scopes were granted
    code = request.args.get('code')
    tokens = exchange_code(code)

    granted = tokens['scope'].split(' ')
    requested = session.get('requested_scopes', [])

    denied = set(requested) - set(granted)
    if denied:
        logger.warning(f"Scopes denied: {denied}")
        # Adjust app functionality based on granted scopes
        update_user_permissions(granted)
```

**Common scope errors:**

❌ **invalid_scope** - Scope doesn't exist
   → Check available scopes: Settings > OAuth > Scopes

❌ **insufficient_scope** - API call needs higher scope
   → Re-authorize with required scope

❌ **scope_too_broad** - Can't grant admin scope
   → Contact support for admin access

**View your granted scopes:**
Settings > OAuth > Authorized Apps > Your App > Scopes"""

    def _guide_authorization_flow(self) -> str:
        """Guide for OAuth authorization flow"""
        return """**🔐 OAuth 2.0 Authorization Flow**

Understanding the complete OAuth authorization flow.

**Flow diagram:**

```plaintext
1. User clicks "Login"
   └─> Your app redirects to authorization URL

2. User sees authorization screen
   ├─ App name & description
   ├─ Requested permissions (scopes)
   └─ "Authorize" or "Deny" buttons

3. User clicks "Authorize"
   └─> Redirected to your callback URL with code

4. Your server exchanges code for tokens
   ├─ Sends code + client_secret
   └─ Receives access_token + refresh_token

5. Your app uses access_token for API calls
   └─> Makes authenticated requests
```

**Complete implementation:**

```python
from flask import Flask, redirect, request, session
import requests
import secrets

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "<YOUR_SECRET_KEY_HERE>")

# OAuth configuration
CLIENT_ID = os.getenv("OAUTH_CLIENT_ID", "<YOUR_CLIENT_ID_HERE>")
CLIENT_SECRET = os.getenv("OAUTH_CLIENT_SECRET", "<YOUR_CLIENT_SECRET_HERE>")
REDIRECT_URI = os.getenv("OAUTH_REDIRECT_URI", "https://your-app.com/callback")
AUTH_URL = "https://api.example.com/oauth/authorize"
TOKEN_URL = "https://api.example.com/oauth/token"

# Step 1: Initiate authorization
@app.route('/login')
def login():
    # Generate state (CSRF protection)
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # Build authorization URL
    params = {
        'client_id': CLIENT_ID,
        'redirect_uri': REDIRECT_URI,
        'response_type': 'code',
        'scope': 'customers:read customers:write',
        'state': state
    }

    auth_url = AUTH_URL + '?' + '&'.join(
        f"{k}={v}" for k, v in params.items()
    )

    return redirect(auth_url)

# Step 2 & 3: User authorizes, receives callback
@app.route('/callback')
def callback():
    # Check for errors
    if 'error' in request.args:
        error = request.args.get('error')
        return f"Authorization failed: {error}", 400

    # Verify state (CSRF protection)
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return "Invalid state", 400

    # Get authorization code
    code = request.args.get('code')

    # Step 4: Exchange code for tokens
    token_response = requests.post(
        TOKEN_URL,
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'redirect_uri': REDIRECT_URI
        }
    )

    if token_response.status_code != 200:
        return f"Token exchange failed: {token_response.text}", 400

    tokens = token_response.json()
    # {
    #   "access_token": "...",
    #   "refresh_token": "...",
    #   "expires_in": 3600,
    #   "token_type": "Bearer",
    #   "scope": "customers:read customers:write"
    # }

    # Store tokens securely
    session['access_token'] = tokens['access_token']
    session['refresh_token'] = tokens['refresh_token']

    # Clean up
    session.pop('oauth_state', None)

    return redirect('/dashboard')

# Step 5: Use access token
@app.route('/api/customers')
def get_customers():
    access_token = session.get('access_token')
    if not access_token:
        return redirect('/login')

    response = requests.get(
        'https://api.example.com/v1/customers',
        headers={'Authorization': f'Bearer {access_token}'}
    )

    return response.json()

# Logout (revoke tokens)
@app.route('/logout')
def logout():
    access_token = session.get('access_token')

    if access_token:
        # Revoke token
        requests.post(
            'https://api.example.com/oauth/revoke',
            data={
                'token': access_token,
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET
            }
        )

    # Clear session
    session.clear()
    return redirect('/')
```

**Authorization URL parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `client_id` | Yes | Your OAuth app client ID |
| `redirect_uri` | Yes | Where to redirect after auth |
| `response_type` | Yes | Always "code" for this flow |
| `scope` | Yes | Requested permissions |
| `state` | Recommended | CSRF protection token |

**Token exchange parameters:**

| Parameter | Required | Description |
|-----------|----------|-------------|
| `grant_type` | Yes | "authorization_code" |
| `code` | Yes | Authorization code from callback |
| `client_id` | Yes | Your client ID |
| `client_secret` | Yes | Your client secret |
| `redirect_uri` | Yes | Must match exactly |

**Security checklist:**
✅ Use HTTPS everywhere
✅ Implement state parameter (CSRF)
✅ Store client_secret securely
✅ Validate redirect_uri
✅ Use short-lived authorization codes (10 min)
✅ Encrypt tokens at rest
✅ Implement token revocation

**Testing the flow:**
1. Open browser to `https://your-app.com/login`
2. Should redirect to authorization screen
3. Click "Authorize"
4. Should redirect back with tokens
5. Test API call with access token"""

    def _guide_pkce(self) -> str:
        """Guide for PKCE (Proof Key for Code Exchange)"""
        return r"""**🔐 PKCE (Proof Key for Code Exchange)**

PKCE adds security for mobile apps and SPAs (Single Page Apps).

**Why PKCE?**
- Mobile apps can't securely store client_secret
- SPAs can't hide client_secret (exposed in browser)
- PKCE eliminates need for client_secret

**How PKCE works:**

```plaintext
1. Generate random code_verifier
   └─> Random string (43-128 characters)

2. Create code_challenge from verifier
   └─> SHA256 hash of code_verifier

3. Send code_challenge in authorization request
   └─> Server stores it

4. Send code_verifier in token exchange
   └─> Server verifies it matches code_challenge
```

**Implementation (Python):**

```python
import secrets
import hashlib
import base64

def generate_pkce_pair():
    \"\"\"Generate code_verifier and code_challenge\"\"\"
    # Generate code_verifier (random string)
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')

    # Generate code_challenge (SHA256 of verifier)
    challenge = hashlib.sha256(code_verifier.encode()).digest()
    code_challenge = base64.urlsafe_b64encode(challenge).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge

# Step 1: Authorization request with PKCE
@app.route('/login')
def login():
    # Generate PKCE pair
    code_verifier, code_challenge = generate_pkce_pair()

    # Store verifier (need it later for token exchange)
    session['code_verifier'] = code_verifier

    # Generate state
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state

    # Authorization URL with PKCE
    auth_url = (
        f"{AUTH_URL}?"
        f"client_id={CLIENT_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=read+write&"
        f"state={state}&"
        f"code_challenge={code_challenge}&"
        f"code_challenge_method=S256"  # SHA256
    )

    return redirect(auth_url)

# Step 2: Token exchange with PKCE
@app.route('/callback')
def callback():
    code = request.args.get('code')
    code_verifier = session.get('code_verifier')

    # Exchange code for token (with verifier, NO client_secret!)
    response = requests.post(
        TOKEN_URL,
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'client_id': CLIENT_ID,
            'redirect_uri': REDIRECT_URI,
            'code_verifier': code_verifier  # PKCE!
        }
    )

    tokens = response.json()
    # Success!

    # Clean up
    session.pop('code_verifier', None)
    session.pop('oauth_state', None)

    return tokens
```

**JavaScript/React implementation:**

```javascript
// Generate PKCE pair
function generatePKCE() {
  // Generate random code_verifier
  const array = new Uint8Array(32);
  crypto.getRandomValues(array);
  const codeVerifier = base64URLEncode(array);

  // Generate code_challenge
  const encoder = new TextEncoder();
  const data = encoder.encode(codeVerifier);

  return crypto.subtle.digest('SHA-256', data).then(hash => {
    const codeChallenge = base64URLEncode(new Uint8Array(hash));

    return { codeVerifier, codeChallenge };
  });
}

function base64URLEncode(buffer) {
  return btoa(String.fromCharCode(...buffer))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');
}

// Authorization request
async function login() {
  const { codeVerifier, codeChallenge } = await generatePKCE();

  // Store verifier in session storage
  sessionStorage.setItem('code_verifier', codeVerifier);

  // Generate state
  const state = base64URLEncode(crypto.getRandomValues(new Uint8Array(32)));
  sessionStorage.setItem('oauth_state', state);

  // Redirect to authorization
  const authUrl = `${AUTH_URL}?` +
    `client_id=${CLIENT_ID}&` +
    `redirect_uri=${REDIRECT_URI}&` +
    `response_type=code&` +
    `scope=read+write&` +
    `state=${state}&` +
    `code_challenge=${codeChallenge}&` +
    `code_challenge_method=S256`;

  window.location.href = authUrl;
}

// Handle callback
async function handleCallback() {
  const params = new URLSearchParams(window.location.search);
  const code = params.get('code');
  const codeVerifier = sessionStorage.getItem('code_verifier');

  // Exchange for token
  const response = await fetch(TOKEN_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      code: code,
      client_id: CLIENT_ID,
      redirect_uri: REDIRECT_URI,
      code_verifier: codeVerifier
    })
  });

  const tokens = await response.json();

  // Clean up
  sessionStorage.removeItem('code_verifier');
  sessionStorage.removeItem('oauth_state');

  return tokens;
}
```

**PKCE parameters:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `code_verifier` | 43-128 chars | Random string |
| `code_challenge` | Base64 hash | SHA256(code_verifier) |
| `code_challenge_method` | S256 | Hashing method |

**When to use PKCE:**
✅ Mobile applications (iOS, Android)
✅ Single Page Apps (React, Vue, Angular)
✅ Desktop apps
✅ Any public client (can't hide secret)

**When NOT to use PKCE:**
- Server-side web apps (use client_secret instead)
- Machine-to-machine (use client credentials flow)

**Benefits:**
- No client_secret needed
- Prevents authorization code interception
- More secure for public clients

**Enable PKCE for your app:**
Settings > OAuth Apps > Your App > Enable PKCE"""

    def _guide_error_fix(self, error_code: str) -> str:
        """Provide specific fix for OAuth error code"""
        error_description = self.ERROR_CODES.get(error_code, "Unknown error")

        fixes = {
            "redirect_uri_mismatch": """**Error: redirect_uri_mismatch**

The redirect URI in your request doesn't match the registered URI.

**Fix:**
1. Check registered URI: **Settings > OAuth Apps > Your App**
2. Update code to match EXACTLY:

```python
# Must match character-for-character
REDIRECT_URI = "https://your-app.com/callback"  # Exact match!

# Common mismatches:
# ❌ http vs https
# ❌ Missing/extra trailing slash
# ❌ Different port
# ❌ Different subdomain
```

3. Or update registered URI to match your code""",

            "invalid_scope": """**Error: invalid_scope**

You requested a scope that doesn't exist or isn't allowed.

**Fix:**
1. Check available scopes: **Settings > OAuth > Scopes**
2. Request only valid scopes:

```python
# Valid scopes
scope = "customers:read customers:write"

# Invalid
scope = "invalid_scope"  # ❌ Doesn't exist
```

3. Contact support if you need a specific scope""",

            "access_denied": """**Error: access_denied**

User clicked "Deny" on authorization screen.

**Fix:**
Handle denial gracefully:

```python
@app.route('/callback')
def callback():
    if request.args.get('error') == 'access_denied':
        return '''
            Authorization required to use this app.
            <a href="/login">Try again</a>
        '''
```""",

            "invalid_grant": """**Error: invalid_grant**

Authorization code is invalid, expired, or already used.

**Causes:**
- Code already exchanged for token (can only use once!)
- Code expired (valid for 10 minutes)
- Code is for different client_id

**Fix:**
Restart OAuth flow - redirect user to authorize again""",

            "unauthorized_client": """**Error: unauthorized_client**

Your OAuth app isn't authorized for this grant type.

**Fix:**
1. Check grant type: Should be `authorization_code`
2. Verify OAuth app settings: **Settings > OAuth Apps**
3. Ensure app is active (not suspended)""",

            "unsupported_grant_type": """**Error: unsupported_grant_type**

Grant type not supported.

**Fix:**
Use correct grant type:

```python
# Correct
data = {
    'grant_type': 'authorization_code',  # For initial token
    # or
    'grant_type': 'refresh_token',  # For refresh
}

# Invalid
data = {
    'grant_type': 'password',  # Not supported
}
```""",
        }

        return fixes.get(error_code, f"""**Error: {error_code}**

{error_description}

Share more details about when this error occurs and I'll help you fix it.""")


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: OAuth setup
        print("=" * 60)
        print("Test 1: OAuth Setup")
        print("=" * 60)

        state = create_initial_state("How do I set up OAuth for my application?")
        state["customer_metadata"] = {"plan": "premium"}

        agent = OAuthSpecialist()
        result = await agent.process(state)

        print(f"\nOAuth topic: {result.get('oauth_topic')}")
        print(f"\nResponse preview:\n{result['agent_response'][:500]}...")
        print(f"Status: {result.get('status')}")

        # Test 2: Token refresh
        print("\n" + "=" * 60)
        print("Test 2: Token Refresh")
        print("=" * 60)

        state2 = create_initial_state("My access token expired. How do I refresh it?")
        result2 = await agent.process(state2)

        print(f"\nOAuth topic: {result2.get('oauth_topic')}")
        print(f"\nResponse preview:\n{result2['agent_response'][:300]}...")

        # Test 3: Redirect URI error
        print("\n" + "=" * 60)
        print("Test 3: Redirect URI Mismatch")
        print("=" * 60)

        state3 = create_initial_state("I'm getting redirect_uri_mismatch error")
        result3 = await agent.process(state3)

        print(f"\nError code: {result3.get('error_code')}")
        print(f"\nResponse preview:\n{result3['agent_response'][:300]}...")

    asyncio.run(test())
    