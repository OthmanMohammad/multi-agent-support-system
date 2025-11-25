import { useMutation, useQueryClient } from "@tanstack/react-query";
import { addMessage } from "../client";
import type { ChatResponse } from "../types";
import { conversationKeys } from "./useConversations";

/**
 * Hook to send a message to a conversation
 */
export function useSendMessage() {
  const queryClient = useQueryClient();

  return useMutation<
    ChatResponse,
    Error,
    {
      conversationId: string;
      content: string;
      role?: "USER" | "ASSISTANT" | "SYSTEM";
      metadata?: Record<string, unknown>;
    }
  >({
    mutationFn: async ({ conversationId, content }) => {
      // Call backend API to send message
      return addMessage(conversationId, content);
    },
    onSuccess: (data, variables) => {
      // Invalidate the conversation to refetch with new messages
      queryClient.invalidateQueries({
        queryKey: conversationKeys.detail(variables.conversationId),
      });
      // Also invalidate list to update last_updated timestamp
      queryClient.invalidateQueries({ queryKey: conversationKeys.lists() });
    },
    onError: (error) => {
      console.error("Failed to send message:", error);
    },
  });
}

/**
 * Helper to optimistically update messages in cache
 */
export function useOptimisticMessage() {
  const queryClient = useQueryClient();

  const addOptimisticMessage = (
    conversationId: string,
    message: {
      role: "user" | "assistant";
      content: string;
      timestamp: string;
    }
  ) => {
    // Update cache optimistically
    queryClient.setQueryData(
      conversationKeys.detail(conversationId),
      (old: any) => {
        if (!old) return old;
        return {
          ...old,
          messages: [...old.messages, message],
        };
      }
    );
  };

  const removeOptimisticMessage = (conversationId: string) => {
    // Refetch to remove optimistic update on error
    queryClient.invalidateQueries({
      queryKey: conversationKeys.detail(conversationId),
    });
  };

  return { addOptimisticMessage, removeOptimisticMessage };
}
