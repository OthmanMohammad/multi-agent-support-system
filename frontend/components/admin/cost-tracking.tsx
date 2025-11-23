"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useCostTracking } from "@/lib/api/hooks";
import { DollarSign } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { format } from "date-fns";

export function CostTracking(): JSX.Element {
  const [period, setPeriod] = useState<"24h" | "7d" | "30d" | "90d">("30d");
  const { data, isLoading } = useCostTracking(period);

  if (isLoading) return <Skeleton className="h-96 w-full" />;
  if (!data) return <p>No cost data available</p>;

  const chartData = data.costByDay.map((d) => ({
    date: format(new Date(d.date), "MMM dd"),
    cost: d.cost,
  }));

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-3">
        <div className="rounded-lg border border-border bg-surface p-6">
          <DollarSign className="mb-2 h-5 w-5 text-green-500" />
          <p className="text-sm text-foreground-secondary">Total Cost</p>
          <p className="text-3xl font-bold">${data.totalCostUsd.toFixed(2)}</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-6">
          <p className="text-sm text-foreground-secondary">OpenAI</p>
          <p className="text-2xl font-bold">${data.costByProvider.openai.toFixed(2)}</p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-6">
          <p className="text-sm text-foreground-secondary">Anthropic</p>
          <p className="text-2xl font-bold">${data.costByProvider.anthropic.toFixed(2)}</p>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="mb-4 font-semibold">Cost Over Time</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Area type="monotone" dataKey="cost" stroke="hsl(var(--accent))" fill="hsl(var(--accent))" fillOpacity={0.3} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="mb-4 font-semibold">Token Usage</h3>
        <div className="grid gap-4 md:grid-cols-3">
          <div>
            <p className="text-sm text-foreground-secondary">Input Tokens</p>
            <p className="text-2xl font-bold">{data.tokenUsage.input.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-foreground-secondary">Output Tokens</p>
            <p className="text-2xl font-bold">{data.tokenUsage.output.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-sm text-foreground-secondary">Total Tokens</p>
            <p className="text-2xl font-bold">{data.tokenUsage.total.toLocaleString()}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
