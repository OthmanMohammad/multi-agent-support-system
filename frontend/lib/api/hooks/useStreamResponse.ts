import { useCallback, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useChatStore } from "@/stores/chat-store";
import { conversationKeys } from "./useConversations";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface UseStreamResponseOptions {
  conversationId: string;
  onComplete?: (message: string) => void;
  onError?: (error: Error) => void;
}

/**
 * Hook for handling streaming AI responses
 *
 * Note: The current backend doesn't support streaming, so this hook
 * uses the regular API and simulates streaming for better UX
 */
export function useStreamResponse({
  conversationId,
  onComplete,
  onError,
}: UseStreamResponseOptions) {
  const queryClient = useQueryClient();
  const abortControllerRef = useRef<AbortController | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);

  const setIsStreamingStore = useChatStore((state) => state.setIsStreaming);
  const appendToStreamingMessage = useChatStore(
    (state) => state.appendToStreamingMessage
  );
  const clearStreamingMessage = useChatStore(
    (state) => state.clearStreamingMessage
  );

  /**
   * Start streaming response for a message
   * Currently simulates streaming since backend returns full response
   */
  const startStream = useCallback(
    async (messageId: string) => {
      // Abort any existing stream
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();
      setIsStreaming(true);
      setIsStreamingStore(true);
      clearStreamingMessage();

      try {
        // For now, since backend doesn't support SSE streaming,
        // we wait for the message mutation to complete
        // The response will be in the conversation data

        // Invalidate conversation to get the latest messages
        await queryClient.invalidateQueries({
          queryKey: conversationKeys.detail(conversationId),
        });

        // Get the updated conversation data
        const conversationData = queryClient.getQueryData(
          conversationKeys.detail(conversationId)
        ) as { messages?: { role: string; content: string }[] } | undefined;

        if (conversationData?.messages) {
          const lastMessage = conversationData.messages
            .filter((m) => m.role === "assistant")
            .pop();

          if (lastMessage) {
            // Simulate streaming by revealing text gradually
            const text = lastMessage.content;
            const words = text.split(" ");

            for (let i = 0; i < words.length; i++) {
              if (abortControllerRef.current?.signal.aborted) break;

              appendToStreamingMessage(words[i] + " ");
              // Small delay to simulate streaming
              await new Promise((resolve) => setTimeout(resolve, 30));
            }

            onComplete?.(text);
          }
        }
      } catch (error) {
        if (error instanceof Error && error.name !== "AbortError") {
          console.error("Stream error:", error);
          onError?.(error);
        }
      } finally {
        setIsStreaming(false);
        setIsStreamingStore(false);
        clearStreamingMessage();
      }
    },
    [
      conversationId,
      queryClient,
      setIsStreamingStore,
      appendToStreamingMessage,
      clearStreamingMessage,
      onComplete,
      onError,
    ]
  );

  /**
   * Stop the current stream
   */
  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsStreaming(false);
    setIsStreamingStore(false);
    clearStreamingMessage();
  }, [setIsStreamingStore, clearStreamingMessage]);

  return {
    startStream,
    stopStream,
    isStreaming,
  };
}

/**
 * Real SSE streaming hook (for when backend supports it)
 */
export function useRealStreamResponse({
  conversationId,
  onComplete,
  onError,
}: UseStreamResponseOptions) {
  const queryClient = useQueryClient();
  const eventSourceRef = useRef<EventSource | null>(null);

  const setIsStreamingStore = useChatStore((state) => state.setIsStreaming);
  const appendToStreamingMessage = useChatStore(
    (state) => state.appendToStreamingMessage
  );
  const clearStreamingMessage = useChatStore(
    (state) => state.clearStreamingMessage
  );

  const startStream = useCallback(
    (messageId: string) => {
      // Close existing connection
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setIsStreamingStore(true);
      clearStreamingMessage();

      // Create SSE connection to backend
      const url = `${API_BASE_URL}/api/conversations/${conversationId}/messages/${messageId}/stream`;
      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === "chunk") {
          appendToStreamingMessage(data.content);
        } else if (data.type === "done") {
          eventSource.close();
          setIsStreamingStore(false);
          clearStreamingMessage();

          // Invalidate conversation to get the full message
          queryClient.invalidateQueries({
            queryKey: conversationKeys.detail(conversationId),
          });

          onComplete?.(data.full_content);
        }
      };

      eventSource.onerror = (error) => {
        console.error("SSE Error:", error);
        eventSource.close();
        setIsStreamingStore(false);
        clearStreamingMessage();
        onError?.(new Error("Stream connection failed"));
      };
    },
    [
      conversationId,
      queryClient,
      setIsStreamingStore,
      appendToStreamingMessage,
      clearStreamingMessage,
      onComplete,
      onError,
    ]
  );

  const stopStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }
    setIsStreamingStore(false);
    clearStreamingMessage();
  }, [setIsStreamingStore, clearStreamingMessage]);

  return {
    startStream,
    stopStream,
  };
}
