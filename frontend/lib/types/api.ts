/**
 * API Type Definitions
 *
 * Enterprise-grade type safety for all API interactions.
 * Matches backend FastAPI response schemas exactly.
 */

import { z } from 'zod';

// =============================================================================
// RESULT PATTERN (Railway-Oriented Programming)
// =============================================================================

export type Result<T, E = Error> =
  | { success: true; data: T }
  | { success: false; error: E };

export const success = <T>(data: T): Result<T> => ({ success: true, data });
export const failure = <E = Error>(error: E): Result<never, E> => ({ success: false, error });

// =============================================================================
// USER & AUTH TYPES
// =============================================================================

export const UserRoleSchema = z.enum(['USER', 'ADMIN', 'MODERATOR']);
export const UserStatusSchema = z.enum(['ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION']);

export const UserProfileSchema = z.object({
  id: z.string().uuid(),
  email: z.string().email(),
  full_name: z.string(),
  organization: z.string().nullable(),
  role: UserRoleSchema,
  status: UserStatusSchema,
  is_active: z.boolean(),
  is_verified: z.boolean(),
  scopes: z.array(z.string()),
  created_at: z.string().datetime(),
  last_login_at: z.string().datetime().nullable(),
});

export const LoginResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.literal('Bearer'),
  expires_in: z.number(),
  user: UserProfileSchema,
});

export const RegisterResponseSchema = z.object({
  user_id: z.string().uuid(),
  email: z.string().email(),
  full_name: z.string(),
  role: z.string(),
  status: z.string(),
  access_token: z.string(),
  refresh_token: z.string(),
  token_type: z.literal('Bearer'),
  expires_in: z.number(),
});

export const RegisterRequestSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  full_name: z.string().min(1),
  organization: z.string().optional(),
});

export type UserProfile = z.infer<typeof UserProfileSchema>;
export type LoginResponse = z.infer<typeof LoginResponseSchema>;
export type RegisterResponse = z.infer<typeof RegisterResponseSchema>;
export type RegisterRequest = z.infer<typeof RegisterRequestSchema>;
export type UserRole = z.infer<typeof UserRoleSchema>;
export type UserStatus = z.infer<typeof UserStatusSchema>;

// =============================================================================
// CONVERSATION TYPES
// =============================================================================

export const MessageRoleSchema = z.enum(['user', 'assistant', 'system']);

export const MessageSchema = z.object({
  role: MessageRoleSchema,
  content: z.string(),
  agent_name: z.string().nullable(),
  timestamp: z.string().datetime(),
});

export const ConversationSchema = z.object({
  conversation_id: z.string().uuid(),
  customer_id: z.string().uuid(),
  status: z.enum(['active', 'resolved', 'escalated']),
  started_at: z.string().datetime(),
  last_updated: z.string().datetime(),
  messages: z.array(MessageSchema),
  agent_history: z.array(z.string()),
  primary_intent: z.string().nullable(),
});

export const ChatResponseSchema = z.object({
  conversation_id: z.string().uuid(),
  message_id: z.string().uuid(),
  response: z.string(),
  agent_name: z.string().nullable(),
  confidence: z.number().nullable(),
  created_at: z.string().datetime(),
});

export type Message = z.infer<typeof MessageSchema>;
export type Conversation = z.infer<typeof ConversationSchema>;
export type ChatResponse = z.infer<typeof ChatResponseSchema>;
export type MessageRole = z.infer<typeof MessageRoleSchema>;

// =============================================================================
// ANALYTICS TYPES
// =============================================================================

export const AnalyticsOverviewSchema = z.object({
  total_conversations: z.number(),
  open_conversations: z.number(),
  resolved_conversations: z.number(),
  escalated_conversations: z.number(),
  average_messages_per_conversation: z.number(),
  average_resolution_time_minutes: z.number().nullable(),
  conversations_today: z.number(),
  conversations_this_week: z.number(),
});

export const AgentPerformanceSchema = z.object({
  agent_name: z.string(),
  total_interactions: z.number(),
  success_rate: z.number(),
  average_confidence: z.number(),
  average_response_time_seconds: z.number(),
});

export type AnalyticsOverview = z.infer<typeof AnalyticsOverviewSchema>;
export type AgentPerformance = z.infer<typeof AgentPerformanceSchema>;

// =============================================================================
// CUSTOMER TYPES
// =============================================================================

export const CustomerSchema = z.object({
  customer_id: z.string().uuid(),
  email: z.string().email(),
  name: z.string().nullable(),
  plan: z.enum(['free', 'basic', 'premium', 'enterprise']),
  created_at: z.string().datetime(),
});

export type Customer = z.infer<typeof CustomerSchema>;

// =============================================================================
// STREAMING TYPES
// =============================================================================

export interface StreamEvent {
  type: 'content' | 'done' | 'error' | 'agent_switch';
  chunk?: string;
  messageId?: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
  from_agent?: string;
  to_agent?: string;
  error?: string;
}

// =============================================================================
// API ERROR TYPES
// =============================================================================

export interface APIError {
  message: string;
  code?: string;
  details?: Record<string, unknown>;
  status: number;
}

export class APIClientError extends Error {
  constructor(
    message: string,
    public status: number,
    public code?: string,
    public details?: Record<string, unknown>
  ) {
    super(message);
    this.name = 'APIClientError';
  }
}
