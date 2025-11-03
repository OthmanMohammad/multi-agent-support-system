"""
Conversation Storage - In-memory storage for conversations
(Will be replaced with PostgreSQL in future)
"""
from typing import Dict, List, Optional
from datetime import datetime
import json
from uuid import uuid4


class ConversationStore:
    """
    In-memory conversation storage
    
    Stores:
    - Full conversation history
    - Agent interactions
    - Metadata
    """
    
    def __init__(self):
        """Initialize empty store"""
        self.conversations: Dict[str, Dict] = {}
        print("✓ ConversationStore initialized (in-memory)")
    
    def create_conversation(
        self,
        conversation_id: str = None,
        customer_id: str = "default_customer"
    ) -> str:
        """
        Create new conversation
        
        Args:
            conversation_id: Optional ID (generated if not provided)
            customer_id: Customer identifier
            
        Returns:
            Conversation ID
        """
        if conversation_id is None:
            conversation_id = str(uuid4())
        
        if conversation_id in self.conversations:
            # Already exists
            return conversation_id
        
        self.conversations[conversation_id] = {
            "conversation_id": conversation_id,
            "customer_id": customer_id,
            "messages": [],
            "agent_history": [],
            "status": "active",
            "started_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }
        
        return conversation_id
    
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        agent_name: Optional[str] = None
    ):
        """
        Add message to conversation
        
        Args:
            conversation_id: Conversation ID
            role: "user" or "assistant"
            content: Message content
            agent_name: Which agent sent this
        """
        if conversation_id not in self.conversations:
            self.create_conversation(conversation_id)
        
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "agent_name": agent_name
        }
        
        self.conversations[conversation_id]["messages"].append(message)
        self.conversations[conversation_id]["last_updated"] = datetime.now().isoformat()
    
    def update_agent_history(
        self,
        conversation_id: str,
        agent_history: List[str]
    ):
        """Update which agents were involved"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["agent_history"] = agent_history
            self.conversations[conversation_id]["last_updated"] = datetime.now().isoformat()
    
    def update_status(
        self,
        conversation_id: str,
        status: str
    ):
        """Update conversation status"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["status"] = status
            self.conversations[conversation_id]["last_updated"] = datetime.now().isoformat()
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get full conversation"""
        return self.conversations.get(conversation_id)
    
    def list_conversations(
        self,
        customer_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        List conversations
        
        Args:
            customer_id: Filter by customer
            limit: Max results
            
        Returns:
            List of conversations
        """
        conversations = list(self.conversations.values())
        
        # Filter by customer
        if customer_id:
            conversations = [
                c for c in conversations
                if c["customer_id"] == customer_id
            ]
        
        # Sort by last updated (newest first)
        conversations.sort(
            key=lambda x: x["last_updated"],
            reverse=True
        )
        
        return conversations[:limit]
    
    def get_stats(self) -> Dict:
        """Get storage statistics"""
        total_conversations = len(self.conversations)
        total_messages = sum(
            len(c["messages"])
            for c in self.conversations.values()
        )
        
        # Count agent usage
        agent_usage = {}
        for conv in self.conversations.values():
            for agent in conv["agent_history"]:
                agent_usage[agent] = agent_usage.get(agent, 0) + 1
        
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "agent_usage": agent_usage
        }
    
    def clear(self):
        """Clear all data (for testing)"""
        self.conversations.clear()


# Global store instance
_store = None


def get_store() -> ConversationStore:
    """Get or create global store"""
    global _store
    if _store is None:
        _store = ConversationStore()
    return _store


if __name__ == "__main__":
    # Test storage
    print("Testing ConversationStore...")
    
    store = ConversationStore()
    
    # Create conversation
    conv_id = store.create_conversation(customer_id="test_user")
    print(f"✓ Created: {conv_id}")
    
    # Add messages
    store.add_message(conv_id, "user", "Hello")
    store.add_message(conv_id, "assistant", "Hi there!", agent_name="router")
    print(f"✓ Added 2 messages")
    
    # Update
    store.update_agent_history(conv_id, ["router", "billing"])
    store.update_status(conv_id, "resolved")
    
    # Get conversation
    conv = store.get_conversation(conv_id)
    print(f"✓ Retrieved conversation: {len(conv['messages'])} messages")
    
    # Stats
    stats = store.get_stats()
    print(f"✓ Stats: {stats}")
    
    print("\n✓ Storage working correctly!")