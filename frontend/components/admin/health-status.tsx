"use client";

import type { JSX } from "react";
import { useHealthCheck } from "@/lib/api/hooks";
import { AlertCircle, CheckCircle2, Clock, XCircle, Zap } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

// ServiceStatus component moved outside to avoid recreating during render
function ServiceStatus({
  name,
  isHealthy,
}: {
  name: string;
  isHealthy: boolean;
}): JSX.Element {
  return (
    <div className="flex items-center justify-between rounded-lg border border-border p-4">
      <span className="font-medium">{name}</span>
      <div className="flex items-center gap-2">
        {isHealthy ? (
          <>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
            <span className="text-sm text-green-500">Healthy</span>
          </>
        ) : (
          <>
            <XCircle className="h-4 w-4 text-red-500" />
            <span className="text-sm text-red-500">Unhealthy</span>
          </>
        )}
      </div>
    </div>
  );
}

/**
 * Health Status Component
 * Display backend system health metrics
 */
export function HealthStatus(): JSX.Element {
  const { data, isLoading, error } = useHealthCheck();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (error || !data) {
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

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    }
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <div className="space-y-6">
      {/* Overall Status */}
      <div className={cn("rounded-lg border border-border p-6", statusBg)}>
        <div className="flex items-center gap-3">
          <StatusIcon className={cn("h-8 w-8", statusColor)} />
          <div>
            <h2 className="text-2xl font-bold capitalize">{data.status}</h2>
            <p className="text-sm text-foreground-secondary">
              Version {data.version}
            </p>
          </div>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-2">
          <div className="flex items-center gap-2">
            <Clock className="h-4 w-4 text-foreground-secondary" />
            <span className="text-sm text-foreground-secondary">Uptime:</span>
            <span className="text-sm font-medium">
              {formatUptime(data.uptime_seconds)}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-foreground-secondary" />
            <span className="text-sm text-foreground-secondary">
              API Latency:
            </span>
            <span className="text-sm font-medium">{data.api_latency_ms}ms</span>
          </div>
        </div>
      </div>

      {/* Services Status */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <h3 className="mb-4 font-semibold">Services</h3>
        <div className="space-y-3">
          <ServiceStatus name="Database" isHealthy={data.database} />
          <ServiceStatus name="Redis" isHealthy={data.redis} />
          <ServiceStatus name="Agents" isHealthy={data.agents} />
        </div>
      </div>
    </div>
  );
}
