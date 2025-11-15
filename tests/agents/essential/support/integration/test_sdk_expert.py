"""
Unit tests for SDK Expert agent.

Tests language detection, SDK topic detection, and language-specific
guidance for Python, JavaScript, Go, and Java SDKs.

Part of: STORY-006 Integration Specialists Sub-Swarm (TASK-604)
"""

import pytest
from unittest.mock import AsyncMock

from src.agents.essential.support.integration.sdk_expert import SDKExpert
from src.workflow.state import create_initial_state


@pytest.fixture
def sdk_expert():
    """Create SDKExpert instance for testing."""
    return SDKExpert()


@pytest.fixture
def sample_state():
    """Create a sample AgentState for testing."""
    return create_initial_state(
        message="Test message",
        context={"customer_metadata": {"plan": "premium"}}
    )


class TestSDKExpertInitialization:
    """Test SDK Expert initialization and configuration."""

    def test_initialization(self, sdk_expert):
        """Test that agent initializes with correct configuration."""
        assert sdk_expert.config.name == "sdk_expert"
        assert sdk_expert.config.type.value == "specialist"
        assert sdk_expert.config.model == "claude-3-haiku-20240307"
        assert sdk_expert.config.temperature == 0.3
        assert sdk_expert.config.tier == "essential"

    def test_has_required_capabilities(self, sdk_expert):
        """Test that agent has required capabilities."""
        from src.agents.base.agent_types import AgentCapability

        capabilities = sdk_expert.config.capabilities
        assert AgentCapability.KB_SEARCH in capabilities
        assert AgentCapability.CONTEXT_AWARE in capabilities

    def test_has_sdk_data(self, sdk_expert):
        """Test that agent has SDK data for supported languages."""
        assert "python" in sdk_expert.SDKS
        assert "javascript" in sdk_expert.SDKS
        assert "go" in sdk_expert.SDKS
        assert "java" in sdk_expert.SDKS


class TestLanguageDetection:
    """Test programming language detection."""

    def test_detect_python(self, sdk_expert):
        """Test detecting Python language."""
        language = sdk_expert._detect_language("I'm using Python and pip")
        assert language == "python"

    def test_detect_javascript(self, sdk_expert):
        """Test detecting JavaScript language."""
        language = sdk_expert._detect_language("I'm using Node.js with npm")
        assert language == "javascript"

    def test_detect_go(self, sdk_expert):
        """Test detecting Go language."""
        language = sdk_expert._detect_language("I'm using golang")
        assert language == "go"

    def test_detect_java(self, sdk_expert):
        """Test detecting Java language."""
        language = sdk_expert._detect_language("I'm using Java with Maven")
        assert language == "java"

    def test_detect_ruby(self, sdk_expert):
        """Test detecting Ruby language."""
        language = sdk_expert._detect_language("I'm using Ruby on Rails")
        assert language == "ruby"

    def test_no_language_detected(self, sdk_expert):
        """Test when no specific language is mentioned."""
        language = sdk_expert._detect_language("I need help with your API")
        assert language is None


class TestTopicDetection:
    """Test SDK topic detection."""

    def test_detect_setup_topic(self, sdk_expert):
        """Test detecting setup requests."""
        topic = sdk_expert._detect_sdk_topic("How do I install the SDK?")
        assert topic == "setup"

    def test_detect_authentication_topic(self, sdk_expert):
        """Test detecting authentication requests."""
        topic = sdk_expert._detect_sdk_topic("How do I authenticate with the SDK?")
        assert topic == "authentication"

    def test_detect_examples_topic(self, sdk_expert):
        """Test detecting example requests."""
        topic = sdk_expert._detect_sdk_topic("Can you show me an example?")
        assert topic == "examples"

    def test_detect_errors_topic(self, sdk_expert):
        """Test detecting error troubleshooting requests."""
        topic = sdk_expert._detect_sdk_topic("I'm getting an error with the SDK")
        assert topic == "errors"

    def test_detect_versions_topic(self, sdk_expert):
        """Test detecting version/compatibility requests."""
        topic = sdk_expert._detect_sdk_topic("What version of the SDK should I use?")
        assert topic == "versions"


class TestSDKProcessing:
    """Test SDK request processing."""

    @pytest.mark.asyncio
    async def test_process_python_setup(self, sdk_expert):
        """Test processing Python SDK setup request."""
        state = create_initial_state("How do I set up the Python SDK?")

        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert result["sdk_language"] == "python"
        assert result["sdk_topic"] == "setup"
        assert "pip install" in result["agent_response"]
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_javascript_authentication(self, sdk_expert):
        """Test processing JavaScript authentication request."""
        state = create_initial_state("How do I authenticate with the Node.js SDK?")

        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert result["sdk_language"] == "javascript"
        assert result["sdk_topic"] == "authentication"
        assert "apiKey" in result["agent_response"] or "api_key" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_go_setup(self, sdk_expert):
        """Test processing Go SDK setup request."""
        state = create_initial_state("How to use the Go SDK?")

        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert result["sdk_language"] == "go"
        assert "go get" in result["agent_response"]
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_java_setup(self, sdk_expert):
        """Test processing Java SDK setup request."""
        state = create_initial_state("How do I use the Java SDK with Maven?")

        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert result["sdk_language"] == "java"
        assert "maven" in result["agent_response"].lower() or "dependency" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_process_no_language_shows_selector(self, sdk_expert):
        """Test that no language shows SDK selector."""
        state = create_initial_state("What SDKs do you have?")

        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert result["sdk_language"] is None
        assert "python" in result["agent_response"].lower()
        assert "javascript" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_includes_kb_results(self, sdk_expert):
        """Test that KB results are included in response."""
        state = create_initial_state("Python SDK help")

        sdk_expert.search_knowledge_base = AsyncMock(return_value=[
            {"title": "Python SDK Guide", "doc_id": "kb_123"},
            {"title": "SDK Examples", "doc_id": "kb_456"}
        ])

        result = await sdk_expert.process(state)

        assert len(result["kb_results"]) == 2
        assert "Related documentation" in result["agent_response"] or "documentation" in result["agent_response"].lower()


