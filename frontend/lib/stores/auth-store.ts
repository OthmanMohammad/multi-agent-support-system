import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

import * as authApi from '@/lib/api/auth';
import { clearAccessToken } from '@/lib/api/client';
import type { User, LoginRequest, RegisterRequest } from '@/types';

// =============================================================================
// Types
// =============================================================================

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  error: string | null;
}

interface AuthActions {
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  clearError: () => void;
  oauthLogin: (provider: 'google' | 'github') => void;
  handleOAuthCallback: (accessToken: string) => Promise<void>;
}

type AuthStore = AuthState & AuthActions;

// =============================================================================
// Store
// =============================================================================

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: false,
      error: null,

      // Actions
      login: async (data: LoginRequest) => {
        set({ isLoading: true, error: null });
        try {
          const response = await authApi.login(data);
          set({
            user: response.user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Login failed';
          set({ isLoading: false, error: message });
          throw error;
        }
      },

      register: async (data: RegisterRequest) => {
        set({ isLoading: true, error: null });
        try {
          await authApi.register(data);
          // After registration, fetch the full user profile
          const user = await authApi.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'Registration failed';
          set({ isLoading: false, error: message });
          throw error;
        }
      },

      logout: async () => {
        set({ isLoading: true });
        try {
          await authApi.logout();
        } finally {
          clearAccessToken();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      checkAuth: async () => {
        // Don't check if already initialized and not authenticated
        if (get().isInitialized && !get().isAuthenticated) {
          return;
        }

        set({ isLoading: true });
        try {
          // Try to refresh token first (refresh token is in httpOnly cookie)
          await authApi.refreshToken();
          // Then get user profile
          const user = await authApi.getCurrentUser();
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            isInitialized: true,
            error: null,
          });
        } catch {
          // Auth check failed - user is not logged in
          clearAccessToken();
          set({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            isInitialized: true,
            error: null,
          });
        }
      },

      clearError: () => {
        set({ error: null });
      },

      oauthLogin: (provider: 'google' | 'github') => {
        authApi.oauthLogin(provider);
      },

      handleOAuthCallback: async (accessToken: string) => {
        set({ isLoading: true, error: null });
        try {
          const user = await authApi.handleOAuthCallback(accessToken);
          set({
            user,
            isAuthenticated: true,
            isLoading: false,
            isInitialized: true,
            error: null,
          });
        } catch (error) {
          const message = error instanceof Error ? error.message : 'OAuth login failed';
          set({ isLoading: false, error: message });
          throw error;
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      // Only persist user data, not loading states
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// =============================================================================
// Selectors (for convenience)
// =============================================================================

export const selectUser = (state: AuthStore) => state.user;
export const selectIsAuthenticated = (state: AuthStore) => state.isAuthenticated;
export const selectIsLoading = (state: AuthStore) => state.isLoading;
export const selectError = (state: AuthStore) => state.error;
