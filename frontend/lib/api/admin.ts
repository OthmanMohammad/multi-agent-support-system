/**
 * Admin API
 *
 * Admin-related API calls for system monitoring and management.
 */

import { apiClient } from '../api-client';
import { type Result } from '../types/api';

// =============================================================================
// TYPES
// =============================================================================

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  database: boolean;
  redis: boolean;
  agents: boolean;
  api_latency_ms: number;
  uptime_seconds: number;
  version: string;
}

export interface AgentInfo {
  name: string;
  type: string;
  status: 'active' | 'inactive' | 'error';
  description?: string;
  success_rate?: number;
  avg_response_time_ms?: number;
}

export interface CostTracking {
  period: string;
  total_tokens: number;
  total_cost_usd: number;
  requests_count: number;
  average_cost_per_request: number;
  breakdown_by_agent: Record<string, { tokens: number; cost_usd: number }>;
}

// =============================================================================
// ADMIN API
// =============================================================================

export const adminAPI = {
  /**
   * Get system health status
   */
  async getHealth(): Promise<Result<HealthStatus>> {
    return apiClient.get<HealthStatus>('/api/health');
  },

  /**
   * Get list of all agents
   */
  async getAgents(): Promise<Result<AgentInfo[]>> {
    return apiClient.get<AgentInfo[]>('/api/admin/agents');
  },

  /**
   * Get cost tracking data
   */
  async getCostTracking(period: '24h' | '7d' | '30d' = '7d'): Promise<Result<CostTracking>> {
    return apiClient.get<CostTracking>(`/api/admin/costs?period=${period}`);
  },

  /**
   * Switch backend provider
   */
  async switchBackend(provider: string): Promise<Result<{ success: boolean }>> {
    return apiClient.post<{ success: boolean }>('/api/admin/switch-backend', {
      provider,
    });
  },
};
