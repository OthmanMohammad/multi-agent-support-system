"""
Pydantic schemas package - Data Transfer Objects
"""
from src.database.schemas.customer import (
    CustomerBase,
    CustomerCreate,
    CustomerUpdate,
    CustomerInDB,
    CustomerResponse,
    CustomerWithConversations,
)
from src.database.schemas.conversation import (
    ConversationBase,
    ConversationCreate,
    ConversationUpdate,
    ConversationInDB,
    ConversationResponse,
    ConversationWithMessages,
    ConversationStatistics,
)
from src.database.schemas.message import (
    MessageBase,
    MessageCreate,
    MessageUpdate,
    MessageInDB,
    MessageResponse,
    MessageSentimentDistribution,
)
from src.database.schemas.agent_performance import (
    AgentPerformanceBase,
    AgentPerformanceCreate,
    AgentPerformanceUpdate,
    AgentPerformanceInDB,
    AgentPerformanceResponse,
    AgentPerformanceSummary,
    AllAgentsSummary,
)

__all__ = [
    # Customer
    "CustomerBase",
    "CustomerCreate",
    "CustomerUpdate",
    "CustomerInDB",
    "CustomerResponse",
    "CustomerWithConversations",
    # Conversation
    "ConversationBase",
    "ConversationCreate",
    "ConversationUpdate",
    "ConversationInDB",
    "ConversationResponse",
    "ConversationWithMessages",
    "ConversationStatistics",
    # Message
    "MessageBase",
    "MessageCreate",
    "MessageUpdate",
    "MessageInDB",
    "MessageResponse",
    "MessageSentimentDistribution",
    # Agent Performance
    "AgentPerformanceBase",
    "AgentPerformanceCreate",
    "AgentPerformanceUpdate",
    "AgentPerformanceInDB",
    "AgentPerformanceResponse",
    "AgentPerformanceSummary",
    "AllAgentsSummary",
]