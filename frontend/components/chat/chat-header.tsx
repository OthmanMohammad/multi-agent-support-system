"use client";

import type { JSX } from "react";
import { useState } from "react";
import { Download, Trash2 } from "lucide-react";
import type { Conversation } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { useConversations } from "@/lib/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";
import { ExportDialog } from "./export-dialog";

interface ChatHeaderProps {
  conversation: Conversation;
}

/**
 * Chat Header Component
 * Header with conversation title and actions
 */
export function ChatHeader({ conversation }: ChatHeaderProps): JSX.Element {
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);

  const { deleteConversation } = useConversations();
  const setCurrentConversation = useChatStore(
    (state) => state.setCurrentConversation
  );
  const messages = useChatStore((state) => state.messages);

  const handleDelete = async (): Promise<void> => {
    // eslint-disable-next-line no-alert -- Simple confirmation for delete action
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      try {
        await deleteConversation(conversation.conversation_id);
        setCurrentConversation(null);
      } catch (error) {
        console.error("Failed to delete conversation:", error);
      }
    }
  };

  const handleExport = (): void => {
    setIsExportDialogOpen(true);
  };

  const displayTitle =
    conversation.primary_intent ||
    `Conversation ${conversation.conversation_id.slice(0, 8)}...`;

  return (
    <>
      <header className="flex items-center justify-between border-b border-border p-4">
        <div>
          <h1 className="text-lg font-semibold">{displayTitle}</h1>
          <p className="text-sm text-foreground-secondary">
            AI-powered multi-agent support
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            size="icon"
            variant="ghost"
            onClick={handleExport}
            title="Export conversation"
          >
            <Download className="h-4 w-4" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            onClick={handleDelete}
            title="Delete conversation"
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
      </header>

      <ExportDialog
        conversation={conversation}
        messages={messages}
        isOpen={isExportDialogOpen}
        onClose={() => setIsExportDialogOpen(false)}
      />
    </>
  );
}
