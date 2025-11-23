"use client";

import type { JSX } from "react";
import { useState } from "react";
import { MoreVertical, Trash2, Edit2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import type { Conversation } from "@/lib/types/api";
import { Button } from "@/components/ui/button";
import { useDeleteConversation, useUpdateConversation } from "@/lib/api/hooks/useConversations";
import { Input } from "@/components/ui/input";
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
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState(conversation.title);
  const [showActions, setShowActions] = useState(false);

  const deleteConversation = useDeleteConversation();
  const updateConversation = useUpdateConversation(conversation.id);

  const handleDelete = async (e: React.MouseEvent): Promise<void> => {
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      try {
        await deleteConversation.mutateAsync(conversation.id);
      } catch (error) {
        console.error("Failed to delete conversation:", error);
      }
    }
  };

  const handleRename = async (): Promise<void> => {
    if (title.trim() && title !== conversation.title) {
      try {
        await updateConversation.mutateAsync({ title: title.trim() });
      } catch (error) {
        console.error("Failed to update conversation:", error);
        setTitle(conversation.title);
      }
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === "Enter") {
      void handleRename();
    } else if (e.key === "Escape") {
      setTitle(conversation.title);
      setIsEditing(false);
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
        {isEditing ? (
          <Input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            onBlur={handleRename}
            onKeyDown={handleKeyDown}
            onClick={(e) => e.stopPropagation()}
            className="h-8 text-sm"
            autoFocus
          />
        ) : (
          <>
            <p className="truncate text-sm font-medium">{conversation.title}</p>
            <p className="text-xs text-foreground-secondary">
              {formatDistanceToNow(new Date(conversation.updatedAt), {
                addSuffix: true,
              })}
            </p>
          </>
        )}
      </div>

      {/* Actions */}
      {showActions && !isEditing && (
        <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={() => setIsEditing(true)}
          >
            <Edit2 className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7 text-error hover:text-error"
            onClick={handleDelete}
            disabled={deleteConversation.isPending}
          >
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
      )}
    </div>
  );
}
