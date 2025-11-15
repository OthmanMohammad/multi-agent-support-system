"""
Rate Limit Advisor Agent - Explains rate limits and optimization.

This agent specializes in helping customers understand API rate limits,
optimize their usage, and avoid hitting limits through best practices.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("rate_limit_advisor", tier="essential", category="integration")
class RateLimitAdvisor(BaseAgent):
    """
    Rate Limit Advisor - Expert in API rate limits and optimization.

    Handles:
    - Explaining rate limits by plan
    - Handling 429 errors
    - Optimization strategies
    - Upgrade recommendations
    - Best practices for API usage
    """

    # Rate limits by plan
    RATE_LIMITS = {
        "free": {
            "requests_per_hour": 100,
            "requests_per_minute": 10,
            "burst": 5,
            "concurrent": 1
        },
        "basic": {
            "requests_per_hour": 1000,
            "requests_per_minute": 50,
            "burst": 20,
            "concurrent": 5
        },
        "premium": {
            "requests_per_hour": 10000,
            "requests_per_minute": 200,
            "burst": 50,
            "concurrent": 20
        },
        "enterprise": {
            "requests_per_hour": 100000,
            "requests_per_minute": 1000,
            "burst": 200,
            "concurrent": 100
        }
    }

    # Rate limit keywords for detection
    RATE_LIMIT_TOPICS = {
        "hitting_limit": ["429", "rate limit", "too many requests", "hitting limit", "limit exceeded"],
        "understand_limits": ["what are the limits", "rate limits", "how many requests", "api limits"],
        "optimize": ["optimize", "reduce requests", "fewer calls", "best practices", "efficiency"],
        "upgrade": ["need more", "increase limit", "upgrade", "higher limit", "more requests"],
        "headers": ["rate limit headers", "x-ratelimit", "check remaining", "how many left"],
    }

    def __init__(self):
        config = AgentConfig(
            name="rate_limit_advisor",
            type=AgentType.SPECIALIST,
            model="claude-3-haiku-20240307",
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
        Process rate limit related requests.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with rate limit guidance
        """
        self.logger.info("rate_limit_advisor_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        customer_context = state.get("customer_metadata", {})
        customer_plan = customer_context.get("plan", "free")

        self.logger.debug(
            "rate_limit_processing_details",
            message_preview=message[:100],
            customer_plan=customer_plan,
            turn_count=state["turn_count"]
        )

        # Detect rate limit topic
        topic = self._detect_rate_limit_topic(message)

        self.logger.info(
            "rate_limit_topic_detected",
            topic=topic,
            customer_plan=customer_plan
        )

        # Search knowledge base for rate limit documentation
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

        # Generate rate limit guidance
        response = self._generate_rate_limit_guide(topic, customer_plan, kb_results)

        state["agent_response"] = response
        state["rate_limit_topic"] = topic
        state["customer_plan"] = customer_plan
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "rate_limit_processing_completed",
            status="resolved",
            topic=topic
        )

        return state

    def _detect_rate_limit_topic(self, message: str) -> str:
        """
        Detect what rate limit topic the user is asking about.

        Args:
            message: User's message

        Returns:
            Rate limit topic identifier
        """
        message_lower = message.lower()

        # Check for specific topics
        for topic, keywords in self.RATE_LIMIT_TOPICS.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic

        # Default to explaining limits
        return "understand_limits"

    def _generate_rate_limit_guide(
        self,
        topic: str,
        customer_plan: str,
        kb_results: list
    ) -> str:
        """
        Generate rate limit guidance based on topic and customer plan.

        Args:
            topic: Rate limit topic
            customer_plan: Customer's current plan
            kb_results: Knowledge base search results

        Returns:
            Formatted rate limit guide
        """
        guides = {
            "hitting_limit": self._guide_handling_429(customer_plan),
            "understand_limits": self._guide_explain_limits(customer_plan),
            "optimize": self._guide_optimization(),
            "upgrade": self._guide_upgrade_options(customer_plan),
            "headers": self._guide_rate_limit_headers(customer_plan),
        }

        guide = guides.get(topic, guides["understand_limits"])

        # Add KB context if available
        if kb_results:
            kb_context = "\n\n**📚 Related documentation:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"
            guide += kb_context

        return guide

    def _guide_explain_limits(self, plan: str) -> str:
        """Explain rate limits for customer's plan"""
        limits = self.RATE_LIMITS.get(plan, self.RATE_LIMITS["free"])

        return f"""**⚡ Your API Rate Limits ({plan.title()} Plan)**

**Current limits:**
- **{limits['requests_per_hour']:,} requests/hour**
- **{limits['requests_per_minute']:,} requests/minute**
- **{limits['burst']} burst requests** (short spikes)
- **{limits['concurrent']} concurrent connections**

**How rate limits work:**

```plaintext
Every request consumes quota from your hourly limit
Quota resets every hour (rolling window)
Short bursts allowed up to burst limit
Exceeding = HTTP 429 error
```

**Rate limit headers (check in every response):**

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: {limits['requests_per_hour']}
X-RateLimit-Remaining: 850
X-RateLimit-Reset: 1700000000

The reset timestamp is when your quota fully refreshes
```

**When you hit the limit:**

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600
X-RateLimit-Limit: {limits['requests_per_hour']}
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1700003600

{{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Try again in 1 hour.",
  "retry_after": 3600
}}
```

**Check your usage:**

```python
import requests

response = requests.get(
    'https://api.example.com/v1/customers',
    headers={{'Authorization': 'Bearer YOUR_TOKEN'}}
)

# Check rate limit headers
limit = response.headers.get('X-RateLimit-Limit')
remaining = response.headers.get('X-RateLimit-Remaining')
reset = response.headers.get('X-RateLimit-Reset')

print(f"Limit: {{limit}}")
print(f"Remaining: {{remaining}}")
print(f"Resets at: {{reset}}")

# Calculate when to slow down
usage_percent = (int(limit) - int(remaining)) / int(limit) * 100
if usage_percent > 80:
    print("⚠️ WARNING: 80% of rate limit used!")
```

**Monitor your usage:**
- Dashboard > API Usage > Rate Limits
- Set up alerts at 80% usage

**Need more requests?**
{self._get_upgrade_suggestion(plan)}

**Best practices:**
✅ Cache responses when possible
✅ Use webhooks instead of polling
✅ Batch requests where supported
✅ Monitor X-RateLimit headers
✅ Implement exponential backoff

**Questions?** Ask me about:
• Handling 429 errors
• Optimization strategies
• Upgrading your plan"""

    def _guide_handling_429(self, plan: str) -> str:
        """Guide for handling 429 rate limit errors"""
        limits = self.RATE_LIMITS.get(plan, self.RATE_LIMITS["free"])

        return f"""**🛑 Handling Rate Limit Errors (HTTP 429)**

You're hitting your rate limit of **{limits['requests_per_hour']:,} requests/hour**.

**Immediate fix: Implement retry with exponential backoff**

```python
import requests
import time

def make_api_call_with_retry(url, max_retries=5):
    \"\"\"Make API call with automatic retry on rate limit\"\"\"
    for attempt in range(max_retries):
        response = requests.get(
            url,
            headers={{'Authorization': 'Bearer YOUR_TOKEN'}}
        )

        # Success
        if response.status_code == 200:
            return response.json()

        # Rate limited
        if response.status_code == 429:
            # Get retry delay from header
            retry_after = int(response.headers.get('Retry-After', 60))

            # Exponential backoff
            wait_time = min(retry_after, 2 ** attempt)

            print(f"Rate limited. Waiting {{wait_time}}s...")
            time.sleep(wait_time)
            continue

        # Other error
        response.raise_for_status()

    raise Exception("Max retries exceeded")

# Usage
data = make_api_call_with_retry('https://api.example.com/customers')
```

**Better: Proactive rate limiting**

```python
import time
from datetime import datetime, timedelta

class RateLimiter:
    def __init__(self, max_requests_per_hour):
        self.max_requests = max_requests_per_hour
        self.requests = []

    def wait_if_needed(self):
        \"\"\"Wait if we're at the rate limit\"\"\"
        now = datetime.now()
        hour_ago = now - timedelta(hours=1)

        # Remove requests older than 1 hour
        self.requests = [r for r in self.requests if r > hour_ago]

        # Check if at limit
        if len(self.requests) >= self.max_requests:
            # Wait until oldest request expires
            oldest = self.requests[0]
            wait_until = oldest + timedelta(hours=1)
            wait_seconds = (wait_until - now).total_seconds()

            if wait_seconds > 0:
                print(f"Rate limit reached. Waiting {{wait_seconds:.0f}}s...")
                time.sleep(wait_seconds)

        # Record this request
        self.requests.append(now)

# Usage
limiter = RateLimiter({limits['requests_per_hour']})

for customer_id in customer_ids:
    limiter.wait_if_needed()
    response = requests.get(f'https://api.example.com/customers/{{customer_id}}')
```

**Best: Monitor headers and throttle proactively**

```python
class SmartAPIClient:
    def __init__(self):
        self.remaining = None
        self.reset_time = None

    def make_request(self, url):
        # Check if we should wait
        if self.remaining is not None and self.remaining < 10:
            # Less than 10 requests left - slow down
            print("⚠️ Low on rate limit quota, slowing down...")
            time.sleep(2)

        if self.remaining == 0:
            # Out of quota - wait for reset
            wait_time = self.reset_time - time.time()
            if wait_time > 0:
                print(f"Rate limit exhausted. Waiting {{wait_time:.0f}}s...")
                time.sleep(wait_time)

        # Make request
        response = requests.get(url, headers={{'Authorization': 'Bearer TOKEN'}})

        # Update rate limit info from headers
        self.remaining = int(response.headers.get('X-RateLimit-Remaining', 100))
        self.reset_time = int(response.headers.get('X-RateLimit-Reset', time.time() + 3600))

        return response

# Usage
client = SmartAPIClient()
for item in items:
    response = client.make_request(f'https://api.example.com/items/{{item}}')
```

**Quick wins to reduce API calls:**

1. **Use webhooks instead of polling:**
```python
# ❌ BAD: Poll every minute (1,440 requests/day)
while True:
    check_for_new_customers()
    time.sleep(60)

# ✅ GOOD: Webhook (0 requests, real-time)
@app.route('/webhook')
def webhook():
    # Notified instantly when new customer
    handle_new_customer(request.json)
```

2. **Batch requests:**
```python
# ❌ BAD: 100 separate requests
for customer_id in customer_ids:
    get_customer(customer_id)

# ✅ GOOD: 1 batch request
get_customers_batch(customer_ids)
```

3. **Cache responses:**
```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=100)
def get_customer(customer_id, cache_time):
    \"\"\"Cached for cache_time period\"\"\"
    return requests.get(f'https://api.example.com/customers/{{customer_id}}').json()

# Usage: Cache for 5 minutes
cache_key = datetime.now().replace(second=0, microsecond=0) // timedelta(minutes=5)
customer = get_customer('cust_123', cache_key)
```

**Your current usage:**
View real-time: Dashboard > API > Rate Limits

**Still hitting limits?**
{self._get_upgrade_suggestion(plan)}

**Need help optimizing?** Share your use case and I'll suggest specific improvements."""

    def _guide_optimization(self) -> str:
        """Guide for API usage optimization"""
        return """**⚡ API Optimization Strategies**

Reduce API calls by 10-100x with these strategies.

**Strategy 1: Webhooks > Polling (Save 99% of requests)**

```python
# ❌ WORST: Poll every 10 seconds (8,640 requests/day)
while True:
    new_orders = api.get_orders(since=last_check)
    if new_orders:
        process_orders(new_orders)
    time.sleep(10)

# ✅ BEST: Webhook (0 requests, instant notifications)
@app.route('/webhook/orders', methods=['POST'])
def order_webhook():
    order = request.json
    process_order(order)  # Instant, no polling!
    return "OK", 200

# Setup: Settings > Webhooks > Subscribe to 'order.created'
```

**Savings: 8,640 → 0 requests/day (100% reduction!)**

**Strategy 2: Batch Requests (Save 90%+ requests)**

```python
# ❌ BAD: 1,000 individual requests
for customer_id in customer_ids:  # 1,000 customers
    customer = api.get_customer(customer_id)
    process(customer)
# Total: 1,000 requests

# ✅ GOOD: 1 batch request
customers = api.get_customers_batch(customer_ids)
for customer in customers:
    process(customer)
# Total: 1 request (or 10 if batch size limit is 100)
```

**Savings: 1,000 → 10 requests (99% reduction)**

**Strategy 3: Smart Caching (Save 80%+ requests)**

```python
import redis
import json
from datetime import timedelta

# Setup Redis cache
cache = redis.Redis(host='localhost', port=6379, db=0)

def get_customer_cached(customer_id, ttl_minutes=30):
    \"\"\"Get customer with caching\"\"\"
    cache_key = f"customer:{{customer_id}}"

    # Try cache first
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    # Cache miss - fetch from API
    customer = api.get_customer(customer_id)

    # Store in cache
    cache.setex(
        cache_key,
        timedelta(minutes=ttl_minutes),
        json.dumps(customer)
    )

    return customer

# Usage
customer = get_customer_cached('cust_123')  # First call: API request
customer = get_customer_cached('cust_123')  # Subsequent calls: Cache hit!
```

**Cache TTL guidelines:**
- Static data (product catalog): 24 hours
- Semi-static (customer profile): 30 minutes
- Dynamic (account balance): 5 minutes
- Real-time (order status): Don't cache, use webhooks

**Strategy 4: Conditional Requests (Save 50% bandwidth)**

```python
def get_customer_if_modified(customer_id, last_etag=None):
    \"\"\"Only fetch if data changed\"\"\"
    headers = {{'Authorization': 'Bearer TOKEN'}}

    # Include ETag from last fetch
    if last_etag:
        headers['If-None-Match'] = last_etag

    response = requests.get(
        f'https://api.example.com/customers/{{customer_id}}',
        headers=headers
    )

    # 304 Not Modified - data hasn't changed
    if response.status_code == 304:
        return None  # Use cached data

    # 200 OK - data changed
    if response.status_code == 200:
        new_etag = response.headers.get('ETag')
        return response.json(), new_etag

# Usage
data, etag = get_customer_if_modified('cust_123')
# Later...
data, etag = get_customer_if_modified('cust_123', etag)  # Might return 304
```

**Strategy 5: Pagination Optimization**

```python
# ❌ BAD: Fetch all pages even if not needed
def get_all_customers():
    customers = []
    page = 1
    while True:
        response = api.get_customers(page=page, per_page=100)
        customers.extend(response['data'])
        if not response['has_more']:
            break
        page += 1
    return customers

# If only need 50 customers, still fetches all 10,000!

# ✅ GOOD: Stream and stop early
def get_customers_until_condition(condition):
    page = 1
    while True:
        response = api.get_customers(page=page, per_page=100)

        for customer in response['data']:
            yield customer
            if condition(customer):
                return  # Stop early!

        if not response['has_more']:
            break
        page += 1

# Usage: Stop after finding target
for customer in get_customers_until_condition(lambda c: c['email'] == target_email):
    # Found it! Stopped early instead of fetching all pages
    break
```

**Strategy 6: Parallel Requests (Same count, faster)**

```python
# ❌ SLOW: Sequential (30 seconds)
results = []
for customer_id in customer_ids:  # 10 customers
    results.append(api.get_customer(customer_id))  # 3s each
# Total time: 30 seconds

# ✅ FAST: Parallel (3 seconds)
import concurrent.futures

def fetch_customer(customer_id):
    return api.get_customer(customer_id)

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch_customer, customer_ids))
# Total time: 3 seconds (same request count, 10x faster!)

# Note: Check your plan's concurrent connection limit!
```

**Strategy 7: Field Filtering (Reduce bandwidth)**

```python
# ❌ BAD: Fetch all fields (slow, large response)
customer = api.get_customer('cust_123')
# Returns: id, name, email, address, phone, orders, ...

# ✅ GOOD: Only fetch needed fields
customer = api.get_customer('cust_123', fields='id,name,email')
# Returns: id, name, email (faster, smaller response)
```

**Optimization checklist:**
- [ ] Replace polling with webhooks
- [ ] Batch requests where possible
- [ ] Cache frequently accessed data
- [ ] Use conditional requests (ETags)
- [ ] Stop pagination early when possible
- [ ] Parallelize independent requests
- [ ] Request only needed fields
- [ ] Monitor rate limit headers

**Measure your optimization:**

```python
# Before optimization
requests_before = 10000
cost_before = requests_before * 0.001  # $10

# After optimization
requests_after = 500
cost_after = requests_after * 0.001  # $0.50
savings = cost_before - cost_after  # $9.50 (95% reduction!)

print(f"Reduced requests by {{(1 - requests_after/requests_before)*100:.1f}}%")
print(f"Saved ${{savings:.2f}}/month")
```

**Need help optimizing your specific use case?**
Share your API usage pattern and I'll suggest targeted improvements."""

    def _guide_upgrade_options(self, current_plan: str) -> str:
        """Guide for upgrading to higher limits"""
        all_plans = ["free", "basic", "premium", "enterprise"]

        # Get plans above current
        try:
            current_index = all_plans.index(current_plan)
            upgrade_plans = all_plans[current_index + 1:]
        except ValueError:
            upgrade_plans = all_plans[1:]  # Default to all paid plans

        if not upgrade_plans:
            return """**🎉 You're on our highest plan!**

You have **Enterprise limits** with up to 100,000 requests/hour.

**Need even more?**
Contact our sales team for:
- Custom rate limits
- Dedicated infrastructure
- SLA guarantees
- White-glove support

**Or optimize your usage:**
Ask me about optimization strategies to reduce API calls by 10-100x."""

        upgrade_options = "\n\n".join([
            self._format_plan_option(plan, current_plan) for plan in upgrade_plans
        ])

        return f"""**📈 Upgrade for Higher Rate Limits**

**Your current plan:** {current_plan.title()}
**Current limit:** {self.RATE_LIMITS[current_plan]['requests_per_hour']:,} requests/hour

{upgrade_options}

**How to upgrade:**
1. Go to **Settings > Billing > Plans**
2. Select your desired plan
3. Updated limits apply immediately

**Not sure which plan?**
- **Basic:** Small businesses, moderate API usage
- **Premium:** Growing companies, high API usage
- **Enterprise:** Large scale, custom limits

**Questions?**
- "What plan do I need for X requests/day?"
- "Can I get a custom limit?"
- "What if I occasionally spike above my limit?"

**Or optimize first (often cheaper than upgrading!):**
Ask me: "How can I optimize my API usage?" """

    def _format_plan_option(self, plan: str, current_plan: str) -> str:
        """Format upgrade plan option"""
        limits = self.RATE_LIMITS[plan]
        current_limits = self.RATE_LIMITS[current_plan]

        multiplier = limits['requests_per_hour'] / current_limits['requests_per_hour']

        return f"""**{plan.title()} Plan** - {multiplier:.0f}x more requests

- ⚡ **{limits['requests_per_hour']:,} requests/hour** ({limits['requests_per_minute']:,}/min)
- 📊 **{limits['burst']} burst limit** (up from {current_limits['burst']})
- 🔗 **{limits['concurrent']} concurrent connections** (up from {current_limits['concurrent']})
- {"🎯 Custom rate limits available" if plan == "enterprise" else ""}"""

    def _guide_rate_limit_headers(self, plan: str) -> str:
        """Guide for understanding rate limit headers"""
        limits = self.RATE_LIMITS.get(plan, self.RATE_LIMITS["free"])

        return f"""**📊 Understanding Rate Limit Headers**

Every API response includes rate limit headers. Monitor them to avoid hitting limits.

**Headers explained:**

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: {limits['requests_per_hour']}      ← Total hourly limit
X-RateLimit-Remaining: 850         ← Requests left this hour
X-RateLimit-Reset: 1700000000      ← Unix timestamp when quota resets
X-RateLimit-Used: 150              ← Requests used this hour
```

**Read headers in your code:**

**Python:**
```python
import requests
from datetime import datetime

response = requests.get(
    'https://api.example.com/customers',
    headers={{'Authorization': 'Bearer YOUR_TOKEN'}}
)

# Extract headers
limit = int(response.headers.get('X-RateLimit-Limit'))
remaining = int(response.headers.get('X-RateLimit-Remaining'))
reset = int(response.headers.get('X-RateLimit-Reset'))

# Calculate usage
used = limit - remaining
usage_percent = (used / limit) * 100

print(f"Rate Limit: {{limit}} requests/hour")
print(f"Used: {{used}} ({{usage_percent:.1f}}%)")
print(f"Remaining: {{remaining}}")

# Convert reset time
reset_time = datetime.fromtimestamp(reset)
print(f"Resets at: {{reset_time.strftime('%H:%M:%S')}}")

# Check if running low
if remaining < limit * 0.2:  # Less than 20% remaining
    print("⚠️ WARNING: Running low on rate limit!")
    # Slow down or implement backoff
```

**JavaScript/Node.js:**
```javascript
const axios = require('axios');

async function checkRateLimits() {{
  const response = await axios.get('https://api.example.com/customers', {{
    headers: {{ 'Authorization': 'Bearer YOUR_TOKEN' }}
  }});

  const limit = parseInt(response.headers['x-ratelimit-limit']);
  const remaining = parseInt(response.headers['x-ratelimit-remaining']);
  const reset = parseInt(response.headers['x-ratelimit-reset']);

  const used = limit - remaining;
  const usagePercent = (used / limit) * 100;

  console.log(`Rate Limit: ${{limit}} requests/hour`);
  console.log(`Used: ${{used}} (${{usagePercent.toFixed(1)}}%)`);
  console.log(`Remaining: ${{remaining}}`);

  // Check if running low
  if (remaining < limit * 0.1) {{  // Less than 10% remaining
    console.warn('⚠️ WARNING: Rate limit nearly exhausted!');
    // Implement slowdown logic
  }}
}}
```

**Curl:**
```bash
# View headers with -i flag
curl -i https://api.example.com/customers \\
  -H "Authorization: Bearer YOUR_TOKEN"

# Or just headers with -I
curl -I https://api.example.com/customers \\
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Build a rate limit monitor:**

```python
class RateLimitMonitor:
    def __init__(self, alert_threshold=0.8):
        self.alert_threshold = alert_threshold  # Alert at 80%
        self.limit = None
        self.remaining = None
        self.reset = None

    def update_from_response(self, response):
        \"\"\"Update rate limit info from response headers\"\"\"
        self.limit = int(response.headers.get('X-RateLimit-Limit', 0))
        self.remaining = int(response.headers.get('X-RateLimit-Remaining', 0))
        self.reset = int(response.headers.get('X-RateLimit-Reset', 0))

        # Check if should alert
        if self.should_alert():
            self.send_alert()

    def should_alert(self):
        \"\"\"Check if usage exceeds threshold\"\"\"
        if not self.limit or not self.remaining:
            return False

        usage = (self.limit - self.remaining) / self.limit
        return usage >= self.alert_threshold

    def send_alert(self):
        \"\"\"Send alert when threshold exceeded\"\"\"
        usage_percent = ((self.limit - self.remaining) / self.limit) * 100

        print(f"🚨 ALERT: {{usage_percent:.1f}}% of rate limit used!")
        print(f"Remaining: {{self.remaining}}/{{self.limit}}")

        reset_time = datetime.fromtimestamp(self.reset)
        print(f"Resets at: {{reset_time}}")

        # Could also: send email, Slack message, etc.

    def time_until_reset(self):
        \"\"\"Calculate seconds until reset\"\"\"
        if not self.reset:
            return None

        now = datetime.now().timestamp()
        return max(0, self.reset - now)

# Usage
monitor = RateLimitMonitor(alert_threshold=0.8)  # Alert at 80%

response = requests.get(url, headers=headers)
monitor.update_from_response(response)

if monitor.should_alert():
    wait_time = monitor.time_until_reset()
    print(f"Consider slowing down. Resets in {{wait_time:.0f}} seconds")
```

**Dashboard monitoring:**
View real-time rate limit usage:
- **Dashboard > API > Rate Limits**
- Set up alerts for 80% and 90% thresholds
- View hourly usage graphs

**Pro tips:**
✅ Check headers after every request
✅ Log rate limit usage for analysis
✅ Set up alerts at 80% usage
✅ Slow down proactively when low
✅ Track usage trends over time

**When you hit the limit (429 error):**

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600                  ← Wait this many seconds
X-RateLimit-Limit: {limits['requests_per_hour']}
X-RateLimit-Remaining: 0           ← Quota exhausted
X-RateLimit-Reset: 1700003600      ← When quota refreshes

{{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Retry after 3600 seconds."
}}
```

**Handle 429 responses:**
```python
if response.status_code == 429:
    retry_after = int(response.headers.get('Retry-After', 3600))
    print(f"Rate limited. Waiting {{retry_after}} seconds...")
    time.sleep(retry_after)
    # Retry request
```

**Questions about rate limits?** Ask me about:
• Optimizing API usage
• Upgrading for higher limits
• Handling 429 errors"""

    def _get_upgrade_suggestion(self, current_plan: str) -> str:
        """Get upgrade suggestion based on current plan"""
        all_plans = ["free", "basic", "premium", "enterprise"]

        try:
            current_index = all_plans.index(current_plan)
            if current_index < len(all_plans) - 1:
                next_plan = all_plans[current_index + 1]
                next_limits = self.RATE_LIMITS[next_plan]
                return f"Upgrade to **{next_plan.title()}** for {next_limits['requests_per_hour']:,} requests/hour"
            else:
                return "Contact sales for custom Enterprise limits"
        except ValueError:
            return "Upgrade to a paid plan for higher limits"


