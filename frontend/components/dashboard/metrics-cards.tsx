"use client";

import type { JSX } from "react";
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  MessageCircle,
  MessageSquare,
  Users,
} from "lucide-react";
import type { AnalyticsOverview } from "@/lib/types/api";

/**
 * Metrics Cards Component
 * Display key metrics in card format
 */

interface MetricsCardsProps {
  data: AnalyticsOverview;
}

export function MetricsCards({ data }: MetricsCardsProps): JSX.Element {
  const metrics = [
    {
      label: "Total Conversations",
      value: data.total_conversations.toLocaleString(),
      icon: MessageSquare,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
    },
    {
      label: "Open Conversations",
      value: data.open_conversations.toLocaleString(),
      icon: MessageCircle,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
    },
    {
      label: "Resolved",
      value: data.resolved_conversations.toLocaleString(),
      icon: CheckCircle,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
    },
    {
      label: "Escalated",
      value: data.escalated_conversations.toLocaleString(),
      icon: AlertTriangle,
      color: "text-orange-500",
      bgColor: "bg-orange-500/10",
    },
    {
      label: "Avg Messages/Conversation",
      value: data.average_messages_per_conversation.toFixed(1),
      icon: Users,
      color: "text-yellow-500",
      bgColor: "bg-yellow-500/10",
    },
    {
      label: "Avg Resolution Time",
      value: data.average_resolution_time_minutes
        ? `${data.average_resolution_time_minutes.toFixed(0)}m`
        : "N/A",
      icon: Clock,
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
