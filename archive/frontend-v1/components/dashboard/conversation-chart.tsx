"use client";

import type { JSX } from "react";
import { useConversationAnalytics } from "@/lib/api/hooks";
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Conversation Chart Component
 * Displays conversation analytics overview
 */

interface ConversationChartProps {
  period: "24h" | "7d" | "30d" | "90d";
}

const periodToDays = (period: string): number => {
  const map: Record<string, number> = {
    "24h": 1,
    "7d": 7,
    "30d": 30,
    "90d": 90,
  };
  return map[period] || 7;
};

export function ConversationChart({
  period,
}: ConversationChartProps): JSX.Element {
  const { data, isLoading } = useConversationAnalytics(periodToDays(period));

  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <Skeleton className="mb-4 h-6 w-48" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <p className="text-foreground-secondary">No data available</p>
      </div>
    );
  }

  // Chart data for status distribution
  const chartData = [
    {
      name: "Open",
      count: data.open_conversations,
      fill: "hsl(217, 91%, 60%)",
    },
    {
      name: "Resolved",
      count: data.resolved_conversations,
      fill: "hsl(142, 71%, 45%)",
    },
    {
      name: "Escalated",
      count: data.escalated_conversations,
      fill: "hsl(0, 84%, 60%)",
    },
  ];

  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Conversation Analytics</h2>
        <p className="mt-1 text-sm text-foreground-secondary">
          Overview for the last {period}
        </p>
      </div>

      {/* Stats Grid */}
      <div className="mb-6 grid gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-border p-3">
          <p className="text-sm font-medium text-foreground-secondary">
            Total Conversations
          </p>
          <p className="mt-1 text-2xl font-bold">
            {data.total_conversations.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg border border-border p-3">
          <p className="text-sm font-medium text-foreground-secondary">Today</p>
          <p className="mt-1 text-2xl font-bold">
            {data.conversations_today.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg border border-border p-3">
          <p className="text-sm font-medium text-foreground-secondary">
            This Week
          </p>
          <p className="mt-1 text-2xl font-bold">
            {data.conversations_this_week.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg border border-border p-3">
          <p className="text-sm font-medium text-foreground-secondary">
            Avg Messages/Conv
          </p>
          <p className="mt-1 text-2xl font-bold">
            {data.average_messages_per_conversation.toFixed(1)}
          </p>
        </div>
      </div>

      {/* Status Distribution Chart */}
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
            <XAxis
              dataKey="name"
              className="text-xs"
              tick={{ fill: "hsl(var(--foreground-secondary))" }}
            />
            <YAxis
              className="text-xs"
              tick={{ fill: "hsl(var(--foreground-secondary))" }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(var(--surface))",
                border: "1px solid hsl(var(--border))",
                borderRadius: "0.5rem",
              }}
            />
            <Bar
              dataKey="count"
              fill="hsl(var(--accent))"
              name="Conversations"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {data.average_resolution_time_minutes !== null && (
        <div className="mt-4 rounded-lg bg-surface-secondary p-3 text-center">
          <p className="text-sm text-foreground-secondary">
            Average Resolution Time:{" "}
            <span className="font-medium">
              {data.average_resolution_time_minutes.toFixed(0)} minutes
            </span>
          </p>
        </div>
      )}
    </div>
  );
}
