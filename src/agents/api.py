"""
API Agent - Handles developer questions about REST API, webhooks, integrations
"""
import sys
from pathlib import Path
from typing import Dict, Optional

project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from workflow.state import AgentState
from agents.base import BaseAgent
from knowledge_base import search_articles


class APIAgent(BaseAgent):
    """
    API Agent - Specialist for developer integrations and API questions.
    
    Handles:
    - REST API endpoints and usage
    - Webhooks and event subscriptions
    - Authentication (API keys, OAuth)
    - Code examples in multiple languages
    - Rate limiting and error handling
    - Best practices and troubleshooting
    """
    
    def __init__(self):
        super().__init__(
            agent_type="api",
            model="claude-3-haiku-20240307",
            temperature=0.2  # Low temp for accurate, consistent code
        )
        
        # Supported programming languages for code examples
        self.supported_languages = [
            "python",
            "javascript", 
            "curl",
            "node",
            "ruby",
            "php"
        ]
    
    def process(self, state: AgentState) -> AgentState:
        """
        Process API-related developer requests
        
        Args:
            state: Current state
            
        Returns:
            Updated state with API documentation and code examples
        """
        print(f"\n{'='*60}")
        print(f"🔌 API AGENT PROCESSING")
        print(f"{'='*60}")
        
        # Add to history
        state = self.add_to_history(state)
        state["turn_count"] = state.get("turn_count", 0) + 1
        
        # Get message and intent
        message = state["current_message"]
        intent = state.get("primary_intent", "integration_api")
        
        print(f"Message: {message[:100]}...")
        print(f"Intent: {intent}")
        
        # Search API documentation in knowledge base
        kb_results = search_articles(
            message,
            category="api",
            limit=5  # More results for technical queries
        )
        state["kb_results"] = kb_results
        
        if kb_results:
            print(f"✓ Found {len(kb_results)} API articles")
            for article in kb_results[:3]:
                print(f"  - {article['title']} (score: {article['similarity_score']:.2f})")
        else:
            print("⚠ No API articles found - will provide general guidance")
        
        # Detect programming language preference
        requested_lang = self.detect_language_preference(message)
        print(f"Language preference: {requested_lang}")
        
        # Generate response with code examples
        response = self.generate_api_response(
            message=message,
            intent=intent,
            kb_results=kb_results,
            language=requested_lang
        )
        
        # Update state
        state["agent_response"] = response
        state["response_confidence"] = 0.9  # High confidence for API queries
        state["next_agent"] = None  # End conversation
        state["status"] = "resolved"
        
        print(f"\n✓ Response generated ({len(response)} chars)")
        
        return state
    
    def detect_language_preference(self, message: str) -> str:
        """
        Detect which programming language the user prefers from their message
        
        Args:
            message: User's message
            
        Returns:
            Detected language (defaults to 'python')
        """
        message_lower = message.lower()
        
        # Check for explicit language mentions
        language_keywords = {
            "python": ["python", "py", "django", "flask", "fastapi"],
            "javascript": ["javascript", "js", "react", "vue", "angular"],
            "node": ["node", "nodejs", "node.js", "express"],
            "curl": ["curl", "command line", "terminal", "bash"],
            "ruby": ["ruby", "rails", "rake"],
            "php": ["php", "laravel", "symfony"]
        }
        
        for lang, keywords in language_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                return lang
        
        # Default to Python (most common)
        return "python"
    
    def generate_api_response(
        self,
        message: str,
        intent: str,
        kb_results: list,
        language: str
    ) -> str:
        """
        Generate comprehensive API response with documentation and code
        
        Args:
            message: User's question
            intent: Classified intent
            kb_results: Knowledge base search results
            language: Preferred programming language
            
        Returns:
            Complete response with explanation and code examples
        """
        # Build KB context from search results
        kb_context = ""
        if kb_results:
            kb_context = "\n\nRelevant API Documentation:\n"
            for i, article in enumerate(kb_results, 1):
                kb_context += f"\n{i}. **{article['title']}**\n"
                kb_context += f"{article['content']}\n"
                kb_context += f"(Relevance: {article['similarity_score']:.0%})\n"
        
        system_prompt = f"""You are an expert API integration specialist helping developers.

Your responses should include:
1. **Clear explanation** of the API concept/endpoint
2. **Working code example** in {language.upper()}
3. **Authentication details** (how to get and use API keys)
4. **Common errors** and how to fix them
5. **Rate limiting** information if relevant
6. **Best practices** and security considerations

Guidelines:
- Always provide COMPLETE, RUNNABLE code examples
- Include proper error handling in code
- Use the provided KB articles as authoritative source
- Cite KB article titles when referencing them
- Use markdown code blocks with language tags
- Be concise but thorough
- Focus on practical implementation

When showing code:
- Include authentication headers
- Show both success and error handling
- Add helpful comments
- Use realistic variable names
- Format code properly"""

        user_prompt = f"""Developer Question: {message}

Intent: {intent}
Preferred Language: {language}
{kb_context}

Provide a complete answer with:
1. Explanation of how to accomplish this
2. Working code example in {language}
3. Any important notes about authentication, rate limits, or errors"""

        response = self.call_llm(
            system_prompt=system_prompt,
            user_message=user_prompt,
            max_tokens=1000  # Longer for code examples
        )
        
        return response


if __name__ == "__main__":
    # Test API agent
    print("=" * 60)
    print("TESTING API AGENT")
    print("=" * 60)
    
    from workflow.state import create_initial_state
    
    # Test case 1: Python API request
    print("\n" + "=" * 60)
    print("TEST 1: Python API Request")
    print("=" * 60)
    
    state = create_initial_state("How do I create a project via API in Python?")
    state["primary_intent"] = "integration_api"
    state["agent_history"] = ["router"]
    
    agent = APIAgent()
    result = agent.process(state)
    
    print(f"\n{'='*60}")
    print("RESULT")
    print(f"{'='*60}")
    print(f"Status: {result['status']}")
    print(f"Confidence: {result['response_confidence']}")
    print(f"Response:\n{result['agent_response']}")
    
    # Test case 2: Language detection
    print("\n\n" + "=" * 60)
    print("TEST 2: Language Detection")
    print("=" * 60)
    
    test_messages = [
        "show me a curl command",
        "give me javascript code",
        "how to do this in python",
        "node.js example please",
        "I need a php script"
    ]
    
    for msg in test_messages:
        detected = agent.detect_language_preference(msg)
        print(f"'{msg}' → {detected}")
    
    print("\n✓ All tests completed!")