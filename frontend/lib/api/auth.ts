/**
 * Authentication API
 *
 * All authentication-related API calls.
 * Handles login, signup, logout, token refresh, OAuth.
 */

import { apiClient, TokenManager } from '../api-client';
import {
  type LoginResponse,
  type RegisterResponse,
  type RegisterRequest,
  type UserProfile,
  type Result,
  LoginResponseSchema,
  RegisterResponseSchema,
  UserProfileSchema,
} from '../types/api';

// =============================================================================
// AUTHENTICATION
// =============================================================================

export const authAPI = {
  /**
   * Register new user
   */
  async register(data: RegisterRequest): Promise<Result<RegisterResponse>> {
    const result = await apiClient.post<RegisterResponse>('/api/auth/register', data);

    if (result.success) {
      // Validate response
      const validated = RegisterResponseSchema.safeParse(result.data);
      if (!validated.success) {
        console.error('Register response validation failed:', validated.error);
        return { success: false, error: new Error('Invalid response format') };
      }

      // Store tokens
      TokenManager.setTokens(
        validated.data.access_token,
        validated.data.refresh_token
      );

      return { success: true, data: validated.data };
    }

    return result;
  },

  /**
   * Login user
   */
  async login(email: string, password: string): Promise<Result<LoginResponse>> {
    const result = await apiClient.post<LoginResponse>('/api/auth/login', {
      email,
      password,
    });

    if (result.success) {
      // Validate response
      const validated = LoginResponseSchema.safeParse(result.data);
      if (!validated.success) {
        return { success: false, error: new Error('Invalid response format') };
      }

      // Store tokens
      TokenManager.setTokens(
        validated.data.access_token,
        validated.data.refresh_token
      );

      return { success: true, data: validated.data };
    }

    return result;
  },

  /**
   * Logout user
   */
  async logout(): Promise<Result<void>> {
    try {
      // Call backend logout (blacklists token)
      await apiClient.post('/api/auth/logout');

      // Clear local tokens
      TokenManager.clearTokens();

      return { success: true, data: undefined };
    } catch (error) {
      // Even if backend call fails, clear local tokens
      TokenManager.clearTokens();
      return { success: false, error: error as Error };
    }
  },

  /**
   * Get current user profile
   */
  async me(): Promise<Result<UserProfile>> {
    const result = await apiClient.get<UserProfile>('/api/auth/me');

    if (result.success) {
      // Validate response
      const validated = UserProfileSchema.safeParse(result.data);
      if (!validated.success) {
        return { success: false, error: new Error('Invalid response format') };
      }

      return { success: true, data: validated.data };
    }

    return result;
  },

  /**
   * Refresh access token
   */
  async refresh(): Promise<Result<{ access_token: string; refresh_token: string }>> {
    const refreshToken = TokenManager.getRefreshToken();

    if (!refreshToken) {
      return {
        success: false,
        error: new Error('No refresh token available'),
      };
    }

    const result = await apiClient.post<{ access_token: string; refresh_token: string }>(
      '/api/auth/refresh',
      { refresh_token: refreshToken }
    );

    if (result.success) {
      // Store new tokens
      TokenManager.setTokens(
        result.data.access_token,
        result.data.refresh_token
      );
    }

    return result;
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<Result<{ message: string }>> {
    return apiClient.post('/api/auth/request-password-reset', { email });
  },

  /**
   * Reset password
   */
  async resetPassword(
    token: string,
    newPassword: string
  ): Promise<Result<{ message: string }>> {
    return apiClient.post('/api/auth/reset-password', {
      token,
      new_password: newPassword,
    });
  },

  /**
   * Verify email
   */
  async verifyEmail(token: string): Promise<Result<{ message: string }>> {
    return apiClient.post('/api/auth/verify-email', { token });
  },
};

// =============================================================================
// OAUTH
// =============================================================================

export const oauthAPI = {
  /**
   * Get available OAuth providers
   */
  async getProviders(): Promise<Result<{ providers: Array<{ name: string; display_name: string; auth_url: string; enabled: boolean }> }>> {
    return apiClient.get('/api/oauth/providers');
  },

  /**
   * Initiate Google OAuth
   */
  initiateGoogle(redirectUri?: string): void {
    const params = new URLSearchParams();
    if (redirectUri) params.set('redirect_uri', redirectUri);

    window.location.href = `${apiClient.getRawClient().defaults.baseURL}/api/oauth/google?${params}`;
  },

  /**
   * Initiate GitHub OAuth
   */
  initiateGitHub(redirectUri?: string): void {
    const params = new URLSearchParams();
    if (redirectUri) params.set('redirect_uri', redirectUri);

    window.location.href = `${apiClient.getRawClient().defaults.baseURL}/api/oauth/github?${params}`;
  },
};
