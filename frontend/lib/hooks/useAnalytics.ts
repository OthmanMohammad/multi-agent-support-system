/**
 * Analytics Hook
 *
 * Provides dashboard analytics data.
 */

'use client';

import useSWR from 'swr';
import { analyticsAPI, type AnalyticsOverview, type AgentPerformance } from '../api';

// =============================================================================
// USE ANALYTICS HOOK
// =============================================================================

export function useAnalytics(days = 7) {
  // Fetch overview
  const {
    data: overview,
    error: overviewError,
    mutate: mutateOverview,
    isLoading: isLoadingOverview,
  } = useSWR<AnalyticsOverview>(
    ['analytics/overview', days],
    async () => {
      const result = await analyticsAPI.getOverview(days);
      if (result.success) {
        return result.data;
      }
      throw result.error;
    },
    {
      revalidateOnFocus: false,
      refreshInterval: 30000, // Refresh every 30 seconds
    }
  );

  // Fetch agent performance
  const {
    data: agentPerformance,
    error: agentError,
    mutate: mutateAgents,
    isLoading: isLoadingAgents,
  } = useSWR<AgentPerformance[]>(
    ['analytics/agents', days],
    async () => {
      const result = await analyticsAPI.getAgentPerformance(days);
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
    // Data
    overview,
    agentPerformance,

    // Loading states
    isLoading: isLoadingOverview || isLoadingAgents,
    isLoadingOverview,
    isLoadingAgents,

    // Errors
    error: overviewError || agentError,
    overviewError,
    agentError,

    // Actions
    refresh: () => {
      mutateOverview();
      mutateAgents();
    },
  };
}
