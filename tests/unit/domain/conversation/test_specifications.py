"""
Tests for Conversation Domain Specifications

These tests verify business rules encapsulated as specifications.
No database needed - just object state checking.
"""
import pytest
from services.domain.conversation.specifications import (
    ConversationIsActive,
    ConversationIsResolved,
    ConversationIsEscalated,
    HasMinimumMessages,
    HasAgentInteraction,
    HasValidSentiment,
    IsWithinMaxTurns,
    CanResolveConversation,
    CanEscalateConversation,
    CanReopenConversation,
)


class TestConversationIsActive:
    """Tests for ConversationIsActive specification"""
    
    def test_active_conversation_satisfies(self, mock_conversation):
        """Active conversation satisfies specification"""
        mock_conversation.status = "active"
        spec = ConversationIsActive()
        
        assert spec.is_satisfied_by(mock_conversation)
    
    def test_resolved_conversation_not_satisfies(self, mock_conversation):
        """Resolved conversation does not satisfy"""
        mock_conversation.status = "resolved"
        spec = ConversationIsActive()
        
        assert not spec.is_satisfied_by(mock_conversation)
        reason = spec.reason_not_satisfied(mock_conversation)
        assert "resolved" in reason
        assert "not 'active'" in reason
    
    def test_escalated_conversation_not_satisfies(self, mock_conversation):
        """Escalated conversation does not satisfy"""
        mock_conversation.status = "escalated"
        spec = ConversationIsActive()
        
        assert not spec.is_satisfied_by(mock_conversation)


class TestConversationIsResolved:
    """Tests for ConversationIsResolved specification"""
    
    def test_resolved_conversation_satisfies(self, resolved_conversation):
        """Resolved conversation satisfies"""
        spec = ConversationIsResolved()
        
        assert spec.is_satisfied_by(resolved_conversation)
    
    def test_active_conversation_not_satisfies(self, mock_conversation):
        """Active conversation does not satisfy"""
        mock_conversation.status = "active"
        spec = ConversationIsResolved()
        
        assert not spec.is_satisfied_by(mock_conversation)


class TestHasMinimumMessages:
    """Tests for HasMinimumMessages specification"""
    
    def test_enough_messages_satisfies(self, active_conversation_with_messages):
        """Conversation with enough messages satisfies"""
        spec = HasMinimumMessages(minimum=2)
        
        assert spec.is_satisfied_by(active_conversation_with_messages)
    
    def test_too_few_messages_not_satisfies(self, conversation_without_agent):
        """Conversation with too few messages does not satisfy"""
        spec = HasMinimumMessages(minimum=2)
        
        assert not spec.is_satisfied_by(conversation_without_agent)
        reason = spec.reason_not_satisfied(conversation_without_agent)
        assert "1 messages" in reason
        assert "needs at least 2" in reason
    
    def test_custom_minimum(self, mock_conversation):
        """Custom minimum value works"""
        from tests.unit.domain.conftest import MockMessage
        
        mock_conversation.messages = [
            MockMessage(),
            MockMessage(),
            MockMessage(),
        ]
        
        spec_2 = HasMinimumMessages(minimum=2)
        spec_5 = HasMinimumMessages(minimum=5)
        
        assert spec_2.is_satisfied_by(mock_conversation)
        assert not spec_5.is_satisfied_by(mock_conversation)


class TestHasAgentInteraction:
    """Tests for HasAgentInteraction specification"""
    
    def test_with_agent_message_satisfies(self, active_conversation_with_messages):
        """Conversation with agent message satisfies"""
        spec = HasAgentInteraction()
        
        assert spec.is_satisfied_by(active_conversation_with_messages)
    
    def test_without_agent_message_not_satisfies(self, conversation_without_agent):
        """Conversation without agent message does not satisfy"""
        spec = HasAgentInteraction()
        
        assert not spec.is_satisfied_by(conversation_without_agent)
        reason = spec.reason_not_satisfied(conversation_without_agent)
        assert "no agent responses" in reason.lower()
    
    def test_multiple_user_messages_no_agent(self, mock_conversation):
        """Multiple user messages but no agent still fails"""
        from tests.unit.domain.conftest import MockMessage
        
        mock_conversation.messages = [
            MockMessage(role="user"),
            MockMessage(role="user"),
            MockMessage(role="user"),
        ]
        spec = HasAgentInteraction()
        
        assert not spec.is_satisfied_by(mock_conversation)


class TestHasValidSentiment:
    """Tests for HasValidSentiment specification"""
    
    @pytest.mark.parametrize("sentiment", [-1.0, -0.5, 0.0, 0.5, 1.0])
    def test_valid_sentiment_satisfies(self, mock_conversation, sentiment):
        """Valid sentiment values satisfy"""
        mock_conversation.sentiment_avg = sentiment
        spec = HasValidSentiment()
        
        assert spec.is_satisfied_by(mock_conversation)
    
    def test_none_sentiment_satisfies(self, mock_conversation):
        """None sentiment (no data yet) satisfies"""
        mock_conversation.sentiment_avg = None
        spec = HasValidSentiment()
        
        assert spec.is_satisfied_by(mock_conversation)
    
    @pytest.mark.parametrize("sentiment", [-1.5, 1.5, 2.0, -2.0])
    def test_invalid_sentiment_not_satisfies(self, mock_conversation, sentiment):
        """Invalid sentiment values do not satisfy"""
        mock_conversation.sentiment_avg = sentiment
        spec = HasValidSentiment()
        
        assert not spec.is_satisfied_by(mock_conversation)
        reason = spec.reason_not_satisfied(mock_conversation)
        assert "outside valid range" in reason


