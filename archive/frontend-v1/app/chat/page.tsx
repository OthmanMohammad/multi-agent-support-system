"use client";

import type { JSX } from "react";
import { useChatStore } from "@/stores/chat-store";
import { ConversationSidebar } from "@/components/chat/conversation-sidebar";
import { ChatArea } from "@/components/chat/chat-area";
import { EmptyState } from "@/components/chat/empty-state";
import { ErrorBoundaryAdvanced } from "@/components/error-boundary-advanced";
import { AuthGuard } from "@/components/auth/auth-guard";

/**
 * Chat Page - Main chat interface
 *
 * Protected route requiring authentication.
 * Features:
 * - Conversation sidebar with search and filters
 * - Real-time message streaming
 * - Markdown rendering with syntax highlighting
 * - File upload support
 * - Keyboard shortcuts
 * - Agent routing visualization
 */
export default function ChatPage(): JSX.Element {
  return (
    <AuthGuard>
      <ChatContent />
    </AuthGuard>
  );
}

/**
 * Chat Content Component
 *
 * Contains the actual chat UI, rendered only when authenticated.
 */
function ChatContent(): JSX.Element {
  const currentConversationId = useChatStore(
    (state) => state.currentConversationId
  );
  const isSidebarOpen = useChatStore((state) => state.isSidebarOpen);

  return (
    <ErrorBoundaryAdvanced
      onError={(error, errorInfo) => {
        // Log to monitoring service
        console.error("Chat page error:", error, errorInfo);
        // TODO: Send to Sentry or other monitoring service
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
          {currentConversationId ? (
            <ChatArea conversationId={currentConversationId} />
          ) : (
            <EmptyState />
          )}
        </main>
      </div>
    </ErrorBoundaryAdvanced>
  );
}
