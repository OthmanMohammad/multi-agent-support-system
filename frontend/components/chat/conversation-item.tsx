"use client";

import type { JSX } from "react";
import { useState } from "react";
import { Trash2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { Conversation } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { useConversations } from "@/lib/hooks/useConversations";
import { cn } from "@/lib/utils";

interface ConversationItemProps {
  conversation: Conversation;
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
  // Generate title from primary_intent or use fallback
  const displayTitle =
    conversation.primary_intent ||
    `Conversation ${conversation.conversation_id.slice(0, 8)}...`;

  const [showActions, setShowActions] = useState(false);

  const { deleteConversation } = useConversations();

  const handleDelete = async (e: React.MouseEvent): Promise<void> => {
    e.stopPropagation();
    // eslint-disable-next-line no-alert -- Simple confirmation for delete action
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      try {
        await deleteConversation(conversation.conversation_id);
      } catch (error) {
        console.error("Failed to delete conversation:", error);
      }
    }
  };

  return (
    <div
      className={cn(
        "group relative flex cursor-pointer items-center gap-3 rounded-lg p-3 transition-colors hover:bg-surface",
        isActive && "bg-surface"
      )}
      onClick={onClick}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
    >
      <div className="flex-1 overflow-hidden">
        <p className="truncate text-sm font-medium">{displayTitle}</p>
        <p className="text-xs text-foreground-secondary">
          {formatDistanceToNow(new Date(conversation.last_updated), {
            addSuffix: true,
          })}
        </p>
      </div>

      {/* Actions */}
      {showActions && (
        <div
          className="flex items-center gap-1"
          onClick={(e) => e.stopPropagation()}
        >
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7 text-error hover:text-error"
            onClick={handleDelete}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}
