"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useConversations } from "@/lib/api/hooks";
import { format } from "date-fns";
import { Search, Filter } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";

/**
 * Recent Conversations Component
 * Display recent conversations with search and filtering
 */

export function RecentConversations(): JSX.Element {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<"active" | "archived" | "all">("all");
  const { data, isLoading } = useConversations({ limit: 10, status });

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

  if (!data || !data.conversations) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <h2 className="text-lg font-semibold">Recent Conversations</h2>
        <p className="mt-2 text-foreground-secondary">No conversations found</p>
      </div>
    );
  }

  // Filter conversations by search
  const filteredConversations = search
    ? data.conversations.filter((conv) =>
        conv.title.toLowerCase().includes(search.toLowerCase())
      )
    : data.conversations;

  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">Recent Conversations</h2>
          <p className="mt-1 text-sm text-foreground-secondary">
            {data.total} total conversations
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
            {(["all", "active", "archived"] as const).map((s) => (
              <Button
                key={s}
                variant="ghost"
                size="sm"
                onClick={() => setStatus(s)}
                className={
                  status === s
                    ? "bg-accent text-accent-foreground"
                    : "text-foreground-secondary"
                }
              >
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </Button>
            ))}
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
                Created
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
                key={conversation.id}
                className="border-b border-border transition-colors hover:bg-surface-hover"
              >
                <td className="py-4">
                  <Link
                    href={`/chat?id=${conversation.id}`}
                    className="font-medium hover:text-accent"
                  >
                    {conversation.title}
                  </Link>
                </td>
                <td className="py-4 text-sm text-foreground-secondary">
                  {format(new Date(conversation.createdAt), "MMM dd, yyyy HH:mm")}
                </td>
                <td className="py-4 text-sm text-foreground-secondary">
                  {format(new Date(conversation.updatedAt), "MMM dd, yyyy HH:mm")}
                </td>
                <td className="py-4 text-right">
                  <Link href={`/chat?id=${conversation.id}`}>
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
