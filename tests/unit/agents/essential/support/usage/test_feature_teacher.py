"""
Unit tests for Feature Teacher agent.
"""

import pytest
from src.agents.essential.support.usage.feature_teacher import FeatureTeacher
from src.workflow.state import create_initial_state


class TestFeatureTeacher:
    """Test suite for Feature Teacher agent"""

    @pytest.fixture
    def feature_teacher(self):
        """Feature Teacher instance"""
        return FeatureTeacher()

    def test_initialization(self, feature_teacher):
        """Test Feature Teacher initializes correctly"""
        assert feature_teacher.config.name == "feature_teacher"
        assert feature_teacher.config.type.value == "specialist"
        assert feature_teacher.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_teach_reports_feature_beginner(self, feature_teacher):
        """Test teaching reports feature to beginner"""
        state = create_initial_state("I want to learn about reports")
        state["customer_metadata"] = {"skill_level": "beginner"}

        result = await feature_teacher.process(state)

        assert result["feature_taught"] == "reports"
        assert result["tutorial_provided"] is True
        assert "step-by-step" in result["agent_response"].lower()
        assert "video tutorial" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_teach_api_feature_advanced(self, feature_teacher):
        """Test teaching API feature to advanced user"""
        state = create_initial_state("How do I use the API?")
        state["customer_metadata"] = {"skill_level": "advanced"}

        result = await feature_teacher.process(state)

        assert result["feature_taught"] == "api"
        assert result["tutorial_provided"] is True
        assert "advanced" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_teach_automation_feature(self, feature_teacher):
        """Test teaching automation feature"""
        state = create_initial_state("Teach me about automation")
        state["customer_metadata"] = {"skill_level": "intermediate"}

        result = await feature_teacher.process(state)

        assert result["feature_taught"] == "automation"
        assert result["tutorial_provided"] is True
        assert "automate" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_list_features_when_unknown(self, feature_teacher):
        """Test listing all features when none specified"""
        state = create_initial_state("What can you teach me?")

        result = await feature_teacher.process(state)

        assert result["tutorial_provided"] is False
        assert "reports" in result["agent_response"].lower()
        assert "api" in result["agent_response"].lower()
        assert "automation" in result["agent_response"].lower()
        assert "dashboards" in result["agent_response"].lower()

    def test_extract_feature_name_direct(self, feature_teacher):
        """Test extracting feature name from message"""
        # Direct matches
        assert feature_teacher._extract_feature_name("I want to learn reports") == "reports"
        assert feature_teacher._extract_feature_name("How do I use the API?") == "api"
        assert feature_teacher._extract_feature_name("Teach me automation") == "automation"

    def test_extract_feature_name_aliases(self, feature_teacher):
        """Test extracting feature name from aliases"""
        # Aliases
        assert feature_teacher._extract_feature_name("I need help with analytics") == "reports"
        assert feature_teacher._extract_feature_name("REST API integration") == "api"
        assert feature_teacher._extract_feature_name("How to automate tasks") == "automation"
        assert feature_teacher._extract_feature_name("Create a dashboard") == "dashboards"

    def test_extract_feature_name_unknown(self, feature_teacher):
        """Test extracting feature name returns None for unknown"""
        assert feature_teacher._extract_feature_name("random question") is None
        assert feature_teacher._extract_feature_name("help me") is None

    def test_create_lesson_beginner(self, feature_teacher):
        """Test lesson creation for beginner"""
        lesson = feature_teacher._create_lesson("reports", "beginner")

        assert lesson["feature"] == "reports"
        assert lesson["skill_level"] == "beginner"
        assert "step-by-step guide" in lesson["content"].lower()
        assert "practice exercise" in lesson["content"].lower()
        assert "tips for beginners" in lesson["content"].lower()

    def test_create_lesson_intermediate(self, feature_teacher):
        """Test lesson creation for intermediate"""
        lesson = feature_teacher._create_lesson("api", "intermediate")

        assert lesson["feature"] == "api"
        assert lesson["skill_level"] == "intermediate"
        assert "pro tips" in lesson["content"].lower()

    def test_create_lesson_advanced(self, feature_teacher):
        """Test lesson creation for advanced"""
        lesson = feature_teacher._create_lesson("automation", "advanced")

        assert lesson["feature"] == "automation"
        assert lesson["skill_level"] == "advanced"
        assert "advanced" in lesson["content"].lower()

    def test_format_steps_detailed(self, feature_teacher):
        """Test formatting steps with detail"""
        steps = ["Step 1", "Step 2", "Step 3"]
        formatted = feature_teacher._format_steps(steps, detailed=True)

        assert "1." in formatted
        assert "Step 1" in formatted
        assert "Take your time" in formatted

    def test_format_steps_brief(self, feature_teacher):
        """Test formatting steps briefly"""
        steps = ["Step 1", "Step 2", "Step 3"]
        formatted = feature_teacher._format_steps(steps, detailed=False)

        assert "1." in formatted
        assert "Step 1" in formatted
        assert "Take your time" not in formatted

    def test_format_kb_links(self, feature_teacher):
        """Test formatting KB article links"""
        articles = ["kb_reports_101", "kb_custom_dashboards"]
        formatted = feature_teacher._format_kb_links(articles)

        assert "Reports 101" in formatted
        assert "Custom Dashboards" in formatted
        assert "/kb/" in formatted

    def test_list_available_features(self, feature_teacher):
        """Test listing all available features"""
        features_list = feature_teacher._list_available_features()

        assert "Reports" in features_list
        assert "API" in features_list
        assert "Automation" in features_list
        assert "Dashboards" in features_list
        assert "Workflows" in features_list

    @pytest.mark.asyncio
    async def test_feature_teacher_confidence(self, feature_teacher):
        """Test Feature Teacher returns high confidence"""
        state = create_initial_state("Teach me about dashboards")

        result = await feature_teacher.process(state)

        assert result["response_confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_feature_teacher_routing(self, feature_teacher):
        """Test Feature Teacher doesn't route to another agent"""
        state = create_initial_state("Learn about workflows")

        result = await feature_teacher.process(state)

        assert result["next_agent"] is None
        assert result["status"] == "resolved"
