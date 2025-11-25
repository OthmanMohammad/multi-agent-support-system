"use client";

import type { JSX } from "react";
import { useChatStore } from "@/stores/chat-store";
import { ConversationSidebar } from "@/components/chat/conversation-sidebar";
import { ChatArea } from "@/components/chat/chat-area";
import { ErrorBoundaryAdvanced } from "@/components/error-boundary-advanced";

/**
 * Chat Page - Main chat interface
 * Features:
 * - Conversation sidebar with search and filters
 * - Real-time message streaming
 * - Markdown rendering with syntax highlighting
 * - File upload support
 * - Keyboard shortcuts
 * - Agent routing visualization
 */
export default function ChatPage(): JSX.Element {
  const currentConversationId = useChatStore(
    (state) => state.currentConversationId
  );
  const isSidebarOpen = useChatStore((state) => state.isSidebarOpen);

  return (
    <ErrorBoundaryAdvanced
      onError={(error, errorInfo) => {
        console.error("Chat page error:", error, errorInfo);
      }}
    >
      <div className="flex h-screen overflow-hidden bg-background">
        {/* Conversation Sidebar */}
        <ConversationSidebar />

        {/* Main Chat Area */}
        <main
          className={`flex flex-1 flex-col transition-all duration-300 ${
            isSidebarOpen ? "ml-0" : "-ml-80"
          }`}
        >
          {/* ChatArea handles both existing conversations and new conversation flow */}
          <ChatArea conversationId={currentConversationId} />
        </main>
      </div>
    </ErrorBoundaryAdvanced>
  );
}
