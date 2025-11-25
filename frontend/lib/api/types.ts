/**
 * API Types - Matches backend FastAPI schemas
 * These types mirror the Pydantic models in the backend
 */

// ==================== Request Types ====================

/**
 * Request to create a new conversation or add a message
 */
export interface ChatRequest {
  message: string;
  conversation_id?: string;
  customer_id?: string;
  customer_email?: string;
  stream?: boolean;
}

/**
 * Request to create a new conversation
 */
export interface CreateConversationRequest {
  message: string;
  customer_email?: string;
}

/**
 * Request to add a message to an existing conversation
 */
export interface AddMessageRequest {
  message: string;
}

// ==================== Response Types ====================

/**
 * Single message in a conversation
 */
export interface Message {
  id?: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
  agent_name?: string | null;
  intent?: string | null;
  sentiment?: number | null;
  confidence?: number | null;
}

/**
 * Response from chat endpoint (create conversation or add message)
 */
export interface ChatResponse {
  conversation_id: string;
  message: string;
  message_id?: string;
  intent?: string | null;
  confidence?: number | null;
  agent_path: string[];
  kb_articles_used: string[];
  status: "active" | "resolved" | "escalated";
  timestamp: string;
  agent_name?: string | null;
}

/**
 * Full conversation with messages
 */
export interface Conversation {
  conversation_id: string;
  customer_id: string;
  messages: Message[];
  agent_history: string[];
  status: "active" | "resolved" | "escalated";
  started_at: string;
  last_updated: string;
  primary_intent?: string | null;
  title?: string;
}

/**
 * Conversation list item (lighter weight for listing)
 */
export interface ConversationListItem {
  conversation_id: string;
  customer_id: string;
  status: "active" | "resolved" | "escalated";
  primary_intent?: string | null;
  started_at: string;
  last_updated: string;
  agent_history: string[];
  title?: string;
}

/**
 * Analytics overview response
 */
export interface AnalyticsOverview {
  total_conversations: number;
  open_conversations: number;
  resolved_conversations: number;
  escalated_conversations: number;
  average_messages_per_conversation: number;
  average_resolution_time_minutes: number;
}

/**
 * Health check response
 */
export interface HealthResponse {
  status: string;
  version: string;
  agents_loaded: string[];
  qdrant_connected: boolean;
  timestamp: string;
}

// ==================== Error Types ====================

export interface APIError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface APIErrorResponse {
  error: APIError;
}

// ==================== Utility Types ====================

export type ConversationStatus = "active" | "resolved" | "escalated";

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  has_more: boolean;
}
