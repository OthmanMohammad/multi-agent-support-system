"""
Conversation Domain Service - Pure business logic, NO external dependencies

CRITICAL: This is PURE BUSINESS LOGIC
- NO database operations (pass all data as parameters)
- NO external API calls
- NO file I/O
- NO event publishing (just return event objects)
- NO reading environment variables

Responsibilities:
- Business rule validation
- Business calculations
- Domain logic that doesn't fit in entity
- Event creation (but NOT publishing)

NOT responsible for:
- Database persistence (application service)
- Transaction management (application service)
- External service calls (infrastructure service)
- Event publishing (application service)
- HTTP handling (API layer)
"""

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

from core.result import Result
from core.errors import BusinessRuleError
from services.domain.conversation.specifications import (
    CanResolveConversation,
    CanEscalateConversation,
    CanReopenConversation,
)
from services.domain.conversation.events import (
    ConversationResolvedEvent,
    ConversationEscalatedEvent,
    ConversationReopenedEvent,
    LowConfidenceDetectedEvent,
    NegativeSentimentDetectedEvent,
)
from services.domain.conversation.validators import ConversationValidators

if TYPE_CHECKING:
    from database.models import Conversation


class ConversationDomainService:
    """
    Domain service for conversation business logic
    
    All methods are PURE - same inputs always produce same outputs.
    """
    
    def __init__(self):
        """Initialize specifications"""
        self.can_resolve_spec = CanResolveConversation()
        self.can_escalate_spec = CanEscalateConversation()
        self.can_reopen_spec = CanReopenConversation()
        self.validators = ConversationValidators()
    
    # ===== Validation Methods =====
    
    def validate_message(self, message: str) -> Result[None]:
        """
        Validate message format and length
        
        Pure function - just validates a string
        """
        return self.validators.validate_message(message)
    
    def validate_conversation_creation(
        self,
        customer_plan: str,
        today_conversation_count: int,
        customer_blocked: bool
    ) -> Result[None]:
        """
        Validate business rules for creating a conversation
        
        Pure function - all data passed as parameters
        
        Business Rules:
        1. Customer cannot be blocked
        2. Customer must be within rate limit for their plan
        
        Args:
            customer_plan: Customer's plan (free, basic, premium, enterprise)
            today_conversation_count: Number of conversations created today
            customer_blocked: Whether customer is blocked
            
        Returns:
            Result with None on success, or error describing violation
        """
        # Rule 1: Customer not blocked
        if customer_blocked:
            return Result.fail(BusinessRuleError(
                message="Customer account is blocked",
                rule="customer_not_blocked",
                entity="Conversation"
            ))
        
        # Rule 2: Within rate limit
        rate_limit = self.get_rate_limit_for_plan(customer_plan)
        if rate_limit is not None and today_conversation_count >= rate_limit:
            return Result.fail(BusinessRuleError(
                message=f"Rate limit exceeded ({rate_limit} conversations/day for {customer_plan} plan)",
                rule="within_rate_limit",
                entity="Conversation"
            ))
        
        return Result.ok(None)
    
    def validate_sentiment(self, sentiment: float) -> Result[None]:
        """Validate sentiment is in valid range"""
        return self.validators.validate_sentiment(sentiment)
    
    def validate_confidence(self, confidence: float) -> Result[None]:
        """Validate confidence is in valid range"""
        return self.validators.validate_confidence(confidence)
    
    # ===== Business Rule Methods =====
    
    def get_rate_limit_for_plan(self, plan: str) -> Optional[int]:
        """
        Get rate limit for plan (business rule)
        
        Pure function - just a lookup
        
        Args:
            plan: Customer plan
            
        Returns:
            Rate limit or None for unlimited
        """
        return {
            "free": 10,      # 10 conversations/day
            "basic": 100,    # 100 conversations/day
            "premium": None, # Unlimited
            "enterprise": None  # Unlimited
        }.get(plan, 10)
    
    def can_resolve(self, conversation: 'Conversation') -> Result[None]:
        """
        Check if conversation can be resolved using specifications
        
        Pure function - just checks object state
        
        Business Rules (in specification):
        - Conversation must be active
        - Must have at least 2 messages (user + agent)
        - Must have agent interaction
        """
        if not self.can_resolve_spec.is_satisfied_by(conversation):
            reason = self.can_resolve_spec.reason_not_satisfied(conversation)
            return Result.fail(BusinessRuleError(
                message=f"Cannot resolve conversation: {reason}",
                rule="can_resolve",
                entity="Conversation"
            ))
        
        return Result.ok(None)
    
    def can_escalate(self, conversation: 'Conversation') -> Result[None]:
        """
        Check if conversation can be escalated
        
        Business Rules (in specification):
        - Conversation must be active
        - Cannot be already escalated
        """
        if not self.can_escalate_spec.is_satisfied_by(conversation):
            reason = self.can_escalate_spec.reason_not_satisfied(conversation)
            return Result.fail(BusinessRuleError(
                message=f"Cannot escalate conversation: {reason}",
                rule="can_escalate",
                entity="Conversation"
            ))
        
        return Result.ok(None)
    
    def can_reopen(self, conversation: 'Conversation') -> Result[None]:
        """
        Check if conversation can be reopened
        
        Business Rules:
        - Must be resolved or escalated (not active)
        """
        if not self.can_reopen_spec.is_satisfied_by(conversation):
            reason = self.can_reopen_spec.reason_not_satisfied(conversation)
            return Result.fail(BusinessRuleError(
                message=f"Cannot reopen conversation: {reason}",
                rule="can_reopen",
                entity="Conversation"
            ))
        
        return Result.ok(None)
    
    # ===== Calculation Methods =====
    
    def calculate_resolution_time(
        self,
        started_at: datetime,
        ended_at: Optional[datetime] = None
    ) -> int:
        """
        Calculate resolution time in seconds
        
        Pure function - just math
        
        Args:
            started_at: Conversation start time
            ended_at: Conversation end time (defaults to now)
            
        Returns:
            Resolution time in seconds
        """
        if ended_at is None:
            ended_at = datetime.utcnow()
        
        return int((ended_at - started_at).total_seconds())
    
    def determine_escalation_priority(
        self,
        customer_plan: str,
        urgency: str,
        sentiment_avg: Optional[float],
        annual_value: float
    ) -> str:
        """
        Determine escalation priority based on business rules
        
        Pure function - all calculations based on inputs
        
        Priority Calculation:
        - Customer tier (free=0, basic=1, premium=2, enterprise=3)
        - Urgency level (low=0, medium=1, high=2, critical=3)
        - Sentiment penalty (negative < -0.5: +2)
        - Account value (> $10k/year: +1)
        
        Priority Mapping:
        - Score >= 7: critical (1hr SLA)
        - Score >= 5: high (4hr SLA)
        - Score >= 3: medium (24hr SLA)
        - Score < 3: low (3 day SLA)
        
        Args:
            customer_plan: Customer's plan
            urgency: Urgency level (low/medium/high/critical)
            sentiment_avg: Average sentiment (-1 to 1)
            annual_value: Annual account value in dollars
            
        Returns:
            Priority level (low/medium/high/critical)
        """
        score = 0
        
        # Customer tier score
        tier_scores = {
            "free": 0,
            "basic": 1,
            "premium": 2,
            "enterprise": 3
        }
        score += tier_scores.get(customer_plan, 0)
        
        # Urgency score
        urgency_scores = {
            "low": 0,
            "medium": 1,
            "high": 2,
            "critical": 3
        }
        score += urgency_scores.get(urgency.lower(), 0)
        
        # Sentiment penalty
        if sentiment_avg is not None and sentiment_avg < -0.5:
            score += 2
        
        # Account value bonus
        if annual_value > 10000:
            score += 1
        
        # Map score to priority
        if score >= 7:
            return "critical"
        elif score >= 5:
            return "high"
        elif score >= 3:
            return "medium"
        else:
            return "low"
    
    def calculate_customer_satisfaction_score(
        self,
        sentiment_avg: Optional[float],
        resolution_time_seconds: Optional[int],
        agent_count: int,
        confidence_avg: Optional[float]
    ) -> Optional[float]:
        """
        Estimate customer satisfaction based on conversation metrics
        
        Pure function - just calculations
        
        Factors:
        - Sentiment average (weighted 40%)
        - Resolution time (weighted 30%)
        - Number of agent switches (weighted 20%)
        - Confidence average (weighted 10%)
        
        Args:
            sentiment_avg: Average sentiment (-1 to 1)
            resolution_time_seconds: Time to resolution
            agent_count: Number of agents involved
            confidence_avg: Average confidence (0 to 1)
            
        Returns:
            Estimated CSAT score (0-5) or None if insufficient data
        """
        if sentiment_avg is None:
            return None
        
        score = 0.0
        
        # Sentiment contribution (0-2 scale mapped to 0-4)
        sentiment_contribution = (sentiment_avg + 1) * 2  # Map -1..1 to 0..4
        score += sentiment_contribution * 0.4
        
        # Resolution time contribution
        if resolution_time_seconds is not None:
            if resolution_time_seconds < 300:  # < 5 min
                time_score = 5.0
            elif resolution_time_seconds < 900:  # < 15 min
                time_score = 4.0
            elif resolution_time_seconds < 3600:  # < 1 hour
                time_score = 3.0
            else:
                time_score = 2.0
            score += time_score * 0.3
        
        # Agent switches (fewer is better)
        if agent_count == 1:
            switch_score = 5.0
        elif agent_count == 2:
            switch_score = 4.0
        elif agent_count == 3:
            switch_score = 3.0
        else:
            switch_score = 2.0
        score += switch_score * 0.2
        
        # Confidence contribution
        if confidence_avg is not None:
            score += (confidence_avg * 5) * 0.1
        else:
            score += 4.0 * 0.1  # Assume good confidence
        
        return round(score, 1)
    
    # ===== Event Factory Methods =====
    
    def create_conversation_resolved_event(
        self,
        conversation_id: UUID,
        customer_id: UUID,
        resolution_time_seconds: int,
        primary_intent: Optional[str],
        agents_involved: list[str],
        sentiment_avg: Optional[float]
    ) -> ConversationResolvedEvent:
        """
        Create a ConversationResolvedEvent
        
        Pure function - just creates an object
        NOTE: Application service will publish this, not domain service
        """
        return ConversationResolvedEvent(
            conversation_id=conversation_id,
            customer_id=customer_id,
            resolution_time_seconds=resolution_time_seconds,
            primary_intent=primary_intent,
            agents_involved=agents_involved,
            sentiment_avg=sentiment_avg
        )
    
    def create_conversation_escalated_event(
        self,
        conversation_id: UUID,
        customer_id: UUID,
        priority: str,
        reason: str,
        agents_involved: list[str]
    ) -> ConversationEscalatedEvent:
        """
        Create a ConversationEscalatedEvent
        
        Pure function - just creates an object
        NOTE: Application service will publish this, not domain service
        """
        return ConversationEscalatedEvent(
            conversation_id=conversation_id,
            customer_id=customer_id,
            priority=priority,
            reason=reason,
            agents_involved=agents_involved
        )
    
    def create_conversation_reopened_event(
        self,
        conversation_id: UUID,
        customer_id: UUID,
        reason: str,
        previous_status: str
    ) -> ConversationReopenedEvent:
        """Create a ConversationReopenedEvent"""
        return ConversationReopenedEvent(
            conversation_id=conversation_id,
            customer_id=customer_id,
            reason=reason,
            previous_status=previous_status
        )
    
    def create_low_confidence_detected_event(
        self,
        conversation_id: UUID,
        customer_id: UUID,
        message_id: UUID,
        confidence: float,
        agent_name: str,
        threshold: float = 0.5
    ) -> LowConfidenceDetectedEvent:
        """Create a LowConfidenceDetectedEvent"""
        return LowConfidenceDetectedEvent(
            conversation_id=conversation_id,
            customer_id=customer_id,
            message_id=message_id,
            confidence=confidence,
            agent_name=agent_name,
            threshold=threshold
        )
    
    def create_negative_sentiment_detected_event(
        self,
        conversation_id: UUID,
        customer_id: UUID,
        message_id: UUID,
        sentiment: float,
        agent_name: Optional[str],
        threshold: float = -0.5
    ) -> NegativeSentimentDetectedEvent:
        """Create a NegativeSentimentDetectedEvent"""
        return NegativeSentimentDetectedEvent(
            conversation_id=conversation_id,
            customer_id=customer_id,
            message_id=message_id,
            sentiment=sentiment,
            agent_name=agent_name,
            threshold=threshold
        )