"use client";

import type { JSX } from "react";
import { useEffect } from "react";
import { useConversation } from "@/lib/api/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";
import { ChatHeader } from "./chat-header";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";

interface ChatAreaProps {
  conversationId: string;
}

/**
 * Chat Area Component
 * Main chat interface with header, messages, and input
 */
export function ChatArea({ conversationId }: ChatAreaProps): JSX.Element {
  const { data: conversation, isLoading } = useConversation(conversationId);
  const setMessages = useChatStore((state) => state.setMessages);
  const clearMessages = useChatStore((state) => state.clearMessages);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversation) {
      // In a real app, fetch messages from API
      // For now, use store
      clearMessages();
    }
  }, [conversation, clearMessages]);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-foreground-secondary">Loading conversation...</div>
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
