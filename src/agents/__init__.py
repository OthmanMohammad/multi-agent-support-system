"""
Agents package - Multi-agent system components

Auto-loads all agents on import to register them in AgentRegistry.
"""

# Auto-load all agents on package import
from src.agents.loader import load_all_agents

# This ensures all agents are registered when you do:
# from src.agents import ...
# or
# import src.agents
load_all_agents()