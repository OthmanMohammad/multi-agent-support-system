"""
Tests for Conversation Domain Validators

These tests verify pure validation functions with no side effects.
No mocking needed - just input/output testing.
"""
import pytest
from services.domain.conversation.validators import ConversationValidators


class TestValidateMessage:
    """Tests for message validation"""
    
    def test_valid_message(self):
        """Valid message passes validation"""
        result = ConversationValidators.validate_message("Hello, I need help")
        
        assert result.is_success
    
    def test_empty_message_fails(self):
        """Empty message fails validation"""
        result = ConversationValidators.validate_message("")
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert "empty" in result.error.message.lower()
        assert result.error.details["field"] == "message"
    
    def test_whitespace_only_message_fails(self):
        """Whitespace-only message fails validation"""
        result = ConversationValidators.validate_message("   \n  \t  ")
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
    
    def test_message_too_long_fails(self):
        """Message exceeding max length fails"""
        long_message = "x" * 10001  # Over 10000 limit
        result = ConversationValidators.validate_message(long_message)
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert "too long" in result.error.message.lower()
        assert result.error.details["field"] == "message"
    
    def test_message_at_max_length_passes(self):
        """Message at exactly max length passes"""
        max_message = "x" * 10000
        result = ConversationValidators.validate_message(max_message)
        
        assert result.is_success
    
    def test_message_with_special_characters_passes(self):
        """Message with special characters passes"""
        result = ConversationValidators.validate_message(
            "Hello! How are you? 你好 🎉 @#$%"
        )
        
        assert result.is_success


class TestValidateSentiment:
    """Tests for sentiment validation"""
    
    @pytest.mark.parametrize("sentiment", [
        -1.0,  # Min valid
        -0.5,  # Negative
        0.0,   # Neutral
        0.5,   # Positive
        1.0,   # Max valid
    ])
    def test_valid_sentiment_range(self, sentiment):
        """Valid sentiment values pass"""
        result = ConversationValidators.validate_sentiment(sentiment)
        
        assert result.is_success
    
    @pytest.mark.parametrize("sentiment", [
        -1.1,   # Below min
        -2.0,   # Way below
        1.1,    # Above max
        2.0,    # Way above
        float('inf'),  # Infinity
    ])
    def test_invalid_sentiment_range(self, sentiment):
        """Invalid sentiment values fail"""
        result = ConversationValidators.validate_sentiment(sentiment)
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert "between -1 and 1" in result.error.message.lower()
    
    def test_sentiment_boundary_values(self):
        """Boundary values are handled correctly"""
        # Exactly at boundaries should pass
        assert ConversationValidators.validate_sentiment(-1.0).is_success
        assert ConversationValidators.validate_sentiment(1.0).is_success
        
        # Just outside boundaries should fail
        assert ConversationValidators.validate_sentiment(-1.0001).is_failure
        assert ConversationValidators.validate_sentiment(1.0001).is_failure


class TestValidateConfidence:
    """Tests for confidence validation"""
    
    @pytest.mark.parametrize("confidence", [
        0.0,   # Min valid
        0.25,
        0.5,
        0.75,
        1.0,   # Max valid
    ])
    def test_valid_confidence_range(self, confidence):
        """Valid confidence values pass"""
        result = ConversationValidators.validate_confidence(confidence)
        
        assert result.is_success
    
    @pytest.mark.parametrize("confidence", [
        -0.1,   # Below min
        -1.0,   # Negative
        1.1,    # Above max
        2.0,    # Way above
        float('inf'),
    ])
    def test_invalid_confidence_range(self, confidence):
        """Invalid confidence values fail"""
        result = ConversationValidators.validate_confidence(confidence)
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert "between 0 and 1" in result.error.message.lower()


class TestValidateStatus:
    """Tests for status validation"""
    
    @pytest.mark.parametrize("status", [
        "active",
        "resolved",
        "escalated",
    ])
    def test_valid_status_values(self, status):
        """Valid status values pass"""
        result = ConversationValidators.validate_status(status)
        
        assert result.is_success
    
    @pytest.mark.parametrize("status", [
        "pending",
        "closed",
        "archived",
        "ACTIVE",  # Wrong case
        "",
        "invalid",
    ])
    def test_invalid_status_values(self, status):
        """Invalid status values fail"""
        result = ConversationValidators.validate_status(status)
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"
        assert "must be one of" in result.error.message.lower()


class TestValidateUrgency:
    """Tests for urgency validation"""
    
    @pytest.mark.parametrize("urgency", [
        "low",
        "medium",
        "high",
        "critical",
        "Low",      # Case insensitive
        "CRITICAL", # Case insensitive
    ])
    def test_valid_urgency_values(self, urgency):
        """Valid urgency values pass"""
        result = ConversationValidators.validate_urgency(urgency)
        
        assert result.is_success
    
    @pytest.mark.parametrize("urgency", [
        "urgent",
        "normal",
        "",
        "invalid",
    ])
    def test_invalid_urgency_values(self, urgency):
        """Invalid urgency values fail"""
        result = ConversationValidators.validate_urgency(urgency)
        
        assert result.is_failure
        assert result.error.code == "VALIDATION_ERROR"