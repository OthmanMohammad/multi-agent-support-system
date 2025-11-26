import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import type { components } from "@/types/api";

/**
 * React Query hooks for AI agent management
 * Type-safe data fetching with automatic caching and revalidation
 */

// Type definitions from OpenAPI schema
type Agent = components["schemas"]["Agent"];
type AgentList = components["schemas"]["AgentList"];
type CreateAgentRequest = components["schemas"]["CreateAgentRequest"];
type UpdateAgentRequest = components["schemas"]["UpdateAgentRequest"];

/**
 * Fetch all configured agents
 */
export function useAgents() {
  return useQuery({
    queryKey: ["agents"],
    queryFn: async (): Promise<AgentList> => {
      const result = await apiClient.get<AgentList>("/api/agents");
      if (!result.success) {
        throw result.error;
      }
      return result.data;
    },
    staleTime: 60000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Fetch a single agent by ID
 */
export function useAgent(agentId: string) {
  return useQuery({
    queryKey: ["agents", agentId],
    queryFn: async (): Promise<Agent> => {
      const result = await apiClient.get<Agent>(`/api/agents/${agentId}`);
      if (!result.success) {
        throw result.error;
      }
      return result.data;
    },
    enabled: !!agentId,
    staleTime: 60000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
  });
}

/**
 * Create a new agent
 */
export function useCreateAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: CreateAgentRequest): Promise<Agent> => {
      const result = await apiClient.post<Agent>("/api/agents", data);
      if (!result.success) {
        throw result.error;
      }
      return result.data;
    },
    onSuccess: () => {
      // Invalidate agents list
      void queryClient.invalidateQueries({
        queryKey: ["agents"],
      });
    },
  });
}

/**
 * Update an agent
 */
export function useUpdateAgent(agentId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: UpdateAgentRequest): Promise<Agent> => {
      const result = await apiClient.patch<Agent>(
        `/api/agents/${agentId}`,
        data
      );
      if (!result.success) {
        throw result.error;
      }
      return result.data;
    },
    onSuccess: () => {
      // Invalidate agent query
      void queryClient.invalidateQueries({
        queryKey: ["agents", agentId],
      });
      // Invalidate agents list
      void queryClient.invalidateQueries({
        queryKey: ["agents"],
      });
    },
  });
}

/**
 * Delete an agent
 */
export function useDeleteAgent() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (agentId: string): Promise<void> => {
      const result = await apiClient.delete<void>(`/api/agents/${agentId}`);
      if (!result.success) {
        throw result.error;
      }
    },
    onSuccess: () => {
      // Invalidate agents list
      void queryClient.invalidateQueries({
        queryKey: ["agents"],
      });
    },
  });
}
