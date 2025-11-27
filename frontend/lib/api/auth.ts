import type {
  ForgotPasswordRequest,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  ResetPasswordRequest,
  User,
} from '@/types';

import { apiClient, setAccessToken } from './client';

// =============================================================================
// Auth API Functions
// =============================================================================

/**
 * Login with email and password
 * Sets access token in memory, refresh token is set as httpOnly cookie by backend
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  const response = await apiClient.post<LoginResponse>('/auth/login', data);
  setAccessToken(response.data.access_token);
  return response.data;
}

/**
 * Register a new user
 * Includes Turnstile captcha token for verification
 */
export async function register(data: RegisterRequest): Promise<RegisterResponse> {
  const response = await apiClient.post<RegisterResponse>('/auth/register', data);
  setAccessToken(response.data.access_token);
  return response.data;
}

/**
 * Logout - clears tokens
 */
export async function logout(): Promise<void> {
  try {
    await apiClient.post('/auth/logout');
  } finally {
    setAccessToken(null);
  }
}

/**
 * Refresh access token
 * Refresh token is sent via httpOnly cookie
 */
export async function refreshToken(): Promise<{ access_token: string }> {
  const response = await apiClient.post<{ access_token: string }>('/auth/refresh');
  setAccessToken(response.data.access_token);
  return response.data;
}

/**
 * Get current user profile
 */
export async function getCurrentUser(): Promise<User> {
  const response = await apiClient.get<User>('/auth/me');
  return response.data;
}

/**
 * Request password reset email
 */
export async function forgotPassword(data: ForgotPasswordRequest): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>('/auth/reset-password', data);
  return response.data;
}

/**
 * Reset password with token
 */
export async function resetPassword(data: ResetPasswordRequest): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>('/auth/reset-password/confirm', data);
  return response.data;
}

/**
 * Verify email with token
 */
export async function verifyEmail(token: string): Promise<{ message: string; user: User }> {
  const response = await apiClient.post<{ message: string; user: User }>('/auth/verify-email', {
    token,
  });
  return response.data;
}

/**
 * Resend verification email
 */
export async function resendVerificationEmail(email: string): Promise<{ message: string }> {
  const response = await apiClient.post<{ message: string }>('/auth/resend-verification', {
    email,
  });
  return response.data;
}

/**
 * OAuth login - redirect to provider
 */
export function oauthLogin(provider: 'google' | 'github'): void {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  window.location.href = `${baseUrl}/api/oauth/${provider}`;
}

/**
 * Handle OAuth callback - exchange token from URL params
 */
export async function handleOAuthCallback(accessToken: string): Promise<User> {
  setAccessToken(accessToken);
  return getCurrentUser();
}