if __name__ == "__main__":
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Explain limits
        print("=" * 60)
        print("Test 1: Explain Rate Limits (Premium)")
        print("=" * 60)

        state = create_initial_state("What are my API rate limits?")
        state["customer_metadata"] = {"plan": "premium"}

        agent = RateLimitAdvisor()
        result = await agent.process(state)

        print(f"\nTopic: {result.get('rate_limit_topic')}")
        print(f"Plan: {result.get('customer_plan')}")
        print(f"\nResponse preview:\n{result['agent_response'][:500]}...")
        print(f"Status: {result.get('status')}")

        # Test 2: Handling 429
        print("\n" + "=" * 60)
        print("Test 2: Handling 429 Errors (Free)")
        print("=" * 60)

        state2 = create_initial_state("I'm getting 429 errors, help!")
        state2["customer_metadata"] = {"plan": "free"}

        result2 = await agent.process(state2)

        print(f"\nTopic: {result2.get('rate_limit_topic')}")
        print(f"\nResponse preview:\n{result2['agent_response'][:400]}...")

        # Test 3: Optimization
        print("\n" + "=" * 60)
        print("Test 3: Optimization Strategies")
        print("=" * 60)

        state3 = create_initial_state("How can I optimize my API usage?")
        result3 = await agent.process(state3)

        print(f"\nTopic: {result3.get('rate_limit_topic')}")
        print(f"\nResponse preview:\n{result3['agent_response'][:300]}...")

    asyncio.run(test())
