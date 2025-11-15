"""
FAQ Generator Agent.

Automatically generates FAQ entries from frequently asked questions in conversations.

Part of: STORY-002 Knowledge Base Swarm (TASK-209)
"""

from typing import List, Dict
from collections import Counter
from datetime import datetime, timedelta
import json
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from src.agents.base.base_agent import BaseAgent
from src.agents.base.agent_types import AgentType
from src.agents.base import AgentConfig
from src.workflow.state import AgentState
from src.database.connection import get_db_session
from src.database.models import Message, Conversation
from src.utils.logging.setup import get_logger

try:
    from sentence_transformers import SentenceTransformer
    from sklearn.cluster import DBSCAN
    CLUSTERING_AVAILABLE = True
except ImportError:
    CLUSTERING_AVAILABLE = False


class FAQGenerator(BaseAgent):
    """
    FAQ Generator Agent.

    Automatically generates FAQs from conversations by:
    - Finding questions asked >10 times/month
    - Clustering similar questions
    - Generating canonical FAQ entry
    - Including best answer from conversations
    """

    def __init__(self):
        """Initialize FAQ Generator agent."""
        config = AgentConfig(
            name="faq_generator",
            type=AgentType.SPECIALIST,
            model="claude-3-sonnet-20240229",  # Better writing
            temperature=0.3,
            max_tokens=1024,
            tier="essential"
        )
        super().__init__(config)
        self.logger = get_logger(__name__)

        # Initialize embedding model for clustering
        if CLUSTERING_AVAILABLE:
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
        else:
            self.embedding_model = None
            self.logger.warning("clustering_unavailable", message="sentence-transformers not installed")

        self.logger.info("faq_generator_initialized")

    async def process(self, state: AgentState) -> AgentState:
        """
        Process state and generate FAQs.

        Args:
            state: AgentState

        Returns:
            Updated state with generated FAQs
        """
        days = state.get("faq_generation_days", 30)
        min_frequency = state.get("faq_min_frequency", 10)
        limit = state.get("faq_limit", 5)

        self.logger.info(
            "faq_generation_started",
            days=days,
            min_frequency=min_frequency,
            limit=limit
        )

        # Generate FAQs
        faqs = await self.generate_faqs(
            days=days,
            min_frequency=min_frequency,
            limit=limit
        )

        # Update state
        state = self.update_state(
            state,
            generated_faqs=faqs,
            faqs_count=len(faqs)
        )

        self.logger.info(
            "faq_generation_completed",
            faqs_count=len(faqs)
        )

        return state

    async def generate_faqs(
        self,
        days: int = 30,
        min_frequency: int = 10,
        limit: int = 5
    ) -> List[Dict]:
        """
        Generate FAQ entries from conversations.

        Args:
            days: Look back period
            min_frequency: Min question frequency
            limit: Max FAQs to generate

        Returns:
            List of FAQ entries
        """
        # Get frequently asked questions
        common_questions = await self._find_common_questions(days, min_frequency)

        if not common_questions:
            self.logger.info("faq_generation_no_common_questions")
            return []

        # Cluster similar questions
        question_clusters = await self._cluster_similar_questions(common_questions)

        # Generate FAQ for each cluster
        faqs = []
        for cluster in question_clusters[:limit]:
            faq = await self._generate_faq_entry(cluster)
            faqs.append(faq)

        return faqs

    async def _find_common_questions(
        self,
        days: int,
        min_frequency: int
    ) -> List[Dict]:
        """
        Find commonly asked questions.

        Args:
            days: Look back period
            min_frequency: Minimum frequency threshold

        Returns:
            List of common questions with counts
        """
        cutoff = datetime.utcnow() - timedelta(days=days)

        try:
            async with get_db_session() as session:
                # Get user messages from conversations
                result = await session.execute(
                    select(Message, Conversation).join(
                        Conversation,
                        Message.conversation_id == Conversation.id
                    ).where(
                        Message.role == 'user',
                        Conversation.created_at >= cutoff
                    )
                )
                rows = result.all()

                # Extract questions (messages containing ?)
                questions = []
                for msg, conv in rows:
                    if '?' in msg.content:
                        questions.append({
                            "content": msg.content,
                            "conversation_id": str(conv.id) if conv else None
                        })

                # Count similar questions (simple lowercase match)
                question_counts = Counter([
                    q["content"].lower().strip()
                    for q in questions
                ])

                # Filter by frequency
                common = [
                    {"question": q, "count": count}
                    for q, count in question_counts.items()
                    if count >= min_frequency
                ]

                self.logger.info(
                    "common_questions_found",
                    total_questions=len(questions),
                    common_questions=len(common)
                )

                return common

        except SQLAlchemyError as e:
            self.logger.error(
                "common_questions_retrieval_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            return []

    async def _cluster_similar_questions(
        self,
        questions: List[Dict]
    ) -> List[List[Dict]]:
        """
        Cluster similar questions together.

        Args:
            questions: List of question dicts

        Returns:
            List of question clusters
        """
        if not questions or not self.embedding_model:
            # Return each question as its own cluster
            return [[q] for q in questions]

        try:
            # Generate embeddings
            question_texts = [q["question"] for q in questions]
            embeddings = self.embedding_model.encode(question_texts)

            # Cluster using DBSCAN
            clustering = DBSCAN(
                eps=0.3,
                min_samples=2,
                metric='cosine'
            ).fit(embeddings)

            # Group by cluster
            clusters = {}
            for idx, label in enumerate(clustering.labels_):
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(questions[idx])

            # Return clusters as list (excluding noise cluster -1 if present)
            cluster_list = [
                cluster
                for label, cluster in clusters.items()
                if label != -1
            ]

            self.logger.info(
                "questions_clustered",
                clusters_count=len(cluster_list)
            )

            return cluster_list

        except Exception as e:
            self.logger.error(
                "question_clustering_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            # Return each question as its own cluster
            return [[q] for q in questions]

    async def _generate_faq_entry(self, question_cluster: List[Dict]) -> Dict:
        """
        Generate FAQ entry from question cluster.

        Args:
            question_cluster: List of similar questions

        Returns:
            FAQ entry dict
        """
        # Get canonical question and answer using LLM
        system_prompt = """You are an FAQ writer.

Given multiple similar questions, create a canonical FAQ entry.

Return ONLY valid JSON with this structure:
{
  "question": "Canonical question form",
  "answer": "Clear, concise answer",
  "alternate_phrasings": ["How to...", "Can I..."],
  "category": "billing|technical|usage|api|integrations|account",
  "confidence": 0.85
}"""

        questions_text = "\n".join([
            f"- {q['question']}" for q in question_cluster
        ])
        user_prompt = f"""Similar questions:\n{questions_text}\n\nCreate FAQ entry."""

        try:
            response = await self.call_llm(
                system_prompt=system_prompt,
                user_message=user_prompt,
                max_tokens=1024
            )

            faq = json.loads(response)

            # Add metadata
            faq["frequency"] = sum(q.get("count", 1) for q in question_cluster)
            faq["status"] = "pending_review"  # Needs human review

            self.logger.info(
                "faq_entry_generated",
                question=faq.get("question", "")[:50],
                frequency=faq["frequency"]
            )

            return faq

        except (json.JSONDecodeError, Exception) as e:
            self.logger.error(
                "faq_generation_failed",
                error=str(e),
                error_type=type(e).__name__
            )
            # Fallback
            return {
                "question": question_cluster[0]["question"],
                "answer": "Answer needed",
                "alternate_phrasings": [],
                "category": "general",
                "frequency": sum(q.get("count", 1) for q in question_cluster),
                "confidence": 0.0,
                "status": "error"
            }


if __name__ == "__main__":
    # Test FAQ Generator
    import asyncio
    from src.workflow.state import create_initial_state

    async def test():
        print("=" * 60)
        print("TESTING FAQ GENERATOR")
        print("=" * 60)

        generator = FAQGenerator()

        print("\nTest 1: Generate FAQs")
        faqs = await generator.generate_faqs(
            days=30,
            min_frequency=5,
            limit=3
        )

        print(f"Generated {len(faqs)} FAQs:")
        for i, faq in enumerate(faqs, 1):
            print(f"\nFAQ {i}:")
            print(f"  Question: {faq.get('question', 'N/A')}")
            print(f"  Answer: {faq.get('answer', 'N/A')[:100]}...")
            print(f"  Category: {faq.get('category', 'N/A')}")
            print(f"  Frequency: {faq.get('frequency', 0)}")
            print(f"  Status: {faq.get('status', 'N/A')}")

        print("\nTest 2: Process with state")
        state = create_initial_state(message="test", context={})
        state = await generator.process(state)
        print(f"FAQs generated: {state.get('faqs_count', 0)}")

        print("\n✓ FAQ Generator tests completed!")

    asyncio.run(test())
