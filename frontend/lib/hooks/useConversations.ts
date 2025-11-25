/**
 * Conversations Hook
 *
 * Provides conversation data and actions with real-time updates.
 */

"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";
import { type ChatResponse, type Conversation, conversationsAPI } from "../api";
import { toast } from "sonner";

// =============================================================================
// USE CONVERSATIONS HOOK
// =============================================================================

export function useConversations(params?: {
  customer_email?: string;
  status?: "active" | "resolved" | "escalated";
  limit?: number;
}) {
  const [isCreating, setIsCreating] = useState(false);

  // Fetch conversations
  const {
    data: conversations,
    error,
    mutate,
    isLoading,
  } = useSWR<Conversation[]>(
    ["conversations", params],
    async () => {
      const result = await conversationsAPI.list(params);
      if (result.success) {
        return result.data;
      }
      throw result.error;
    },
    {
      revalidateOnFocus: false,
      refreshInterval: 5000, // Refresh every 5 seconds
    }
  );

  // Create conversation
  const createConversation = useCallback(
    async (
      message: string,
      customerEmail?: string
    ): Promise<ChatResponse | null> => {
      setIsCreating(true);

      try {
        const result = await conversationsAPI.create(message, customerEmail);

        if (!result.success) {
          toast.error(result.error.message || "Failed to create conversation");
          return null;
        }

        // Refresh conversations list
        await mutate();

        return result.data;
      } catch (_error) {
        toast.error("An unexpected error occurred");
        return null;
      } finally {
        setIsCreating(false);
      }
    },
    [mutate]
  );

  // Delete conversation
  const deleteConversation = useCallback(
    async (conversationId: string) => {
      try {
        const result = await conversationsAPI.delete(conversationId);

        if (!result.success) {
          toast.error(result.error.message || "Failed to delete conversation");
          return { success: false };
        }

        // Optimistic update
        await mutate(
          conversations?.filter((c) => c.conversation_id !== conversationId),
          false
        );

        toast.success("Conversation deleted");
        return { success: true };
      } catch (_error) {
        toast.error("An unexpected error occurred");
        return { success: false };
      }
    },
    [conversations, mutate]
  );

  return {
    // Data
    conversations,
    isLoading,
    error,

    // Actions
    createConversation,
    deleteConversation,
    refresh: mutate,

    // State
    isCreating,
  };
}

// =============================================================================
// USE CONVERSATION (Single)
// =============================================================================

export function useConversation(conversationId: string | null) {
  const [isSending, setIsSending] = useState(false);

  // Fetch single conversation
  const {
    data: conversation,
    error,
    mutate,
    isLoading,
  } = useSWR<Conversation>(
    conversationId ? ["conversation", conversationId] : null,
    async ([, id]: [string, string]) => {
      const result = await conversationsAPI.get(id);
      if (result.success) {
        return result.data;
      }
      throw result.error;
    },
    {
      revalidateOnFocus: false,
      refreshInterval: 3000, // Refresh every 3 seconds
    }
  );

  // Send message
  const sendMessage = useCallback(
    async (message: string): Promise<ChatResponse | null> => {
      if (!conversationId) {
        return null;
      }

      setIsSending(true);

      try {
        const result = await conversationsAPI.addMessage(
          conversationId,
          message
        );

        if (!result.success) {
          toast.error(result.error.message || "Failed to send message");
          return null;
        }

        // Refresh conversation
        await mutate();

        return result.data;
      } catch (_error) {
        toast.error("An unexpected error occurred");
        return null;
      } finally {
        setIsSending(false);
      }
    },
    [conversationId, mutate]
  );

  // Resolve conversation
  const resolve = useCallback(async () => {
    if (!conversationId) {
      return { success: false };
    }

    try {
      const result = await conversationsAPI.resolve(conversationId);

      if (!result.success) {
        toast.error(result.error.message || "Failed to resolve conversation");
        return { success: false };
      }

      await mutate();
      toast.success("Conversation resolved");
      return { success: true };
    } catch (_error) {
      toast.error("An unexpected error occurred");
      return { success: false };
    }
  }, [conversationId, mutate]);

  // Escalate conversation
  const escalate = useCallback(
    async (reason: string) => {
      if (!conversationId) {
        return { success: false };
      }

      try {
        const result = await conversationsAPI.escalate(conversationId, reason);

        if (!result.success) {
          toast.error(
            result.error.message || "Failed to escalate conversation"
          );
          return { success: false };
        }

        await mutate();
        toast.success("Conversation escalated");
        return { success: true };
      } catch (_error) {
        toast.error("An unexpected error occurred");
        return { success: false };
      }
    },
    [conversationId, mutate]
  );

  // Reopen conversation
  const reopen = useCallback(async () => {
    if (!conversationId) {
      return { success: false };
    }

    try {
      const result = await conversationsAPI.reopen(conversationId);

      if (!result.success) {
        toast.error(result.error.message || "Failed to reopen conversation");
        return { success: false };
      }

      await mutate();
      toast.success("Conversation reopened");
      return { success: true };
    } catch (_error) {
      toast.error("An unexpected error occurred");
      return { success: false };
    }
  }, [conversationId, mutate]);

  return {
    // Data
    conversation,
    isLoading,
    error,

    // Actions
    sendMessage,
    resolve,
    escalate,
    reopen,
    refresh: mutate,

    // State
    isSending,
  };
}
