# Test Organization

This directory contains all tests for the Multi-Agent Support System, organized according to software engineering best practices.

## Directory Structure

```
tests/
├── README.md                    # This file
├── conftest.py                  # Shared pytest fixtures and configuration
├── __init__.py                  # Package initialization
│
├── unit/                        # Unit tests (fast, isolated, no external dependencies)
│   ├── agents/                  # Agent-specific unit tests
│   │   ├── test_essential_agents.py
│   │   ├── test_revenue_agents.py
│   │   ├── test_operational_agents.py
│   │   └── test_advanced_agents.py
│   ├── services/                # Service layer tests
│   │   ├── test_job_store.py   # Job store unit tests
│   │   └── __init__.py
│   ├── workflow/                # Workflow pattern tests
│   │   ├── test_patterns.py    # Workflow pattern unit tests
│   │   └── __init__.py
│   └── test_agent_basic.py      # Basic agent functionality tests
│
├── integration/                 # Integration tests (test component interactions)
│   ├── test_api_client.py      # API client integration tests
│   ├── test_repositories.py    # Database repository tests
│   ├── test_unit_of_work.py    # UnitOfWork pattern tests
│   ├── test_kb_search.py       # Knowledge base search tests
│   └── test_search_comparison.py
│
├── e2e/                         # End-to-end tests (full system tests)
│   ├── test_simple_routing.py  # Simple routing flow
│   ├── test_comprehensive_flow.py  # Comprehensive agent workflows
│   ├── test_debate_pattern.py  # Debate pattern E2E test
│   └── test_workflow_execution.py  # Full workflow execution
│
├── performance/                 # Performance and load tests
│   └── (performance test files)
│
└── context/                     # Context enrichment tests
    └── (context provider tests)
```

## Test Categories

### Unit Tests (`tests/unit/`)
- **Purpose:** Test individual components in isolation
- **Speed:** Very fast (< 1 second per test)
- **Dependencies:** No external services (mocked)
- **Coverage Target:** 80%+
- **Run with:** `pytest tests/unit/ -v`

### Integration Tests (`tests/integration/`)
- **Purpose:** Test interactions between components
- **Speed:** Moderate (1-5 seconds per test)
- **Dependencies:** May use test database, Redis, etc.
- **Coverage Target:** 60%+
- **Run with:** `pytest tests/integration/ -v`

### End-to-End Tests (`tests/e2e/`)
- **Purpose:** Test complete user workflows
- **Speed:** Slower (5-30 seconds per test)
- **Dependencies:** Full system stack required
- **Coverage Target:** Critical paths only
- **Run with:** `pytest tests/e2e/ -v`

### Performance Tests (`tests/performance/`)
- **Purpose:** Benchmark and load testing
- **Speed:** Variable (can be slow)
- **Dependencies:** Full system or specific services
- **Run with:** `pytest tests/performance/ -v --benchmark-only`

## Running Tests

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Category
```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v
```

### Run with Coverage
```bash
pytest tests/ -v --cov=src --cov-report=html
```

### Run Specific Test File
```bash
pytest tests/unit/services/test_job_store.py -v
```

### Run Specific Test Function
```bash
pytest tests/unit/services/test_job_store.py::test_create_agent_job -v
```

### Run Tests Matching Pattern
```bash
# Run all tests with "job" in the name
pytest tests/ -v -k "job"

# Run all tests with "agent" but not "workflow"
pytest tests/ -v -k "agent and not workflow"
```

### Parallel Test Execution
```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -v -n 4
```

## Test Best Practices

### 1. Test Naming Convention
- Test files: `test_*.py`
- Test functions: `test_<feature>_<scenario>()`
- Test classes: `Test<Feature>`

**Examples:**
```python
# Good
def test_create_job_success()
def test_create_job_with_invalid_type_raises_error()

# Bad
def test1()
def testCreateJob()
```

### 2. Test Organization
```python
# Arrange - Set up test data
job_store = InMemoryJobStore()

# Act - Execute the code under test
job_id = await job_store.create_job(...)

# Assert - Verify the results
assert job_id is not None
```

### 3. Use Fixtures
```python
@pytest.fixture
async def job_store():
    """Reusable job store fixture"""
    store = InMemoryJobStore()
    await store.initialize()
    yield store
    await store.close()

async def test_create_job(job_store):
    """Use the fixture"""
    job_id = await job_store.create_job(...)
```

### 4. Async Tests
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### 5. Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "HELLO"),
    ("world", "WORLD"),
])
def test_uppercase(input, expected):
    assert input.upper() == expected
```

### 6. Mocking External Services
```python
from unittest.mock import AsyncMock, patch

@patch('src.services.anthropic.client')
async def test_agent_call(mock_client):
    mock_client.messages.create = AsyncMock(return_value={"content": "test"})
    result = await agent.process(state)
    assert result is not None
```

## Test Fixtures

Shared fixtures are defined in `tests/conftest.py`:

- `async_client` - FastAPI test client
- `db_session` - Test database session
- `redis_client` - Test Redis client
- `job_store` - Job store instance
- `mock_anthropic` - Mocked Anthropic API

## Continuous Integration

Tests are run automatically on:
- Every pull request
- Every commit to main branch
- Nightly builds (full test suite + performance tests)

### CI Pipeline
1. **Fast Tests** (< 5 min): Unit tests + linting
2. **Integration Tests** (< 15 min): Integration tests
3. **E2E Tests** (< 30 min): End-to-end tests
4. **Performance Tests** (weekly): Benchmarks and load tests

## Test Coverage

Current coverage targets:
- **Overall:** 80%
- **Critical paths:** 95%
- **New code:** 90%

View coverage report:
```bash
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

## Debugging Tests

### Run with Verbose Output
```bash
pytest tests/ -vv
```

### Show Print Statements
```bash
pytest tests/ -s
```

### Drop into Debugger on Failure
```bash
pytest tests/ --pdb
```

### Run Only Failed Tests
```bash
# Run all tests once
pytest tests/

# Re-run only failed tests
pytest tests/ --lf
```

### Show Slowest Tests
```bash
pytest tests/ --durations=10
```

## Adding New Tests

1. **Determine test type**: Unit, integration, or E2E?
2. **Create test file** in appropriate directory
3. **Write test following AAA pattern** (Arrange, Act, Assert)
4. **Add fixtures** if needed in `conftest.py`
5. **Run test** to verify it passes
6. **Check coverage** to ensure adequate coverage

## Questions or Issues?

- See pytest documentation: https://docs.pytest.org/
- See project contributing guide: `../CONTRIBUTING.md`
- Ask in team chat or create an issue
