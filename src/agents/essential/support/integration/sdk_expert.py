"""
SDK Expert Agent - Helps with SDKs (Python, JavaScript, Go, Java).

This agent specializes in helping customers use official SDKs, providing
language-specific guidance, code examples, and troubleshooting SDK issues.
"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("sdk_expert", tier="essential", category="integration")
class SDKExpert(BaseAgent):
    """
    SDK Expert - Specialist in official SDKs and language-specific integrations.

    Handles:
    - SDK installation and setup
    - Language-specific code examples
    - Authentication configuration
    - SDK error troubleshooting
    - Version compatibility
    """

    # Supported SDKs and their details
    SDKS = {
        "python": {
            "name": "Python SDK",
            "install": "pip install example-sdk",
            "import": "from example_sdk import Client",
            "docs": "https://docs.example.com/python",
            "github": "https://github.com/example/sdk-python",
            "versions": "Python 3.7+",
        },
        "javascript": {
            "name": "JavaScript/Node.js SDK",
            "install": "npm install example-sdk",
            "import": "const ExampleSDK = require('example-sdk');",
            "docs": "https://docs.example.com/javascript",
            "github": "https://github.com/example/sdk-javascript",
            "versions": "Node.js 14+",
        },
        "go": {
            "name": "Go SDK",
            "install": "go get github.com/example/sdk-go",
            "import": 'import "github.com/example/sdk-go"',
            "docs": "https://docs.example.com/go",
            "github": "https://github.com/example/sdk-go",
            "versions": "Go 1.18+",
        },
        "java": {
            "name": "Java SDK",
            "install": "Maven/Gradle dependency",
            "import": "import com.example.sdk.*;",
            "docs": "https://docs.example.com/java",
            "github": "https://github.com/example/sdk-java",
            "versions": "Java 11+",
        },
        "ruby": {
            "name": "Ruby SDK (Community)",
            "install": "gem install example-sdk",
            "import": "require 'example_sdk'",
            "docs": "https://docs.example.com/ruby",
            "github": "https://github.com/example/sdk-ruby",
            "versions": "Ruby 2.7+",
        },
    }

    # SDK-related topics
    SDK_TOPICS = {
        "setup": ["setup", "install", "getting started", "how to use", "initialize"],
        "authentication": ["auth", "api key", "token", "authenticate", "credentials"],
        "examples": ["example", "how to", "code sample", "tutorial"],
        "errors": ["error", "exception", "failing", "not working", "issue"],
        "versions": ["version", "compatibility", "upgrade", "update"],
    }

    # Language detection keywords
    LANGUAGE_KEYWORDS = {
        "python": ["python", "pip", "django", "flask", "fastapi", "requests", "py"],
        "javascript": [
            "javascript",
            "js",
            "node",
            "npm",
            "react",
            "vue",
            "express",
            "typescript",
            "ts",
        ],
        "go": ["go", "golang", "go get"],
        "java": ["java", "maven", "gradle", "spring"],
        "ruby": ["ruby", "rails", "gem"],
        "curl": ["curl", "bash", "shell", "terminal"],
        "rest": ["rest api", "http", "postman"],
    }

    def __init__(self):
        config = AgentConfig(
            name="sdk_expert",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.CONTEXT_AWARE],
            kb_category="integration",
            tier="essential",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """
        Process SDK-related requests.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with SDK guidance
        """
        self.logger.info("sdk_expert_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        state.get("customer_metadata", {})

        self.logger.debug(
            "sdk_processing_details", message_preview=message[:100], turn_count=state["turn_count"]
        )

        # Detect language preference
        language = self._detect_language(message)

        # Detect SDK topic
        topic = self._detect_sdk_topic(message)

        self.logger.info("sdk_request_detected", language=language, topic=topic)

        # Search knowledge base for SDK documentation
        kb_results = await self.search_knowledge_base(message, category="integration", limit=2)
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info("kb_articles_found", count=len(kb_results))

        # Generate SDK guidance
        response = self._generate_sdk_guide(language, topic, kb_results)

        state["agent_response"] = response
        state["sdk_language"] = language
        state["sdk_topic"] = topic
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"

        self.logger.info(
            "sdk_processing_completed", status="resolved", language=language, topic=topic
        )

        return state

    def _detect_language(self, message: str) -> str | None:
        """
        Detect which programming language the user prefers.

        Args:
            message: User's message

        Returns:
            Language identifier or None
        """
        message_lower = message.lower()

        # Check for language keywords
        for language, keywords in self.LANGUAGE_KEYWORDS.items():
            if any(keyword in message_lower for keyword in keywords):
                # Only return if it's a supported SDK
                if language in self.SDKS:
                    return language

        # Default to Python (most popular)
        return None

    def _detect_sdk_topic(self, message: str) -> str:
        """
        Detect what SDK topic the user is asking about.

        Args:
            message: User's message

        Returns:
            SDK topic identifier
        """
        message_lower = message.lower()

        # Check for specific topics
        for topic, keywords in self.SDK_TOPICS.items():
            if any(keyword in message_lower for keyword in keywords):
                return topic

        # Default to setup
        return "setup"

    def _generate_sdk_guide(self, language: str | None, topic: str, kb_results: list) -> str:
        """
        Generate SDK guidance based on language and topic.

        Args:
            language: Programming language
            topic: SDK topic
            kb_results: Knowledge base search results

        Returns:
            Formatted SDK guide
        """
        # If no language detected, show language selector
        if not language:
            guide = self._guide_language_selector()
        else:
            # Generate language-specific guide for topic
            topic_guides = {
                "setup": self._guide_setup,
                "authentication": self._guide_authentication,
                "examples": self._guide_examples,
                "errors": self._guide_errors,
                "versions": self._guide_versions,
            }

            guide_func = topic_guides.get(topic, self._guide_setup)
            guide = guide_func(language)

        # Add KB context if available
        if kb_results:
            kb_context = "\n\n**📚 Related documentation:**\n"
            for i, article in enumerate(kb_results[:2], 1):
                kb_context += f"{i}. {article['title']}\n"
            guide += kb_context

        return guide

    def _guide_language_selector(self) -> str:
        """Guide for selecting SDK language"""
        sdk_list = "\n\n".join(
            [
                f"""**{sdk["name"]}**
