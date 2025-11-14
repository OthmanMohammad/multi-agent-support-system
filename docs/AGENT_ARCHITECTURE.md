# Agent Architecture Documentation

## Overview

This document describes the refactored agent architecture that supports 243 agents across 17 swarms with a clean, scalable folder structure.

## Directory Structure

```
src/agents/
├── base/                          # Enhanced base classes
│   ├── __init__.py
│   ├── base_agent.py             # BaseAgent, RoutingAgent, SpecialistAgent
│   ├── agent_types.py            # Enums for agent types, capabilities, domains
│   ├── capabilities.py           # Capability mixins
│   ├── decorators.py             # Agent decorators (logging, retry, etc.)
│   └── exceptions.py             # Agent-specific exceptions
│
├── essential/               # Tier 1: Essential agents
│   ├── routing/                  # Request routing agents
│   │   ├── meta_router.py       # Main entry point router
│   │   └── __init__.py
│   │
│   ├── knowledge_base/           # KB management agents
│   │   └── __init__.py
│   │
│   └── support/                  # Support specialists
│       ├── billing/             # Billing agents
│       │   ├── upgrade_specialist.py
│       │   └── __init__.py
│       ├── technical/           # Technical agents
│       │   ├── bug_triager.py
│       │   └── __init__.py
│       ├── usage/               # Usage agents
│       │   ├── onboarding_guide.py
│       │   └── __init__.py
│       ├── integration/         # Integration agents
│       │   ├── api_debugger.py
│       │   └── __init__.py
│       └── account/             # Account management agents
│           └── __init__.py
│
├── revenue/                # Tier 2: Revenue-focused agents (placeholder)
├── operational/            # Tier 3: Operational agents (placeholder)
└── advanced/               # Tier 4: Advanced AI agents (placeholder)
```

## Enhanced BaseAgent Class

### Key Features

1. **Configuration-based initialization** with `AgentConfig` dataclass
2. **Built-in capabilities** (KB search, context enrichment, collaboration)
3. **Comprehensive logging** with structlog integration
4. **Error handling** with custom exceptions
5. **State management** utilities
6. **Escalation logic** for complex scenarios
7. **LLM interaction** with retry and monitoring

### Agent Configuration

```python
from src.agents.base import AgentConfig, AgentType, AgentCapability

config = AgentConfig(
    name="billing_agent",
    type=AgentType.SPECIALIST,
    model="claude-3-haiku-20240307",
    temperature=0.3,
    max_tokens=1000,
    capabilities=[
        AgentCapability.KB_SEARCH,
        AgentCapability.CONTEXT_AWARE
    ],
    kb_category="billing",
    tier="essential"
)
```

### Creating a New Agent

```python
from src.agents.base import BaseAgent, AgentConfig, AgentType
from src.workflow.state import AgentState
from src.services.infrastructure.agent_registry import AgentRegistry

@AgentRegistry.register("my_agent", tier="essential", category="support")
class MyAgent(BaseAgent):
    def __init__(self):
        config = AgentConfig(
            name="my_agent",
            type=AgentType.SPECIALIST,
            capabilities=[AgentCapability.KB_SEARCH]
        )
        super().__init__(config)

    async def process(self, state: AgentState) -> AgentState:
        # Update state
        state = self.update_state(state)

        # Your agent logic here
        message = state["current_message"]
        response = await self.call_llm(
            system_prompt="You are a helpful agent",
            user_message=message
        )

        # Update state with response
        state["agent_response"] = response
        state["next_agent"] = None
        state["status"] = "resolved"

        return state
```

## Agent Types and Capabilities

### Agent Types

- `ROUTER`: Routes requests to appropriate specialists
- `SPECIALIST`: Resolves specific types of queries
- `COORDINATOR`: Coordinates multi-agent workflows
- `ANALYZER`: Analyzes data and provides insights
- `GENERATOR`: Generates content or responses

### Agent Capabilities

- `KB_SEARCH`: Can search knowledge base
- `CONTEXT_AWARE`: Can enrich context with customer data
- `MULTI_TURN`: Supports multi-turn conversations
- `COLLABORATION`: Can collaborate with other agents
- `EXTERNAL_API`: Can call external APIs
- `DATABASE_WRITE`: Can write to database
- `SENTIMENT_ANALYSIS`: Can analyze sentiment
- `ENTITY_EXTRACTION`: Can extract entities

## Capability Mixins

### KBSearchCapability

```python
from src.agents.base.capabilities import KBSearchCapability

class MyAgent(BaseAgent, KBSearchCapability):
    async def process(self, state: AgentState) -> AgentState:
        # Search and synthesize KB articles
        kb_context = await self.search_and_synthesize(
            query=state["current_message"],
            category="technical",
            limit=3
        )
```

### CollaborationCapability

