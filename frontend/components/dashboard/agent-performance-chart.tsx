"use client";

import type { JSX } from "react";
import { useAgentPerformance } from "@/lib/api/hooks";
import {
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

/**
 * Agent Performance Chart Component
 * Displays performance metrics for each AI agent
 */

interface AgentPerformanceChartProps {
  period: "24h" | "7d" | "30d" | "90d";
}

export function AgentPerformanceChart({
  period,
}: AgentPerformanceChartProps): JSX.Element {
  const { data, isLoading } = useAgentPerformance(period);

  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <Skeleton className="mb-4 h-6 w-48" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (!data || !data.agents || data.agents.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <h2 className="text-lg font-semibold">Agent Performance</h2>
        <p className="mt-2 text-foreground-secondary">No data available</p>
      </div>
    );
  }

  // Prepare chart data
  const chartData = data.agents.map((agent) => ({
    name: agent.agentName.split(" ")[0], // Shorten name for chart
    conversations: agent.totalConversations,
    messages: agent.totalMessages,
    responseTime: agent.avgResponseTime,
    satisfaction: agent.satisfactionScore,
    cost: agent.costUsd,
  }));

  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">Agent Performance</h2>
        <p className="mt-1 text-sm text-foreground-secondary">
          Comparing agent metrics over the last {period}
        </p>
      </div>

      {/* Agent Stats Table */}
      <div className="mb-6 overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              <th className="pb-2 text-left font-medium text-foreground-secondary">
                Agent
              </th>
              <th className="pb-2 text-right font-medium text-foreground-secondary">
                Convs
              </th>
              <th className="pb-2 text-right font-medium text-foreground-secondary">
                Msgs
              </th>
              <th className="pb-2 text-right font-medium text-foreground-secondary">
                Resp Time
              </th>
              <th className="pb-2 text-right font-medium text-foreground-secondary">
                Satisfaction
              </th>
              <th className="pb-2 text-right font-medium text-foreground-secondary">
                Cost
              </th>
            </tr>
          </thead>
          <tbody>
            {data.agents.map((agent) => (
              <tr key={agent.agentId} className="border-b border-border">
                <td className="py-3 font-medium">{agent.agentName}</td>
                <td className="py-3 text-right">
                  {agent.totalConversations.toLocaleString()}
                </td>
                <td className="py-3 text-right">
                  {agent.totalMessages.toLocaleString()}
                </td>
                <td className="py-3 text-right">
                  {agent.avgResponseTime.toFixed(1)}s
                </td>
                <td className="py-3 text-right">
                  <span className="inline-flex items-center gap-1">
                    {agent.satisfactionScore.toFixed(1)}
                    <span className="text-foreground-secondary">/5.0</span>
                  </span>
                </td>
                <td className="py-3 text-right font-mono">
                  ${agent.costUsd.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Performance Chart */}
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
            <Legend />
            <Bar
              dataKey="conversations"
              fill="hsl(var(--accent))"
              name="Conversations"
            />
            <Bar dataKey="messages" fill="hsl(217, 91%, 60%)" name="Messages" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
