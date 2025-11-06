"""
Technical Agent - Handles bugs, errors, sync issues, performance
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from workflow.state import AgentState
from agents.base import BaseAgent
from knowledge_base import search_articles


class TechnicalAgent(BaseAgent):
    """
    Technical Agent - Specialist for technical issues.
    
    Handles:
    - Bugs and errors
    - Sync issues
    - Performance problems
    - Login issues
    """
    
    def __init__(self):
        super().__init__(
            agent_type="technical",
            model="claude-3-haiku-20240307",
            temperature=0.3
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process technical support requests"""
        print(f"\n{'='*60}")
        print(f"🔧 TECHNICAL AGENT PROCESSING")
        print(f"{'='*60}")
        
        state = self.add_to_history(state)
        state["turn_count"] = state.get("turn_count", 0) + 1
        
        message = state["current_message"]
        intent = state.get("primary_intent", "technical_bug")
        
        print(f"Message: {message[:100]}...")
        print(f"Intent: {intent}")
        
        # Search technical KB articles
        kb_results = search_articles(message, category="technical", limit=3)
        state["kb_results"] = kb_results
        
        if kb_results:
            print(f"✓ Found {len(kb_results)} technical articles")
        
        # Generate troubleshooting response
        response = self.generate_response(message, intent, kb_results)
        
        state["agent_response"] = response
        state["response_confidence"] = 0.8
        state["next_agent"] = None
        state["status"] = "resolved"
        
        print(f"✓ Response generated")
        
        return state
    
    def generate_response(self, message: str, intent: str, kb_results: list) -> str:
        """Generate technical troubleshooting response"""
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant troubleshooting articles:\n"
            for i, article in enumerate(kb_results, 1):
                kb_context += f"\n{i}. {article['title']}\n{article['content']}\n"
        
        system_prompt = """You are a technical support specialist.

Guidelines:
1. Provide step-by-step troubleshooting
2. Ask clarifying questions if needed (browser, OS, error messages)
3. Check common causes first (cache, cookies, internet)
4. Cite KB articles when relevant
5. If unresolved, offer to create a bug ticket

Be methodical and patient."""

        user_prompt = f"""Technical issue: {message}

Intent: {intent}
{kb_context}

Provide troubleshooting steps."""

        return self.call_llm(system_prompt, user_prompt, max_tokens=600)


if __name__ == "__main__":
    from workflow.state import create_initial_state
    
    state = create_initial_state("My tasks are not syncing")
    state["primary_intent"] = "technical_sync"
    
    agent = TechnicalAgent()
    result = agent.process(state)
    
    print(f"\n{'='*60}")
    print(f"Response:\n{result['agent_response']}")