"""
API Agent - Helps with API integration and webhooks.

Specialist for API and webhook questions with code examples.
"""

from src.workflow.state import AgentState
from src.agents.base import BaseAgent, AgentConfig, AgentType, AgentCapability
from src.utils.logging.setup import get_logger
from src.services.infrastructure.agent_registry import AgentRegistry


@AgentRegistry.register("api_agent", tier="essential", category="integration")
class APIAgent(BaseAgent):
    """
    API Agent - Specialist for API and webhook questions.

    Handles:
    - REST API usage
    - Authentication (API keys, OAuth)
    - Webhooks setup
    - Rate limits
    - API errors and debugging
    """

    def __init__(self):
        config = AgentConfig(
            name="api_agent",
            type=AgentType.SPECIALIST,
            temperature=0.3,
            capabilities=[
                AgentCapability.KB_SEARCH,
                AgentCapability.CONTEXT_AWARE
            ],
            kb_category="api",
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

    async def process(self, state: AgentState) -> AgentState:
        """Process API-related questions"""
        self.logger.info("api_agent_processing_started")

        state = self.update_state(state)

        message = state["current_message"]
        intent = state.get("primary_intent", "integration_api")

        self.logger.debug(
            "api_processing_message",
            message_preview=message[:100],
            intent=intent,
            turn_count=state["turn_count"]
        )

        # Search API KB articles
        kb_results = await self.search_knowledge_base(message, category="api", limit=3)
        state["kb_results"] = kb_results

        if kb_results:
            self.logger.info(
                "api_kb_articles_found",
                count=len(kb_results),
                top_score=kb_results[0].get("similarity_score", 0) if kb_results else 0
            )
            for article in kb_results:
                self.logger.debug(
                    "api_kb_article",
                    title=article.get("title"),
                    score=article.get("similarity_score", 0)
                )
        else:
            self.logger.warning(
                "api_no_kb_articles_found",
                intent=intent,
                message_preview=message[:50]
            )

        # Detect programming language preference
        requested_lang = self._detect_language_preference(message)
        if requested_lang:
            self.logger.info(
                "api_language_detected",
                language=requested_lang
            )

        # Generate technical response with code examples and conversation context
        response = await self.generate_response(message, intent, kb_results, requested_lang, state)

        state["agent_response"] = response
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        # Keep status "active" to allow multi-turn conversations
        # Only resolve when user explicitly ends or issue is confirmed resolved
        state["status"] = "active"

        self.logger.info(
            "api_response_generated",
            response_length=len(response),
            language=requested_lang,
            status="active"
        )

        return state

    async def generate_response(
        self,
        message: str,
        intent: str,
        kb_results: list,
        language: str = None,
        state: AgentState = None
    ) -> str:
        """Generate API documentation response with code examples"""
        self.logger.debug(
            "api_response_generation_started",
            intent=intent,
            kb_articles_count=len(kb_results),
            language=language
        )

        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant API documentation:\n"
            for i, article in enumerate(kb_results, 1):
                kb_context += f"\n{i}. {article['title']}\n{article['content']}\n"

        lang_instruction = ""
        if language:
            lang_instruction = f"\nProvide code examples in {language}."

        # Get conversation history for multi-turn context
        conversation_history = []
        if state:
            conversation_history = self.get_conversation_context(state)
            self.logger.debug(
                "api_conversation_context",
                history_length=len(conversation_history)
            )

        system_prompt = f"""You are an API integration specialist.

Our API Base URL: https://api.example.com/v1
Authentication: Bearer token in Authorization header

Guidelines:
1. Provide clear API endpoint examples
2. Include sample request/response JSON
3. Show authentication headers
4. Explain rate limits (100 req/min)
5. Include error handling examples
6. Cite API documentation when relevant
7. IMPORTANT: Consider the conversation history to provide contextual responses. If the developer has already asked related questions, build on previous explanations.{lang_instruction}

Be technical but clear."""

        user_prompt = f"""Developer question: {message}

Intent: {intent}
{kb_context}

Provide API guidance with examples that takes into account any previous conversation context."""

        # CRITICAL: Pass conversation history for multi-turn context
        response = await self.call_llm(
            system_prompt,
            user_prompt,
            max_tokens=700,
            conversation_history=conversation_history
        )

        self.logger.debug(
            "api_llm_response_received",
            response_length=len(response)
        )

        return response

    def _detect_language_preference(self, message: str) -> str:
        """Detect if user prefers specific programming language"""
        message_lower = message.lower()

        language_keywords = {
            "python": ["python", "django", "flask", "requests"],
            "javascript": ["javascript", "js", "node", "axios", "fetch"],
            "curl": ["curl", "bash", "shell"],
            "php": ["php", "laravel"],
            "ruby": ["ruby", "rails"],
            "java": ["java", "spring"],
            "go": ["golang", "go"],
            "csharp": ["c#", "csharp", ".net", "dotnet"]
        }

        for lang, keywords in language_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                self.logger.debug(
                    "language_preference_detected",
                    language=lang,
                    keywords_matched=[k for k in keywords if k in message_lower]
                )
                return lang

        return None
