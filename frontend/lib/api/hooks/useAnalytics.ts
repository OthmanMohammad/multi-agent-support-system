/**
 * Analytics Hooks
 *
 * Provides analytics data for dashboards.
 */

'use client';

import useSWR from 'swr';
import { analyticsAPI } from '../analytics';
import type { AnalyticsOverview, AgentPerformance } from '@/lib/types/api';

// =============================================================================
// USE ANALYTICS OVERVIEW
// =============================================================================

type PeriodString = '24h' | '7d' | '30d' | '90d';

function periodToDays(period: number | PeriodString): number {
  if (typeof period === 'number') return period;
  switch (period) {
    case '24h': return 1;
    case '7d': return 7;
    case '30d': return 30;
    case '90d': return 90;
    default: return 7;
  }
}

export function useAnalyticsOverview(period: number | PeriodString = 7) {
  const days = periodToDays(period);
  const {
    data: overview,
    error,
    mutate,
    isLoading,
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
      refreshInterval: 30000,
    }
  );

  return {
    overview,
    data: overview,
    isLoading,
    error,
    refresh: mutate,
  };
}

// =============================================================================
// USE AGENT PERFORMANCE
// =============================================================================

export function useAgentPerformance(days = 7) {
  const {
    data: agents,
    error,
    mutate,
    isLoading,
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
    agents,
    agentPerformance: agents,
    data: agents,
    isLoading,
    error,
    refresh: mutate,
  };
}

// =============================================================================
// USE CONVERSATION ANALYTICS
// =============================================================================

export function useConversationAnalytics(days = 7) {
  const {
    data: analytics,
    error,
    mutate,
    isLoading,
  } = useSWR<AnalyticsOverview>(
    ['analytics/conversations', days],
    async () => {
      const result = await analyticsAPI.getOverview(days);
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
    analytics,
    data: analytics,
    isLoading,
    error,
    refresh: mutate,
  };
}
