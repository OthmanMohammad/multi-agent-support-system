"""
Simple chat agent - MVP with conversation memory
"""
from anthropic import Anthropic
import os
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a helpful customer support agent for a project management SaaS tool.

Be:
- Concise and friendly
- Professional but approachable
- Solution-oriented

If you don't know something, say so clearly."""


def chat(message: str, conversation_history: list = None) -> tuple[str, list]:
    """
    Send a message and get a response
    
    Args:
        message: User's message
        conversation_history: List of previous messages
        
    Returns:
        (response_text, updated_history)
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Initialize history if none provided
    if conversation_history is None:
        conversation_history = []
    
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": message
    })
    
    # Get response
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=conversation_history
    )
    
    response_text = response.content[0].text
    
    # Add assistant response to history
    conversation_history.append({
        "role": "assistant",
        "content": response_text
    })
    
    return response_text, conversation_history


def interactive_chat():
    """Run an interactive chat session"""
    print("Chat Agent Ready! (type 'quit' to exit)")
    print("-" * 50)
    
    conversation_history = []
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
            
        if not user_input:
            continue
            
        try:
            response, conversation_history = chat(user_input, conversation_history)
            print(f"\nAgent: {response}")
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    interactive_chat()