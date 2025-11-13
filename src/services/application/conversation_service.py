"""
Conversation Application Service - Orchestrates conversation use cases

"""

from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timezone

from src.core.result import Result, Error
from src.core.errors import ValidationError, BusinessRuleError, NotFoundError, InternalError
from src.core.events import get_event_bus
from src.database.unit_of_work import UnitOfWork
from src.services.domain.conversation.domain_service import ConversationDomainService
from src.services.infrastructure.customer_service import CustomerInfrastructureService
from src.services.infrastructure.analytics_service import AnalyticsService
from src.workflow.engine import AgentWorkflowEngine
from src.utils.logging.setup import get_logger


class ConversationApplicationService:
    """
    Application service for conversation use cases
    
    """
    
    def __init__(
        self,
        uow: UnitOfWork,
        domain_service: ConversationDomainService,
        customer_service: CustomerInfrastructureService,
        workflow_engine: AgentWorkflowEngine,
        analytics_service: Optional[AnalyticsService] = None
    ):
        self.uow = uow
        self.domain = domain_service
        self.customer_service = customer_service
        self.workflow_engine = workflow_engine
        self.analytics_service = analytics_service
        self.event_bus = get_event_bus()
        self.logger = get_logger(__name__)
        
        self.logger.debug("conversation_application_service_initialized")
    
    async def create_conversation(
        self,
        customer_email: str,
        message: str
    ) -> Result[Dict[str, Any]]:
        """Create a new conversation with initial message"""
        try:
            self.logger.info(
                "conversation_creation_started",
                customer_email=customer_email,
                message_length=len(message)
            )
            
            # Validate message
            validation_result = self.domain.validate_message(message)
            if validation_result.is_failure:
                self.logger.warning(
                    "conversation_creation_validation_failed",
                    customer_email=customer_email,
                    error="invalid_message"
                )
                return Result.fail(validation_result.error)
            
            # Get/create customer
            customer_result = await self.customer_service.get_or_create_by_email(
                customer_email
            )
            if customer_result.is_failure:
                return Result.fail(customer_result.error)
            
            customer = customer_result.value
            
            self.logger.debug(
                "customer_retrieved",
                customer_id=str(customer.id),
                customer_plan=customer.plan
            )
            
            # Get today's conversation count
            count_result = await self.customer_service.get_conversation_count_for_date(
                customer.id,
                datetime.now(timezone.utc)
            )
            if count_result.is_failure:
                return Result.fail(count_result.error)
            
            today_count = count_result.value
            
            # Check rate limits
            can_create = self.domain.validate_conversation_creation(
                customer_plan=customer.plan,
                today_conversation_count=today_count,
                customer_blocked=customer.extra_metadata.get("blocked", False) if customer.extra_metadata else False
            )
            
            if can_create.is_failure:
                self.logger.warning(
                    "conversation_creation_rate_limit_exceeded",
                    customer_id=str(customer.id),
                    today_count=today_count,
                    plan=customer.plan
                )
                return Result.fail(can_create.error)
            
            # Create conversation
            conversation = await self.uow.conversations.create_with_customer(
                customer_id=customer.id,
                status="active",
                created_by=self.uow.current_user_id
            )
            
            self.logger.debug(
                "conversation_created_in_db",
                conversation_id=str(conversation.id),
                customer_id=str(customer.id)
            )
            
            # Save user message
            await self.uow.messages.create_message(
                conversation_id=conversation.id,
                role="user",
                content=message,
                created_by=self.uow.current_user_id
            )
            
            # Run through workflow
            self.logger.info(
                "workflow_execution_starting",
                conversation_id=str(conversation.id),
                customer_id=str(customer.id)
            )
            
            agent_result = await self.workflow_engine.execute(
                message=message,
                context={
                    "conversation_id": str(conversation.id),
                    "customer_id": str(customer.id),
                    "customer_metadata": {
                        "plan": customer.plan,
                        "email": customer.email
                    }
                }
            )
            
            # Extract agent response data
            response_text = agent_result.get("agent_response", "")
            intent = agent_result.get("primary_intent")
            confidence = agent_result.get("intent_confidence", 0.0)
            sentiment = agent_result.get("sentiment", 0.0)
            agent_path = agent_result.get("agent_history", [])
            kb_articles = agent_result.get("kb_articles_used", [])
            status = agent_result.get("status", "active")
            
            self.logger.info(
                "workflow_completed",
                conversation_id=str(conversation.id),
                status=status,
                intent=intent,
                confidence=round(confidence, 2),
                agent_path=agent_path
            )
            
            # Save agent response
            agent_name = agent_path[-1] if agent_path else "router"
            await self.uow.messages.create_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                agent_name=agent_name,
                intent=intent,
                sentiment=sentiment,
                confidence=confidence,
                created_by=self.uow.current_user_id
            )
            
            # Update conversation metadata
            await self.uow.conversations.update(
                conversation.id,
                primary_intent=intent,
                agents_involved=agent_path,
                sentiment_avg=sentiment,
                kb_articles_used=kb_articles,
                status=status,
                updated_by=self.uow.current_user_id
            )
            
            # Handle resolution or escalation
            if status == "resolved":
                resolution_time = self.domain.calculate_resolution_time(
                    conversation.started_at,
                    datetime.now(timezone.utc)
                )
                await self.uow.conversations.mark_resolved(
                    conversation.id,
                    resolution_time
                )
                
                self.logger.info(
                    "conversation_resolved",
                    conversation_id=str(conversation.id),
                    resolution_time_seconds=resolution_time
                )
                
                event = self.domain.create_conversation_resolved_event(
                    conversation_id=conversation.id,
                    customer_id=customer.id,
                    resolution_time_seconds=resolution_time,
                    primary_intent=intent,
                    agents_involved=agent_path,
                    sentiment_avg=sentiment
                )
                self.event_bus.publish(event)
            
            elif status == "escalated":
                await self.uow.conversations.mark_escalated(conversation.id)
                
                priority = self.domain.determine_escalation_priority(
                    customer_plan=customer.plan,
                    urgency="high",
                    sentiment_avg=sentiment,
                    annual_value=customer.extra_metadata.get("annual_value", 0) if customer.extra_metadata else 0
                )
                
                self.logger.warning(
                    "conversation_escalated",
                    conversation_id=str(conversation.id),
                    priority=priority,
                    reason=agent_result.get("escalation_reason", "Low confidence")
                )
                
                event = self.domain.create_conversation_escalated_event(
                    conversation_id=conversation.id,
                    customer_id=customer.id,
                    priority=priority,
                    reason=agent_result.get("escalation_reason", "Low confidence"),
                    agents_involved=agent_path
                )
                self.event_bus.publish(event)
            
            # Track analytics
            if self.analytics_service and agent_name:
                await self.analytics_service.track_agent_interaction(
                    agent_name=agent_name,
                    success=(status == "resolved"),
                    confidence=confidence
                )
            
            self.logger.info(
                "conversation_created",
                conversation_id=str(conversation.id),
                customer_id=str(customer.id),
                status=status,
                intent=intent
            )
            
            return Result.ok({
                "conversation_id": str(conversation.id),
                "customer_id": str(customer.id),
                "message": response_text,
                "intent": intent,
                "confidence": confidence,
                "sentiment": sentiment,
                "agent_path": agent_path,
                "kb_articles_used": kb_articles,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            self.logger.error(
                "conversation_creation_failed",
                customer_email=customer_email,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to create conversation: {str(e)}",
                operation="create_conversation",
                component="ConversationApplicationService"
            ))
    
    async def add_message(
        self,
        conversation_id: UUID,
        message: str
    ) -> Result[Dict[str, Any]]:
        """Add message to existing conversation"""
        try:
            self.logger.info(
                "add_message_started",
                conversation_id=str(conversation_id),
                message_length=len(message)
            )
            
            validation_result = self.domain.validate_message(message)
            if validation_result.is_failure:
                return Result.fail(validation_result.error)
            
            conversation = await self.uow.conversations.get_by_id(conversation_id)
            if not conversation:
                self.logger.warning(
                    "conversation_not_found",
                    conversation_id=str(conversation_id)
                )
                return Result.fail(NotFoundError(
                    resource="Conversation",
                    identifier=str(conversation_id)
                ))
            
            if conversation.status != "active":
                self.logger.warning(
                    "add_message_conversation_not_active",
                    conversation_id=str(conversation_id),
                    status=conversation.status
                )
                return Result.fail(BusinessRuleError(
                    message=f"Cannot add message to {conversation.status} conversation",
                    rule="conversation_must_be_active",
                    entity="Conversation"
                ))
            
            await self.uow.messages.create_message(
                conversation_id=conversation.id,
                role="user",
                content=message,
                created_by=self.uow.current_user_id
            )
            
            agent_result = await self.workflow_engine.execute(
                message=message,
                context={
                    "conversation_id": str(conversation.id),
                    "customer_id": str(conversation.customer_id)
                }
            )
            
            response_text = agent_result.get("agent_response", "")
            intent = agent_result.get("primary_intent")
            confidence = agent_result.get("intent_confidence", 0.0)
            sentiment = agent_result.get("sentiment", 0.0)
            agent_path = agent_result.get("agent_history", [])
            status = agent_result.get("status", "active")
            
            agent_name = agent_path[-1] if agent_path else "router"
            await self.uow.messages.create_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                agent_name=agent_name,
                intent=intent,
                sentiment=sentiment,
                confidence=confidence,
                created_by=self.uow.current_user_id
            )
            
            await self.uow.conversations.update(
                conversation.id,
                status=status,
                sentiment_avg=sentiment,
                updated_by=self.uow.current_user_id
            )
            
            self.logger.info(
                "message_added",
                conversation_id=str(conversation.id),
                status=status,
                agent=agent_name
            )
            
            return Result.ok({
                "conversation_id": str(conversation.id),
                "message": response_text,
                "intent": intent,
                "confidence": confidence,
                "sentiment": sentiment,
                "agent_path": agent_path,
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        except Exception as e:
            self.logger.error(
                "add_message_failed",
                conversation_id=str(conversation_id),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to add message: {str(e)}",
                operation="add_message",
                component="ConversationApplicationService"
            ))
    
    async def get_conversation(
        self,
        conversation_id: UUID
    ) -> Result[Dict[str, Any]]:
        """Get conversation with messages"""
        try:
            self.logger.debug(
                "get_conversation_requested",
                conversation_id=str(conversation_id)
            )
            
            conversation = await self.uow.conversations.get_with_messages(
                conversation_id
            )
            
            if not conversation:
                return Result.fail(NotFoundError(
                    resource="Conversation",
                    identifier=str(conversation_id)
                ))
            
            self.logger.debug(
                "conversation_retrieved",
                conversation_id=str(conversation_id),
                message_count=len(conversation.messages)
            )
            
            return Result.ok({
                "conversation_id": str(conversation.id),
                "customer_id": str(conversation.customer_id),
                "status": conversation.status,
                "started_at": conversation.started_at.isoformat(),
                "last_updated": conversation.updated_at.isoformat() if conversation.updated_at else conversation.started_at.isoformat(),
                "messages": [
                    {
                        "role": msg.role,
                        "content": msg.content,
                        "agent_name": msg.agent_name,
                        "timestamp": msg.created_at.isoformat()
                    }
                    for msg in conversation.messages
                ],
                "agent_history": conversation.agents_involved or [],
                "primary_intent": conversation.primary_intent
            })
            
        except Exception as e:
            self.logger.error(
                "get_conversation_failed",
                conversation_id=str(conversation_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to fetch conversation: {str(e)}",
                operation="get_conversation",
                component="ConversationApplicationService"
            ))
    
    async def resolve_conversation(
        self,
        conversation_id: UUID
    ) -> Result[None]:
        """Mark conversation as resolved"""
        try:
            self.logger.info(
                "resolve_conversation_started",
                conversation_id=str(conversation_id)
            )
            
            conversation = await self.uow.conversations.get_by_id(conversation_id)
            
            if not conversation:
                return Result.fail(NotFoundError(
                    resource="Conversation",
                    identifier=str(conversation_id)
                ))
            
            can_resolve = self.domain.can_resolve(conversation)
            if can_resolve.is_failure:
                return Result.fail(can_resolve.error)
            
            resolution_time = self.domain.calculate_resolution_time(
                conversation.started_at,
                datetime.now(timezone.utc)
            )
            
            await self.uow.conversations.mark_resolved(
                conversation.id,
                resolution_time
            )
            
            event = self.domain.create_conversation_resolved_event(
                conversation_id=conversation.id,
                customer_id=conversation.customer_id,
                resolution_time_seconds=resolution_time,
                primary_intent=conversation.primary_intent,
                agents_involved=conversation.agents_involved or [],
                sentiment_avg=conversation.sentiment_avg
            )
            self.event_bus.publish(event)
            
            self.logger.info(
                "conversation_resolved",
                conversation_id=str(conversation_id),
                resolution_time_seconds=resolution_time
            )
            
            return Result.ok(None)
            
        except Exception as e:
            self.logger.error(
                "resolve_conversation_failed",
                conversation_id=str(conversation_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to resolve conversation: {str(e)}",
                operation="resolve_conversation",
                component="ConversationApplicationService"
            ))
    
    async def escalate_conversation(
        self,
        conversation_id: UUID,
        reason: str
    ) -> Result[None]:
        """Escalate conversation to human"""
        try:
            self.logger.warning(
                "escalate_conversation_started",
                conversation_id=str(conversation_id),
                reason=reason
            )
            
            conversation = await self.uow.conversations.get_by_id(conversation_id)
            
            if not conversation:
                return Result.fail(NotFoundError(
                    resource="Conversation",
                    identifier=str(conversation_id)
                ))
            
            can_escalate = self.domain.can_escalate(conversation)
            if can_escalate.is_failure:
                return Result.fail(can_escalate.error)
            
            customer_result = await self.customer_service.get_by_id(
                conversation.customer_id
            )
            if customer_result.is_failure:
                return Result.fail(customer_result.error)
            
            customer = customer_result.value
            
            priority = self.domain.determine_escalation_priority(
                customer_plan=customer.plan,
                urgency="high",
                sentiment_avg=conversation.sentiment_avg,
                annual_value=customer.extra_metadata.get("annual_value", 0) if customer.extra_metadata else 0
            )
            
            await self.uow.conversations.mark_escalated(conversation.id)
            
            event = self.domain.create_conversation_escalated_event(
                conversation_id=conversation.id,
                customer_id=conversation.customer_id,
                priority=priority,
                reason=reason,
                agents_involved=conversation.agents_involved or []
            )
            self.event_bus.publish(event)
            
            self.logger.warning(
                "conversation_escalated",
                conversation_id=str(conversation_id),
                priority=priority,
                reason=reason
            )
            
            return Result.ok(None)
            
        except Exception as e:
            self.logger.error(
                "escalate_conversation_failed",
                conversation_id=str(conversation_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to escalate conversation: {str(e)}",
                operation="escalate_conversation",
                component="ConversationApplicationService"
            ))
    
    async def list_conversations(
        self,
        customer_email: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> Result[list]:
        """List conversations with filters"""
        try:
            self.logger.debug(
                "list_conversations_requested",
                customer_email=customer_email,
                status=status,
                limit=limit
            )
            
            conversations = []
            
            if customer_email:
                customer_result = await self.customer_service.get_by_email(
                    customer_email
                )
                if customer_result.is_failure:
                    return Result.fail(customer_result.error)
                
                customer = customer_result.value
                if customer:
                    conversations = await self.uow.conversations.get_by_customer(
                        customer.id,
                        limit=limit,
                        status=status
                    )
            else:
                conversations = await self.uow.conversations.get_all(limit=limit)
            
            if status and not customer_email:
                conversations = [c for c in conversations if c.status == status]
            
            result_list = [
                {
                    "conversation_id": str(conv.id),
                    "customer_id": str(conv.customer_id),
                    "status": conv.status,
                    "primary_intent": conv.primary_intent,
                    "started_at": conv.started_at.isoformat(),
                    "last_updated": conv.updated_at.isoformat() if conv.updated_at else conv.started_at.isoformat(),
                    "agent_history": conv.agents_involved or []
                }
                for conv in conversations
            ]
            
            self.logger.info(
                "conversations_listed",
                count=len(result_list),
                customer_email=customer_email,
                status=status
            )
            
            return Result.ok(result_list)
            
        except Exception as e:
            self.logger.error(
                "list_conversations_failed",
                customer_email=customer_email,
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to list conversations: {str(e)}",
                operation="list_conversations",
                component="ConversationApplicationService"
            ))