class TestIsWithinMaxTurns:
    """Tests for IsWithinMaxTurns specification"""
    
    def test_within_limit_satisfies(self, active_conversation_with_messages):
        """Conversation within limit satisfies"""
        spec = IsWithinMaxTurns(max_turns=50)
        
        assert spec.is_satisfied_by(active_conversation_with_messages)
    
    def test_exceeds_limit_not_satisfies(self, mock_conversation):
        """Conversation exceeding limit does not satisfy"""
        from tests.unit.domain.conftest import MockMessage
        
        # Create conversation with 11 messages
        mock_conversation.messages = [MockMessage() for _ in range(11)]
        spec = IsWithinMaxTurns(max_turns=10)
        
        assert not spec.is_satisfied_by(mock_conversation)
        reason = spec.reason_not_satisfied(mock_conversation)
        assert "11 messages" in reason
        assert "exceeds maximum of 10" in reason


class TestCanResolveConversation:
    """Tests for CanResolveConversation composite specification"""
    
    def test_valid_conversation_can_resolve(self, active_conversation_with_messages):
        """Active conversation with messages can be resolved"""
        spec = CanResolveConversation()
        
        assert spec.is_satisfied_by(active_conversation_with_messages)
    
    def test_resolved_conversation_cannot_resolve(self, resolved_conversation):
        """Already resolved conversation cannot be resolved again"""
        spec = CanResolveConversation()
        
        assert not spec.is_satisfied_by(resolved_conversation)
        reason = spec.reason_not_satisfied(resolved_conversation)
        assert "resolved" in reason.lower()
    
    def test_conversation_without_agent_cannot_resolve(self, conversation_without_agent):
        """Conversation without agent response cannot be resolved"""
        spec = CanResolveConversation()
        
        assert not spec.is_satisfied_by(conversation_without_agent)
        reason = spec.reason_not_satisfied(conversation_without_agent)
        assert "no agent responses" in reason.lower()
    
    def test_conversation_with_one_message_cannot_resolve(self, mock_conversation):
        """Conversation with only one message cannot be resolved"""
        from tests.unit.domain.conftest import MockMessage
        
        mock_conversation.status = "active"
        mock_conversation.messages = [MockMessage(role="user")]
        spec = CanResolveConversation()
        
        assert not spec.is_satisfied_by(mock_conversation)


class TestCanEscalateConversation:
    """Tests for CanEscalateConversation composite specification"""
    
    def test_active_conversation_can_escalate(self, active_conversation_with_messages):
        """Active conversation can be escalated"""
        spec = CanEscalateConversation()
        
        assert spec.is_satisfied_by(active_conversation_with_messages)
    
    def test_escalated_conversation_cannot_escalate(self, escalated_conversation):
        """Already escalated conversation cannot be escalated again"""
        spec = CanEscalateConversation()
        
        assert not spec.is_satisfied_by(escalated_conversation)
    
    def test_resolved_conversation_cannot_escalate(self, resolved_conversation):
        """Resolved conversation cannot be escalated"""
        spec = CanEscalateConversation()
        
        assert not spec.is_satisfied_by(resolved_conversation)


class TestCanReopenConversation:
    """Tests for CanReopenConversation composite specification"""
    
    def test_resolved_conversation_can_reopen(self, resolved_conversation):
        """Resolved conversation can be reopened"""
        spec = CanReopenConversation()
        
        assert spec.is_satisfied_by(resolved_conversation)
    
    def test_escalated_conversation_can_reopen(self, escalated_conversation):
        """Escalated conversation can be reopened"""
        spec = CanReopenConversation()
        
        assert spec.is_satisfied_by(escalated_conversation)
    
    def test_active_conversation_cannot_reopen(self, active_conversation_with_messages):
        """Active conversation cannot be reopened"""
        spec = CanReopenConversation()
        
        assert not spec.is_satisfied_by(active_conversation_with_messages)


class TestSpecificationComposition:
    """Tests for specification composition (AND, OR, NOT)"""
    
    def test_and_composition(self, active_conversation_with_messages):
        """AND composition works correctly"""
        spec = ConversationIsActive().and_(HasAgentInteraction())
        
        assert spec.is_satisfied_by(active_conversation_with_messages)
    
    def test_and_composition_fails_if_one_fails(self, conversation_without_agent):
        """AND composition fails if any part fails"""
        spec = ConversationIsActive().and_(HasAgentInteraction())
        
        assert not spec.is_satisfied_by(conversation_without_agent)
    
    def test_or_composition(self, resolved_conversation):
        """OR composition works correctly"""
        spec = ConversationIsResolved().or_(ConversationIsEscalated())
        
        assert spec.is_satisfied_by(resolved_conversation)
    
    def test_not_composition(self, active_conversation_with_messages):
        """NOT composition works correctly"""
        spec = ConversationIsResolved().not_()
        
        assert spec.is_satisfied_by(active_conversation_with_messages)
    
    def test_complex_composition(self, active_conversation_with_messages):
        """Complex composition with multiple operators"""
        spec = (
            ConversationIsActive()
            .and_(HasMinimumMessages(2))
            .and_(HasAgentInteraction())
        )
        
        assert spec.is_satisfied_by(active_conversation_with_messages)