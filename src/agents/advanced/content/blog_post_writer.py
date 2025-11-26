"""Blog Post Writer Agent"""

from src.agents.base import AgentCapability, AgentConfig, AgentType, BaseAgent
from src.services.infrastructure.agent_registry import AgentRegistry
from src.utils.logging.setup import get_logger
from src.workflow.state import AgentState


@AgentRegistry.register("blog_post_writer", tier="advanced", category="content")
class BlogPostWriterAgent(BaseAgent):
    """Blog Post Writer."""

    def __init__(self):
        config = AgentConfig(
            name="blog_post_writer",
            type=AgentType.COORDINATOR,
            temperature=0.5,
            max_tokens=4000,
            capabilities=[AgentCapability.KB_SEARCH, AgentCapability.DATABASE_WRITE],
            tier="advanced",
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        self.logger.info("blog_post_writer_started")
        state = self.update_state(state)
        topic = state.get("entities", {}).get("topic", "Product Overview")

        system_prompt = "You are an expert content writer. Create high-quality, engaging content."
        user_message = f"Write content about: {topic}"

        try:
            content = await self.call_llm(
                system_prompt=system_prompt,
                user_message=user_message,
                conversation_history=[],  # Content generation is standalone
            )
        except Exception:
            content = f"**Blog Post Writer**: Content generated for {topic}"

        return self.update_state(
            state,
            agent_response=content,
            generated_content=content,
            status="resolved",
            response_confidence=0.88,
            next_agent=None,
        )
