"""
Unit tests for Collaboration Expert agent.
"""

import pytest
from src.agents.essential.support.usage.collaboration_expert import CollaborationExpert
from src.workflow.state import create_initial_state


class TestCollaborationExpert:
    """Test suite for Collaboration Expert agent"""

    @pytest.fixture
    def collaboration_expert(self):
        """Collaboration Expert instance"""
        return CollaborationExpert()

    def test_initialization(self, collaboration_expert):
        """Test Collaboration Expert initializes correctly"""
        assert collaboration_expert.config.name == "collaboration_expert"
        assert collaboration_expert.config.type.value == "specialist"
        assert collaboration_expert.config.tier == "essential"

    @pytest.mark.asyncio
    async def test_suggest_inviting_team_for_solo_user(self, collaboration_expert):
        """Test suggesting team invite for solo user"""
        state = create_initial_state("How do I collaborate?")
        state["customer_metadata"] = {"seats_used": 1}

        result = await collaboration_expert.process(state)

        assert result["team_size"] == 1
        assert "invite" in result["agent_response"].lower()
        assert "team" in result["agent_response"].lower()
        assert result["status"] == "resolved"

    @pytest.mark.asyncio
    async def test_teach_sharing_feature(self, collaboration_expert):
        """Test teaching sharing feature"""
        state = create_initial_state("How do I share a project?")
        state["customer_metadata"] = {"seats_used": 5}

        result = await collaboration_expert.process(state)

        assert result["collaboration_feature"] == "sharing"
        assert result["team_size"] == 5
        assert "share" in result["agent_response"].lower()
        assert "permission" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_teach_mentions_feature(self, collaboration_expert):
        """Test teaching @mentions feature"""
        state = create_initial_state("How do I @mention someone?")
        state["customer_metadata"] = {"seats_used": 10}

        result = await collaboration_expert.process(state)

        assert result["collaboration_feature"] == "mentions"
        assert "@mention" in result["agent_response"].lower() or "mention" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_teach_permissions_feature(self, collaboration_expert):
        """Test teaching permissions feature"""
        state = create_initial_state("Explain permission levels")
        state["customer_metadata"] = {"seats_used": 8}

        result = await collaboration_expert.process(state)

        assert result["collaboration_feature"] == "permissions"
        assert "viewer" in result["agent_response"].lower()
        assert "editor" in result["agent_response"].lower()
        assert "admin" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_teach_comments_feature(self, collaboration_expert):
        """Test teaching comments feature"""
        state = create_initial_state("How do comments work?")
        state["customer_metadata"] = {"seats_used": 3}

        result = await collaboration_expert.process(state)

        assert result["collaboration_feature"] == "comments"
        assert "comment" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_teach_notifications_feature(self, collaboration_expert):
        """Test teaching notifications feature"""
        state = create_initial_state("Configure my notifications")
        state["customer_metadata"] = {"seats_used": 5}

        result = await collaboration_expert.process(state)

        assert result["collaboration_feature"] == "notifications"
        assert "notification" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_teach_realtime_feature(self, collaboration_expert):
        """Test teaching real-time collaboration"""
        state = create_initial_state("How does real-time collaboration work?")
        state["customer_metadata"] = {"seats_used": 7}

        result = await collaboration_expert.process(state)

        assert result["collaboration_feature"] == "realtime"
        assert "real" in result["agent_response"].lower() or "presence" in result["agent_response"].lower()

    @pytest.mark.asyncio
    async def test_collaboration_overview(self, collaboration_expert):
        """Test providing collaboration overview"""
        state = create_initial_state("What collaboration features do you have?")
        state["customer_metadata"] = {"seats_used": 10}

        result = await collaboration_expert.process(state)

        assert result["collaboration_feature"] is None
        assert "sharing" in result["agent_response"].lower()
        assert "mention" in result["agent_response"].lower()
        assert "comment" in result["agent_response"].lower()

    def test_detect_sharing_feature(self, collaboration_expert):
        """Test detecting sharing feature"""
        assert collaboration_expert._detect_collaboration_feature("how to share") == "sharing"
        assert collaboration_expert._detect_collaboration_feature("invite team members") == "sharing"

    def test_detect_mentions_feature(self, collaboration_expert):
        """Test detecting mentions feature"""
        assert collaboration_expert._detect_collaboration_feature("use @mentions") == "mentions"
        assert collaboration_expert._detect_collaboration_feature("how to tag someone") == "mentions"

    def test_detect_permissions_feature(self, collaboration_expert):
        """Test detecting permissions feature"""
        assert collaboration_expert._detect_collaboration_feature("permission levels") == "permissions"
        assert collaboration_expert._detect_collaboration_feature("viewer access") == "permissions"
        assert collaboration_expert._detect_collaboration_feature("admin role") == "permissions"

    def test_detect_comments_feature(self, collaboration_expert):
        """Test detecting comments feature"""
        assert collaboration_expert._detect_collaboration_feature("how to comment") == "comments"
        assert collaboration_expert._detect_collaboration_feature("add discussion") == "comments"

    def test_detect_notifications_feature(self, collaboration_expert):
        """Test detecting notifications feature"""
        assert collaboration_expert._detect_collaboration_feature("notification settings") == "notifications"
        assert collaboration_expert._detect_collaboration_feature("configure alerts") == "notifications"

    def test_detect_realtime_feature(self, collaboration_expert):
        """Test detecting real-time feature"""
        assert collaboration_expert._detect_collaboration_feature("real-time collaboration") == "realtime"
        assert collaboration_expert._detect_collaboration_feature("live updates") == "realtime"
        assert collaboration_expert._detect_collaboration_feature("presence indicators") == "realtime"

    def test_detect_no_feature(self, collaboration_expert):
        """Test detecting no specific feature"""
        assert collaboration_expert._detect_collaboration_feature("general help") is None

    def test_suggest_inviting_team_content(self, collaboration_expert):
        """Test content of team invite suggestion"""
        suggestion = collaboration_expert._suggest_inviting_team()

        assert "invite" in suggestion.lower()
        assert "team" in suggestion.lower()
        assert "productivity" in suggestion.lower()

    def test_teach_sharing_has_steps(self, collaboration_expert):
        """Test sharing teaching includes steps"""
        teaching = collaboration_expert._teach_feature("sharing")

        assert "step" in teaching.lower() or "how to share" in teaching.lower()
        assert "permission" in teaching.lower()

    def test_teach_mentions_has_best_practices(self, collaboration_expert):
        """Test mentions teaching includes best practices"""
        teaching = collaboration_expert._teach_feature("mentions")

        assert "when to" in teaching.lower() or "best practice" in teaching.lower()

    def test_teach_permissions_has_levels(self, collaboration_expert):
        """Test permissions teaching includes all levels"""
        teaching = collaboration_expert._teach_feature("permissions")

        assert "viewer" in teaching.lower()
        assert "editor" in teaching.lower()
        assert "admin" in teaching.lower()
        assert "owner" in teaching.lower()

    def test_teach_comments_has_formatting(self, collaboration_expert):
        """Test comments teaching includes formatting tips"""
        teaching = collaboration_expert._teach_feature("comments")

        assert "format" in teaching.lower() or "bold" in teaching.lower()

    def test_teach_notifications_has_channels(self, collaboration_expert):
        """Test notifications teaching includes channels"""
        teaching = collaboration_expert._teach_feature("notifications")

        assert "email" in teaching.lower()
        assert "digest" in teaching.lower() or "notification" in teaching.lower()

    def test_teach_realtime_has_features(self, collaboration_expert):
        """Test real-time teaching includes features"""
        teaching = collaboration_expert._teach_feature("realtime")

        assert "presence" in teaching.lower() or "real" in teaching.lower()

    def test_overview_lists_all_features(self, collaboration_expert):
        """Test overview lists all collaboration features"""
        overview = collaboration_expert._overview_collaboration()

        assert "sharing" in overview.lower()
        assert "mention" in overview.lower()
        assert "permission" in overview.lower()
        assert "comment" in overview.lower()
        assert "notification" in overview.lower()

    def test_format_permission_levels(self, collaboration_expert):
        """Test formatting permission levels"""
        formatted = collaboration_expert._format_permission_levels()

        assert "Viewer" in formatted
        assert "Editor" in formatted
        assert "Admin" in formatted
        assert "Owner" in formatted

    @pytest.mark.asyncio
    async def test_collaboration_expert_confidence(self, collaboration_expert):
        """Test Collaboration Expert returns high confidence"""
        state = create_initial_state("How to collaborate")
        state["customer_metadata"] = {"seats_used": 5}

        result = await collaboration_expert.process(state)

        assert result["response_confidence"] == 0.9

    @pytest.mark.asyncio
    async def test_collaboration_expert_routing(self, collaboration_expert):
        """Test Collaboration Expert doesn't route to another agent"""
        state = create_initial_state("Share project")
        state["customer_metadata"] = {"seats_used": 5}

        result = await collaboration_expert.process(state)

        assert result["next_agent"] is None
        assert result["status"] == "resolved"
