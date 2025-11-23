"use client";

import type { JSX } from "react";
import { useAgents } from "@/lib/api/hooks";
import { Bot, CheckCircle, XCircle } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

export function AgentManagement(): JSX.Element {
  const { data, isLoading } = useAgents();

  if (isLoading) return <Skeleton className="h-64 w-full" />;
  if (!data || !data.agents) return <p>No agents configured</p>;

  return (
    <div className="space-y-4">
      {data.agents.map((agent) => (
        <div key={agent.id} className="rounded-lg border border-border bg-surface p-6">
          <div className="flex items-start justify-between">
            <div className="flex gap-3">
              <Bot className="h-5 w-5 text-accent" />
              <div>
                <h3 className="font-semibold">{agent.name}</h3>
                {agent.description && (
                  <p className="text-sm text-foreground-secondary">{agent.description}</p>
                )}
                <div className="mt-2 flex gap-4 text-sm">
                  <span className="text-foreground-secondary">Provider: <span className="font-medium">{agent.provider}</span></span>
                  <span className="text-foreground-secondary">Model: <span className="font-medium">{agent.model}</span></span>
                  <span className="text-foreground-secondary">Temp: <span className="font-medium">{agent.temperature}</span></span>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {agent.isActive ? (
                <><CheckCircle className="h-4 w-4 text-green-500" /><span className="text-sm">Active</span></>
              ) : (
                <><XCircle className="h-4 w-4 text-foreground-secondary" /><span className="text-sm">Inactive</span></>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