```python
from src.agents.base.capabilities import CollaborationCapability

class MyAgent(BaseAgent, CollaborationCapability):
    async def process(self, state: AgentState) -> AgentState:
        # Request collaboration from other agents
        result = await self.request_collaboration(
            agent_names=["expert1", "expert2"],
            pattern="debate",
            context=state
        )
```

## Agent Registry

The `AgentRegistry` enables dynamic agent discovery and management:

```python
from src.services.infrastructure.agent_registry import AgentRegistry

# Register an agent
@AgentRegistry.register("my_agent", tier="essential", category="support")
class MyAgent(BaseAgent):
    pass

# Get an agent class
AgentClass = AgentRegistry.get_agent("my_agent")

# List all agents
agents = AgentRegistry.list_agents()

# Get agents by tier
tier1_agents = AgentRegistry.get_agents_by_tier("essential")

# Get agents by category
support_agents = AgentRegistry.get_agents_by_category("support")
```

## Decorators

### @log_agent_action

```python
from src.agents.base.decorators import log_agent_action

class MyAgent(BaseAgent):
    @log_agent_action("intent_classification")
    async def classify_intent(self, message: str):
        # Automatically logs start, completion, duration, and errors
        return await self.call_llm(...)
```

### @retry_on_error

```python
from src.agents.base.decorators import retry_on_error

class MyAgent(BaseAgent):
    @retry_on_error(max_retries=3, delay=2.0)
    async def call_external_api(self):
        # Automatically retries on failure
        return await external_api.call()
```

### @validate_state

```python
from src.agents.base.decorators import validate_state

class MyAgent(BaseAgent):
    @validate_state(["current_message", "customer_id"])
    async def process(self, state: AgentState) -> AgentState:
        # Validates required state fields before processing
        pass
```

## Exception Handling

```python
from src.agents.base.exceptions import (
    AgentError,
    AgentProcessingError,
    AgentLLMError,
    AgentKnowledgeBaseError
)

try:
    result = await agent.process(state)
except AgentLLMError as e:
    logger.error(f"LLM call failed: {e}")
except AgentProcessingError as e:
    logger.error(f"Processing failed: {e}")
```

## Migration Guide

### Old Structure (Deprecated)

```python
from src.agents.base import BaseAgent
from src.agents.router import RouterAgent
from src.agents.billing import BillingAgent
```

### New Structure (Recommended)

```python
from src.agents.base import BaseAgent, AgentConfig, AgentType
from src.agents.essential.routing.meta_router import MetaRouterAgent
from src.agents.essential.support.billing.upgrade_specialist import BillingAgent
```

### Backward Compatibility

The old agent files (router.py, billing.py, etc.) are kept in place for backward compatibility, but all new development should use the new structure.

## Tier System

### Tier 1: Essential (Implemented)
- Core routing and classification
- Basic support specialists
- Knowledge base management

### Tier 2: Revenue (Placeholder)
- Sales agents
- Customer success agents
- Monetization agents

### Tier 3: Operational (Placeholder)
- Workflow automation
- Process optimization
- Resource management

### Tier 4: Advanced (Placeholder)
- Predictive analytics
- Sentiment analysis
- Proactive support
- Intelligence gathering

## Workflow Patterns (Future)

Located in `src/workflow/patterns/`:

- **Sequential**: Agents execute one after another
- **Parallel**: Multiple agents execute simultaneously
- **Debate**: Agents discuss and reach consensus
- **Verification**: One agent verifies another's output
- **Expert Panel**: Multiple expert agents contribute

## Best Practices

1. **Always use AgentConfig** for agent initialization
2. **Register agents** with `@AgentRegistry.register` decorator
3. **Use capability mixins** for reusable functionality
4. **Leverage decorators** for cross-cutting concerns
5. **Handle errors** with specific exception types
6. **Log extensively** using structlog
7. **Update state** using `self.update_state()` method
8. **Check capabilities** before using features
9. **Test agents** in isolation before integration
10. **Document** agent purpose and capabilities

## Testing

```python
import asyncio
from src.workflow.state import create_initial_state
from src.agents.essential.routing.meta_router import MetaRouterAgent

async def test_router():
    agent = MetaRouterAgent()
    state = create_initial_state("I want to upgrade my plan")
    result = await agent.process(state)
    assert result["primary_intent"] == "billing_upgrade"

asyncio.run(test_router())
```

## Future Enhancements

1. **Agent collaboration patterns** implementation
2. **Context enrichment service** integration
3. **Knowledge base service** integration
4. **Multi-agent workflows** with LangGraph
5. **Agent performance metrics** and analytics
6. **Dynamic agent loading** and hot-reloading
7. **Agent versioning** and A/B testing
8. **Agent orchestration** at scale

## References

- [Database Schema Documentation](./issues/001-infrastructure-database-schema.md)
- [Folder Structure Issue](./issues/002-infrastructure-folder-structure.md)
- [Workflow State Documentation](../src/workflow/state.py)
- [Agent Registry](../src/services/infrastructure/agent_registry.py)
