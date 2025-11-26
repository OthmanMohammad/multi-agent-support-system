/**
 * Admin Hooks
 *
 * Provides admin functionality for system monitoring and management.
 */

"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";
import {
  adminAPI,
  type AgentInfo,
  type CostTracking,
  type HealthStatus,
} from "../admin";

// =============================================================================
// USE HEALTH CHECK
// =============================================================================

export function useHealthCheck() {
  const {
    data: health,
    error,
    mutate,
    isLoading,
  } = useSWR<HealthStatus>(
    "health",
    async () => {
      const result = await adminAPI.getHealth();
      if (result.success) {
        return result.data;
      }
      throw result.error;
    },
    {
      revalidateOnFocus: false,
      refreshInterval: 10000, // Refresh every 10 seconds
    }
  );

  return {
    health,
    status: health,
    data: health,
    isLoading,
    error,
    refresh: mutate,
  };
}

// =============================================================================
// USE AGENTS
// =============================================================================

export function useAgents() {
  const {
    data: agents,
    error,
    mutate,
    isLoading,
  } = useSWR<AgentInfo[]>(
    "admin/agents",
    async () => {
      const result = await adminAPI.getAgents();
      if (result.success) {
        return result.data;
      }
      throw result.error;
    },
    {
      revalidateOnFocus: false,
      refreshInterval: 30000,
    }
  );

  return {
    agents,
    data: { agents },
    isLoading,
    error,
    refresh: mutate,
  };
}

// =============================================================================
// USE COST TRACKING
// =============================================================================

export function useCostTracking(period: "24h" | "7d" | "30d" = "7d") {
  const {
    data: costs,
    error,
    mutate,
    isLoading,
  } = useSWR<CostTracking>(
    ["admin/costs", period],
    async () => {
      const result = await adminAPI.getCostTracking(period);
      if (result.success) {
        return result.data;
      }
      throw result.error;
    },
    {
      revalidateOnFocus: false,
      refreshInterval: 60000, // Refresh every minute
    }
  );

  return {
    costs,
    data: costs,
    isLoading,
    error,
    refresh: mutate,
  };
}

// =============================================================================
// USE SWITCH BACKEND
// =============================================================================

export function useSwitchBackend() {
  const [isSwitching, setIsSwitching] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const switchBackend = useCallback(async (provider: string) => {
    setIsSwitching(true);
    setError(null);

    try {
      const result = await adminAPI.switchBackend(provider);
      if (!result.success) {
        setError(result.error);
        return { success: false };
      }
      return { success: true };
    } catch (err) {
      setError(err as Error);
      return { success: false };
    } finally {
      setIsSwitching(false);
    }
  }, []);

  return {
    switchBackend,
    mutate: switchBackend,
    isSwitching,
    isPending: isSwitching,
    error,
  };
}
