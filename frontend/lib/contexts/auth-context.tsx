/**
 * Authentication Context
 *
 * Enterprise-grade authentication state management with:
 * - Global auth state accessible throughout the app
 * - Automatic token refresh and session management
 * - Type-safe context with proper error handling
 * - Integration with NextAuth for session persistence
 * - SWR for efficient data fetching and caching
 */

"use client";

import {
  createContext,
  useContext,
  useCallback,
  useEffect,
  useMemo,
  useState,
  useRef,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { signIn, signOut, useSession } from "next-auth/react";
import { toast } from "sonner";
import {
  authAPI,
  type RegisterRequest,
  type UserProfile,
} from "../api";
import { TokenManager } from "../api-client";

// =============================================================================
// TYPES
// =============================================================================

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  isNewUser: boolean; // True when user just registered (first-time user)
  error: Error | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<{ success: boolean }>;
  register: (data: RegisterRequest) => Promise<{ success: boolean }>;
  logout: () => Promise<void>;
  loginWithGoogle: () => void;
  loginWithGitHub: () => void;
  refreshUser: () => Promise<void>;
  clearNewUserFlag: () => void; // Clear the isNewUser flag after onboarding
}

// =============================================================================
// INITIAL STATE
// =============================================================================

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  isInitialized: false,
  isNewUser: false,
  error: null,
};

