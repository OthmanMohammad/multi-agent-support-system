/**
 * Analytics API
 *
 * Dashboard analytics and reporting endpoints.
 */

import { apiClient } from '../api-client';
import {
  type AnalyticsOverview,
  type AgentPerformance,
  type Result,
} from '../types/api';

// =============================================================================
// ANALYTICS
// =============================================================================

export const analyticsAPI = {
  /**
   * Get analytics overview
   */
  async getOverview(days = 7): Promise<Result<AnalyticsOverview>> {
    return apiClient.get<AnalyticsOverview>(`/api/analytics/conversations?days=${days}`);
  },

  /**
   * Get agent performance metrics
   */
  async getAgentPerformance(days = 7): Promise<Result<AgentPerformance[]>> {
    return apiClient.get<AgentPerformance[]>(`/api/analytics/agents?days=${days}`);
  },

  /**
   * Get specific agent performance
   */
  async getAgentDetails(agentName: string, days = 7): Promise<Result<AgentPerformance>> {
    return apiClient.get<AgentPerformance>(
      `/api/analytics/agents/${agentName}?days=${days}`
    );
  },

  /**
   * Get customer satisfaction scores
   */
  async getCSAT(days = 30): Promise<Result<{
    avg_sentiment: number;
    total_responses: number;
    sentiment_distribution: { positive: number; neutral: number; negative: number };
  }>> {
    return apiClient.get(`/api/analytics/csat?days=${days}`);
  },

  /**
   * Get intent distribution
   */
  async getIntentDistribution(days = 7): Promise<Result<Array<{
    intent: string;
    count: number;
    percentage: number;
  }>>> {
    return apiClient.get(`/api/analytics/intents?days=${days}`);
  },

  /**
   * Get resolution time trends
   */
  async getResolutionTimeTrends(days = 7): Promise<Result<{
    avg_resolution_seconds: number;
    trend_data: Array<{ date: string; avg_seconds: number }>;
  }>> {
    return apiClient.get(`/api/analytics/resolution-time?days=${days}`);
  },

  /**
   * Get escalation rate
   */
  async getEscalationRate(days = 7): Promise<Result<{
    escalation_rate: number;
    total_conversations: number;
    escalated_count: number;
  }>> {
    return apiClient.get(`/api/analytics/escalation-rate?days=${days}`);
  },

  /**
   * Get knowledge base effectiveness
   */
  async getKBEffectiveness(days = 7): Promise<Result<{
    kb_usage_rate: number;
    total_queries: number;
    kb_assisted: number;
    top_articles: Array<{ article_id: string; title: string; usage_count: number }>;
  }>> {
    return apiClient.get(`/api/analytics/kb-effectiveness?days=${days}`);
  },
};
