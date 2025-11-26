/**
 * Conversations API
 *
 * All conversation and messaging API calls.
 * Handles chat creation, message sending, and streaming.
 */

import { apiClient } from "../api-client";
import {
  type ChatResponse,
  ChatResponseSchema,
  type Conversation,
  ConversationSchema,
  type Result,
  type StreamEvent,
} from "../types/api";

// =============================================================================
// CONVERSATIONS
// =============================================================================

export const conversationsAPI = {
  /**
   * Create new conversation with initial message
   */
  async create(
    message: string,
    customerEmail?: string
  ): Promise<Result<ChatResponse>> {
    const result = await apiClient.post<ChatResponse>("/api/conversations", {
      message,
      customer_email: customerEmail,
    });

    if (result.success) {
      // Validate response
      const validated = ChatResponseSchema.safeParse(result.data);
      if (!validated.success) {
        return { success: false, error: new Error("Invalid response format") };
      }

      return { success: true, data: validated.data };
    }

    return result;
  },

  /**
   * Get conversation by ID
   */
  async get(conversationId: string): Promise<Result<Conversation>> {
    const result = await apiClient.get<Conversation>(
      `/api/conversations/${conversationId}`
    );

    if (result.success) {
      // Validate response
      const validated = ConversationSchema.safeParse(result.data);
      if (!validated.success) {
        return { success: false, error: new Error("Invalid response format") };
      }

      return { success: true, data: validated.data };
    }

    return result;
  },

  /**
   * List all conversations
   */
  async list(params?: {
    customer_email?: string;
    status?: "active" | "resolved" | "escalated";
    limit?: number;
  }): Promise<Result<Conversation[]>> {
    const queryParams = new URLSearchParams();
    if (params?.customer_email) {
      queryParams.set("customer_email", params.customer_email);
    }
    if (params?.status) {
      queryParams.set("status", params.status);
    }
    if (params?.limit) {
      queryParams.set("limit", params.limit.toString());
    }

    const url = `/api/conversations?${queryParams.toString()}`;
    return apiClient.get<Conversation[]>(url);
  },

  /**
   * Add message to existing conversation
   */
  async addMessage(
    conversationId: string,
    message: string
  ): Promise<Result<ChatResponse>> {
    const result = await apiClient.post<ChatResponse>(
      `/api/conversations/${conversationId}/messages`,
      { message }
    );

    if (result.success) {
      // Validate response
      const validated = ChatResponseSchema.safeParse(result.data);
      if (!validated.success) {
        return { success: false, error: new Error("Invalid response format") };
      }

      return { success: true, data: validated.data };
    }

    return result;
  },

  /**
   * Stream message response (SSE)
   */
  async streamMessage(
    conversationId: string,
    message: string,
    onChunk: (event: StreamEvent) => void,
    onError?: (error: Error) => void,
    onComplete?: () => void
  ): Promise<void> {
    try {
      const baseURL = apiClient.getRawClient().defaults.baseURL;
      const token =
        typeof window !== "undefined"
          ? localStorage.getItem("access_token")
          : null;

      const response = await fetch(
        `${baseURL}/api/conversations/${conversationId}/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...(token && { Authorization: `Bearer ${token}` }),
          },
          body: JSON.stringify({ message }),
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      if (!response.body) {
        throw new Error("Response body is null");
      }

      // Read SSE stream
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          onComplete?.();
          break;
        }

        // Decode chunk
        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE messages
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));
              const event = data as StreamEvent;

              if (event.type === "error") {
                onError?.(new Error(event.error || "Stream error"));
                return;
              }

              if (event.type === "done") {
                onComplete?.();
                return;
              }

              onChunk(event);
            } catch (parseError) {
              console.error("Failed to parse SSE event:", parseError);
            }
          }
        }
      }
    } catch (error) {
      onError?.(error as Error);
    }
  },

  /**
   * Resolve conversation
   */
  async resolve(conversationId: string): Promise<Result<void>> {
    return apiClient.post(`/api/conversations/${conversationId}/resolve`);
  },

  /**
   * Reopen a resolved or escalated conversation
   */
  async reopen(conversationId: string): Promise<Result<void>> {
    return apiClient.post(`/api/conversations/${conversationId}/reopen`);
  },

  /**
   * Escalate conversation
   */
  async escalate(
    conversationId: string,
    reason: string
  ): Promise<Result<void>> {
    return apiClient.post(`/api/conversations/${conversationId}/escalate`, {
      reason,
    });
  },

  /**
   * Delete conversation
   */
  async delete(conversationId: string): Promise<Result<void>> {
    return apiClient.delete(`/api/conversations/${conversationId}`);
  },
};
