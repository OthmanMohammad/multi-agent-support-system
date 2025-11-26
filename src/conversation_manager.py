"""
Conversation Manager - Load and list saved conversations
"""

import json
import os
from datetime import datetime

CONVERSATIONS_DIR = "data/conversations"


def list_conversations() -> list[dict]:
    """
    List all saved conversations

    Returns:
        List of conversation metadata sorted by date (newest first)
    """
    if not os.path.exists(CONVERSATIONS_DIR):
        return []

    conversations = []

    for filename in os.listdir(CONVERSATIONS_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            try:
                with open(filepath, encoding="utf-8") as f:
                    data = json.load(f)

                    # Extract summary info
                    conversations.append(
                        {
                            "filename": filename,
                            "date": data.get("date"),
                            "timestamp": data.get("timestamp"),
                            "turns": data.get("turns", 0),
                            "articles": data.get("articles_referenced", 0),
                            "first_message": data["messages"][0]["content"][:50] + "..."
                            if data["messages"]
                            else "Empty",
                        }
                    )
            except Exception as e:
                print(f"Error reading {filename}: {e}")

    # Sort by date (newest first)
    conversations.sort(key=lambda x: x["timestamp"], reverse=True)

    return conversations


def load_conversation(filename: str) -> dict | None:
    """
    Load a specific conversation by filename

    Args:
        filename: Name of conversation file

    Returns:
        Conversation data or None if not found
    """
    filepath = os.path.join(CONVERSATIONS_DIR, filename)

    if not os.path.exists(filepath):
        print(f"Conversation not found: {filename}")
        return None

    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading conversation: {e}")
        return None


def display_conversation_list():
    """Display all saved conversations in a nice format"""
    conversations = list_conversations()

    if not conversations:
        print("No saved conversations found.")
        return

    print("\n" + "=" * 70)
    print("📁 Saved Conversations")
    print("=" * 70)

    for i, conv in enumerate(conversations, 1):
        date_obj = datetime.fromisoformat(conv["date"])
        date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n{i}. {conv['filename']}")
        print(f"   Date: {date_str}")
        print(f"   Turns: {conv['turns']} | Articles: {conv['articles']}")
        print(f"   Preview: {conv['first_message']}")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Test the conversation manager
    display_conversation_list()
