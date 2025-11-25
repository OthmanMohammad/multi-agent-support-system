import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api/client";
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
      return apiClient.get<AgentList>("/api/agents");
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
      return apiClient.get<Agent>(`/api/agents/${agentId}`);
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
      return apiClient.post<Agent>("/api/agents", data);
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
      return apiClient.patch<Agent>(`/api/agents/${agentId}`, data);
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
      return apiClient.delete<void>(`/api/agents/${agentId}`);
    },
    onSuccess: () => {
      // Invalidate agents list
      void queryClient.invalidateQueries({
        queryKey: ["agents"],
      });
    },
  });
}
