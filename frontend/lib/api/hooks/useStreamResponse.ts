/**
 * Stream Response Hook
 *
 * Handles streaming message responses via SSE.
 */

"use client";

import { useCallback, useRef, useState } from "react";
import { conversationsAPI } from "../conversations";
import type { StreamEvent } from "@/lib/types/api";

interface StreamState {
  isStreaming: boolean;
  content: string;
  error: Error | null;
  messageId: string | null;
  agentName: string | null;
}

export function useStreamResponse() {
  const [state, setState] = useState<StreamState>({
    isStreaming: false,
    content: "",
    error: null,
    messageId: null,
    agentName: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const streamMessage = useCallback(
    async (
      conversationId: string,
      message: string,
      onChunk?: (content: string) => void,
      onDone?: (fullContent: string) => void,
      onAgentSwitch?: (fromAgent: string, toAgent: string) => void
    ) => {
      // Cancel any existing stream before starting new one
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create new AbortController for this stream
      abortControllerRef.current = new AbortController();
      const signal = abortControllerRef.current.signal;

      // Reset state
      setState({
        isStreaming: true,
        content: "",
        error: null,
        messageId: null,
        agentName: null,
      });

      let fullContent = "";

      try {
        await conversationsAPI.streamMessage(
          conversationId,
          message,
          // On chunk
          (event: StreamEvent) => {
            if (event.type === "content" && event.chunk) {
              fullContent += event.chunk;
              setState((prev) => ({
                ...prev,
                content: fullContent,
                messageId: event.messageId || prev.messageId,
              }));
              onChunk?.(fullContent);
            } else if (event.type === "agent_switch") {
              setState((prev) => ({
                ...prev,
                agentName: event.to_agent || prev.agentName,
              }));
              if (event.from_agent && event.to_agent) {
                onAgentSwitch?.(event.from_agent, event.to_agent);
              }
            }
          },
          // On error
          (error: Error) => {
            setState((prev) => ({
              ...prev,
              isStreaming: false,
              error,
            }));
          },
          // On complete
          () => {
            setState((prev) => ({
              ...prev,
              isStreaming: false,
            }));
            onDone?.(fullContent);
          },
          // Abort signal for cancellation
          signal
        );
      } catch (error) {
        setState((prev) => ({
          ...prev,
          isStreaming: false,
          error: error as Error,
        }));
      }
    },
    []
  );

  const cancelStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setState((prev) => ({
      ...prev,
      isStreaming: false,
    }));
  }, []);

  const reset = useCallback(() => {
    setState({
      isStreaming: false,
      content: "",
      error: null,
      messageId: null,
      agentName: null,
    });
  }, []);

  return {
    // State
    ...state,
    isPending: state.isStreaming,

    // Actions
    streamMessage,
    cancelStream,
    reset,
  };
}
