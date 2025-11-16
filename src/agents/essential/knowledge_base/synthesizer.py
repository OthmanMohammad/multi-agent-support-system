"""
KB Synthesizer Agent.

Combines multiple KB articles into a coherent, comprehensive answer with proper citations.
Uses Claude Sonnet for better synthesis quality.

"""

from typing import List, Dict

from src.agents.base.base_agent import BaseAgent
from src.agents.base.agent_types import AgentType, AgentCapability
from src.agents.base import AgentConfig
from src.workflow.state import AgentState
from src.utils.logging.setup import get_logger


class KBSynthesizer(BaseAgent):
    """
    Knowledge Base Synthesizer Agent.

    Combines multiple KB articles into a coherent answer with citations.
    Ensures no hallucinations by only using provided article content.
    """

    def __init__(self):
        """Initialize KB Synthesizer agent."""
        config = AgentConfig(
            name="kb_synthesizer",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",  # Better synthesis quality
            temperature=0.3,  # Some creativity but mostly factual
            max_tokens=2048,
            capabilities=[AgentCapability.KB_SEARCH],
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        self.logger.info("kb_synthesizer_initialized")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and synthesize KB articles into answer.

        Args:
            state: AgentState with user_message and kb_ranked_results

        Returns:
            Updated state with synthesized answer
        """
        user_message = state.get("current_message", "")
        kb_results = state.get("kb_ranked_results", [])

        if not kb_results:
            # No KB results to synthesize
            self.logger.info("kb_synthesizer_no_results")
            state = self.update_state(
                state,
                synthesized_answer=None,
                synthesis_confidence=0.0,
                sources_used=[]
            )
            return state

        # Limit to top N articles (avoid context overflow)
        max_articles = 5
        kb_results = kb_results[:max_articles]

        self.logger.info(
            "kb_synthesis_started",
            query_preview=user_message[:100],
            articles_count=len(kb_results)
        )

        # Synthesize answer
        result = await self.synthesize(user_message, kb_results)

        # Update state
        state = self.update_state(
            state,
            synthesized_answer=result["synthesized_answer"],
            sources_used=result["sources_used"],
            synthesis_confidence=result["synthesis_confidence"],
            synthesis_tokens_used=result.get("tokens_used", 0)
        )

        self.logger.info(
            "kb_synthesis_completed",
            answer_length=len(result["synthesized_answer"]),
            sources_count=len(result["sources_used"]),
            confidence=result["synthesis_confidence"]
        )

        return state

    async def synthesize(
        self,
        user_message: str,
        kb_articles: List[Dict]
    ) -> Dict:
        """
        Synthesize KB articles into coherent answer.

        Args:
            user_message: User's question
            kb_articles: List of ranked KB articles

        Returns:
            Dict with synthesized answer and metadata
        """
        # Build system prompt
        system_prompt = self._build_system_prompt()

        # Build user prompt with articles
        user_prompt = self._build_user_prompt(user_message, kb_articles)

        # Call LLM
        response = await self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            max_tokens=2048
        )

        # Parse response
        synthesized_answer = response.strip()

        # Calculate confidence (simple heuristic for now)
        confidence = self._calculate_confidence(kb_articles, synthesized_answer)

        # Track sources used
        sources_used = [
            {
                "article_id": article["article_id"],
                "title": article["title"],
                "url": article.get("url", ""),
                "final_score": article.get("final_score", article.get("similarity_score", 0))
            }
            for article in kb_articles
        ]

        # Approximate token usage
        tokens_used = len(response.split())

        return {
            "synthesized_answer": synthesized_answer,
            "sources_used": sources_used,
            "synthesis_confidence": round(confidence, 2),
            "tokens_used": tokens_used
        }

    def _build_system_prompt(self) -> str:
        """Build system prompt for synthesis."""
        return """You are a Knowledge Base Synthesizer for a SaaS support system.

Your job is to answer user questions by synthesizing information from multiple KB articles.

CRITICAL RULES:
1. ONLY use information from the provided articles
2. NEVER make up or hallucinate information
3. ALWAYS cite sources at the end
4. Combine information from multiple articles when relevant
5. Be concise but complete
6. Use clear formatting (bullet points, numbered lists, bold headings)
7. If articles don't fully answer the question, say so
8. Maintain a helpful and professional tone

CITATION FORMAT:
End your answer with:

**Sources:**
- [Article Title](article_url)
- [Article Title 2](article_url_2)

TONE:
- Helpful and professional
- Clear and easy to understand
- Empathetic when needed
- Direct and actionable"""

    def _build_user_prompt(
        self,
        user_message: str,
        kb_articles: List[Dict]
    ) -> str:
        """Build user prompt with question and articles."""
        prompt = f"**User Question:**\n{user_message}\n\n"
        prompt += "**Knowledge Base Articles:**\n\n"

        for idx, article in enumerate(kb_articles, 1):
            prompt += f"--- Article {idx}: {article['title']} ---\n"
            prompt += f"{article['content']}\n\n"

        prompt += "**Instructions:**\n"
        prompt += "Synthesize the above articles to answer the user's question. "
        prompt += "Cite all sources at the end using the citation format specified in the system prompt."

        return prompt

    def _calculate_confidence(
        self,
        kb_articles: List[Dict],
        synthesized_answer: str
    ) -> float:
        """
        Calculate confidence in synthesis.

        Simple heuristic based on:
        - Number of high-quality sources
        - Average article scores
        - Answer length (too short = incomplete)

        Args:
            kb_articles: Articles used for synthesis
            synthesized_answer: Generated answer

        Returns:
            Confidence score (0-1)
        """
        if not kb_articles:
            return 0.0

        # Average final scores of articles used
        avg_score = sum(
            a.get("final_score", a.get("similarity_score", 0))
            for a in kb_articles
        ) / len(kb_articles)

        # Penalize very short answers
        answer_length = len(synthesized_answer.split())
        length_penalty = 1.0 if answer_length >= 50 else answer_length / 50

        # Bonus for multiple sources
        source_bonus = min(len(kb_articles) * 0.05, 0.15)

        # Combined confidence
        confidence = (avg_score * 0.7 + source_bonus + length_penalty * 0.2)

        return min(max(confidence, 0.0), 1.0)


if __name__ == "__main__":
    # Test KB Synthesizer
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING KB SYNTHESIZER")
        print("=" * 60)

        synthesizer = KBSynthesizer()

        # Test articles
        test_articles = [
            {
                "article_id": "kb_upgrade",
                "title": "How to Upgrade Your Plan",
                "content": """
To upgrade your plan:
1. Navigate to Settings
2. Click on Billing
3. Select your desired plan
4. Confirm the upgrade

You'll be charged a prorated amount for the remaining days in your current billing cycle.
                """,
                "url": "/kb/upgrade",
                "final_score": 0.92
            },
            {
                "article_id": "kb_pricing",
                "title": "Plan Pricing",
                "content": """
Our plans:
- Basic: $10/user/month - Up to 25 users, core features
- Premium: $25/user/month - Unlimited users, advanced features, priority support
- Enterprise: Custom pricing - Dedicated support, SLA, custom solutions
                """,
                "url": "/kb/pricing",
                "final_score": 0.85
            }
        ]

        print("\nTest 1: Synthesize answer")
        result = await synthesizer.synthesize(
            user_message="How do I upgrade to Premium and how much does it cost?",
            kb_articles=test_articles
        )

        print("\nSynthesized Answer:")
        print(result["synthesized_answer"])
        print(f"\nConfidence: {result['synthesis_confidence']}")
        print(f"Sources used: {len(result['sources_used'])}")

        print("\nTest 2: Process with state")
        state = create_initial_state(
            message="What are the pricing options?",
            context={}
        )
        state["kb_ranked_results"] = test_articles
        state = await synthesizer.process(state)

        print(f"\nAnswer length: {len(state['synthesized_answer'])}")
        print(f"Confidence: {state['synthesis_confidence']}")

        print("\n✓ KB Synthesizer tests completed!")

    asyncio.run(test())
