"""
Usage Agent - Teaches users how to use features
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from state import AgentState
from agents.base import BaseAgent
from knowledge_base import search_articles


class UsageAgent(BaseAgent):
    """
    Usage Agent - Specialist for feature usage and how-to questions.
    
    Handles:
    - How to create/edit features
    - How to invite team members
    - How to export data
    - Keyboard shortcuts
    - Best practices
    """
    
    def __init__(self):
        super().__init__(
            agent_type="usage",
            model="claude-3-5-sonnet-20241022",
            temperature=0.4
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process feature usage questions"""
        print(f"\n{'='*60}")
        print(f"📖 USAGE AGENT PROCESSING")
        print(f"{'='*60}")
        
        state = self.add_to_history(state)
        state["turn_count"] = state.get("turn_count", 0) + 1
        
        message = state["current_message"]
        intent = state.get("primary_intent", "feature_create")
        
        print(f"Message: {message[:100]}...")
        print(f"Intent: {intent}")
        
        # Search usage KB articles
        kb_results = search_articles(message, category="usage", limit=3)
        state["kb_results"] = kb_results
        
        if kb_results:
            print(f"✓ Found {len(kb_results)} usage articles")
        
        # Generate tutorial-style response
        response = self.generate_response(message, intent, kb_results)
        
        state["agent_response"] = response
        state["response_confidence"] = 0.9
        state["next_agent"] = None
        state["status"] = "resolved"
        
        print(f"✓ Response generated")
        
        return state
    
    def generate_response(self, message: str, intent: str, kb_results: list) -> str:
        """Generate step-by-step tutorial response"""
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant how-to articles:\n"
            for i, article in enumerate(kb_results, 1):
                kb_context += f"\n{i}. {article['title']}\n{article['content']}\n"
        
        system_prompt = """You are a feature usage specialist.

Guidelines:
1. Provide clear step-by-step instructions
2. Use numbered lists for steps
3. Include helpful tips and best practices
4. Mention related features they might find useful
5. Cite KB articles when relevant

Be encouraging and educational."""

        user_prompt = f"""User question: {message}

Intent: {intent}
{kb_context}

Provide a helpful how-to guide."""

        return self.call_llm(system_prompt, user_prompt, max_tokens=500)


if __name__ == "__main__":
    from state import create_initial_state
    
    state = create_initial_state("How do I add team members?")
    state["primary_intent"] = "feature_invite"
    
    agent = UsageAgent()
    result = agent.process(state)
    
    print(f"\n{'='*60}")
    print(f"Response:\n{result['agent_response']}")