// =============================================================================
// CONTEXT
// =============================================================================

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// =============================================================================
// PROVIDER
// =============================================================================

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  const { data: session, status: sessionStatus } = useSession();
  const [state, setState] = useState<AuthState>(initialState);

  // Track if we've manually authenticated (login/register) to skip re-initialization
  // This prevents the useEffect from resetting state when NextAuth session updates
  const manualAuthCompletedRef = useRef(false);

  // ---------------------------------------------------------------------------
  // FETCH USER PROFILE
  // ---------------------------------------------------------------------------

  const fetchUserProfile = useCallback(async (): Promise<UserProfile | null> => {
    const token = TokenManager.getAccessToken();
    if (!token) {
      return null;
    }

    try {
      const result = await authAPI.me();
      if (result.success) {
        return result.data;
      }
      return null;
    } catch (error) {
      console.error("Failed to fetch user profile:", error);
      return null;
    }
  }, []);

  // ---------------------------------------------------------------------------
  // INITIALIZE AUTH STATE
  // ---------------------------------------------------------------------------

  useEffect(() => {
    const initializeAuth = async () => {
      // Wait for NextAuth session to load
      if (sessionStatus === "loading") {
        return;
      }

      // Skip re-initialization if we've manually authenticated via login/register
      // This prevents state reset when NextAuth session updates after login
      if (manualAuthCompletedRef.current) {
        return;
      }

      setState((prev) => ({ ...prev, isLoading: true }));

      try {
        // Check for tokens in localStorage
        const hasToken = !!TokenManager.getAccessToken();

        if (hasToken) {
          // Fetch user profile
          const user = await fetchUserProfile();

          if (user) {
            // Mark as completed to prevent future re-runs
            manualAuthCompletedRef.current = true;
            setState({
              user,
              isAuthenticated: true,
              isLoading: false,
              isInitialized: true,
              isNewUser: false, // Returning user from stored token
              error: null,
            });
            return;
          }
        }

        // If NextAuth session exists but no localStorage token,
        // try to sync from session
        if (session?.accessToken) {
          TokenManager.setTokens(
            session.accessToken as string,
            session.refreshToken as string || ""
          );

          const user = await fetchUserProfile();

          if (user) {
            // Mark as completed to prevent future re-runs
            manualAuthCompletedRef.current = true;
            setState({
              user,
              isAuthenticated: true,
              isLoading: false,
              isInitialized: true,
              isNewUser: session?.isNewUser ?? false, // Check session for OAuth isNewUser flag
              error: null,
            });
            return;
          }
        }

        // No valid auth
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isInitialized: true,
          isNewUser: false,
          error: null,
        });
      } catch (error) {
        console.error("Auth initialization failed:", error);
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isInitialized: true,
          isNewUser: false,
          error: error instanceof Error ? error : new Error("Auth initialization failed"),
        });
      }
    };

    initializeAuth();
  }, [sessionStatus, session?.accessToken, session?.refreshToken, fetchUserProfile]);

  // ---------------------------------------------------------------------------
  // LOGIN
  // ---------------------------------------------------------------------------

  const login = useCallback(
    async (email: string, password: string): Promise<{ success: boolean }> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        // Step 1: Call backend login API to get tokens
        const result = await authAPI.login(email, password);

        if (!result.success) {
          const errorMessage = result.error?.message || "Login failed";
          toast.error(errorMessage);
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: new Error(errorMessage),
          }));
          return { success: false };
        }

        // Tokens are stored by authAPI.login() via TokenManager

        // Mark manual auth as completed BEFORE signIn to prevent useEffect race condition
        // When signIn updates the NextAuth session, useEffect will check this flag
        manualAuthCompletedRef.current = true;

        // Step 2: Create NextAuth session for cookie-based persistence
        const nextAuthResult = await signIn("credentials", {
          email,
          password,
          redirect: false,
        });

        if (nextAuthResult?.error) {
          console.warn("NextAuth session creation failed:", nextAuthResult.error);
          // Continue anyway - we have backend tokens
        }

        // Step 3: Update state with user data
        const user = result.data.user;

        setState({
          user,
          isAuthenticated: true,
          isLoading: false,
          isInitialized: true,
          isNewUser: false, // Existing user logging in
          error: null,
        });

        toast.success("Logged in successfully!");
        router.push("/dashboard");

        return { success: true };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred";
        toast.error(errorMessage);
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error : new Error(errorMessage),
        }));
        return { success: false };
      }
    },
    [router]
  );

  // ---------------------------------------------------------------------------
  // REGISTER
  // ---------------------------------------------------------------------------

  const register = useCallback(
    async (data: RegisterRequest): Promise<{ success: boolean }> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        // Step 1: Call backend register API
        const result = await authAPI.register(data);

        if (!result.success) {
          const errorMessage = result.error?.message || "Registration failed";
          toast.error(errorMessage);
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: new Error(errorMessage),
          }));
          return { success: false };
        }

        // Tokens are stored by authAPI.register() via TokenManager

        // Mark manual auth as completed BEFORE signIn to prevent useEffect race condition
        // When signIn updates the NextAuth session, useEffect will check this flag
        manualAuthCompletedRef.current = true;

        // Step 2: Create NextAuth session
        const nextAuthResult = await signIn("credentials", {
          email: data.email,
          password: data.password,
          redirect: false,
        });

        if (nextAuthResult?.error) {
          console.warn("NextAuth session creation failed:", nextAuthResult.error);
        }

        // Step 3: Fetch full user profile
        const userProfile = await fetchUserProfile();

        if (userProfile) {
          setState({
            user: userProfile,
            isAuthenticated: true,
            isLoading: false,
            isInitialized: true,
            isNewUser: true, // New user just registered
            error: null,
          });
        } else {
          // Use registration response data as fallback
          setState({
            user: {
              id: result.data.user_id,
              email: result.data.email,
              full_name: result.data.full_name,
              organization: null,
              role: result.data.role as "user" | "admin" | "moderator",
              status: result.data.status as "active" | "inactive" | "suspended" | "pending_verification",
              is_active: true,
              is_verified: false,
              scopes: [],
              created_at: new Date().toISOString(),
              last_login_at: null,
            },
            isAuthenticated: true,
            isLoading: false,
            isInitialized: true,
            isNewUser: true, // New user just registered
            error: null,
          });
        }

        toast.success("Account created successfully!");
        router.push("/dashboard");

        return { success: true };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : "An unexpected error occurred";
        toast.error(errorMessage);
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: error instanceof Error ? error : new Error(errorMessage),
        }));
        return { success: false };
      }
    },
    [router, fetchUserProfile]
  );

  // ---------------------------------------------------------------------------
  // LOGOUT
  // ---------------------------------------------------------------------------

  const logout = useCallback(async () => {
    setState((prev) => ({ ...prev, isLoading: true }));

    // Reset manual auth flag so next login can initialize properly
    manualAuthCompletedRef.current = false;

    try {
      // Step 1: Clear state immediately for instant UI update
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: true,
        isInitialized: true,
        isNewUser: false,
        error: null,
      });

      // Step 2: Call backend logout (blacklist token)
      await authAPI.logout();

      // Step 3: Sign out from NextAuth
      await signOut({ redirect: false });

      // Step 4: Clear tokens (already done by authAPI.logout())
      TokenManager.clearTokens();

      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        isInitialized: true,
        isNewUser: false,
        error: null,
      });

      toast.success("Logged out successfully");
      router.push("/");
    } catch (error) {
      console.error("Logout error:", error);
      // Force logout even if there's an error
      TokenManager.clearTokens();
      setState({
        user: null,
        isAuthenticated: false,
        isLoading: false,
        isInitialized: true,
        isNewUser: false,
        error: null,
      });
      toast.success("Logged out successfully");
      router.push("/");
    }
  }, [router]);

  // ---------------------------------------------------------------------------
  // OAUTH
  // ---------------------------------------------------------------------------

  const loginWithGoogle = useCallback(() => {
    signIn("google", { callbackUrl: "/dashboard" });
  }, []);

  const loginWithGitHub = useCallback(() => {
    signIn("github", { callbackUrl: "/dashboard" });
  }, []);

  // ---------------------------------------------------------------------------
  // REFRESH USER
  // ---------------------------------------------------------------------------

  const refreshUser = useCallback(async () => {
    const user = await fetchUserProfile();
    if (user) {
      setState((prev) => ({
        ...prev,
        user,
        isAuthenticated: true,
      }));
    }
  }, [fetchUserProfile]);

  // ---------------------------------------------------------------------------
  // CLEAR NEW USER FLAG
  // ---------------------------------------------------------------------------

  const clearNewUserFlag = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isNewUser: false,
    }));
  }, []);

  // ---------------------------------------------------------------------------
  // CONTEXT VALUE
  // ---------------------------------------------------------------------------

  const value = useMemo<AuthContextValue>(
    () => ({
      ...state,
      login,
      register,
      logout,
      loginWithGoogle,
      loginWithGitHub,
      refreshUser,
      clearNewUserFlag,
    }),
    [state, login, register, logout, loginWithGoogle, loginWithGitHub, refreshUser, clearNewUserFlag]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// =============================================================================
// HOOK
// =============================================================================

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);

  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }

  return context;
}

// =============================================================================
// EXPORTS
// =============================================================================

export { AuthContext };
export type { AuthContextValue, AuthState };
