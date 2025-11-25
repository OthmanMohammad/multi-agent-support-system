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
// USE AUTH HOOK
// =============================================================================

export function useAuth() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);

  // Fetch current user profile
  const {
    data: user,
    error,
    mutate,
    isLoading: isLoadingUser,
  } = useSWR<UserProfile>(
    "auth/me",
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