class TestSetupGuides:
    """Test SDK setup guides."""

    def test_python_setup_guide(self, sdk_expert):
        """Test Python setup guide contains correct info."""
        guide = sdk_expert._guide_setup("python")

        assert "pip install" in guide
        assert "from example_sdk import Client" in guide or "import" in guide.lower()
        assert "client = Client" in guide or "api_key" in guide.lower()

    def test_javascript_setup_guide(self, sdk_expert):
        """Test JavaScript setup guide contains correct info."""
        guide = sdk_expert._guide_setup("javascript")

        assert "npm install" in guide
        assert "require" in guide or "import" in guide
        assert "apiKey" in guide or "api_key" in guide.lower()

    def test_go_setup_guide(self, sdk_expert):
        """Test Go setup guide contains correct info."""
        guide = sdk_expert._guide_setup("go")

        assert "go get" in guide
        assert "import" in guide.lower()
        assert "NewClient" in guide or "client" in guide.lower()

    def test_java_setup_guide(self, sdk_expert):
        """Test Java setup guide contains correct info."""
        guide = sdk_expert._guide_setup("java")

        assert "maven" in guide.lower() or "gradle" in guide.lower()
        assert "import" in guide.lower()


class TestAuthenticationGuides:
    """Test SDK authentication guides."""

    def test_python_auth_guide(self, sdk_expert):
        """Test Python authentication guide."""
        guide = sdk_expert._guide_authentication("python")

        assert "api_key" in guide.lower()
        assert "environment" in guide.lower() or "env" in guide.lower()

    def test_javascript_auth_guide(self, sdk_expert):
        """Test JavaScript authentication guide."""
        guide = sdk_expert._guide_authentication("javascript")

        assert "apiKey" in guide or "api_key" in guide.lower()
        assert "process.env" in guide or "environment" in guide.lower()

    def test_go_auth_guide(self, sdk_expert):
        """Test Go authentication guide."""
        guide = sdk_expert._guide_authentication("go")

        assert "api" in guide.lower()
        assert "os.Getenv" in guide or "environment" in guide.lower()

    def test_java_auth_guide(self, sdk_expert):
        """Test Java authentication guide."""
        guide = sdk_expert._guide_authentication("java")

        assert "api" in guide.lower()
        assert "System.getenv" in guide or "environment" in guide.lower()


class TestSDKData:
    """Test SDK data structure."""

    def test_python_sdk_data(self, sdk_expert):
        """Test Python SDK data is complete."""
        python_sdk = sdk_expert.SDKS["python"]

        assert "install" in python_sdk
        assert "pip install" in python_sdk["install"]
        assert "docs" in python_sdk
        assert "github" in python_sdk

    def test_javascript_sdk_data(self, sdk_expert):
        """Test JavaScript SDK data is complete."""
        js_sdk = sdk_expert.SDKS["javascript"]

        assert "install" in js_sdk
        assert "npm install" in js_sdk["install"]
        assert "docs" in js_sdk
        assert "github" in js_sdk

    def test_all_sdks_have_required_fields(self, sdk_expert):
        """Test that all SDKs have required fields."""
        required_fields = ["name", "install", "import", "docs", "github", "versions"]

        for lang, sdk_data in sdk_expert.SDKS.items():
            for field in required_fields:
                assert field in sdk_data, f"{lang} SDK missing {field}"


class TestLanguageSelector:
    """Test language selector guide."""

    def test_language_selector_contains_all_sdks(self, sdk_expert):
        """Test that language selector shows all major SDKs."""
        guide = sdk_expert._guide_language_selector()

        assert "python" in guide.lower()
        assert "javascript" in guide.lower()
        assert "go" in guide.lower()
        assert "java" in guide.lower()

    def test_language_selector_has_install_commands(self, sdk_expert):
        """Test that language selector includes install commands."""
        guide = sdk_expert._guide_language_selector()

        assert "pip install" in guide
        assert "npm install" in guide
        assert "go get" in guide


class TestStateUpdates:
    """Test state updates."""

    @pytest.mark.asyncio
    async def test_updates_agent_history(self, sdk_expert):
        """Test that agent is added to history."""
        state = create_initial_state("SDK help")
        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert "sdk_expert" in result["agent_history"]

    @pytest.mark.asyncio
    async def test_sets_response_confidence(self, sdk_expert):
        """Test that response confidence is set."""
        state = create_initial_state("Python SDK setup")
        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert "response_confidence" in result
        assert result["response_confidence"] >= 0.8

    @pytest.mark.asyncio
    async def test_includes_sdk_language(self, sdk_expert):
        """Test that SDK language is included in result."""
        state = create_initial_state("Python SDK help")
        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert "sdk_language" in result

    @pytest.mark.asyncio
    async def test_includes_sdk_topic(self, sdk_expert):
        """Test that SDK topic is included in result."""
        state = create_initial_state("SDK setup")
        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert "sdk_topic" in result

    @pytest.mark.asyncio
    async def test_marks_as_resolved(self, sdk_expert):
        """Test that status is marked as resolved."""
        state = create_initial_state("SDK help")
        sdk_expert.search_knowledge_base = AsyncMock(return_value=[])

        result = await sdk_expert.process(state)

        assert result["status"] == "resolved"
        assert result["next_agent"] is None
