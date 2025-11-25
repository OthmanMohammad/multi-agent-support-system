"use client";

import type { JSX } from "react";
import { useState } from "react";
import { Download, Trash2, CheckCircle, AlertTriangle, MessageSquare } from "lucide-react";
import type { Conversation } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { useDeleteConversation, useResolveConversation } from "@/lib/api/hooks/useConversations";
import { useChatStore } from "@/stores/chat-store";
import { ExportDialog } from "./export-dialog";
import { Badge } from "@/components/ui/badge";

interface ChatHeaderProps {
  conversation: Conversation;
}

/**
 * Chat Header Component
 * Header with conversation title, status, and actions
 */
export function ChatHeader({ conversation }: ChatHeaderProps): JSX.Element {
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);

  const deleteConversation = useDeleteConversation();
  const resolveConversation = useResolveConversation();
  const setCurrentConversation = useChatStore(
    (state) => state.setCurrentConversation
  );
  const messages = useChatStore((state) => state.messages);

  // Generate display title from primary_intent or default
  const displayTitle = conversation.title ||
    conversation.primary_intent?.replace(/_/g, " ") ||
    "Conversation";

  const handleDelete = async (): Promise<void> => {
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      try {
        await deleteConversation.mutateAsync(conversation.conversation_id);
        setCurrentConversation(null);
      } catch (error) {
        console.error("Failed to delete conversation:", error);
      }
    }
  };

  const handleResolve = async (): Promise<void> => {
    try {
      await resolveConversation.mutateAsync(conversation.conversation_id);
    } catch (error) {
      console.error("Failed to resolve conversation:", error);
    }
  };

  const handleExport = (): void => {
    setIsExportDialogOpen(true);
  };

  const getStatusBadge = () => {
    switch (conversation.status) {
      case "resolved":
        return (
          <Badge variant="outline" className="bg-success/10 text-success border-success/20">
            <CheckCircle className="h-3 w-3 mr-1" />
            Resolved
          </Badge>
        );
      case "escalated":
        return (
          <Badge variant="outline" className="bg-warning/10 text-warning border-warning/20">
            <AlertTriangle className="h-3 w-3 mr-1" />
            Escalated
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" className="bg-accent/10 text-accent border-accent/20">
            <MessageSquare className="h-3 w-3 mr-1" />
            Active
          </Badge>
        );
    }
  };

  return (
    <>
      <header className="flex items-center justify-between border-b border-border p-4">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-lg font-semibold capitalize">{displayTitle}</h1>
            {getStatusBadge()}
          </div>
          <p className="text-sm text-foreground-secondary">
            {conversation.agent_history && conversation.agent_history.length > 0
              ? `Agents: ${conversation.agent_history.join(" → ")}`
              : "AI-powered multi-agent support"}
          </p>
        </div>

        <div className="flex items-center gap-2">
          {conversation.status === "active" && (
            <Button
              size="icon"
              variant="ghost"
              onClick={handleResolve}
              disabled={resolveConversation.isPending}
              title="Mark as resolved"
              className="text-success hover:text-success"
            >
              <CheckCircle className="h-4 w-4" />
            </Button>
          )}
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
            disabled={deleteConversation.isPending}
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
