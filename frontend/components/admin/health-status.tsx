"use client";

import type { JSX } from "react";
import { useHealthCheck } from "@/lib/api/hooks";
import { CheckCircle2, XCircle, AlertCircle, Database, Brain } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { format } from "date-fns";
import { cn } from "@/lib/utils";

/**
 * Health Status Component
 * Display backend system health metrics
 */
export function HealthStatus(): JSX.Element {
  const { data, isLoading, isError } = useHealthCheck();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-lg border border-destructive bg-destructive/5 p-6">
        <div className="flex items-center gap-2">
          <XCircle className="h-5 w-5 text-destructive" />
          <h3 className="font-semibold text-destructive">
            Unable to connect to backend
          </h3>
        </div>
        <p className="mt-2 text-sm text-foreground-secondary">
          The backend API is not responding. Please check your backend server.
        </p>
      </div>
    );
  }

  const statusColor = {
    healthy: "text-green-500",
    degraded: "text-yellow-500",
    unhealthy: "text-red-500",
  }[data.status];

  const statusBg = {
    healthy: "bg-green-500/10",
    degraded: "bg-yellow-500/10",
    unhealthy: "bg-red-500/10",
  }[data.status];

  const StatusIcon = {
    healthy: CheckCircle2,
    degraded: AlertCircle,
    unhealthy: XCircle,
  }[data.status];

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <div className={cn("rounded-lg border border-border p-6", statusBg)}>
        <div className="flex items-center gap-3">
          <StatusIcon className={cn("h-8 w-8", statusColor)} />
          <div>
            <h2 className="text-2xl font-bold capitalize">{data.status}</h2>
            <p className="text-sm text-foreground-secondary">
              System status as of{" "}
              {format(new Date(data.timestamp), "MMM dd, yyyy HH:mm:ss")}
            </p>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-4 text-sm">
          <div>
            <span className="text-foreground-secondary">Version:</span>{" "}
            <span className="font-mono font-medium">{data.version}</span>
          </div>
        </div>
      </div>

      {/* Database Status */}
      {data.database && (
        <div className="rounded-lg border border-border bg-surface p-6">
          <div className="mb-4 flex items-center gap-2">
            <Database className="h-5 w-5" />
            <h3 className="font-semibold">Database</h3>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="text-sm text-foreground-secondary">Status</p>
              <p className="mt-1 font-medium capitalize">{data.database.status}</p>
            </div>
            <div>
              <p className="text-sm text-foreground-secondary">Latency</p>
              <p className="mt-1 font-medium">{data.database.latency}ms</p>
            </div>
          </div>
        </div>
      )}

      {/* AI Providers Status */}
      {data.aiProviders && (
        <div className="rounded-lg border border-border bg-surface p-6">
          <div className="mb-4 flex items-center gap-2">
            <Brain className="h-5 w-5" />
            <h3 className="font-semibold">AI Providers</h3>
          </div>
          <div className="space-y-4">
            {/* OpenAI */}
            {data.aiProviders.openai && (
              <div className="rounded-lg border border-border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">OpenAI</h4>
                    <p className="text-sm capitalize text-foreground-secondary">
                      {data.aiProviders.openai.status}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-foreground-secondary">Latency</p>
                    <p className="font-medium">{data.aiProviders.openai.latency}ms</p>
                  </div>
                </div>
              </div>
            )}

            {/* Anthropic */}
            {data.aiProviders.anthropic && (
              <div className="rounded-lg border border-border p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Anthropic</h4>
                    <p className="text-sm capitalize text-foreground-secondary">
                      {data.aiProviders.anthropic.status}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-foreground-secondary">Latency</p>
                    <p className="font-medium">{data.aiProviders.anthropic.latency}ms</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
