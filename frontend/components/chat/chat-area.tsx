"use client";

import type { JSX } from "react";
import { useEffect, useState } from "react";
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
 */
export function ChatArea({ conversationId }: ChatAreaProps): JSX.Element {
  const { conversation, isLoading, reopen } = useConversation(conversationId);
  const clearMessages = useChatStore((state) => state.clearMessages);
  const [isReopening, setIsReopening] = useState(false);

  // Load messages when conversation changes
  useEffect(() => {
    if (conversation) {
      // In a real app, fetch messages from API
      // For now, use store
      clearMessages();
    }
  }, [conversation, clearMessages]);

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
