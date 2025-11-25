"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useConversations } from "@/lib/api/hooks";
import { format } from "date-fns";
import { Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

/**
 * Recent Conversations Component
 * Display recent conversations with search and filtering
 */

type StatusFilter = "active" | "resolved" | "escalated" | undefined;

export function RecentConversations(): JSX.Element {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>(undefined);
  const { conversations, isLoading } = useConversations(
    statusFilter ? { limit: 10, status: statusFilter } : { limit: 10 }
  );

  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <Skeleton className="mb-4 h-6 w-48" />
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      </div>
    );
  }

  if (!conversations || conversations.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <h2 className="text-lg font-semibold">Recent Conversations</h2>
        <p className="mt-2 text-foreground-secondary">No conversations found</p>
      </div>
    );
  }

  // Filter conversations by search
  const filteredConversations = search
    ? conversations.filter((conv) =>
        (conv.primary_intent || conv.conversation_id)
          .toLowerCase()
          .includes(search.toLowerCase())
      )
    : conversations;

  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Recent Conversations</h2>
          <p className="mt-1 text-sm text-foreground-secondary">
            {conversations.length} conversations
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
            <input
              type="text"
              placeholder="Search conversations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-10 w-64 rounded-lg border border-border bg-background pl-9 pr-4 text-sm placeholder:text-foreground-secondary focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2 rounded-lg border border-border bg-background p-1">
            {([undefined, "active", "resolved", "escalated"] as const).map(
              (s) => (
                <Button
                  key={s || "all"}
                  variant="ghost"
                  size="sm"
                  onClick={() => setStatusFilter(s)}
                  className={
                    statusFilter === s
                      ? "bg-accent text-accent-foreground"
                      : "text-foreground-secondary"
                  }
                >
                  {s ? s.charAt(0).toUpperCase() + s.slice(1) : "All"}
                </Button>
              )
            )}
          </div>
        </div>
      </div>

      {/* Conversations Table */}
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-border text-left text-sm">
              <th className="pb-3 font-medium text-foreground-secondary">
                Title
              </th>
              <th className="pb-3 font-medium text-foreground-secondary">
                Status
              </th>
              <th className="pb-3 font-medium text-foreground-secondary">
                Last Updated
              </th>
              <th className="pb-3 text-right font-medium text-foreground-secondary">
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredConversations.map((conversation) => (
              <tr
                key={conversation.conversation_id}
                className="border-b border-border transition-colors hover:bg-surface-hover"
              >
                <td className="py-4">
                  <Link
                    href={`/chat?id=${conversation.conversation_id}`}
                    className="font-medium hover:text-accent"
                  >
                    {conversation.primary_intent ||
                      `Conversation ${conversation.conversation_id.slice(0, 8)}...`}
                  </Link>
                </td>
                <td className="py-4">
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-1 text-xs font-medium ${
                      conversation.status === "active"
                        ? "bg-blue-500/10 text-blue-500"
                        : conversation.status === "resolved"
                          ? "bg-green-500/10 text-green-500"
                          : "bg-red-500/10 text-red-500"
                    }`}
                  >
                    {conversation.status}
                  </span>
                </td>
                <td className="py-4 text-sm text-foreground-secondary">
                  {format(
                    new Date(conversation.last_updated),
                    "MMM dd, yyyy HH:mm"
                  )}
                </td>
                <td className="py-4 text-right">
                  <Link href={`/chat?id=${conversation.conversation_id}`}>
                    <Button variant="ghost" size="sm">
                      View
                    </Button>
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {filteredConversations.length === 0 && (
          <div className="py-12 text-center text-foreground-secondary">
            No conversations match your search
          </div>
        )}
      </div>

      {/* View All Link */}
      <div className="mt-4 text-center">
        <Link href="/chat">
          <Button variant="outline">View All Conversations</Button>
        </Link>
      </div>
    </div>
  );
}
