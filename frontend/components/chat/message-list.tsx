"use client";

import type { JSX } from "react";
import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores/chat-store";
import { Message } from "./message";
import { TypingIndicator } from "./typing-indicator";
import { ScrollArea } from "@/components/ui/scroll-area";

interface MessageListProps {
  conversationId: string;
}

/**
 * Message List Component
 * Displays list of messages with auto-scroll
 */
export function MessageList({ conversationId }: MessageListProps): JSX.Element {
  const messages = useChatStore((state) => state.messages);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const streamingMessage = useChatStore((state) => state.streamingMessage);

  const scrollRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingMessage]);

  return (
    <ScrollArea ref={scrollRef} className="flex-1 p-4">
      <div className="mx-auto max-w-3xl space-y-6">
        {messages.length === 0 && !isStreaming ? (
          <div className="flex h-full items-center justify-center py-12 text-center">
            <div>
              <p className="text-lg font-medium text-foreground-secondary">
                Start a conversation
              </p>
              <p className="mt-2 text-sm text-foreground-secondary">
                Type a message below to begin chatting with our AI support
                agents.
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <Message key={message.id} message={message} />
            ))}

            {/* Streaming message */}
            {isStreaming && streamingMessage && (
              <Message
                message={{
                  id: "streaming",
                  conversationId,
                  userId: "system",
                  role: "ASSISTANT",
                  content: streamingMessage,
                  metadata: null,
                  createdAt: new Date(),
                }}
                isStreaming
              />
            )}

            {/* Typing indicator */}
            {isStreaming && !streamingMessage && <TypingIndicator />}
          </>
        )}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
