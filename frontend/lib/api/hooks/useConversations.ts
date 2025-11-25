import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  getConversations,
  getConversation,
  createConversation,
  resolveConversation,
  escalateConversation,
  deleteConversation,
} from "../client";
import type { Conversation, ConversationListItem, ChatResponse } from "../types";

/**
 * Query Keys for conversations
 */
export const conversationKeys = {
  all: ["conversations"] as const,
  lists: () => [...conversationKeys.all, "list"] as const,
  list: (filters: { status?: string; customer_email?: string }) =>
    [...conversationKeys.lists(), filters] as const,
  details: () => [...conversationKeys.all, "detail"] as const,
  detail: (id: string) => [...conversationKeys.details(), id] as const,
};

/**
 * Hook to fetch all conversations
 */
export function useConversations(params?: {
  status?: "active" | "resolved" | "escalated";
  customer_email?: string;
  limit?: number;
}) {
  return useQuery<ConversationListItem[], Error>({
    queryKey: conversationKeys.list(params || {}),
    queryFn: () => getConversations(params),
  });
}

/**
 * Hook to fetch a single conversation with messages
 */
export function useConversation(conversationId: string | null) {
  return useQuery<Conversation, Error>({
    queryKey: conversationKeys.detail(conversationId || ""),
    queryFn: () => getConversation(conversationId!),
    enabled: !!conversationId,
  });
}

/**
 * Hook to create a new conversation
 */
export function useCreateConversation() {
  const queryClient = useQueryClient();

  return useMutation<
    ChatResponse,
    Error,
    { message: string; customer_email?: string }
  >({
    mutationFn: ({ message, customer_email }) =>
      createConversation(message, customer_email),
    onSuccess: () => {
      // Invalidate conversations list to refetch
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
    },
  });
}

/**
 * Hook to resolve a conversation
 */
export function useResolveConversation() {
  const queryClient = useQueryClient();

  return useMutation<
    { status: string; conversation_id: string },
    Error,
    string
  >({
    mutationFn: (conversationId) => resolveConversation(conversationId),
    onSuccess: (_, conversationId) => {
      // Invalidate specific conversation and list
      queryClient.invalidateQueries({
        queryKey: conversationKeys.detail(conversationId),
      });
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
    },
  });
}

/**
 * Hook to escalate a conversation
 */
export function useEscalateConversation() {
  const queryClient = useQueryClient();

  return useMutation<
    { status: string; conversation_id: string },
    Error,
    { conversationId: string; reason: string }
  >({
    mutationFn: ({ conversationId, reason }) =>
      escalateConversation(conversationId, reason),
    onSuccess: (_, { conversationId }) => {
      queryClient.invalidateQueries({
        queryKey: conversationKeys.detail(conversationId),
      });
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
    },
  });
}

/**
 * Hook to delete a conversation
 */
export function useDeleteConversation() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (conversationId) => deleteConversation(conversationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
    },
  });
}
