/**
 * Authentication Hook
 *
 * Provides authentication state and actions.
 * Integrates with NextAuth for session management.
 */

"use client";

import { useCallback, useState, useEffect } from "react";
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
 * Used to conditionally fetch user profile
 */
const hasAccessToken = (): boolean => {
  if (typeof window === "undefined") return false;
  return !!localStorage.getItem("access_token");
};

// =============================================================================
// USE AUTH HOOK
// =============================================================================

export function useAuth() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [hasToken, setHasToken] = useState(false);

  // Check for token on mount and after auth actions
  useEffect(() => {
    setHasToken(hasAccessToken());
  }, []);

  // Fetch current user profile - only when token exists
  // Using null key to skip fetch when no token
  const {
    data: user,
    error,
    mutate,
    isLoading: isLoadingUser,
  } = useSWR<UserProfile>(
    hasToken ? "auth/me" : null,
    async () => {
      const result = await authAPI.me();
      if (result.success) {
        return result.data;
      }
      throw result.error;
    },
    {
      revalidateOnFocus: false,
      shouldRetryOnError: false,
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

        // Update token state to trigger SWR fetch
        setHasToken(true);

        // Refresh user data
        await mutate(result.data.user);

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

        // Update token state to trigger SWR fetch
        setHasToken(true);

        // Refresh user data - revalidate to fetch complete profile
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

      // Clear token state FIRST to stop SWR polling
      setHasToken(false);

      // Clear user data
      await mutate(undefined);

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
