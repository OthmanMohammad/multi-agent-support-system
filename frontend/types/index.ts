// =============================================================================
// User & Auth Types
// =============================================================================

export interface User {
  id: string;
  email: string;
  full_name: string;
  organization: string | null;
  role: UserRole;
  status: UserStatus;
  is_active: boolean;
  is_verified: boolean;
  scopes: string[];
  created_at: string;
  last_login_at: string | null;
}

export type UserRole = 'admin' | 'support' | 'user';
export type UserStatus = 'active' | 'pending_verification' | 'suspended' | 'deactivated';

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginResponse extends AuthTokens {
  user: User;
  is_new_user?: boolean;
}

export interface RegisterResponse {
  user_id: string;
  email: string;
  full_name: string;
  role: string;
  status: string;
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

// =============================================================================
// API Request/Response Types
// =============================================================================

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
  organization?: string;
  turnstile_token: string;
}

export interface ForgotPasswordRequest {
  email: string;
}

export interface ResetPasswordRequest {
  token: string;
  new_password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

// =============================================================================
// Conversation Types
// =============================================================================

export interface Conversation {
  id: string;
  customer_id: string;
  customer_name?: string;
  status: ConversationStatus;
  priority: Priority;
  channel: Channel;
  subject: string | null;
  created_at: string;
  updated_at: string;
  last_message_at: string | null;
  message_count: number;
}

export type ConversationStatus = 'active' | 'waiting' | 'resolved' | 'closed';
export type Priority = 'low' | 'medium' | 'high' | 'urgent';
export type Channel = 'chat' | 'email' | 'phone' | 'web';

export interface Message {
  id: string;
  conversation_id: string;
  role: MessageRole;
  content: string;
  agent_name?: string;
  agent_tier?: number;
  confidence_score?: number;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export type MessageRole = 'user' | 'assistant' | 'system';

export interface SendMessageRequest {
  content: string;
}

// =============================================================================
// Customer Types
// =============================================================================

export interface Customer {
  id: string;
  email: string;
  name: string;
  company: string | null;
  phone: string | null;
  tier: CustomerTier;
  status: CustomerStatus;
  health_score: number;
  lifetime_value: number;
  created_at: string;
  last_contact_at: string | null;
}

export type CustomerTier = 'free' | 'starter' | 'professional' | 'enterprise';
export type CustomerStatus = 'active' | 'churned' | 'at_risk' | 'new';

// =============================================================================
// API Error Types
// =============================================================================

export interface ApiError {
  detail: string;
  status_code?: number;
}

// =============================================================================
// Pagination Types
// =============================================================================

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PaginationParams {
  page?: number;
  page_size?: number;
}
