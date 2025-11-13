"""
API Agent - Helps with API integration and webhooks

"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.workflow.state import AgentState
from src.agents.base import BaseAgent
from knowledge_base import search_articles
from src.utils.logging.setup import get_logger


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
        super().__init__(
            agent_type="api",
            model="claude-3-haiku-20240307",
            temperature=0.3
        )
        self.logger = get_logger(__name__)
    
    def process(self, state: AgentState) -> AgentState:
        """Process API-related questions"""
        self.logger.info("api_agent_processing_started")
        
        state = self.add_to_history(state)
        state["turn_count"] = state.get("turn_count", 0) + 1
        
        message = state["current_message"]
        intent = state.get("primary_intent", "integration_api")
        
        self.logger.debug(
            "api_processing_message",
            message_preview=message[:100],
            intent=intent,
            turn_count=state["turn_count"]
        )
        
        # Search API KB articles
        kb_results = search_articles(message, category="api", limit=3)
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
        
        # Generate technical response with code examples
        response = self.generate_response(message, intent, kb_results, requested_lang)
        
        state["agent_response"] = response
        state["response_confidence"] = 0.85
        state["next_agent"] = None
        state["status"] = "resolved"
        
        self.logger.info(
            "api_response_generated",
            response_length=len(response),
            language=requested_lang,
            status="resolved"
        )
        
        return state
    
    def generate_response(
        self, 
        message: str, 
        intent: str, 
        kb_results: list,
        language: str = None
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
        
        system_prompt = f"""You are an API integration specialist.

Our API Base URL: https://api.example.com/v1
Authentication: Bearer token in Authorization header

Guidelines:
1. Provide clear API endpoint examples
2. Include sample request/response JSON
3. Show authentication headers
4. Explain rate limits (100 req/min)
5. Include error handling examples
6. Cite API documentation when relevant{lang_instruction}

Be technical but clear."""

        user_prompt = f"""Developer question: {message}

Intent: {intent}
{kb_context}

Provide API guidance with examples."""

        response = self.call_llm(system_prompt, user_prompt, max_tokens=700)
        
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


if __name__ == "__main__":
    from src.workflow.state import create_initial_state
    
    state = create_initial_state("How do I authenticate with the API using Python?")
    state["primary_intent"] = "integration_api"
    
    agent = APIAgent()
    result = agent.process(state)
    
    print(f"\n{'='*60}")
    print(f"Response:\n{result['agent_response']}")