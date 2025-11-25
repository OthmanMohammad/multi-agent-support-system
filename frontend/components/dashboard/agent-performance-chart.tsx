"use client";

import type { JSX } from "react";
import { useAgentPerformance } from "@/lib/api/hooks";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Agent Performance Chart Component
 * Displays performance metrics for each AI agent
 */

interface AgentPerformanceChartProps {
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

export function AgentPerformanceChart({
  period,
}: AgentPerformanceChartProps): JSX.Element {
  const { data, isLoading } = useAgentPerformance(periodToDays(period));

  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <Skeleton className="mb-4 h-6 w-48" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-6">
        <h2 className="text-lg font-semibold">Agent Performance</h2>
        <p className="mt-2 text-foreground-secondary">No data available</p>
      </div>
    );
  }

  // Prepare chart data
  const chartData = data.map((agent) => ({
    name: agent.agent_name.split(" ")[0], // Shorten name for chart
    interactions: agent.total_interactions,
    successRate: Math.round(agent.success_rate * 100),
    confidence: Math.round(agent.average_confidence * 100),
    responseTime: agent.average_response_time_seconds,
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
                Interactions
              </th>
              <th className="pb-2 text-right font-medium text-foreground-secondary">
                Success Rate
              </th>
              <th className="pb-2 text-right font-medium text-foreground-secondary">
                Confidence
              </th>
              <th className="pb-2 text-right font-medium text-foreground-secondary">
                Resp Time
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((agent) => (
              <tr key={agent.agent_name} className="border-b border-border">
                <td className="py-3 font-medium">{agent.agent_name}</td>
                <td className="py-3 text-right">
                  {agent.total_interactions.toLocaleString()}
                </td>
                <td className="py-3 text-right">
                  {(agent.success_rate * 100).toFixed(1)}%
                </td>
                <td className="py-3 text-right">
                  {(agent.average_confidence * 100).toFixed(1)}%
                </td>
                <td className="py-3 text-right">
                  {agent.average_response_time_seconds.toFixed(2)}s
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
              dataKey="interactions"
              fill="hsl(var(--accent))"
              name="Interactions"
            />
            <Bar
              dataKey="successRate"
              fill="hsl(142, 71%, 45%)"
              name="Success %"
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
