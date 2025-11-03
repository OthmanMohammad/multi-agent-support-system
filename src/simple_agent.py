"""
Simple chat agent - MVP
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


def chat(message: str) -> str:
    """Send a message and get a response"""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": message
        }]
    )
    
    return response.content[0].text


def interactive_chat():
    """Run an interactive chat session"""
    print("Chat Agent Ready! (type 'quit' to exit)")
    print("-" * 50)
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
            
        if not user_input:
            continue
            
        try:
            response = chat(user_input)
            print(f"\nAgent: {response}")
        except Exception as e:
            print(f"\nError: {e}")


if __name__ == "__main__":
    interactive_chat()