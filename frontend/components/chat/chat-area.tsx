"use client";

import type { JSX } from "react";
import { useEffect, useState, useRef } from "react";
import { useConversation } from "@/lib/api/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";
import { ChatHeader } from "./chat-header";
import { MessageList } from "./message-list";
import { MessageInput } from "./message-input";
import { Button } from "@/components/ui/button";
import { RotateCcw, AlertCircle } from "lucide-react";

interface ChatAreaProps {
  conversationId: string;
}

/**
 * Chat Area Component
 * Main chat interface with header, messages, and input
 *
 * Architecture:
 * - Messages are sourced from API (conversation.messages)
 * - Zustand store is synchronized with API data
 * - Optimistic updates happen in message-input, then sync on API refresh
 */
export function ChatArea({ conversationId }: ChatAreaProps): JSX.Element {
  const { conversation, isLoading, reopen } = useConversation(conversationId);
  const setMessages = useChatStore((state) => state.setMessages);
  const setCurrentConversation = useChatStore((state) => state.setCurrentConversation);
  const [isReopening, setIsReopening] = useState(false);

  // Track previous conversation ID to detect actual conversation changes
  const prevConversationIdRef = useRef<string | null>(null);

  // Sync messages from API to store when conversation data changes
  useEffect(() => {
    if (conversation?.messages) {
      // Convert API messages to store format and sync
      const formattedMessages = conversation.messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
        agent_name: msg.agent_name,
        timestamp: msg.timestamp,
      }));
      setMessages(formattedMessages);
    }
  }, [conversation?.messages, setMessages]);

  // Track current conversation ID in store
  useEffect(() => {
    if (conversationId !== prevConversationIdRef.current) {
      setCurrentConversation(conversationId);
      prevConversationIdRef.current = conversationId;
    }
  }, [conversationId, setCurrentConversation]);

  const handleReopen = async (): Promise<void> => {
    setIsReopening(true);
    try {
      await reopen();
    } finally {
      setIsReopening(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-foreground-secondary">Loading conversation...</div>
      </div>
    );
  }

  // Clear stale conversation ID if conversation is not found (404)
  useEffect(() => {
    if (!isLoading && !conversation) {
      // Conversation doesn't exist - clear the stale ID from store
      setCurrentConversation(null);
    }
  }, [isLoading, conversation, setCurrentConversation]);

  if (!conversation) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-foreground-secondary">Conversation not found</div>
      </div>
    );
  }

  const isActive = conversation.status === "active";

  return (
    <div className="flex h-full flex-col">
      <ChatHeader conversation={conversation} />

      {/* Status Banner for non-active conversations */}
      {!isActive && (
        <div className="flex items-center justify-between gap-3 border-b border-border bg-amber-50 px-4 py-3 dark:bg-amber-950/20">
          <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">
              This conversation is {conversation.status}. Reopen to continue chatting.
            </span>
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={handleReopen}
            disabled={isReopening}
            className="shrink-0"
          >
            <RotateCcw className={`mr-2 h-4 w-4 ${isReopening ? "animate-spin" : ""}`} />
            {isReopening ? "Reopening..." : "Reopen"}
          </Button>
        </div>
      )}

      <MessageList conversationId={conversationId} />
      <MessageInput conversationId={conversationId} disabled={!isActive} />
    </div>
  );
}
