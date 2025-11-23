"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useAnalyticsOverview } from "@/lib/api/hooks";
import { AnalyticsPeriodSelector } from "@/components/dashboard/analytics-period-selector";
import { MetricsCards } from "@/components/dashboard/metrics-cards";
import { ConversationChart } from "@/components/dashboard/conversation-chart";
import { AgentPerformanceChart } from "@/components/dashboard/agent-performance-chart";
import { RecentConversations } from "@/components/dashboard/recent-conversations";
import { Skeleton } from "@/components/ui/skeleton";

/**
 * Dashboard Page
 * Analytics overview, metrics, and charts for multi-agent support system
 */
export default function DashboardPage(): JSX.Element {
  const [period, setPeriod] = useState<"24h" | "7d" | "30d" | "90d">("7d");
  const { data: overview, isLoading } = useAnalyticsOverview(period);

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="mt-1 text-foreground-secondary">
              Analytics and insights for your multi-agent support system
            </p>
          </div>
          <AnalyticsPeriodSelector value={period} onChange={setPeriod} />
        </div>

        {/* Metrics Cards */}
        {isLoading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-32 rounded-lg" />
            ))}
          </div>
        ) : overview ? (
          <MetricsCards data={overview} />
        ) : null}

        {/* Charts */}
        <div className="grid gap-6 lg:grid-cols-2">
          <ConversationChart period={period} />
          <AgentPerformanceChart period={period} />
        </div>

        {/* Recent Activity */}
        <RecentConversations />
      </div>
    </div>
  );
}
