"""
Unit tests for Workflow Optimizer agent.
"""

import pytest
from src.agents.essential.support.usage.workflow_optimizer import WorkflowOptimizer
from src.workflow.state import create_initial_state


class TestWorkflowOptimizer:
    """Test suite for Workflow Optimizer agent"""

    @pytest.fixture
    def workflow_optimizer(self):
        """Workflow Optimizer instance"""
        return WorkflowOptimizer()

    def test_initialization(self, workflow_optimizer):
        """Test Workflow Optimizer initializes correctly"""
        assert workflow_optimizer.config.name == "workflow_optimizer"
        assert workflow_optimizer.config.type.value == "specialist"
        assert workflow_optimizer.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_analyze_inefficient_workflow(self, workflow_optimizer):
        """Test analyzing workflow with multiple inefficiencies"""
        state = create_initial_state("Analyze my workflow")
        state["customer_metadata"] = {
            "feature_usage": {
                "automation_enabled": False,
                "project_count": 15,
                "uses_templates": False,
                "uses_collaboration": False
            },
            "seats_used": 5,
            "account_age_days": 90
        }

        result = await workflow_optimizer.process(state)

        assert result["workflow_score"] < 100
        assert result["time_savings_estimate"] > 0
        assert result["optimizations_suggested"] > 0
        assert "automation" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_analyze_optimized_workflow(self, workflow_optimizer):
        """Test analyzing already optimized workflow"""
        state = create_initial_state("How's my workflow?")
        state["customer_metadata"] = {
            "feature_usage": {
                "automation_enabled": True,
                "project_count": 20,
                "uses_templates": True,
                "uses_collaboration": True,
                "uses_shortcuts": True,
                "uses_integrations": True
            },
            "seats_used": 10,
            "account_age_days": 180
        }

        result = await workflow_optimizer.process(state)

        assert result["workflow_score"] == 100
        assert result["time_savings_estimate"] == 0
        assert "excellent" in result["agent_response"].lower()

    def test_detect_manual_repetition(self, workflow_optimizer):
        """Test detecting manual repetition inefficiency"""
        context = {
            "feature_usage": {
                "automation_enabled": False,
                "project_count": 10
            },
            "account_age_days": 60
        }

        analysis = workflow_optimizer._analyze_workflow(context, "", "")

        inefficiencies = [i for i in analysis["inefficiencies"] if i["type"] == "manual_repetition"]
        assert len(inefficiencies) > 0

    def test_detect_no_templates(self, workflow_optimizer):
        """Test detecting lack of templates"""
        context = {
            "feature_usage": {
                "project_count": 15,
                "uses_templates": False
            }
        }

        analysis = workflow_optimizer._analyze_workflow(context, "", "")

        inefficiencies = [i for i in analysis["inefficiencies"] if i["type"] == "no_templates"]
        assert len(inefficiencies) > 0

    def test_detect_poor_collaboration(self, workflow_optimizer):
        """Test detecting poor collaboration for teams"""
        context = {
            "feature_usage": {
                "uses_collaboration": False
            },
            "seats_used": 5
        }

        analysis = workflow_optimizer._analyze_workflow(context, "", "")

        inefficiencies = [i for i in analysis["inefficiencies"] if i["type"] == "poor_collaboration"]
        assert len(inefficiencies) > 0

    def test_calculate_workflow_score(self, workflow_optimizer):
        """Test workflow score calculation"""
        # No inefficiencies = 100 score
        assert workflow_optimizer._calculate_workflow_score([]) == 100

        # High impact inefficiency
        high_impact = [{"impact": "high"}]
        assert workflow_optimizer._calculate_workflow_score(high_impact) == 70

        # Medium impact inefficiency
        medium_impact = [{"impact": "medium"}]
        assert workflow_optimizer._calculate_workflow_score(medium_impact) == 85

        # Low impact inefficiency
        low_impact = [{"impact": "low"}]
        assert workflow_optimizer._calculate_workflow_score(low_impact) == 95

        # Multiple inefficiencies
        multiple = [{"impact": "high"}, {"impact": "medium"}]
        assert workflow_optimizer._calculate_workflow_score(multiple) == 55

    def test_generate_optimizations_perfect_workflow(self, workflow_optimizer):
        """Test optimization generation for perfect workflow"""
        analysis = {
            "inefficiencies": [],
            "workflow_score": 100
        }

        optimizations = workflow_optimizer._generate_optimizations(analysis)

        assert optimizations["time_saved_hours_per_week"] == 0
        assert "excellent" in optimizations["message"].lower()

    def test_generate_optimizations_with_issues(self, workflow_optimizer):
        """Test optimization generation with inefficiencies"""
        analysis = {
            "inefficiencies": [
                {
                    "type": "manual_repetition",
                    "description": "Too many manual tasks",
                    "impact": "high",
                    "time_saved_hours": 5
                },
                {
                    "type": "no_templates",
                    "description": "Not using templates",
                    "impact": "medium",
                    "time_saved_hours": 2
                }
            ],
            "workflow_score": 55
        }

        optimizations = workflow_optimizer._generate_optimizations(analysis)

        assert optimizations["time_saved_hours_per_week"] == 7
        assert "automation" in optimizations["message"].lower()
        assert "templates" in optimizations["message"].lower()

    def test_all_inefficiency_types_covered(self, workflow_optimizer):
        """Test that all inefficiency types generate recommendations"""
        inefficiency_types = [
            "manual_repetition",
            "no_templates",
            "poor_collaboration",
            "no_shortcuts",
            "manual_bulk_ops",
            "no_integrations",
            "browse_instead_search",
            "notification_overload"
        ]

        for ineff_type in inefficiency_types:
            analysis = {
                "inefficiencies": [{
                    "type": ineff_type,
                    "description": f"Test {ineff_type}",
                    "impact": "medium",
                    "time_saved_hours": 2
                }],
                "workflow_score": 85
            }

            optimizations = workflow_optimizer._generate_optimizations(analysis)
            assert len(optimizations["message"]) > 0

    @pytest.mark.asyncio
    async def test_workflow_optimizer_confidence(self, workflow_optimizer):
        """Test Workflow Optimizer returns high confidence"""
        state = create_initial_state("Optimize my workflow")
        state["customer_metadata"] = {"feature_usage": {}}

        result = await workflow_optimizer.process(state)

        assert result["response_confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_workflow_optimizer_routing(self, workflow_optimizer):
        """Test Workflow Optimizer doesn't route to another agent"""
        state = create_initial_state("Analyze workflow")
        state["customer_metadata"] = {"feature_usage": {}}

        result = await workflow_optimizer.process(state)

        assert result["next_agent"] is None
        assert result["status"] == "resolved"