- Install: `{sdk["install"]}`
- Docs: {sdk["docs"]}
- GitHub: {sdk["github"]}
- Requires: {sdk["versions"]}"""
                for lang, sdk in self.SDKS.items()
                if lang in ["python", "javascript", "go", "java"]
            ]
        )

        return f"""**🛠️ Official SDKs**

Choose your language to get started:

{sdk_list}

**Community SDKs:**
- Ruby, PHP, .NET (community-maintained)
- See GitHub: https://github.com/example/awesome-sdks

**No SDK for your language?**
Use our REST API directly - it's well documented!
- REST API Docs: https://docs.example.com/api
- API Reference: https://api.example.com/docs

**Which language are you using?**
Let me know and I'll provide specific setup instructions!"""

    def _guide_setup(self, language: str) -> str:
        """Generate SDK setup guide for specific language"""
        sdk = self.SDKS.get(language)
        if not sdk:
            return self._guide_language_selector()

        if language == "python":
            return f"""**🐍 Python SDK Setup**

**Step 1: Install**

```bash
# Install via pip
{sdk["install"]}

# Or with specific version
pip install example-sdk==2.1.0

# Or in requirements.txt
echo "example-sdk>=2.0.0" >> requirements.txt
pip install -r requirements.txt
```

**Step 2: Initialize client**

```python
{sdk["import"]}

# Initialize with API key
client = Client(api_key='your_api_key_here')

# Or use environment variable (recommended)
import os
client = Client(api_key=os.environ.get('EXAMPLE_API_KEY'))
```

**Step 3: Make your first request**

```python
# Get all customers
customers = client.customers.list()

for customer in customers:
    print(f"{{customer.id}}: {{customer.email}}")

# Get specific customer
customer = client.customers.retrieve('cust_123')
print(customer.name)

# Create new customer
new_customer = client.customers.create(
    email='user@example.com',
    name='John Doe',
    plan='premium'
)
print(f"Created: {{new_customer.id}}")
```

**Step 4: Error handling**

```python
from example_sdk import APIError, AuthenticationError, RateLimitError

try:
    customer = client.customers.retrieve('cust_123')
except AuthenticationError as e:
    print(f"Invalid API key: {{e}}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {{e}}")
    # Wait and retry
    time.sleep(int(e.retry_after))
except APIError as e:
    print(f"API error ({{e.status_code}}): {{e.message}}")
```

**Configuration options:**

```python
client = Client(
    api_key='your_api_key',
    api_version='2025-11-01',  # Specific API version
    timeout=30,  # Request timeout (seconds)
    max_retries=3,  # Auto-retry failed requests
)
```

**Async support (Python 3.7+):**

```python
import asyncio
from example_sdk import AsyncClient

async def main():
    client = AsyncClient(api_key='your_api_key')

    # Async requests
    customers = await client.customers.list()

    # Concurrent requests
    customer_ids = ['cust_1', 'cust_2', 'cust_3']
    customers = await asyncio.gather(*[
        client.customers.retrieve(id) for id in customer_ids
    ])

asyncio.run(main())
```

**Get your API key:**
Settings > Developer > API Keys > Create Key

**Documentation:**
- Full docs: {sdk["docs"]}
- GitHub: {sdk["github"]}
- Examples: {sdk["github"]}/tree/main/examples

**Need help with:**
• Authentication
• Specific API calls
• Error handling
• Async usage"""

        elif language == "javascript":
            return f"""**📦 JavaScript/Node.js SDK Setup**

**Step 1: Install**

```bash
# Install via npm
{sdk["install"]}

# Or via yarn
yarn add example-sdk

# Add to package.json
npm install --save example-sdk
```

**Step 2: Initialize client**

```javascript
{sdk["import"]}

// Initialize with API key
const client = new ExampleSDK({{
  apiKey: 'your_api_key_here'
}});

// Or use environment variable (recommended)
const client = new ExampleSDK({{
  apiKey: process.env.EXAMPLE_API_KEY
}});
```

**Step 3: Make your first request**

```javascript
// Using async/await (recommended)
async function getCustomers() {{
  try {{
    // Get all customers
    const customers = await client.customers.list();

    customers.forEach(customer => {{
      console.log(`${{customer.id}}: ${{customer.email}}`);
    }});

    // Get specific customer
    const customer = await client.customers.retrieve('cust_123');
    console.log(customer.name);

    // Create new customer
    const newCustomer = await client.customers.create({{
      email: 'user@example.com',
      name: 'John Doe',
      plan: 'premium'
    }});
    console.log(`Created: ${{newCustomer.id}}`);

  }} catch (error) {{
    console.error('Error:', error.message);
  }}
}}

getCustomers();
```

**Using Promises:**

```javascript
// Promise chain
client.customers.list()
  .then(customers => {{
    customers.forEach(customer => {{
      console.log(`${{customer.id}}: ${{customer.email}}`);
    }});
  }})
  .catch(error => {{
    console.error('Error:', error.message);
  }});
```

**Step 4: Error handling**

```javascript
const {{ APIError, AuthenticationError, RateLimitError }} = require('example-sdk');

async function makeRequest() {{
  try {{
    const customer = await client.customers.retrieve('cust_123');
    return customer;

  }} catch (error) {{
    if (error instanceof AuthenticationError) {{
      console.error('Invalid API key');
    }} else if (error instanceof RateLimitError) {{
      console.error('Rate limit exceeded');
      // Wait and retry
      await new Promise(resolve => setTimeout(resolve, error.retryAfter * 1000));
      return makeRequest(); // Retry
    }} else if (error instanceof APIError) {{
      console.error(`API error (${{error.statusCode}}): ${{error.message}}`);
    }} else {{
      console.error('Unexpected error:', error);
    }}
    throw error;
  }}
}}
```

**Configuration options:**

```javascript
const client = new ExampleSDK({{
  apiKey: 'your_api_key',
  apiVersion: '2025-11-01',  // Specific API version
  timeout: 30000,  // Request timeout (milliseconds)
  maxRetries: 3,  // Auto-retry failed requests
}});
```

**TypeScript support:**

```typescript
import ExampleSDK, {{ Customer, CreateCustomerParams }} from 'example-sdk';

const client = new ExampleSDK({{
  apiKey: process.env.EXAMPLE_API_KEY!
}});

// Typed responses
const customer: Customer = await client.customers.retrieve('cust_123');

// Typed parameters
const params: CreateCustomerParams = {{
  email: 'user@example.com',
  name: 'John Doe',
  plan: 'premium'
}};

const newCustomer = await client.customers.create(params);
```

**Express.js integration:**

```javascript
const express = require('express');
const ExampleSDK = require('example-sdk');

const app = express();
const client = new ExampleSDK({{ apiKey: process.env.EXAMPLE_API_KEY }});

app.get('/customers', async (req, res) => {{
  try {{
    const customers = await client.customers.list();
    res.json(customers);
  }} catch (error) {{
    res.status(500).json({{ error: error.message }});
  }}
}});

app.listen(3000);
```

**Get your API key:**
Settings > Developer > API Keys > Create Key

**Documentation:**
- Full docs: {sdk["docs"]}
- GitHub: {sdk["github"]}
- Examples: {sdk["github"]}/tree/main/examples
- TypeScript: {sdk["docs"]}/typescript

**Need help with:**
• Authentication
• TypeScript integration
• Error handling
• Webhooks in Express"""

        elif language == "go":
            return f"""**🔷 Go SDK Setup**

**Step 1: Install**

```bash
# Install via go get
{sdk["install"]}

# Or add to go.mod
go mod init your-app
{sdk["install"]}
```

**Step 2: Initialize client**

```go
package main

{sdk["import"]}
"os"

func main() {{
    // Initialize with API key
    client := sdk.NewClient("your_api_key_here")

    // Or use environment variable (recommended)
    client := sdk.NewClient(os.Getenv("EXAMPLE_API_KEY"))
}}
```

**Step 3: Make your first request**

```go
package main

import (
    "fmt"
    "log"
    {sdk["import"]}
    "os"
)

func main() {{
    client := sdk.NewClient(os.Getenv("EXAMPLE_API_KEY"))

    // Get all customers
    customers, err := client.Customers.List(context.Background(), &sdk.CustomerListParams{{}})
    if err != nil {{
        log.Fatal(err)
    }}

    for _, customer := range customers.Data {{
        fmt.Printf("%s: %s\\n", customer.ID, customer.Email)
    }}

    // Get specific customer
    customer, err := client.Customers.Retrieve(
        context.Background(),
        "cust_123",
    )
    if err != nil {{
        log.Fatal(err)
    }}
    fmt.Println(customer.Name)

    // Create new customer
    newCustomer, err := client.Customers.Create(
        context.Background(),
        &sdk.CustomerCreateParams{{
            Email: sdk.String("user@example.com"),
            Name:  sdk.String("John Doe"),
            Plan:  sdk.String("premium"),
        }},
    )
    if err != nil {{
        log.Fatal(err)
    }}
    fmt.Printf("Created: %s\\n", newCustomer.ID)
}}
```

**Step 4: Error handling**

```go
import (
    "errors"
    "github.com/example/sdk-go"
    "net/http"
)

func getCustomer(id string) (*sdk.Customer, error) {{
    customer, err := client.Customers.Retrieve(context.Background(), id)

    if err != nil {{
        var apiErr *sdk.APIError
        if errors.As(err, &apiErr) {{
            switch apiErr.StatusCode {{
            case http.StatusUnauthorized:
                return nil, fmt.Errorf("invalid API key")
            case http.StatusTooManyRequests:
                // Handle rate limit
                return nil, fmt.Errorf("rate limit exceeded")
            case http.StatusNotFound:
                return nil, fmt.Errorf("customer not found")
            default:
                return nil, fmt.Errorf("API error: %s", apiErr.Message)
            }}
        }}
        return nil, err
    }}

    return customer, nil
}}
```

**Configuration options:**

```go
client := sdk.NewClient(
    apiKey,
    sdk.WithAPIVersion("2025-11-01"),  // Specific API version
    sdk.WithTimeout(30 * time.Second),  // Request timeout
    sdk.WithMaxRetries(3),  // Auto-retry
)
```

**Context support:**

```go
import "context"

// With timeout
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

customer, err := client.Customers.Retrieve(ctx, "cust_123")

// With cancellation
ctx, cancel := context.WithCancel(context.Background())
defer cancel()

// Cancel if needed
go func() {{
    <-someChannel
    cancel()  // Cancel request
}}()

customer, err := client.Customers.List(ctx, params)
```

**Pagination:**

```go
// Iterate through all pages
params := &sdk.CustomerListParams{{
    Limit: sdk.Int64(100),
}}

for {{
    customers, err := client.Customers.List(ctx, params)
    if err != nil {{
        return err
    }}

    for _, customer := range customers.Data {{
        fmt.Println(customer.ID)
    }}

    if !customers.HasMore {{
        break
    }}

    // Get next page
    params.StartingAfter = sdk.String(customers.Data[len(customers.Data)-1].ID)
}}
```

**Get your API key:**
Settings > Developer > API Keys > Create Key

**Documentation:**
- Full docs: {sdk["docs"]}
- GitHub: {sdk["github"]}
- Examples: {sdk["github"]}/tree/main/examples
- GoDoc: https://pkg.go.dev/{sdk["github"]}

**Need help with:**
• Authentication
• Context usage
• Error handling
• Pagination"""

        elif language == "java":
            return f"""**☕ Java SDK Setup**

**Step 1: Install**

**Maven (pom.xml):**
```xml
<dependency>
    <groupId>com.example</groupId>
    <artifactId>example-sdk</artifactId>
    <version>2.1.0</version>
</dependency>
```

**Gradle (build.gradle):**
```gradle
dependencies {{
    implementation 'com.example:example-sdk:2.1.0'
}}
```

**Step 2: Initialize client**

```java
{sdk["import"]}

public class ExampleApp {{
    public static void main(String[] args) {{
        // Initialize with API key
        ExampleClient client = new ExampleClient("your_api_key_here");

        // Or use environment variable (recommended)
        String apiKey = System.getenv("EXAMPLE_API_KEY");
        ExampleClient client = new ExampleClient(apiKey);
    }}
}}
```

**Step 3: Make your first request**

```java
import com.example.sdk.*;
import com.example.sdk.models.*;
import java.util.List;

public class ExampleApp {{
    public static void main(String[] args) {{
        ExampleClient client = new ExampleClient(
            System.getenv("EXAMPLE_API_KEY")
        );

        try {{
            // Get all customers
            List<Customer> customers = client.customers().list();

            for (Customer customer : customers) {{
                System.out.println(customer.getId() + ": " + customer.getEmail());
            }}

            // Get specific customer
            Customer customer = client.customers().retrieve("cust_123");
            System.out.println(customer.getName());

            // Create new customer
            CustomerCreateParams params = CustomerCreateParams.builder()
                .email("user@example.com")
                .name("John Doe")
                .plan("premium")
                .build();

            Customer newCustomer = client.customers().create(params);
            System.out.println("Created: " + newCustomer.getId());

        }} catch (APIException e) {{
            System.err.println("API error: " + e.getMessage());
        }}
    }}
}}
```

**Step 4: Error handling**

```java
import com.example.sdk.exceptions.*;

try {{
    Customer customer = client.customers().retrieve("cust_123");
    return customer;

}} catch (AuthenticationException e) {{
    System.err.println("Invalid API key");
}} catch (RateLimitException e) {{
    System.err.println("Rate limit exceeded");
    // Wait and retry
    Thread.sleep(e.getRetryAfter() * 1000);
}} catch (NotFoundException e) {{
    System.err.println("Customer not found");
}} catch (APIException e) {{
    System.err.println("API error (" + e.getStatusCode() + "): " + e.getMessage());
}}
```

**Configuration options:**

```java
ExampleClientConfig config = ExampleClientConfig.builder()
    .apiKey("your_api_key")
    .apiVersion("2025-11-01")  // Specific API version
    .connectTimeout(30)  // Connection timeout (seconds)
    .readTimeout(60)  // Read timeout (seconds)
    .maxRetries(3)  // Auto-retry
    .build();

ExampleClient client = new ExampleClient(config);
```

**Async requests (CompletableFuture):**

```java
import java.util.concurrent.CompletableFuture;

// Async client
AsyncExampleClient asyncClient = new AsyncExampleClient(apiKey);

// Make async request
CompletableFuture<Customer> futureCustomer =
    asyncClient.customers().retrieve("cust_123");

// Handle response
futureCustomer.thenAccept(customer -> {{
    System.out.println("Customer: " + customer.getName());
}}).exceptionally(error -> {{
    System.err.println("Error: " + error.getMessage());
    return null;
}});
```

**Spring Boot integration:**

```java
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;

@SpringBootApplication
public class Application {{

    @Bean
    public ExampleClient exampleClient() {{
        return new ExampleClient(
            System.getenv("EXAMPLE_API_KEY")
        );
    }}

    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}
}}

// Use in controller
@RestController
public class CustomerController {{

    @Autowired
    private ExampleClient client;

    @GetMapping("/customers")
    public List<Customer> getCustomers() {{
        return client.customers().list();
    }}
}}
```

**Get your API key:**
Settings > Developer > API Keys > Create Key

**Documentation:**
- Full docs: {sdk["docs"]}
- GitHub: {sdk["github"]}
- Examples: {sdk["github"]}/tree/main/examples
- JavaDoc: {sdk["docs"]}/javadoc

**Need help with:**
• Authentication
• Spring Boot integration
• Async requests
• Error handling"""

        else:
            return self._guide_language_selector()

    def _guide_authentication(self, language: str) -> str:
        """Generate authentication guide for specific language"""
        guides = {
            "python": """**🔐 Python SDK Authentication**

**Method 1: Direct API key (quick start)**
```python
from example_sdk import Client

client = Client(api_key='sk_live_abc123...')
```

**Method 2: Environment variable (recommended)**
```python
import os
from example_sdk import Client

# Set environment variable
# export EXAMPLE_API_KEY='sk_live_abc123...'

client = Client(api_key=os.environ.get('EXAMPLE_API_KEY'))

# Or use python-dotenv
from dotenv import load_dotenv
load_dotenv()  # Loads from .env file

client = Client(api_key=os.environ['EXAMPLE_API_KEY'])
```

**Method 3: OAuth token**
```python
# After OAuth flow, use access token
client = Client(access_token='oauth_access_token_here')
```

**Security best practices:**
✅ Never commit API keys to git
✅ Use environment variables
✅ Use different keys for dev/staging/prod
✅ Rotate keys every 90 days

**.env file example:**
```env
# .env (add to .gitignore!)
EXAMPLE_API_KEY=sk_live_abc123...
EXAMPLE_API_VERSION=2025-11-01
```

**.gitignore:**
```
.env
*.env
```

**Get your API key:**
Settings > Developer > API Keys > Create Key""",
            "javascript": """**🔐 JavaScript/Node.js SDK Authentication**

**Method 1: Direct API key (quick start)**
```javascript
const ExampleSDK = require('example-sdk');

const client = new ExampleSDK({{
  apiKey: 'sk_live_abc123...'
}});
```

**Method 2: Environment variable (recommended)**
```javascript
// Set environment variable
// export EXAMPLE_API_KEY='sk_live_abc123...'

const client = new ExampleSDK({{
  apiKey: process.env.EXAMPLE_API_KEY
}});

// Or use dotenv
require('dotenv').config();

const client = new ExampleSDK({{
  apiKey: process.env.EXAMPLE_API_KEY
}});
```

**Method 3: OAuth token**
```javascript
// After OAuth flow, use access token
const client = new ExampleSDK({{
  accessToken: 'oauth_access_token_here'
}});
```

**TypeScript:**
```typescript
import ExampleSDK from 'example-sdk';

const client = new ExampleSDK({{
  apiKey: process.env.EXAMPLE_API_KEY!
}});
```

**Security best practices:**
✅ Never commit API keys to git
✅ Use environment variables
✅ Use different keys for dev/staging/prod
✅ Never expose keys in frontend code

**.env file example:**
```env
# .env (add to .gitignore!)
EXAMPLE_API_KEY=sk_live_abc123...
EXAMPLE_API_VERSION=2025-11-01
```

**package.json:**
```json
{{
  "scripts": {{
    "dev": "node -r dotenv/config app.js"
  }},
  "dependencies": {{
    "dotenv": "^16.0.0"
  }}
}}
```

**Get your API key:**
Settings > Developer > API Keys > Create Key""",
            "go": """**🔐 Go SDK Authentication**

**Method 1: Direct API key**
```go
import "github.com/example/sdk-go"

client := sdk.NewClient("sk_live_abc123...")
```

**Method 2: Environment variable (recommended)**
```go
import (
    "os"
    "github.com/example/sdk-go"
)

client := sdk.NewClient(os.Getenv("EXAMPLE_API_KEY"))
```

**Method 3: OAuth token**
```go
// After OAuth flow, use access token
client := sdk.NewClientWithOAuth("oauth_access_token_here")
```

**Using godotenv:**
```go
import (
    "github.com/joho/godotenv"
    "github.com/example/sdk-go"
    "log"
    "os"
)

func main() {{
    // Load .env file
    err := godotenv.Load()
    if err != nil {{
        log.Fatal("Error loading .env file")
    }}

    client := sdk.NewClient(os.Getenv("EXAMPLE_API_KEY"))
}}
```

**Security best practices:**
✅ Never commit API keys to git
✅ Use environment variables
✅ Use different keys for dev/staging/prod

**.env file:**
```env
EXAMPLE_API_KEY=sk_live_abc123...
```

**Get your API key:**
Settings > Developer > API Keys > Create Key""",
            "java": """**🔐 Java SDK Authentication**

**Method 1: Direct API key**
```java
ExampleClient client = new ExampleClient("sk_live_abc123...");
```

**Method 2: Environment variable (recommended)**
```java
String apiKey = System.getenv("EXAMPLE_API_KEY");
ExampleClient client = new ExampleClient(apiKey);
```

**Method 3: Properties file**
```java
import java.util.Properties;
import java.io.InputStream;

Properties props = new Properties();
try (InputStream input = getClass().getResourceAsStream("/config.properties")) {{
    props.load(input);
    String apiKey = props.getProperty("api.key");
    ExampleClient client = new ExampleClient(apiKey);
}}
```

**Spring Boot (application.properties):**
```properties
# application.properties
example.api.key=${{EXAMPLE_API_KEY}}
```

```java
@Configuration
public class ExampleConfig {{

    @Value("${{example.api.key}}")
    private String apiKey;

    @Bean
    public ExampleClient exampleClient() {{
        return new ExampleClient(apiKey);
    }}
}}
```

**Security best practices:**
✅ Never commit API keys to git
✅ Use environment variables
✅ Add config files to .gitignore

**Get your API key:**
Settings > Developer > API Keys > Create Key""",
        }

        return guides.get(language, "Select a language for authentication guide.")

    def _guide_examples(self, language: str) -> str:
        """Generate code examples for specific language"""
        return f"""**💡 {self.SDKS[language]["name"]} - Common Examples**

**Full code examples:**
{self.SDKS[language]["github"]}/tree/main/examples

**Quick examples:**

Need help with:
• "How to list all customers"
• "How to create a customer"
• "How to update customer data"
• "How to handle pagination"
• "How to use webhooks"

**Let me know what you'd like to do and I'll provide specific code examples!**

**Or browse documentation:**
{self.SDKS[language]["docs"]}"""

    def _guide_errors(self, language: str) -> str:
        """Generate error handling guide for specific language"""
        return f"""**🐛 {self.SDKS[language]["name"]} - Error Troubleshooting**

**Common errors:**

1. **Authentication error**
   - Check API key is correct
   - Ensure key has required permissions
   - Verify key is not expired

2. **Import error**
   - Reinstall SDK: `{self.SDKS[language]["install"]}`
   - Check SDK version compatibility
   - Clear package cache

3. **API errors (4xx, 5xx)**
   - Check error message in exception
   - Verify request parameters
   - Check API documentation

**Get detailed help:**
Share the specific error message you're seeing and I'll help debug!

**Documentation:**
{self.SDKS[language]["docs"]}/troubleshooting

**GitHub Issues:**
{self.SDKS[language]["github"]}/issues"""

    def _guide_versions(self, language: str) -> str:
        """Generate version compatibility guide"""
        sdk = self.SDKS[language]

        return f"""**📦 {sdk["name"]} - Version Information**

**Requirements:**
- {sdk["versions"]}

**Latest version:**
Check: {sdk["github"]}/releases

**Upgrade:**
```bash
{sdk["install"]}
```

**Version compatibility:**
- SDK 2.x → API 2025-11-01+
- SDK 1.x → API 2024-01-01+

**Migration guides:**
{sdk["docs"]}/migration

**Breaking changes:**
{sdk["github"]}/blob/main/CHANGELOG.md

**Need help upgrading?**
Let me know your current version and I'll guide you through the upgrade!"""


