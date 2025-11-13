"""
Conversation Domain Validators - Pure validation functions
These validators contain NO business logic, just input validation.
They are static helpers used by the domain service.
"""
from typing import Optional
from src.core.result import Result
from src.core.errors import ValidationError
class ConversationValidators:
    """Pure validation functions for conversation domain"""
    @staticmethod
    def validate_message(message: str) -> Result[None]:
        """
        Validate message format and length
        
        Pure function - just validates a string
        
        Args:
            message: Message content
            
        Returns:
            Result with None on success, error on failure
        """
        if not message or not message.strip():
            return Result.fail(ValidationError(
                message="Message cannot be empty",
                field="message",
                constraint="not_empty"
            ))
        
        if len(message) > 10000:
            return Result.fail(ValidationError(
                message="Message too long (max 10000 characters)",
                field="message",
                value=f"{len(message)} characters",
                constraint="max_length"
            ))
        
        return Result.ok(None)

    @staticmethod
    def validate_sentiment(sentiment: float) -> Result[None]:
        """
        Validate sentiment is in valid range [-1, 1]
        
        Args:
            sentiment: Sentiment score
            
        Returns:
            Result with None if valid, error otherwise
        """
        if sentiment < -1.0 or sentiment > 1.0:
            return Result.fail(ValidationError(
                message=f"Sentiment must be between -1 and 1, got {sentiment}",
                field="sentiment",
                value=sentiment,
                constraint="range"
            ))
        return Result.ok(None)

    @staticmethod
    def validate_confidence(confidence: float) -> Result[None]:
        """
        Validate confidence is in valid range [0, 1]
        
        Args:
            confidence: Confidence score
            
        Returns:
            Result with None if valid, error otherwise
        """
        if confidence < 0.0 or confidence > 1.0:
            return Result.fail(ValidationError(
                message=f"Confidence must be between 0 and 1, got {confidence}",
                field="confidence",
                value=confidence,
                constraint="range"
            ))
        return Result.ok(None)

    @staticmethod
    def validate_status(status: str) -> Result[None]:
        """
        Validate conversation status is valid
        
        Args:
            status: Conversation status
            
        Returns:
            Result with None if valid, error otherwise
        """
        valid_statuses = ["active", "resolved", "escalated"]
        
        if status not in valid_statuses:
            return Result.fail(ValidationError(
                message=f"Status must be one of {valid_statuses}, got '{status}'",
                field="status",
                value=status,
                constraint="valid_enum"
            ))
        
        return Result.ok(None)

    @staticmethod
    def validate_urgency(urgency: str) -> Result[None]:
        """
        Validate urgency level is valid
        
        Args:
            urgency: Urgency level
            
        Returns:
            Result with None if valid, error otherwise
        """
        valid_urgencies = ["low", "medium", "high", "critical"]
        
        if urgency.lower() not in valid_urgencies:
            return Result.fail(ValidationError(
                message=f"Urgency must be one of {valid_urgencies}, got '{urgency}'",
                field="urgency",
                value=urgency,
                constraint="valid_enum"
            ))
        
        return Result.ok(None)