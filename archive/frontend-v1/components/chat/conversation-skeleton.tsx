import type { JSX } from "react";
import { ShimmerSkeleton } from "@/components/ui/skeleton";

/**
 * Conversation Item Skeleton
 * Loading state for conversation list items
 */
export function ConversationItemSkeleton(): JSX.Element {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-border bg-surface p-3">
      <ShimmerSkeleton className="h-10 w-10 shrink-0 rounded-full" />
      <div className="flex-1 space-y-2">
        <ShimmerSkeleton className="h-4 w-3/4" />
        <ShimmerSkeleton className="h-3 w-1/2" />
      </div>
      <ShimmerSkeleton className="h-8 w-8 rounded" />
    </div>
  );
}

/**
 * Conversation Sidebar Skeleton
 * Loading state for entire conversation sidebar
 */
export function ConversationSidebarSkeleton(): JSX.Element {
  return (
    <div className="space-y-4 p-4">
      {/* Search bar */}
      <ShimmerSkeleton className="h-10 w-full rounded-lg" />

      {/* New conversation button */}
      <ShimmerSkeleton className="h-10 w-full rounded-lg" />

      {/* Conversation list */}
      <div className="space-y-2">
        {Array.from({ length: 5 }).map((_, i) => (
          <ConversationItemSkeleton key={i} />
        ))}
      </div>
    </div>
  );
}
