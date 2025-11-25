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
from src.database.schemas.conversation import ConversationWithMessages, ConversationInDB
from src.database.schemas.message import MessageInDB
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
        self._event_bus = None  # Lazy initialization
        self.logger = get_logger(__name__)

        self.logger.debug("conversation_application_service_initialized")

    @property
    def event_bus(self):
        """Lazy-load event bus to allow test mocking"""
        if self._event_bus is None:
            self._event_bus = get_event_bus()
        return self._event_bus

    @event_bus.setter
    def event_bus(self, value):
        """Allow direct setting for tests"""
        self._event_bus = value
    
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

            # Check rate limits - DISABLED FOR DEVELOPMENT
            # TODO: Re-enable rate limiting in production
            # can_create = self.domain.validate_conversation_creation(
            #     customer_plan=customer.plan,
            #     today_conversation_count=today_count,
            #     customer_blocked=customer.extra_metadata.get("blocked", False) if customer.extra_metadata else False
            # )
            #
            # if can_create.is_failure:
            #     self.logger.warning(
            #         "conversation_creation_rate_limit_exceeded",
            #         customer_id=str(customer.id),
            #         today_count=today_count,
            #         plan=customer.plan
            #     )
            #     return Result.fail(can_create.error)

            self.logger.info(
                "conversation_creation_rate_limit_check_disabled",
                customer_id=str(customer.id),
                today_count=today_count,
                note="Rate limiting disabled for development"
            )
            
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
            agent_suggested_status = agent_result.get("status", "active")
            escalation_reason = agent_result.get("escalation_reason")
            should_escalate = agent_result.get("should_escalate", False)

            self.logger.info(
                "workflow_completed",
                conversation_id=str(conversation.id),
                agent_suggested_status=agent_suggested_status,
                intent=intent,
                confidence=round(confidence, 2),
                agent_path=agent_path
            )

            # Save agent response
            agent_name = agent_path[-1] if agent_path else "router"
            agent_message = await self.uow.messages.create_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                agent_name=agent_name,
                intent=intent,
                sentiment=sentiment,
                confidence=confidence,
                created_by=self.uow.current_user_id
            )

            # Determine actual status using business rules:
            # 1. Agents CANNOT auto-resolve conversations - user must explicitly resolve
            # 2. Agents CAN escalate if they flag should_escalate or have low confidence
            # 3. Default is to keep conversation active for user to continue
            final_status = "active"  # Default: keep conversation active

            # Check for legitimate escalation conditions
            should_actually_escalate = (
                should_escalate or
                agent_suggested_status == "escalated" or
                (confidence < 0.4 and escalation_reason) or  # Low confidence with reason
                sentiment < -0.7  # Very negative sentiment
            )

            if should_actually_escalate:
                final_status = "escalated"
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
                    reason=escalation_reason or "Low confidence or negative sentiment"
                )

                event = self.domain.create_conversation_escalated_event(
                    conversation_id=conversation.id,
                    customer_id=customer.id,
                    priority=priority,
                    reason=escalation_reason or "Low confidence or negative sentiment",
                    agents_involved=agent_path
                )
                self.event_bus.publish(event)
            else:
                # Keep conversation active - update with metadata only
                await self.uow.conversations.update(
                    conversation.id,
                    primary_intent=intent,
                    agents_involved=agent_path,
                    sentiment_avg=sentiment,
                    kb_articles_used=kb_articles,
                    status="active",  # Always keep active - user resolves when satisfied
                    updated_by=self.uow.current_user_id
                )
            
            # Track analytics
            if self.analytics_service and agent_name:
                await self.analytics_service.track_agent_interaction(
                    agent_name=agent_name,
                    success=(final_status == "active"),  # Success if not escalated
                    confidence=confidence
                )

            self.logger.info(
                "conversation_created",
                conversation_id=str(conversation.id),
                customer_id=str(customer.id),
                status=final_status,
                agent_suggested_status=agent_suggested_status,
                intent=intent,
                note="Agent status ignored; conversation kept active unless escalation triggered"
            )

            return Result.ok({
                "conversation_id": conversation.id,
                "message_id": agent_message.id,
                "response": response_text,
                "agent_name": agent_name,
                "confidence": confidence,
                "created_at": agent_message.created_at,
                # Additional metadata (not in ChatResponse but useful for logging)
                "customer_id": str(customer.id),
                "intent": intent,
                "sentiment": sentiment,
                "agent_path": agent_path,
                "kb_articles_used": kb_articles,
                "status": final_status
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
            agent_suggested_status = agent_result.get("status", "active")
            escalation_reason = agent_result.get("escalation_reason")
            should_escalate = agent_result.get("should_escalate", False)

            agent_name = agent_path[-1] if agent_path else "router"
            agent_message = await self.uow.messages.create_message(
                conversation_id=conversation.id,
                role="assistant",
                content=response_text,
                agent_name=agent_name,
                intent=intent,
                sentiment=sentiment,
                confidence=confidence,
                created_by=self.uow.current_user_id
            )

            # Determine actual status using business rules:
            # 1. Agents CANNOT auto-resolve conversations - user must explicitly resolve
            # 2. Agents CAN escalate if they flag should_escalate or have low confidence
            # 3. Default is to keep conversation active for user to continue
            final_status = "active"  # Default: keep conversation active

            # Check for legitimate escalation conditions
            should_actually_escalate = (
                should_escalate or
                agent_suggested_status == "escalated" or
                (confidence < 0.4 and escalation_reason) or  # Low confidence with reason
                sentiment < -0.7  # Very negative sentiment
            )

            if should_actually_escalate:
                final_status = "escalated"
                await self.uow.conversations.mark_escalated(conversation.id)

                # Get customer for priority calculation
                customer_result = await self.customer_service.get_by_id(
                    conversation.customer_id
                )
                if customer_result.is_success:
                    customer = customer_result.value
                    priority = self.domain.determine_escalation_priority(
                        customer_plan=customer.plan,
                        urgency="high",
                        sentiment_avg=sentiment,
                        annual_value=customer.extra_metadata.get("annual_value", 0) if customer.extra_metadata else 0
                    )

                    self.logger.warning(
                        "conversation_escalated_in_add_message",
                        conversation_id=str(conversation.id),
                        priority=priority,
                        reason=escalation_reason or "Low confidence or negative sentiment",
                        confidence=confidence,
                        sentiment=sentiment
                    )

                    event = self.domain.create_conversation_escalated_event(
                        conversation_id=conversation.id,
                        customer_id=conversation.customer_id,
                        priority=priority,
                        reason=escalation_reason or "Low confidence or negative sentiment",
                        agents_involved=agent_path
                    )
                    self.event_bus.publish(event)
            else:
                # Keep conversation active - user can resolve when satisfied
                await self.uow.conversations.update(
                    conversation.id,
                    status="active",
                    sentiment_avg=sentiment,
                    updated_by=self.uow.current_user_id
                )

            self.logger.info(
                "message_added",
                conversation_id=str(conversation.id),
                status=final_status,
                agent_suggested_status=agent_suggested_status,
                agent=agent_name,
                note="Agent status ignored; conversation kept active unless escalation triggered"
            )

            return Result.ok({
                "conversation_id": conversation.id,
                "message_id": agent_message.id,
                "response": response_text,
                "agent_name": agent_name,
                "confidence": confidence,
                "created_at": agent_message.created_at,
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
    ) -> Result[ConversationWithMessages]:
        """Get conversation with messages

        Returns:
            Result containing ConversationWithMessages schema object
        """
        try:
            self.logger.debug(
                "get_conversation_requested",
                conversation_id=str(conversation_id)
            )

            # Get conversation with messages from repository
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

            # Convert SQLAlchemy model to Pydantic schema
            # Pydantic handles UUID -> UUID and datetime -> datetime conversion
            conversation_schema = ConversationWithMessages.model_validate(conversation)

            return Result.ok(conversation_schema)

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
    
    async def reopen_conversation(
        self,
        conversation_id: UUID
    ) -> Result[None]:
        """Reopen a resolved or escalated conversation"""
        try:
            self.logger.info(
                "reopen_conversation_started",
                conversation_id=str(conversation_id)
            )

            conversation = await self.uow.conversations.get_by_id(conversation_id)

            if not conversation:
                return Result.fail(NotFoundError(
                    resource="Conversation",
                    identifier=str(conversation_id)
                ))

            if conversation.status == "active":
                return Result.fail(BusinessRuleError(
                    message="Conversation is already active",
                    rule="conversation_not_closed",
                    entity="Conversation"
                ))

            # Update status to active
            await self.uow.conversations.update(
                conversation.id,
                status="active",
                updated_by=self.uow.current_user_id
            )

            self.logger.info(
                "conversation_reopened",
                conversation_id=str(conversation_id),
                previous_status=conversation.status
            )

            return Result.ok(None)

        except Exception as e:
            self.logger.error(
                "reopen_conversation_failed",
                conversation_id=str(conversation_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to reopen conversation: {str(e)}",
                operation="reopen_conversation",
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
    ) -> Result[list[ConversationInDB]]:
        """List conversations with filters

        Returns:
            Result containing list of ConversationInDB schema objects
        """
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

            # Convert SQLAlchemy models to Pydantic schemas
            conversation_schemas = [
                ConversationInDB.model_validate(conv)
                for conv in conversations
            ]

            self.logger.info(
                "conversations_listed",
                count=len(conversation_schemas),
                customer_email=customer_email,
                status=status
            )

            return Result.ok(conversation_schemas)

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

    async def delete_conversation(
        self,
        conversation_id: UUID
    ) -> Result[None]:
        """Delete a conversation and its messages"""
        try:
            self.logger.info(
                "delete_conversation_started",
                conversation_id=str(conversation_id)
            )

            # Check if conversation exists
            conversation = await self.uow.conversations.get_by_id(conversation_id)
            if not conversation:
                return Result.fail(NotFoundError(
                    resource="Conversation",
                    identifier=str(conversation_id)
                ))

            # Delete the conversation (cascade will delete messages)
            deleted = await self.uow.conversations.delete(conversation_id)

            if not deleted:
                return Result.fail(InternalError(
                    message="Failed to delete conversation",
                    operation="delete_conversation",
                    component="ConversationApplicationService"
                ))

            self.logger.info(
                "conversation_deleted",
                conversation_id=str(conversation_id)
            )

            return Result.ok(None)

        except Exception as e:
            self.logger.error(
                "delete_conversation_failed",
                conversation_id=str(conversation_id),
                error=str(e),
                exc_info=True
            )
            return Result.fail(InternalError(
                message=f"Failed to delete conversation: {str(e)}",
                operation="delete_conversation",
                component="ConversationApplicationService"
            ))