"""
Base Agent - Abstract class that all agents inherit from
"""
from abc import ABC, abstractmethod
from typing import Optional
from anthropic import Anthropic
import os
from dotenv import load_dotenv

# Import state from workflow package
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from workflow.state import AgentState, AgentType

load_dotenv()


class BaseAgent(ABC):
    """
    Abstract base class for all agents.
    
    Each agent must implement:
    - process(): Main logic to handle state
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        model: str = "claude-3-haiku-20240307",
        temperature: float = 0.3
    ):
        """
        Initialize base agent
        
        Args:
            agent_type: Type of agent (router, billing, etc.)
            model: Claude model to use
            temperature: LLM temperature (0-1)
        """
        self.agent_type = agent_type
        self.model = model
        self.temperature = temperature
        
        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        
        self.client = Anthropic(api_key=api_key)
        
        print(f"✓ {self.agent_type.upper()} agent initialized")
    
    @abstractmethod
    def process(self, state: AgentState) -> AgentState:
        """
        Process the state and return updated state.
        
        This is the main method each agent must implement.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated agent state with:
            - agent_response: What to say to user
            - next_agent: Where to route next (or None for END)
            - Other updates as needed
        """
        pass
    
    def call_llm(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1024
    ) -> str:
        """
        Call Claude with a prompt
        
        Args:
            system_prompt: System instructions
            user_message: User's message
            max_tokens: Max response length
            
        Returns:
            Claude's response text
        """
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": user_message
                    }
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            return f"Error: {str(e)}"
    
    def should_escalate(self, state: AgentState) -> bool:
        """
        Determine if conversation should escalate to human
        
        Args:
            state: Current state
            
        Returns:
            True if should escalate
        """
        # Low confidence
        if state.get("response_confidence", 1.0) < 0.4:
            return True
        
        # Too many agent hops (circular routing)
        if state.get("turn_count", 0) >= state.get("max_turns", 5):
            return True
        
        # Very negative sentiment
        if state.get("sentiment", 0.0) < -0.7:
            return True
        
        # Already marked for escalation
        if state.get("should_escalate", False):
            return True
        
        return False
    
    def add_to_history(self, state: AgentState) -> AgentState:
        """
        Add current agent to agent_history
        
        Args:
            state: Current state
            
        Returns:
            Updated state with agent in history
        """
        agent_history = state.get("agent_history", [])
        if self.agent_type not in agent_history:
            agent_history.append(self.agent_type)
        
        state["agent_history"] = agent_history
        state["current_agent"] = self.agent_type
        
        return state


if __name__ == "__main__":
    # Test base agent (can't instantiate abstract class directly)
    print("BaseAgent is an abstract class.")
    print("Test by creating a concrete agent (router, billing, etc.)")