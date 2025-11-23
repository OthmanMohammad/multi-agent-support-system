"use client";

import type { JSX } from "react";
import { useConversationAnalytics } from "@/lib/api/hooks";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";

/**
 * Conversation Chart Component
 * Displays conversation and message trends over time
 */

interface ConversationChartProps {
  period: "24h" | "7d" | "30d" | "90d";
}

export function ConversationChart({ period }: ConversationChartProps): JSX.Element {
  const { data, isLoading } = useConversationAnalytics(period);

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

  // Combine conversation and message data
  const chartData = data.conversationsByDay.map((conv, index) => ({
    date: format(new Date(conv.date), "MMM dd"),
    conversations: conv.count,
    messages: data.messagesByDay[index]?.count || 0,
  }));

  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Conversation & Message Trends</h2>
        <p className="mt-1 text-sm text-foreground-secondary">
          Daily activity over the last {period}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border p-3">
          <p className="text-sm font-medium text-foreground-secondary">
            Avg Messages/Conversation
          </p>
          <p className="mt-1 text-2xl font-bold">
            {data.avgMessagesPerConversation.toFixed(1)}
          </p>
        </div>
        <div className="rounded-lg border border-border p-3">
          <p className="text-sm font-medium text-foreground-secondary">
            Avg Duration
          </p>
          <p className="mt-1 text-2xl font-bold">
            {Math.floor(data.avgConversationDuration / 60)}m{" "}
            {data.avgConversationDuration % 60}s
          </p>
        </div>
      </div>

      <div className="mt-6 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
            <XAxis
              dataKey="date"
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
            <Legend />
            <Line
              type="monotone"
              dataKey="conversations"
              stroke="hsl(var(--accent))"
              strokeWidth={2}
              name="Conversations"
              dot={{ fill: "hsl(var(--accent))" }}
            />
            <Line
              type="monotone"
              dataKey="messages"
              stroke="hsl(217, 91%, 60%)"
              strokeWidth={2}
              name="Messages"
              dot={{ fill: "hsl(217, 91%, 60%)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
