"use client";

import type { JSX } from "react";
import { useState } from "react";
import { Trash2, CheckCircle, AlertTriangle, MessageSquare } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { ConversationListItem } from "@/lib/api/types";
import { Button } from "@/components/ui/button";
import { useDeleteConversation, useResolveConversation } from "@/lib/api/hooks/useConversations";
import { cn } from "@/lib/utils";

interface ConversationItemProps {
  conversation: ConversationListItem;
  isActive: boolean;
  onClick: () => void;
}

/**
 * Conversation Item Component
 * Individual conversation in the sidebar with actions
 */
export function ConversationItem({
  conversation,
  isActive,
  onClick,
}: ConversationItemProps): JSX.Element {
  const [showActions, setShowActions] = useState(false);

  const deleteConversation = useDeleteConversation();
  const resolveConversation = useResolveConversation();

  // Generate a display title from intent or use default
  const displayTitle = conversation.title ||
    conversation.primary_intent?.replace(/_/g, " ") ||
    "New Conversation";

  const handleDelete = async (e: React.MouseEvent): Promise<void> => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      try {
        await deleteConversation.mutateAsync(conversation.conversation_id);
      } catch (error) {
        console.error("Failed to delete conversation:", error);
      }
    }
  };

  const handleResolve = async (e: React.MouseEvent): Promise<void> => {
    e.stopPropagation();
    try {
      await resolveConversation.mutateAsync(conversation.conversation_id);
    } catch (error) {
      console.error("Failed to resolve conversation:", error);
    }
  };

  // Status indicator
  const getStatusIcon = () => {
    switch (conversation.status) {
      case "resolved":
        return <CheckCircle className="h-3 w-3 text-success" />;
      case "escalated":
        return <AlertTriangle className="h-3 w-3 text-warning" />;
      default:
        return <MessageSquare className="h-3 w-3 text-accent" />;
    }
  };

  return (
    <div
      className={cn(
        "group relative flex cursor-pointer items-center gap-3 rounded-lg p-3 transition-colors hover:bg-surface",
        isActive && "bg-surface",
        conversation.status === "resolved" && "opacity-70"
      )}
      onClick={onClick}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      {/* Status Icon */}
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-surface">
        {getStatusIcon()}
      </div>

      <div className="flex-1 overflow-hidden">
        <p className="truncate text-sm font-medium capitalize">{displayTitle}</p>
        <div className="flex items-center gap-2 text-xs text-foreground-secondary">
          <span>
            {formatDistanceToNow(new Date(conversation.last_updated || conversation.started_at), {
              addSuffix: true,
            })}
          </span>
          {conversation.agent_history && conversation.agent_history.length > 0 && (
            <span className="truncate">
              {conversation.agent_history[conversation.agent_history.length - 1]}
            </span>
          )}
        </div>
      </div>

      {/* Actions */}
      {showActions && (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          {conversation.status === "active" && (
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-success hover:text-success"
              onClick={handleResolve}
              disabled={resolveConversation.isPending}
              title="Mark as resolved"
            >
              <CheckCircle className="h-3.5 w-3.5" />
            </Button>
          )}
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7 text-error hover:text-error"
            onClick={handleDelete}
            disabled={deleteConversation.isPending}
            title="Delete conversation"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}
