"""
Webhook Troubleshooter Agent - Fixes webhook delivery issues.

This agent specializes in diagnosing and resolving webhook-related problems
including delivery failures, timeouts, authentication errors, and payload issues.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import os

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("webhook_troubleshooter", tier="essential", category="integration")
class WebhookTroubleshooter(BaseAgent):
    """
    Webhook Troubleshooter - Diagnoses and fixes webhook delivery issues.

    Handles:
    - Webhook not receiving events
    - Delivery timeouts
    - Authentication/signature failures
    - Payload format issues
    - Configuration problems
    """

    # Common webhook issues and patterns
    WEBHOOK_ISSUES = {
        "not_receiving": ["not receiving", "no webhooks", "not getting", "not delivered"],
        "timeout": ["timeout", "slow", "taking too long", "response time"],
        "auth_error": ["signature", "verification", "authentication", "unauthorized"],
        "payload": ["wrong payload", "incorrect data", "missing fields", "bad format"],
        "ssl": ["ssl", "certificate", "https", "tls"],
        "firewall": ["blocked", "firewall", "whitelist", "ip"],
    }

    def __init__(self):
        config = AgentConfig(
            name="webhook_troubleshooter",
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
        Process webhook troubleshooting requests.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with webhook troubleshooting guidance
        """
        self.logger.info("webhook_troubleshooter_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})

        self.logger.debug(
            "webhook_troubleshooting_details",
            message_preview=message[:100],
            turn_count=state["turn_count"]
        )

        # Detect webhook issue type
        issue_type = self._detect_issue_type(message)

        self.logger.info(
            "webhook_issue_detected",
            issue_type=issue_type
        )

        # Search knowledge base for webhook documentation
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

        # Generate troubleshooting response
        response = self._generate_troubleshooting_guide(issue_type, kb_results)

        state["agent_response"] = response
        state["detected_issue"] = issue_type
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "webhook_troubleshooting_completed",
            status="resolved",
            issue_type=issue_type
        )

        return state

    def _detect_issue_type(self, message: str) -> str:
        """
        Detect the type of webhook issue from user message.

        Args:
            message: User's message

        Returns:
            Issue type identifier
        """
        message_lower = message.lower()

        # Check for specific issue patterns
        for issue_type, keywords in self.WEBHOOK_ISSUES.items():
            if any(keyword in message_lower for keyword in keywords):
                return issue_type

        # Default to general webhook help
        return "general"

    def _generate_troubleshooting_guide(
        self,
        issue_type: str,
        kb_results: list
    ) -> str:
        """
        Generate webhook troubleshooting guidance based on issue type.

        Args:
            issue_type: Type of webhook issue
            kb_results: Knowledge base search results

        Returns:
            Formatted troubleshooting guide
        """
        guides = {
            "not_receiving": self._guide_not_receiving(),
            "timeout": self._guide_timeout(),
            "auth_error": self._guide_auth_error(),
            "payload": self._guide_payload_issues(),
            "ssl": self._guide_ssl_issues(),
            "firewall": self._guide_firewall_issues(),
            "general": self._guide_general_setup()
        }

        guide = guides.get(issue_type, guides["general"])

        # Add KB context if available
        if kb_results:
            kb_context = "\n\n**📚 Related documentation:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"
            guide += kb_context

        return guide

    def _guide_not_receiving(self) -> str:
        """Guide for webhooks not being received"""
        return """**🔍 Webhook Not Receiving Events**

Let's diagnose why your webhook isn't receiving events.

**Quick diagnostics checklist:**

1. **Verify webhook is active:**
   - Go to Settings > Webhooks
   - Check if webhook shows "Active" status
   - Ensure correct events are selected

2. **Test endpoint reachability:**
```bash
# Test your endpoint manually
curl -X POST https://your-webhook-url.com/webhook \\
  -H "Content-Type: application/json" \\
  -d '{"test": "data"}'
```

3. **Common causes:**
   ❌ Endpoint URL typo or wrong port
   ❌ Firewall blocking our webhook IPs
   ❌ HTTPS certificate issues
   ❌ Server is down or unreachable
   ❌ Wrong event types selected

**Our webhook IP ranges to whitelist:**
```
52.89.214.238/32
54.218.53.128/32
52.32.178.7/32
```

**Quick fix steps:**

1. **Update webhook URL** (if wrong):
   Settings > Webhooks > Edit > Save

2. **Check server logs** for incoming requests:
```bash
tail -f /var/log/nginx/access.log | grep webhook
```

3. **Enable webhook logging:**
   Settings > Webhooks > Enable Debug Mode

**Test webhook delivery:**
I can send a test webhook to verify your endpoint. Just confirm your webhook URL and I'll trigger a test event.

**Still not working?** Share your webhook URL and any error logs you're seeing."""

    def _guide_timeout(self) -> str:
        """Guide for webhook timeout issues"""
        return """**⏱️ Webhook Timeout Issues**

Your webhook endpoint is timing out. Here's how to fix it.

**The problem:**
- Your endpoint must respond within **30 seconds**
- Taking longer causes timeout and retry attempts
- Retries can cause duplicate events

**Solution 1: Respond immediately (recommended)**
```python
@app.route('/webhook', methods=['POST'])
def webhook():
    # Get webhook data
    payload = request.json

    # Queue for background processing (fast!)
    task_queue.enqueue(process_webhook, payload)

    # Respond immediately (< 1 second)
    return jsonify({"status": "received"}), 200

# Process in background
def process_webhook(payload):
    # Do slow work here (database writes, API calls, etc.)
    # This won't block the webhook response
    pass
```

**Solution 2: Optimize your endpoint**
```python
# ❌ BAD - Slow operations in webhook handler
@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    send_email(data)  # Slow!
    update_database(data)  # Slow!
    call_external_api(data)  # Slow!
    return "OK", 200

# ✅ GOOD - Queue for background
@app.route('/webhook', methods=['POST'])
def webhook():
    background_task.delay(request.json)
    return "OK", 200
```

**Best practices:**
• Respond within 3 seconds (aim for < 1 second)
• Use job queues (Celery, RQ, Bull, etc.)
• Log webhook receipt immediately
• Handle idempotency (track event IDs)

**Check webhook retry history:**
Settings > Webhooks > Delivery Log

**Pro tip:** Store event ID to prevent duplicate processing:
```python
event_id = payload['event_id']
if not already_processed(event_id):
    process_event(payload)
    mark_processed(event_id)
```"""

    def _guide_auth_error(self) -> str:
        """Guide for webhook authentication/signature verification errors"""
        return """**🔐 Webhook Signature Verification**

Your webhook signature verification is failing. Let's fix it.

**How webhook signatures work:**
1. We send webhook with signature in header: `X-Webhook-Signature`
2. You calculate expected signature using your webhook secret
3. Compare signatures to verify authenticity

**Correct verification (Python):**
```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    \"\"\"Verify webhook came from us\"\"\"
    # Calculate expected signature
    expected = hmac.new(
        key=secret.encode('utf-8'),
        msg=payload.encode('utf-8'),
        digestmod=hashlib.sha256
    ).hexdigest()

    # Secure comparison (prevents timing attacks)
    return hmac.compare_digest(expected, signature)

# In your webhook handler
@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.get_data(as_text=True)  # Raw body!
    signature = request.headers.get('X-Webhook-Signature')

    if not verify_webhook_signature(payload, signature, WEBHOOK_SECRET):
        return "Invalid signature", 401

    # Process webhook
    data = json.loads(payload)
    process_event(data)
    return "OK", 200
```

**Common mistakes:**

❌ **Using wrong secret**
   → Check Settings > Webhooks > Show Secret

❌ **Signing parsed JSON instead of raw body**
```python
# Wrong:
payload = request.json
signature = sign(json.dumps(payload))

# Correct:
payload = request.get_data(as_text=True)  # Raw!
signature = sign(payload)
```

❌ **String comparison (timing attack vulnerability)**
```python
# Wrong:
if calculated_sig == provided_sig:

# Correct:
if hmac.compare_digest(calculated_sig, provided_sig):
```

❌ **Using wrong encoding**
```python
# Must be UTF-8
secret.encode('utf-8')
```

**Other languages:**

**JavaScript/Node.js:**
```javascript
const crypto = require('crypto');

function verifyWebhook(payload, signature, secret) {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload, 'utf8')
    .digest('hex');

  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature)
  );
}
```

**Your webhook secret:**
Go to Settings > Webhooks > Show Secret

**Test it:** I can send a test webhook with proper signature to verify your implementation."""

    def _guide_payload_issues(self) -> str:
        """Guide for webhook payload format issues"""
        return """**📦 Webhook Payload Format**

Understanding webhook payload structure and handling.

**Standard webhook payload:**
```json
{
  "event_id": "evt_123abc456def",
  "event_type": "customer.created",
  "timestamp": "2025-11-15T10:30:00Z",
  "data": {
    "customer_id": "cust_789xyz",
    "email": "user@example.com",
    "plan": "premium",
    "created_at": "2025-11-15T10:30:00Z"
  },
  "api_version": "2025-11-01"
}
```

**Available event types:**
- `customer.created` - New customer signup
- `customer.updated` - Customer data changed
- `customer.deleted` - Customer account deleted
- `subscription.created` - New subscription
- `subscription.updated` - Subscription changed
- `payment.succeeded` - Payment processed
- `payment.failed` - Payment failed

**Parse webhook safely:**
```python
def handle_webhook(request):
    try:
        payload = request.json

        # Extract key fields
        event_type = payload.get('event_type')
        event_id = payload.get('event_id')
        data = payload.get('data', {})

        # Route to handler based on event type
        handlers = {
            'customer.created': handle_customer_created,
            'payment.succeeded': handle_payment_succeeded,
            # ... etc
        }

        handler = handlers.get(event_type)
        if handler:
            handler(data, event_id)
        else:
            logger.warning(f"Unknown event type: {event_type}")

        return "OK", 200

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500
```

**Handle missing fields gracefully:**
```python
def handle_customer_created(data, event_id):
    # Use .get() with defaults
    customer_id = data.get('customer_id')
    email = data.get('email', 'no-email@example.com')
    plan = data.get('plan', 'free')

    # Validate required fields
    if not customer_id:
        logger.error(f"Missing customer_id in {event_id}")
        return

    # Process...
```

**Content-Type:** Always `application/json`

**View webhook payload examples:**
Settings > Webhooks > Event Catalog > View Sample Payload"""

    def _guide_ssl_issues(self) -> str:
        """Guide for SSL/HTTPS certificate issues"""
        return """**🔒 Webhook SSL/HTTPS Issues**

Webhooks require valid HTTPS with proper SSL certificate.

**Requirements:**
✅ HTTPS (not HTTP)
✅ Valid SSL certificate (not self-signed)
✅ TLS 1.2 or higher
✅ Certificate not expired

**Check your SSL certificate:**
```bash
# Test your SSL
curl -v https://your-webhook-url.com 2>&1 | grep SSL

# Check certificate expiry
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | \\
  openssl x509 -noout -dates
```

**Common issues:**

❌ **Self-signed certificate**
   → Get proper certificate (Let's Encrypt is free!)

❌ **Certificate expired**
   → Renew certificate (most expire after 90 days)

❌ **Wrong domain on certificate**
   → Certificate must match your webhook domain exactly

❌ **Missing intermediate certificates**
   → Include full certificate chain

**Free SSL certificate with Let's Encrypt:**
```bash
# Install certbot
sudo apt-get install certbot

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com

# Auto-renew
sudo certbot renew --dry-run
```

**For development/testing:**
- Use **ngrok** to create HTTPS tunnel
- Use **webhook.site** to test without server

**Ngrok example:**
```bash
# Install ngrok
brew install ngrok  # Mac
# or download from ngrok.com

# Create tunnel
ngrok http 3000

# Use the https://xxx.ngrok.io URL for webhooks
```

**Still having SSL issues?** Share your webhook URL and I'll check the certificate."""

    def _guide_firewall_issues(self) -> str:
        """Guide for firewall/IP whitelisting issues"""
        return """**🛡️ Webhook Firewall & IP Whitelisting**

Your firewall may be blocking webhook delivery.

**Our webhook source IPs (whitelist these):**
```
52.89.214.238/32
54.218.53.128/32
52.32.178.7/32
34.210.28.39/32
44.230.98.17/32
```

**Firewall configuration examples:**

**AWS Security Group:**
```bash
# Allow from our IPs
aws ec2 authorize-security-group-ingress \\
  --group-id sg-xxxxx \\
  --protocol tcp \\
  --port 443 \\
  --cidr 52.89.214.238/32
```

**UFW (Ubuntu firewall):**
```bash
# Allow from webhook IPs
sudo ufw allow from 52.89.214.238 to any port 443
sudo ufw allow from 54.218.53.128 to any port 443
sudo ufw allow from 52.32.178.7/32 to any port 443
```

**Nginx allow list:**
```nginx
location /webhook {
    # Only allow our IPs
    allow 52.89.214.238;
    allow 54.218.53.128;
    allow 52.32.178.7;
    deny all;

    proxy_pass http://localhost:3000;
}
```

**Cloud firewall (GCP, Azure, etc.):**
- Create firewall rule
- Source IP ranges: (list above)
- Target: Your webhook server
- Ports: 443 (HTTPS)
- Protocol: TCP

**Check if firewall is blocking:**
```bash
# Check firewall rules
sudo iptables -L -n | grep 443

# Test connection from our IP
# (We can send test webhook to verify)
```

**Corporate firewall?**
Contact your IT/DevOps team to whitelist our IPs.

**Alternative: Webhook relay service**
If you can't modify firewall, consider using a webhook relay service like **webhookrelay.com** or **ngrok**.

**Need help?** I can send a test webhook to check if it gets through your firewall."""

    def _guide_general_setup(self) -> str:
        """General webhook setup guide"""
        return """**🔗 Webhook Setup Guide**

Set up webhooks to receive real-time event notifications.

**Step 1: Create webhook endpoint**
```python
from flask import Flask, request
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "<YOUR_WEBHOOK_SECRET_HERE>")  # From settings

@app.route('/webhook', methods=['POST'])
def webhook():
    # 1. Verify signature
    payload = request.get_data(as_text=True)
    signature = request.headers.get('X-Webhook-Signature')

    if not verify_signature(payload, signature, WEBHOOK_SECRET):
        return "Invalid signature", 401

    # 2. Parse event
    event = request.json
    event_type = event['event_type']

    # 3. Handle event
    if event_type == 'customer.created':
        handle_new_customer(event['data'])

    # 4. Respond quickly
    return "OK", 200

def verify_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

**Step 2: Deploy endpoint (must be HTTPS!)**
- Use ngrok for testing: `ngrok http 5000`
- Production: Deploy to cloud with SSL

**Step 3: Register webhook**
1. Go to Settings > Webhooks > Add Webhook
2. Enter your endpoint URL: `https://your-domain.com/webhook`
3. Select events to receive
4. Save and copy webhook secret

**Step 4: Test webhook**
```bash
# Send test event
curl -X POST https://your-webhook-url.com/webhook \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Signature: test_signature" \\
  -d '{
    "event_type": "test",
    "event_id": "test_123",
    "data": {}
  }'
```

**Best practices:**
✅ Verify webhook signatures
✅ Respond within 30 seconds
✅ Handle idempotency (track event IDs)
✅ Use HTTPS with valid certificate
✅ Log all webhook events
✅ Queue long-running tasks

**Monitor webhooks:**
Settings > Webhooks > Delivery Logs

**Common events:**
- `customer.created` - New customer
- `payment.succeeded` - Payment processed
- `subscription.updated` - Subscription changed

**Need specific help?** Let me know what issue you're experiencing:
• Not receiving webhooks
• Authentication errors
• Timeout issues
• Payload questions"""


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Not receiving webhooks
        print("=" * 60)
        print("Test 1: Webhook Not Receiving")
        print("=" * 60)

        state = create_initial_state("My webhook is not receiving any events")
        state["customer_metadata"] = {"plan": "premium"}

        agent = WebhookTroubleshooter()
        result = await agent.process(state)

        print(f"\nDetected issue: {result.get('detected_issue')}")
        print(f"\nResponse:\n{result['agent_response']}")
        print(f"Status: {result.get('status')}")

        # Test 2: Signature verification
        print("\n" + "=" * 60)
        print("Test 2: Signature Verification")
        print("=" * 60)

        state2 = create_initial_state("How do I verify webhook signatures?")
        result2 = await agent.process(state2)

        print(f"\nDetected issue: {result2.get('detected_issue')}")
        print(f"\nResponse preview:\n{result2['agent_response'][:300]}...")

    asyncio.run(test())
