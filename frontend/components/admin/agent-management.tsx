"use client";

import type { JSX } from "react";
import { useAgents } from "@/lib/api/hooks";
import { AlertCircle, Bot, CheckCircle, XCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function AgentManagement(): JSX.Element {
  const { data, isLoading } = useAgents();

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }
  if (!data || !data.agents || data.agents.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-8 text-center">
        <Bot className="mx-auto h-12 w-12 text-foreground-secondary" />
        <p className="mt-4 text-lg font-medium">No agents configured</p>
        <p className="mt-2 text-sm text-foreground-secondary">
          Agents will appear here once they are configured
        </p>
      </div>
    );
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "active":
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <XCircle className="h-4 w-4 text-foreground-secondary" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "text-green-500";
      case "error":
        return "text-red-500";
      default:
        return "text-foreground-secondary";
    }
  };

  return (
    <div className="space-y-4">
      {data.agents.map((agent, index) => (
        <div
          key={agent.name || index}
          className="rounded-lg border border-border bg-surface p-6"
        >
          <div className="flex items-start justify-between">
            <div className="flex gap-3">
              <Bot className="h-5 w-5 text-accent" />
              <div>
                <h3 className="font-semibold">{agent.name}</h3>
                {agent.description && (
                  <p className="text-sm text-foreground-secondary">
                    {agent.description}
                  </p>
                )}
                <div className="mt-2 flex gap-4 text-sm">
                  <span className="text-foreground-secondary">
                    Type: <span className="font-medium">{agent.type}</span>
                  </span>
                  {agent.success_rate !== undefined && (
                    <span className="text-foreground-secondary">
                      Success:{" "}
                      <span className="font-medium">
                        {(agent.success_rate * 100).toFixed(1)}%
                      </span>
                    </span>
                  )}
                  {agent.avg_response_time_ms !== undefined && (
                    <span className="text-foreground-secondary">
                      Avg Time:{" "}
                      <span className="font-medium">
                        {agent.avg_response_time_ms}ms
                      </span>
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {getStatusIcon(agent.status)}
              <span
                className={`text-sm capitalize ${getStatusColor(agent.status)}`}
              >
                {agent.status}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
