import type { JSX } from "react";
import { ShimmerSkeleton, SkeletonText } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface MessageSkeletonProps {
  variant?: "user" | "assistant";
}

/**
 * Message Skeleton Component
 * Loading state for individual messages
 */
export function MessageSkeleton({
  variant = "assistant",
}: MessageSkeletonProps): JSX.Element {
  const isUser = variant === "user";

  return (
    <div
      className={cn(
        "group flex gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      {/* Avatar */}
      <ShimmerSkeleton className="h-8 w-8 shrink-0 rounded-full" />

      {/* Message content */}
      <div className={cn("flex-1 space-y-2", isUser ? "items-end" : "items-start")}>
        {/* Message bubble */}
        <div
          className={cn(
            "max-w-[80%] rounded-lg border border-border p-4",
            isUser
              ? "ml-auto bg-accent/10"
              : "mr-auto bg-surface"
          )}
        >
          <SkeletonText
            lines={3}
            lastLineWidth={isUser ? "60%" : "75%"}
            className="space-y-3"
          />
        </div>

        {/* Timestamp */}
        <ShimmerSkeleton
          className={cn("h-3 w-16", isUser ? "ml-auto" : "mr-auto")}
        />
      </div>
    </div>
  );
}

/**
 * Message List Skeleton
 * Loading state for entire message list
 */
export function MessageListSkeleton(): JSX.Element {
  return (
    <div className="space-y-6 p-4">
      <MessageSkeleton variant="user" />
      <MessageSkeleton variant="assistant" />
      <MessageSkeleton variant="user" />
      <MessageSkeleton variant="assistant" />
      <MessageSkeleton variant="user" />
    </div>
  );
}

/**
 * Chat Area Skeleton
 * Loading state for entire chat area (header + messages + input)
 */
export function ChatAreaSkeleton(): JSX.Element {
  return (
    <div className="flex h-full flex-col">
      {/* Header skeleton */}
      <div className="border-b border-border p-4">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <ShimmerSkeleton className="h-6 w-48" />
            <ShimmerSkeleton className="h-4 w-32" />
          </div>
          <div className="flex gap-2">
            <ShimmerSkeleton className="h-8 w-8 rounded" />
            <ShimmerSkeleton className="h-8 w-8 rounded" />
          </div>
        </div>
      </div>

      {/* Messages skeleton */}
      <div className="flex-1 overflow-y-auto">
        <MessageListSkeleton />
      </div>

      {/* Input skeleton */}
      <div className="border-t border-border p-4">
        <ShimmerSkeleton className="h-20 w-full rounded-lg" />
      </div>
    </div>
  );
}
