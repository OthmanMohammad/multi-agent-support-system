"use client";

import type { JSX } from "react";
import { useEffect } from "react";
import { useConversation } from "@/lib/api/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";
import { ChatHeader } from "./chat-header";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";

interface ChatAreaProps {
  conversationId: string | null;
}

/**
 * Chat Area Component
 * Main chat interface with header, messages, and input
 */
export function ChatArea({ conversationId }: ChatAreaProps): JSX.Element {
  const { data: conversation, isLoading, error } = useConversation(conversationId);
  const setMessages = useChatStore((state) => state.setMessages);
  const clearMessages = useChatStore((state) => state.clearMessages);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversation?.messages) {
      // Transform backend messages to store format
      const storeMessages = conversation.messages.map((msg, index) => ({
        id: `${conversationId}-${index}`,
        conversationId: conversationId || "",
        userId: msg.role === "user" ? "current-user" : "assistant",
        role: msg.role.toUpperCase() as "USER" | "ASSISTANT" | "SYSTEM",
        content: msg.content,
        metadata: msg.agent_name ? { agent: msg.agent_name } : null,
        createdAt: new Date(msg.timestamp || new Date()),
      }));
      setMessages(storeMessages);
    } else if (!conversationId) {
      clearMessages();
    }
  }, [conversation, conversationId, setMessages, clearMessages]);

  // No conversation selected - show empty state
  if (!conversationId) {
    return (
      <div className="flex h-full flex-col">
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-xl font-semibold mb-2">Welcome to AI Support</h2>
            <p className="text-foreground-secondary mb-4">
              Start a new conversation or select one from the sidebar.
            </p>
            <p className="text-sm text-foreground-secondary">
              Type your message below to begin.
            </p>
          </div>
        </div>
        <MessageInput conversationId={null} />
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-foreground-secondary">Loading conversation...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center">
          <p className="text-error mb-2">Failed to load conversation</p>
          <p className="text-sm text-foreground-secondary">
            {error.message || "An unexpected error occurred"}
          </p>
        </div>
      </div>
    );
  }

  if (!conversation) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-foreground-secondary">Conversation not found</div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      <ChatHeader conversation={conversation} />
      <MessageList conversationId={conversationId} />
      <MessageInput conversationId={conversationId} />
    </div>
  );
}
