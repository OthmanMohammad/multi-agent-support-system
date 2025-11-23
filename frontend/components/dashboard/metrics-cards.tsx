"use client";

import type { JSX } from "react";
import { MessageSquare, Users, MessageCircle, Clock, Star, Bot } from "lucide-react";
import type { components } from "@/types/api";

/**
 * Metrics Cards Component
 * Display key metrics in card format
 */

type AnalyticsOverview = components["schemas"]["AnalyticsOverview"];

interface MetricsCardsProps {
  data: AnalyticsOverview;
}

export function MetricsCards({ data }: MetricsCardsProps): JSX.Element {
  const metrics = [
    {
      label: "Total Conversations",
      value: data.totalConversations.toLocaleString(),
      icon: MessageSquare,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "Total Messages",
      value: data.totalMessages.toLocaleString(),
      icon: MessageCircle,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
    },
    {
      label: "Total Customers",
      value: data.totalCustomers.toLocaleString(),
      icon: Users,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
    },
    {
      label: "Avg Response Time",
      value: `${data.avgResponseTime.toFixed(1)}s`,
      icon: Clock,
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
    },
    {
      label: "Satisfaction Score",
      value: data.satisfactionScore.toFixed(1),
      icon: Star,
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
      suffix: "/5.0",
    },
    {
      label: "Active Agents",
      value: data.activeAgents.toString(),
      icon: Bot,
      color: "text-cyan-500",
      bgColor: "bg-cyan-500/10",
    },
  ];

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {metrics.map((metric) => {
        const Icon = metric.icon;
        return (
          <div
            key={metric.label}
            className="rounded-lg border border-border bg-surface p-6 transition-all hover:shadow-md"
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <p className="text-sm font-medium text-foreground-secondary">
                  {metric.label}
                </p>
                <p className="mt-2 flex items-baseline gap-1 text-3xl font-bold">
                  {metric.value}
                  {metric.suffix && (
                    <span className="text-lg font-normal text-foreground-secondary">
                      {metric.suffix}
                    </span>
                  )}
                </p>
              </div>
              <div className={`rounded-full p-3 ${metric.bgColor}`}>
                <Icon className={`h-6 w-6 ${metric.color}`} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
