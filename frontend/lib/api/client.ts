import axios, { AxiosError, AxiosInstance, AxiosResponse } from "axios";
import type {
  ChatRequest,
  ChatResponse,
  Conversation,
  ConversationListItem,
  AddMessageRequest,
  AnalyticsOverview,
  HealthResponse,
  APIErrorResponse,
} from "./types";

/**
 * Backend API Client
 * Handles all HTTP requests to the FastAPI backend
 */

// Base URL for the backend API
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Create axios instance with default config
 */
const createApiClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    headers: {
      "Content-Type": "application/json",
    },
    timeout: 60000, // 60 second timeout for AI responses
  });

  // Request interceptor for auth headers
  client.interceptors.request.use(
    (config) => {
      // Add auth token if available (from NextAuth session)
      const token = typeof window !== "undefined"
        ? localStorage.getItem("auth_token")
        : null;

      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }

      return config;
    },
    (error) => Promise.reject(error)
  );

  // Response interceptor for error handling
  client.interceptors.response.use(
    (response) => response,
    (error: AxiosError<APIErrorResponse>) => {
      // Log error for debugging
      console.error("API Error:", {
        url: error.config?.url,
        status: error.response?.status,
        data: error.response?.data,
      });

      // Handle specific error codes
      if (error.response?.status === 401) {
        // Unauthorized - could trigger logout
        console.warn("Unauthorized request - token may be expired");
      }

      return Promise.reject(error);
    }
  );

  return client;
};

// Singleton API client instance
const apiClient = createApiClient();

/**
 * API Methods
 */

// ==================== Conversations ====================

/**
 * Create a new conversation with an initial message
 */
export async function createConversation(
  message: string,
  customerEmail?: string
): Promise<ChatResponse> {
  const request: ChatRequest = {
    message,
    customer_email: customerEmail,
  };

  const response: AxiosResponse<ChatResponse> = await apiClient.post(
    "/api/conversations",
    request
  );

  return response.data;
}

/**
 * Get all conversations (with optional filters)
 */
export async function getConversations(params?: {
  customer_email?: string;
  status?: "active" | "resolved" | "escalated";
  limit?: number;
}): Promise<ConversationListItem[]> {
  const response: AxiosResponse<ConversationListItem[]> = await apiClient.get(
    "/api/conversations",
    { params }
  );

  return response.data;
}

/**
 * Get a single conversation with all messages
 */
export async function getConversation(
  conversationId: string
): Promise<Conversation> {
  const response: AxiosResponse<Conversation> = await apiClient.get(
    `/api/conversations/${conversationId}`
  );

  return response.data;
}

/**
 * Add a message to an existing conversation
 */
export async function addMessage(
  conversationId: string,
  message: string
): Promise<ChatResponse> {
  const request: AddMessageRequest = { message };

  const response: AxiosResponse<ChatResponse> = await apiClient.post(
    `/api/conversations/${conversationId}/messages`,
    request
  );

  return response.data;
}

/**
 * Mark a conversation as resolved
 */
export async function resolveConversation(
  conversationId: string
): Promise<{ status: string; conversation_id: string }> {
  const response = await apiClient.post(
    `/api/conversations/${conversationId}/resolve`
  );

  return response.data;
}

/**
 * Escalate a conversation to human support
 */
export async function escalateConversation(
  conversationId: string,
  reason: string
): Promise<{ status: string; conversation_id: string }> {
  const response = await apiClient.post(
    `/api/conversations/${conversationId}/escalate`,
    null,
    { params: { reason } }
  );

  return response.data;
}

/**
 * Delete a conversation
 */
export async function deleteConversation(
  conversationId: string
): Promise<void> {
  await apiClient.delete(`/api/conversations/${conversationId}`);
}

// ==================== Analytics ====================

/**
 * Get analytics overview
 */
export async function getAnalyticsOverview(): Promise<AnalyticsOverview> {
  const response: AxiosResponse<AnalyticsOverview> = await apiClient.get(
    "/api/analytics/overview"
  );

  return response.data;
}

// ==================== Health ====================

/**
 * Check API health
 */
export async function getHealth(): Promise<HealthResponse> {
  const response: AxiosResponse<HealthResponse> = await apiClient.get(
    "/api/health"
  );

  return response.data;
}

// ==================== Export API client ====================

export { apiClient };
export default apiClient;
