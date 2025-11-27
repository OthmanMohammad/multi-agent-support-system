"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useCostTracking } from "@/lib/api/hooks";
import { Bot, Calculator, DollarSign, Hash } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";

type Period = "24h" | "7d" | "30d";

const PERIODS: { value: Period; label: string }[] = [
  { value: "24h", label: "24 Hours" },
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
];

export function CostTracking(): JSX.Element {
  const [period, setPeriod] = useState<Period>("30d");
  const { data, isLoading } = useCostTracking(period);

  if (isLoading) {
    return <Skeleton className="h-96 w-full" />;
  }
  if (!data) {
    return <p>No cost data available</p>;
  }

  const agentBreakdown = Object.entries(data.breakdown_by_agent || {});

  return (
    <div className="space-y-6">
      <div className="flex gap-2">
        {PERIODS.map((p) => (
          <Button
            key={p.value}
            variant={period === p.value ? "default" : "outline"}
            size="sm"
            onClick={() => setPeriod(p.value)}
          >
            {p.label}
          </Button>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-4">
        <div className="rounded-lg border border-border bg-surface p-6">
          <DollarSign className="mb-2 h-5 w-5 text-green-500" />
          <p className="text-sm text-foreground-secondary">Total Cost</p>
          <p className="text-3xl font-bold">
            ${data.total_cost_usd.toFixed(2)}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-6">
          <Hash className="mb-2 h-5 w-5 text-blue-500" />
          <p className="text-sm text-foreground-secondary">Total Tokens</p>
          <p className="text-2xl font-bold">
            {data.total_tokens.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-6">
          <Calculator className="mb-2 h-5 w-5 text-purple-500" />
          <p className="text-sm text-foreground-secondary">Requests</p>
          <p className="text-2xl font-bold">
            {data.requests_count.toLocaleString()}
          </p>
        </div>
        <div className="rounded-lg border border-border bg-surface p-6">
          <DollarSign className="mb-2 h-5 w-5 text-orange-500" />
          <p className="text-sm text-foreground-secondary">Avg Cost/Request</p>
          <p className="text-2xl font-bold">
            ${data.average_cost_per_request.toFixed(4)}
          </p>
        </div>
      </div>

      {agentBreakdown.length > 0 && (
        <div className="rounded-lg border border-border bg-surface p-6">
          <h3 className="mb-4 font-semibold">Cost by Agent</h3>
          <div className="space-y-3">
            {agentBreakdown.map(([agent, stats]) => (
              <div
                key={agent}
                className="flex items-center justify-between rounded-md bg-background p-3"
              >
                <div className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-accent" />
                  <span className="font-medium">{agent}</span>
                </div>
                <div className="flex gap-6 text-sm">
                  <span className="text-foreground-secondary">
                    {stats.tokens.toLocaleString()} tokens
                  </span>
                  <span className="font-medium text-green-500">
                    ${stats.cost_usd.toFixed(2)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
