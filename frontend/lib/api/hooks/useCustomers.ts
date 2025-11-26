/**
 * Customer Hooks
 *
 * Provides customer data and management functionality.
 */

"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";
import { customersAPI } from "../customers";
import type { Customer } from "@/lib/types/api";

// =============================================================================
// USE CUSTOMERS (List)
// =============================================================================

export function useCustomers(params?: {
  plan?: "free" | "basic" | "premium" | "enterprise";
  limit?: number;
}) {
  const {
    data: customers,
    error,
    mutate,
    isLoading,
  } = useSWR<Customer[]>(
    ["customers", params],
    async () => {
      const result = await customersAPI.list(params);
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
    customers,
    isLoading,
    error,
    refresh: mutate,
  };
}

// =============================================================================
// USE CUSTOMER (Single)
// =============================================================================

export function useCustomer(customerId: string | null) {
  const {
    data: customer,
    error,
    mutate,
    isLoading,
  } = useSWR<
    Customer & {
      total_conversations: number;
      active_conversations: number;
      lifetime_value: number;
      health_score: number;
    }
  >(
    customerId ? ["customer", customerId] : null,
    async ([, id]: [string, string]) => {
      const result = await customersAPI.get(id);
      if (result.success) {
        return result.data;
      }
      throw result.error;
    },
    {
      revalidateOnFocus: false,
    }
  );

  return {
    customer,
    data: customer,
    isLoading,
    error,
    refresh: mutate,
  };
}

// =============================================================================
// USE CUSTOMER INTERACTIONS (Placeholder)
// =============================================================================

export function useCustomerInteractions(_customerId: string | null) {
  // Placeholder - interactions would come from a dedicated API endpoint
  const [isLoading] = useState(false);
  const interactions: unknown[] = [];

  return {
    interactions,
    data: interactions,
    isLoading,
    error: null,
    refresh: () => {},
  };
}

// =============================================================================
// USE CREATE CUSTOMER
// =============================================================================

export function useCreateCustomer() {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createCustomer = useCallback(
    async (data: {
      email: string;
      name?: string;
      plan?: "free" | "basic" | "premium" | "enterprise";
    }) => {
      setIsCreating(true);
      setError(null);

      try {
        const result = await customersAPI.create(data);
        if (!result.success) {
          setError(result.error);
          return null;
        }
        return result.data;
      } catch (err) {
        setError(err as Error);
        return null;
      } finally {
        setIsCreating(false);
      }
    },
    []
  );

  return {
    createCustomer,
    isCreating,
    isPending: isCreating,
    error,
  };
}
