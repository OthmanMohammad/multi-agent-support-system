"""
Simple chat agent with conversation memory and vector-based knowledge base
semantic search powered by Qdrant Cloud
"""
from anthropic import Anthropic
import os
from dotenv import load_dotenv
from knowledge_base import search_articles

load_dotenv()

SYSTEM_PROMPT = """You are a helpful customer support agent for a project management SaaS tool.

Be:
- Concise and friendly
- Professional but approachable
- Solution-oriented

When you use information from the knowledge base, cite the article title.

If you don't know something, say so clearly."""

MAX_HISTORY_MESSAGES = 20


def chat(message: str, conversation_history: list = None) -> tuple[str, list, list]:
    """
    Send a message and get a response with knowledge base search
    
    Args:
        message: User's message
        conversation_history: List of previous messages
        
    Returns:
        (response_text, updated_history, kb_results)
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    
    # Initialize history if none provided
    if conversation_history is None:
        conversation_history = []
    
    # Search knowledge base with vector search
    print(f"🔍 Searching KB for: '{message[:50]}...'")
    kb_results = search_articles(message, limit=3, use_vector=True)
    
    # Build context from KB
    kb_context = ""
    if kb_results:
        kb_context = "\n\nRelevant Knowledge Base Articles:\n"
        for i, article in enumerate(kb_results, 1):
            kb_context += f"\n{i}. {article['title']}\n{article['content']}\n"
            kb_context += f"   (Relevance: {article['similarity_score']:.2%})\n"
        print(f"✓ Found {len(kb_results)} relevant articles")
    else:
        print("⚠ No relevant articles found")
    
    # Add user message with KB context to history
    user_message = message
    if kb_context:
        user_message += kb_context
    
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    # Trim history if too long
    if len(conversation_history) > MAX_HISTORY_MESSAGES:
        conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]
    
    # Get response from Claude
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
    
    return response_text, conversation_history, kb_results


def interactive_chat():
    """Run an interactive chat session with memory and vector search"""
    print("=" * 60)
    print("🤖 AI Customer Support Agent (Vector Search Enabled!)")
    print("=" * 60)
    print("Type 'quit' to exit")
    print("-" * 60)
    
    conversation_history = []
    turn_count = 0
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            # Show conversation stats
            print("\n" + "=" * 60)
            print("📊 Conversation Summary:")
            print(f"   Turns: {turn_count}")
            print(f"   Total messages: {len(conversation_history)}")
            print("=" * 60)
            print("Goodbye! 👋")
            break
            
        if not user_input:
            continue
            
        try:
            response, conversation_history, kb_results = chat(
                user_input, 
                conversation_history
            )
            turn_count += 1
            
            # Show which articles were used
            if kb_results:
                print(f"\n📚 Using {len(kb_results)} KB articles:")
                for i, article in enumerate(kb_results, 1):
                    score_pct = article['similarity_score'] * 100
                    print(f"   {i}. {article['title']} ({score_pct:.0f}% relevant)")
            
            print(f"\nAgent: {response}")
            print(f"\n(Turn {turn_count})")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    interactive_chat()