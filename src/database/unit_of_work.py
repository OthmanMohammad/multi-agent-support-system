"""
Unit of Work Pattern - Manages database transactions across repositories
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db_session
from src.database.repositories import (
    ABTestRepository,
    AgentCollaborationRepository,
    AgentHandoffRepository,
    AgentPerformanceRepository,
    APIKeyRepository,
    AuditLogRepository,
    ConversationAnalyticsRepository,
    ConversationRepository,
    ConversationTagRepository,
    CreditRepository,
    CustomerContactRepository,
    CustomerHealthEventRepository,
    CustomerIntegrationRepository,
    CustomerNoteRepository,
    CustomerRepository,
    CustomerSegmentRepository,
    DealRepository,
    EmployeeRepository,
    FeatureUsageRepository,
    InvoiceRepository,
    LeadRepository,
    MessageRepository,
    PaymentRepository,
    QuoteRepository,
    SalesActivityRepository,
    ScheduledTaskRepository,
    SubscriptionRepository,
    UsageEventRepository,
    UserRepository,
    WorkflowExecutionRepository,
    WorkflowRepository,
)


class UnitOfWork:
    """
    Unit of Work - Coordinates database operations in a single transaction

    Benefits:
    - Atomic operations (all succeed or all fail)
    - Consistent state across repositories
    - Automatic rollback on errors
    - Lazy repository initialization

    Attributes:
        session: Database session
        customers: Customer repository
        conversations: Conversation repository
        messages: Message repository
        agent_performance: Agent performance repository
    """

    def __init__(self, session: AsyncSession, current_user_id: UUID | None = None):
        """
        Initialize Unit of Work

        Args:
            session: Async database session
            current_user_id: ID of user performing operations (for audit trail)
        """
        self.session = session
        self.current_user_id = current_user_id

        # Lazy-loaded repositories - Authentication
        self._user_repo: UserRepository | None = None
        self._api_key_repo: APIKeyRepository | None = None

        # Lazy-loaded repositories - Core
        self._customer_repo: CustomerRepository | None = None
        self._conversation_repo: ConversationRepository | None = None
        self._message_repo: MessageRepository | None = None
        self._agent_performance_repo: AgentPerformanceRepository | None = None

        # Lazy-loaded repositories - Customer Health
        self._customer_health_event_repo: CustomerHealthEventRepository | None = None
        self._customer_segment_repo: CustomerSegmentRepository | None = None
        self._customer_note_repo: CustomerNoteRepository | None = None
        self._customer_contact_repo: CustomerContactRepository | None = None
        self._customer_integration_repo: CustomerIntegrationRepository | None = None

        # Lazy-loaded repositories - Subscription & Billing
        self._subscription_repo: SubscriptionRepository | None = None
        self._invoice_repo: InvoiceRepository | None = None
        self._payment_repo: PaymentRepository | None = None
        self._usage_event_repo: UsageEventRepository | None = None
        self._credit_repo: CreditRepository | None = None

        # Lazy-loaded repositories - Sales
        self._employee_repo: EmployeeRepository | None = None
        self._lead_repo: LeadRepository | None = None
        self._deal_repo: DealRepository | None = None
        self._sales_activity_repo: SalesActivityRepository | None = None
        self._quote_repo: QuoteRepository | None = None

        # Lazy-loaded repositories - Analytics
        self._conversation_analytics_repo: ConversationAnalyticsRepository | None = None
        self._feature_usage_repo: FeatureUsageRepository | None = None
        self._ab_test_repo: ABTestRepository | None = None

        # Lazy-loaded repositories - Workflow
        self._workflow_repo: WorkflowRepository | None = None
        self._workflow_execution_repo: WorkflowExecutionRepository | None = None
        self._scheduled_task_repo: ScheduledTaskRepository | None = None

        # Lazy-loaded repositories - Agent Handoff
        self._agent_handoff_repo: AgentHandoffRepository | None = None
        self._agent_collaboration_repo: AgentCollaborationRepository | None = None
        self._conversation_tag_repo: ConversationTagRepository | None = None

        # Lazy-loaded repositories - Audit
        self._audit_log_repo: AuditLogRepository | None = None

    # Authentication Repositories
    @property
    def users(self) -> UserRepository:
        """Get user repository (lazy-loaded)"""
        if self._user_repo is None:
            self._user_repo = UserRepository(self.session)
        return self._user_repo

    @property
    def api_keys(self) -> APIKeyRepository:
        """Get API key repository (lazy-loaded)"""
        if self._api_key_repo is None:
            self._api_key_repo = APIKeyRepository(self.session)
        return self._api_key_repo

    @property
    def customers(self) -> CustomerRepository:
        """Get customer repository (lazy-loaded)"""
        if self._customer_repo is None:
            self._customer_repo = CustomerRepository(self.session)
        return self._customer_repo

    @property
    def conversations(self) -> ConversationRepository:
        """Get conversation repository (lazy-loaded)"""
        if self._conversation_repo is None:
            self._conversation_repo = ConversationRepository(self.session)
        return self._conversation_repo

    @property
    def messages(self) -> MessageRepository:
        """Get message repository (lazy-loaded)"""
        if self._message_repo is None:
            self._message_repo = MessageRepository(self.session)
        return self._message_repo

    @property
    def agent_performance(self) -> AgentPerformanceRepository:
        """Get agent performance repository (lazy-loaded)"""
        if self._agent_performance_repo is None:
            self._agent_performance_repo = AgentPerformanceRepository(self.session)
        return self._agent_performance_repo

    # Customer Health Repositories
    @property
    def customer_health_events(self) -> CustomerHealthEventRepository:
        """Get customer health event repository (lazy-loaded)"""
        if self._customer_health_event_repo is None:
            self._customer_health_event_repo = CustomerHealthEventRepository(self.session)
        return self._customer_health_event_repo

    @property
    def customer_segments(self) -> CustomerSegmentRepository:
        """Get customer segment repository (lazy-loaded)"""
        if self._customer_segment_repo is None:
            self._customer_segment_repo = CustomerSegmentRepository(self.session)
        return self._customer_segment_repo

    @property
    def customer_notes(self) -> CustomerNoteRepository:
        """Get customer note repository (lazy-loaded)"""
        if self._customer_note_repo is None:
            self._customer_note_repo = CustomerNoteRepository(self.session)
        return self._customer_note_repo

    @property
    def customer_contacts(self) -> CustomerContactRepository:
        """Get customer contact repository (lazy-loaded)"""
        if self._customer_contact_repo is None:
            self._customer_contact_repo = CustomerContactRepository(self.session)
        return self._customer_contact_repo

    @property
    def customer_integrations(self) -> CustomerIntegrationRepository:
        """Get customer integration repository (lazy-loaded)"""
        if self._customer_integration_repo is None:
            self._customer_integration_repo = CustomerIntegrationRepository(self.session)
        return self._customer_integration_repo

    # Subscription & Billing Repositories
    @property
    def subscriptions(self) -> SubscriptionRepository:
        """Get subscription repository (lazy-loaded)"""
        if self._subscription_repo is None:
            self._subscription_repo = SubscriptionRepository(self.session)
        return self._subscription_repo

    @property
    def invoices(self) -> InvoiceRepository:
        """Get invoice repository (lazy-loaded)"""
        if self._invoice_repo is None:
            self._invoice_repo = InvoiceRepository(self.session)
        return self._invoice_repo

    @property
    def payments(self) -> PaymentRepository:
        """Get payment repository (lazy-loaded)"""
        if self._payment_repo is None:
            self._payment_repo = PaymentRepository(self.session)
        return self._payment_repo

    @property
    def usage_events(self) -> UsageEventRepository:
        """Get usage event repository (lazy-loaded)"""
        if self._usage_event_repo is None:
            self._usage_event_repo = UsageEventRepository(self.session)
        return self._usage_event_repo

    @property
    def credits(self) -> CreditRepository:
        """Get credit repository (lazy-loaded)"""
        if self._credit_repo is None:
            self._credit_repo = CreditRepository(self.session)
        return self._credit_repo

    # Sales Repositories
    @property
    def employees(self) -> EmployeeRepository:
        """Get employee repository (lazy-loaded)"""
        if self._employee_repo is None:
            self._employee_repo = EmployeeRepository(self.session)
        return self._employee_repo

    @property
    def leads(self) -> LeadRepository:
        """Get lead repository (lazy-loaded)"""
        if self._lead_repo is None:
            self._lead_repo = LeadRepository(self.session)
        return self._lead_repo

    @property
    def deals(self) -> DealRepository:
        """Get deal repository (lazy-loaded)"""
        if self._deal_repo is None:
            self._deal_repo = DealRepository(self.session)
        return self._deal_repo

    @property
    def sales_activities(self) -> SalesActivityRepository:
        """Get sales activity repository (lazy-loaded)"""
        if self._sales_activity_repo is None:
            self._sales_activity_repo = SalesActivityRepository(self.session)
        return self._sales_activity_repo

    @property
    def quotes(self) -> QuoteRepository:
        """Get quote repository (lazy-loaded)"""
        if self._quote_repo is None:
            self._quote_repo = QuoteRepository(self.session)
        return self._quote_repo

    # Analytics Repositories
    @property
    def conversation_analytics(self) -> ConversationAnalyticsRepository:
        """Get conversation analytics repository (lazy-loaded)"""
        if self._conversation_analytics_repo is None:
            self._conversation_analytics_repo = ConversationAnalyticsRepository(self.session)
        return self._conversation_analytics_repo

    @property
    def feature_usage(self) -> FeatureUsageRepository:
        """Get feature usage repository (lazy-loaded)"""
        if self._feature_usage_repo is None:
            self._feature_usage_repo = FeatureUsageRepository(self.session)
        return self._feature_usage_repo

    @property
    def ab_tests(self) -> ABTestRepository:
        """Get A/B test repository (lazy-loaded)"""
        if self._ab_test_repo is None:
            self._ab_test_repo = ABTestRepository(self.session)
        return self._ab_test_repo

    # Workflow Repositories
    @property
    def workflows(self) -> WorkflowRepository:
        """Get workflow repository (lazy-loaded)"""
        if self._workflow_repo is None:
            self._workflow_repo = WorkflowRepository(self.session)
        return self._workflow_repo

    @property
    def workflow_executions(self) -> WorkflowExecutionRepository:
        """Get workflow execution repository (lazy-loaded)"""
        if self._workflow_execution_repo is None:
            self._workflow_execution_repo = WorkflowExecutionRepository(self.session)
        return self._workflow_execution_repo

    @property
    def scheduled_tasks(self) -> ScheduledTaskRepository:
        """Get scheduled task repository (lazy-loaded)"""
        if self._scheduled_task_repo is None:
            self._scheduled_task_repo = ScheduledTaskRepository(self.session)
        return self._scheduled_task_repo

    # Agent Handoff Repositories
    @property
    def agent_handoffs(self) -> AgentHandoffRepository:
        """Get agent handoff repository (lazy-loaded)"""
        if self._agent_handoff_repo is None:
            self._agent_handoff_repo = AgentHandoffRepository(self.session)
        return self._agent_handoff_repo

    @property
    def agent_collaborations(self) -> AgentCollaborationRepository:
        """Get agent collaboration repository (lazy-loaded)"""
        if self._agent_collaboration_repo is None:
            self._agent_collaboration_repo = AgentCollaborationRepository(self.session)
        return self._agent_collaboration_repo

    @property
    def conversation_tags(self) -> ConversationTagRepository:
        """Get conversation tag repository (lazy-loaded)"""
        if self._conversation_tag_repo is None:
            self._conversation_tag_repo = ConversationTagRepository(self.session)
        return self._conversation_tag_repo

    # Audit Repository
    @property
    def audit_logs(self) -> AuditLogRepository:
        """Get audit log repository (lazy-loaded)"""
        if self._audit_log_repo is None:
            self._audit_log_repo = AuditLogRepository(self.session)
        return self._audit_log_repo

    async def commit(self):
        """Commit the current transaction"""
        await self.session.commit()

    async def rollback(self):
        """Rollback the current transaction"""
        await self.session.rollback()

    async def flush(self):
        """
        Flush pending changes without committing
        Useful for getting auto-generated IDs
        """
        await self.session.flush()

    async def refresh(self, instance):
        """
        Refresh instance with latest data from database

        Args:
            instance: SQLAlchemy model instance
        """
        await self.session.refresh(instance)


@asynccontextmanager
async def get_unit_of_work(current_user_id: UUID | None = None) -> AsyncIterator[UnitOfWork]:
    """
    Context manager for Unit of Work pattern

    Automatically commits on success, rolls back on exception.

    Args:
        current_user_id: ID of user performing operations (for audit)

    Usage:
        async with get_unit_of_work() as uow:
            customer = await uow.customers.create(...)
            conversation = await uow.conversations.create(...)
            # Commits automatically here

    Yields:
        UnitOfWork instance

    Raises:
        Exception: Any exception from nested operations (after rollback)
    """
    async with get_db_session() as session:
        uow = UnitOfWork(session, current_user_id)
        try:
            yield uow
            await uow.commit()
        except Exception as e:
            await uow.rollback()
            # Re-raise exception after rollback
            raise e


# Convenience function for backward compatibility
@asynccontextmanager
async def get_uow(current_user_id: UUID | None = None) -> AsyncIterator[UnitOfWork]:
    """Alias for get_unit_of_work"""
    async with get_unit_of_work(current_user_id) as uow:
        yield uow


if __name__ == "__main__":
    import asyncio
    from uuid import uuid4

    async def test_unit_of_work():
        """Test Unit of Work pattern"""
        print("=" * 70)
        print("TESTING UNIT OF WORK")
        print("=" * 70)

        # Test successful transaction
        print("\n1. Testing successful transaction...")
        try:
            async with get_unit_of_work() as uow:
                customer = await uow.customers.create(
                    email=f"test_{uuid4().hex[:8]}@example.com",
                    name="Test User",
                    plan="free",
                    extra_metadata={},
                )
                print(f"   ✓ Customer created: {customer.email}")

                conversation = await uow.conversations.create_with_customer(customer_id=customer.id)
                print(f"   ✓ Conversation created: {conversation.id}")

                # Transaction commits here

            print("   ✓ Transaction committed successfully")
        except Exception as e:
            print(f"   ✗ Error: {e}")

        # Test rollback on error
        print("\n2. Testing rollback on error...")
        try:
            async with get_unit_of_work() as uow:
                customer = await uow.customers.create(
                    email=f"test_{uuid4().hex[:8]}@example.com",
                    name="Test User 2",
                    plan="free",
                    extra_metadata={},
                )
                print(f"   ✓ Customer created: {customer.email}")

                # Simulate error
                raise ValueError("Simulated error")
        except ValueError:
            print("   ✓ Exception caught, transaction rolled back")

        print("\n✓ Unit of Work tests passed")

    asyncio.run(test_unit_of_work())
