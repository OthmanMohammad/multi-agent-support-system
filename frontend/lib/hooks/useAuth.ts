/**
 * Authentication Hook
 *
 * Provides authentication state and actions.
 * Integrates with NextAuth for session management.
 */

"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { signIn, signOut } from "next-auth/react";
import useSWR from "swr";
import { authAPI, type RegisterRequest, type UserProfile } from "../api";
import { toast } from "sonner";

// =============================================================================
// TOKEN CHECK HELPER
// =============================================================================

/**
 * Check if access token exists in localStorage
 */
const getAccessToken = (): string | null => {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
};

// =============================================================================
// USE AUTH HOOK
// =============================================================================

export function useAuth() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  // Fetch current user profile
  // Key is always "auth/me" - the fetcher handles token check
  const {
    data: user,
    error,
    mutate,
    isLoading: isLoadingUser,
  } = useSWR<UserProfile | undefined>(
    "auth/me",
    async () => {
      // Check for token first - skip API call if no token
      const token = getAccessToken();
      if (!token) {
        return undefined;
      }

      const result = await authAPI.me();
      if (result.success) {
        return result.data;
      }
      // On auth error (401, expired token, etc.), return undefined
      return undefined;
    },
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
      dedupingInterval: 5000, // Prevent duplicate requests within 5s
    }
  );

  // Login
  const login = useCallback(
    async (email: string, password: string) => {
      setIsLoading(true);

      try {
        // Call backend login
        const result = await authAPI.login(email, password);

        if (!result.success) {
          toast.error(result.error.message || "Login failed");
          return { success: false };
        }

        // Sign in to NextAuth
        const nextAuthResult = await signIn("credentials", {
          email,
          password,
          redirect: false,
        });

        if (nextAuthResult?.error) {
          toast.error("Session creation failed");
          return { success: false };
        }

        // Revalidate SWR - will now find the token and fetch user
        await mutate();

        toast.success("Logged in successfully!");
        router.push("/dashboard");

        return { success: true };
      } catch (_error) {
        toast.error("An unexpected error occurred");
        return { success: false };
      } finally {
        setIsLoading(false);
      }
    },
    [router, mutate]
  );

  // Register
  const register = useCallback(
    async (data: RegisterRequest) => {
      setIsLoading(true);

      try {
        const result = await authAPI.register(data);

        if (!result.success) {
          toast.error(result.error.message || "Registration failed");
          return { success: false };
        }

        // Auto-login after registration
        const nextAuthResult = await signIn("credentials", {
          email: data.email,
          password: data.password,
          redirect: false,
        });

        if (nextAuthResult?.error) {
          toast.error("Login after registration failed");
          router.push("/auth/signin");
          return { success: false };
        }

        // Revalidate SWR - will now find the token and fetch user
        await mutate();

        toast.success("Account created successfully!");
        router.push("/dashboard");

        return { success: true };
      } catch (_error) {
        toast.error("An unexpected error occurred");
        return { success: false };
      } finally {
        setIsLoading(false);
      }
    },
    [router, mutate]
  );

  // Logout
  const logout = useCallback(async () => {
    setIsLoading(true);

    try {
      // Call backend logout (blacklist token)
      await authAPI.logout();

      // Sign out from NextAuth
      await signOut({ redirect: false });

      // Revalidate SWR - fetcher will find no token and return undefined
      await mutate(undefined, { revalidate: true });

      toast.success("Logged out successfully");
      router.push("/");
    } catch (_error) {
      toast.error("Logout failed");
    } finally {
      setIsLoading(false);
    }
  }, [router, mutate]);

  // OAuth login
  const loginWithGoogle = useCallback(() => {
    signIn("google", { callbackUrl: "/dashboard" });
  }, []);

  const loginWithGitHub = useCallback(() => {
    signIn("github", { callbackUrl: "/dashboard" });
  }, []);

  return {
    // State
    user,
    isAuthenticated: !!user,
    isLoading: isLoading || isLoadingUser,
    error,

    // Actions
    login,
    register,
    logout,
    loginWithGoogle,
    loginWithGitHub,

    // Utilities
    refresh: mutate,
  };
}
