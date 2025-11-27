/**
 * Authentication Context
 *
 * Clean architecture:
 * - Email/password auth: Direct API calls to FastAPI backend
 * - OAuth (Google/GitHub): Handled by NextAuth, synced to context
 * - Token storage: localStorage for persistence
 *
 * This separation ensures:
 * - No double API calls
 * - No dependency on NextAuth for credential auth
 * - Clear, debuggable auth flow
>>>>>>> 5663ce9 (refactor: clean auth architecture - NextAuth for OAuth only)
 */

"use client";

import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useRouter } from "next/navigation";
import { signIn, signOut, useSession } from "next-auth/react";
import { toast } from "sonner";
import { authAPI, type RegisterRequest, type UserProfile } from "../api";
import { TokenManager } from "../api-client";

// =============================================================================
// TYPES
// =============================================================================

interface AuthState {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  isInitialized: boolean;
  isNewUser: boolean;
  error: Error | null;
}

interface AuthContextValue extends AuthState {
  login: (email: string, password: string) => Promise<{ success: boolean }>;
  register: (data: RegisterRequest) => Promise<{ success: boolean }>;
  logout: () => Promise<void>;
  loginWithGoogle: () => void;
  loginWithGitHub: () => void;
  refreshUser: () => Promise<void>;
  clearNewUserFlag: () => void;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  isInitialized: false,
  isNewUser: false,
  error: null,
};

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

  // Prevent re-initialization after manual login/register
  const manualAuthCompletedRef = useRef(false);

  // ---------------------------------------------------------------------------
  // FETCH USER PROFILE
  // ---------------------------------------------------------------------------

  const fetchUserProfile =
    useCallback(async (): Promise<UserProfile | null> => {
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
      // Skip if already manually authenticated
      if (manualAuthCompletedRef.current) {
        return;
      }

      setState((prev) => ({ ...prev, isLoading: true }));

      try {
        // Step 1: Check localStorage tokens (from credential login)
        const hasToken = !!TokenManager.getAccessToken();

        if (hasToken) {
          const user = await fetchUserProfile();

          if (user) {
            manualAuthCompletedRef.current = true;
            setState({
              user,
              isAuthenticated: true,
              isLoading: false,
              isInitialized: true,
              isNewUser: false,
              error: null,
            });
            return;
          }
          // Token invalid - clear it
          TokenManager.clearTokens();
        }

        // Step 2: Check NextAuth session (from OAuth login)
        // Only proceed if NextAuth has finished loading
        if (sessionStatus === "loading") {
          return; // Will re-run when session loads
        }

        if (sessionStatus === "authenticated" && session?.accessToken) {
          // Sync OAuth tokens to localStorage
          TokenManager.setTokens(
            session.accessToken as string,
            (session.refreshToken as string) || ""
          );

          const user = await fetchUserProfile();

          if (user) {
            manualAuthCompletedRef.current = true;
            setState({
              user,
              isAuthenticated: true,
              isLoading: false,
              isInitialized: true,
              isNewUser: session.isNewUser ?? false,
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
        TokenManager.clearTokens();
        setState({
          user: null,
          isAuthenticated: false,
          isLoading: false,
          isInitialized: true,
          isNewUser: false,
          error: error instanceof Error ? error : new Error("Auth failed"),
        });
      }
    };

    initializeAuth();
  }, [sessionStatus, session, fetchUserProfile]);

  // ---------------------------------------------------------------------------
  // LOGIN (Direct API - no NextAuth)
  // ---------------------------------------------------------------------------

  const login = useCallback(
    async (email: string, password: string): Promise<{ success: boolean }> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
        const result = await authAPI.login(email, password);

        if (!result.success) {
          const errorMessage = result.error?.message || "Invalid credentials";
          toast.error(errorMessage);
          setState((prev) => ({
            ...prev,
            isLoading: false,
            error: new Error(errorMessage),
          }));
          return { success: false };
        }

        // Tokens already stored by authAPI.login()
        manualAuthCompletedRef.current = true;
        setState({
          user: result.data.user,
          isAuthenticated: true,
          isLoading: false,
          isInitialized: true,
          isNewUser: false,
          error: null,
        });

        toast.success("Welcome back!");
        router.push("/dashboard");
        return { success: true };
      } catch (error) {
        const message = error instanceof Error ? error.message : "Login failed";
        toast.error(message);
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: new Error(message),
        }));
        return { success: false };
      }
    },
    [router]
  );

  // ---------------------------------------------------------------------------
  // REGISTER (Direct API - no NextAuth)
  // ---------------------------------------------------------------------------

  const register = useCallback(
    async (data: RegisterRequest): Promise<{ success: boolean }> => {
      setState((prev) => ({ ...prev, isLoading: true, error: null }));

      try {
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

        // Tokens already stored by authAPI.register()
        manualAuthCompletedRef.current = true;

        // Fetch full profile
        const userProfile = await fetchUserProfile();

        setState({
          user: userProfile || {
            id: result.data.user_id,
            email: result.data.email,
            full_name: result.data.full_name,
            organization: null,
            role: result.data.role as "user" | "admin" | "moderator",
            status: result.data.status as
              | "active"
              | "inactive"
              | "suspended"
              | "pending_verification",
            is_active: true,
            is_verified: false,
            scopes: [],
            created_at: new Date().toISOString(),
            last_login_at: null,
          },
          isAuthenticated: true,
          isLoading: false,
          isInitialized: true,
          isNewUser: true,
          error: null,
        });

        toast.success("Account created!");
        router.push("/dashboard");
        return { success: true };
      } catch (error) {
        const message =
          error instanceof Error ? error.message : "Registration failed";
        toast.error(message);
        setState((prev) => ({
          ...prev,
          isLoading: false,
          error: new Error(message),
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
    manualAuthCompletedRef.current = false;

    // Clear state immediately
    setState({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      isInitialized: true,
      isNewUser: false,
      error: null,
    });

    try {
      // Call backend logout
      await authAPI.logout();
    } catch (error) {
      console.error("Backend logout error:", error);
    }

    // Clear tokens
    TokenManager.clearTokens();

    // Sign out from NextAuth (for OAuth users)
    await signOut({ redirect: false });

    toast.success("Logged out");
    router.push("/");
  }, [router]);

  // ---------------------------------------------------------------------------
  // OAUTH (uses NextAuth)
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
      setState((prev) => ({ ...prev, user, isAuthenticated: true }));
    }
  }, [fetchUserProfile]);

  // ---------------------------------------------------------------------------
  // CLEAR NEW USER FLAG
  // ---------------------------------------------------------------------------

  const clearNewUserFlag = useCallback(() => {
    setState((prev) => ({ ...prev, isNewUser: false }));
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
    [
      state,
      login,
      register,
      logout,
      loginWithGoogle,
      loginWithGitHub,
      refreshUser,
      clearNewUserFlag,
    ]
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

export { AuthContext };
export type { AuthContextValue, AuthState };
