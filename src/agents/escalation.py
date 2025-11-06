"""
Escalation Agent - Hands off to human agents
"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from workflow.state import AgentState
from agents.base import BaseAgent


class EscalationAgent(BaseAgent):
    """
    Escalation Agent - Creates tickets and hands off to humans.
    
    Handles:
    - Low confidence situations
    - Complex issues beyond AI capability
    - Angry customers (negative sentiment)
    - Unclear intents
    """
    
    def __init__(self):
        super().__init__(
            agent_type="escalation",
            model="claude-3-haiku-20240307",
            temperature=0.3
        )
    
    def process(self, state: AgentState) -> AgentState:
        """Process escalation"""
        print(f"\n{'='*60}")
        print(f"🚨 ESCALATION AGENT PROCESSING")
        print(f"{'='*60}")
        
        state = self.add_to_history(state)
        state["turn_count"] = state.get("turn_count", 0) + 1
        
        message = state["current_message"]
        reason = state.get("escalation_reason", "Low confidence")
        
        print(f"Message: {message[:100]}...")
        print(f"Reason: {reason}")
        
        # Generate handoff message
        response = self.generate_handoff_message(message, reason, state)
        
        state["agent_response"] = response
        state["should_escalate"] = True
        state["next_agent"] = None
        state["status"] = "escalated"
        
        print(f"✓ Escalated to human")
        
        return state
    
    def generate_handoff_message(self, message: str, reason: str, state: AgentState) -> str:
        """Generate friendly escalation message"""
        system_prompt = """You are creating a handoff message to a human agent.

Be:
1. Empathetic and apologetic
2. Explain you're connecting them with a specialist
3. Set expectations (response time)
4. Thank them for patience

Keep it brief and professional."""

        user_prompt = f"""Customer message: {message}

Escalation reason: {reason}

Create a friendly handoff message."""

        return self.call_llm(system_prompt, user_prompt, max_tokens=200)


if __name__ == "__main__":
    from workflow.state import create_initial_state
    
    state = create_initial_state("This is really frustrating!")
    state["escalation_reason"] = "Negative sentiment"
    
    agent = EscalationAgent()
    result = agent.process(state)
    
    print(f"\n{'='*60}")
    print(f"Response:\n{result['agent_response']}")