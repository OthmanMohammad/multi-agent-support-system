/**
 * Messages Hook
 *
 * Provides message sending functionality.
 */

"use client";

import { useCallback, useState } from "react";
import { conversationsAPI } from "../conversations";
import type { ChatResponse } from "@/lib/types/api";
import { toast } from "sonner";

export function useSendMessage(conversationId: string | null) {
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const sendMessage = useCallback(
    async (message: string): Promise<ChatResponse | null> => {
      if (!conversationId) {
        setError(new Error("No conversation ID provided"));
        return null;
      }

      setIsSending(true);
      setError(null);

      try {
        const result = await conversationsAPI.addMessage(
          conversationId,
          message
        );

        if (!result.success) {
          const err = new Error(
            result.error.message || "Failed to send message"
          );
          setError(err);
          toast.error("Failed to send message");
          return null;
        }

        return result.data;
      } catch (err) {
        const error = err as Error;
        setError(error);
        toast.error("An unexpected error occurred");
        return null;
      } finally {
        setIsSending(false);
      }
    },
    [conversationId]
  );

  return {
    sendMessage,
    isSending,
    isPending: isSending,
    error,
  };
}

export function useCreateMessage() {
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const createMessage = useCallback(
    async (
      conversationId: string,
      message: string
    ): Promise<ChatResponse | null> => {
      setIsCreating(true);
      setError(null);

      try {
        const result = await conversationsAPI.addMessage(
          conversationId,
          message
        );

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
    createMessage,
    isCreating,
    isPending: isCreating,
    error,
  };
}