if __name__ == "__main__":
    import asyncio

    from src.workflow.state import create_initial_state

    async def test():
        # Test 1: Python SDK setup
        print("=" * 60)
        print("Test 1: Python SDK Setup")
        print("=" * 60)

        state = create_initial_state("How do I set up the Python SDK?")
        state["customer_metadata"] = {"plan": "premium"}

        agent = SDKExpert()
        result = await agent.process(state)

        print(f"\nLanguage: {result.get('sdk_language')}")
        print(f"Topic: {result.get('sdk_topic')}")
        print(f"\nResponse preview:\n{result['agent_response'][:500]}...")
        print(f"Status: {result.get('status')}")

        # Test 2: Language detection (JavaScript)
        print("\n" + "=" * 60)
        print("Test 2: JavaScript SDK")
        print("=" * 60)

        state2 = create_initial_state("I'm using Node.js, how do I authenticate?")
        result2 = await agent.process(state2)

        print(f"\nLanguage: {result2.get('sdk_language')}")
        print(f"Topic: {result2.get('sdk_topic')}")
        print(f"\nResponse preview:\n{result2['agent_response'][:400]}...")

        # Test 3: No language specified
        print("\n" + "=" * 60)
        print("Test 3: SDK Selection")
        print("=" * 60)

        state3 = create_initial_state("What SDKs do you have?")
        result3 = await agent.process(state3)

        print(f"\nLanguage: {result3.get('sdk_language')}")
        print(f"\nResponse preview:\n{result3['agent_response'][:400]}...")

    asyncio.run(test())
