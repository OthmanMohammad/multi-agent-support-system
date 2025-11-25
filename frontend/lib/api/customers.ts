/**
 * Customers API
 *
 * Customer management endpoints.
 */

import { apiClient } from '../api-client';
import { type Customer, type Result } from '../types/api';

// =============================================================================
// CUSTOMERS
// =============================================================================

export const customersAPI = {
  /**
   * Create new customer
   */
  async create(data: {
    email: string;
    name?: string;
    plan?: 'free' | 'basic' | 'premium' | 'enterprise';
  }): Promise<Result<Customer>> {
    return apiClient.post<Customer>('/api/customers', data);
  },

  /**
   * Get customer by ID
   */
  async get(customerId: string): Promise<Result<Customer & {
    total_conversations: number;
    active_conversations: number;
    lifetime_value: number;
    health_score: number;
  }>> {
    return apiClient.get(`/api/customers/${customerId}`);
  },

  /**
   * List all customers
   */
  async list(params?: {
    plan?: 'free' | 'basic' | 'premium' | 'enterprise';
    limit?: number;
  }): Promise<Result<Customer[]>> {
    const queryParams = new URLSearchParams();
    if (params?.plan) queryParams.set('plan', params.plan);
    if (params?.limit) queryParams.set('limit', params.limit.toString());

    const url = `/api/customers?${queryParams.toString()}`;
    return apiClient.get<Customer[]>(url);
  },

  /**
   * Upgrade customer plan
   */
  async upgrade(
    customerId: string,
    newPlan: 'free' | 'basic' | 'premium' | 'enterprise'
  ): Promise<Result<{
    old_plan: string;
    new_plan: string;
    upgraded_at: string;
  }>> {
    return apiClient.post(`/api/customers/${customerId}/upgrade`, {
      new_plan: newPlan,
    });
  },

  /**
   * Downgrade customer plan
   */
  async downgrade(
    customerId: string,
    newPlan: 'free' | 'basic' | 'premium' | 'enterprise'
  ): Promise<Result<{
    old_plan: string;
    new_plan: string;
    downgraded_at: string;
  }>> {
    return apiClient.post(`/api/customers/${customerId}/downgrade`, {
      new_plan: newPlan,
    });
  },

  /**
   * Delete customer
   */
  async delete(customerId: string): Promise<Result<void>> {
    return apiClient.delete(`/api/customers/${customerId}`);
  },
};
