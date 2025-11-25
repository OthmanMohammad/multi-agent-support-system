"use client";

import type { JSX } from "react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Github } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { signInSchema, type SignInFormData } from "@/lib/validations/auth";
import { useAuth } from "@/lib/contexts/auth-context";
import { useOAuthProviders } from "@/lib/hooks/use-oauth-providers";

/**
 * Sign In Page
 *
 * Enterprise-grade authentication page with:
 * - Email/password login via useAuth context
 * - OAuth support (Google, GitHub)
 * - Form validation with Zod
 * - Redirect handling for callback URLs
 * - Auto-redirect if already authenticated
 */
export default function SignInPage(): JSX.Element {
  const router = useRouter();
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";
  const registered = searchParams.get("registered") === "true";

  // Use the auth context for login
  const {
    login,
    loginWithGoogle,
    loginWithGitHub,
    isLoading,
    isAuthenticated,
    isInitialized,
  } = useAuth();

  // Check which OAuth providers are available
  const oauthProviders = useOAuthProviders();

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<SignInFormData>({
    resolver: zodResolver(signInSchema),
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isInitialized && isAuthenticated) {
      router.replace(callbackUrl);
    }
  }, [isInitialized, isAuthenticated, router, callbackUrl]);

  // Handle form submission
  const onSubmit = async (data: SignInFormData): Promise<void> => {
    const result = await login(data.email, data.password);

    if (!result.success) {
      setError("root", {
        type: "manual",
        message: "Invalid email or password",
      });
    }
    // Success case: login() handles redirect to dashboard
  };

  // Handle OAuth sign in
  const handleOAuthSignIn = (provider: "google" | "github"): void => {
    if (provider === "google") {
      loginWithGoogle();
    } else {
      loginWithGitHub();
    }
  };

  // Show loading while checking auth state
  if (!isInitialized) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // Already authenticated - show loading while redirecting
  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold">Welcome back</CardTitle>
          <CardDescription>
            Enter your credentials to access your account
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Success message from registration */}
          {registered && (
            <div className="rounded-md bg-success/10 p-3 text-sm text-success">
              Account created successfully! Please sign in.
            </div>
          )}

          {/* Error message */}
          {errors.root && (
            <div className="rounded-md bg-error/10 p-3 text-sm text-error">
              {errors.root.message}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="name@example.com"
                disabled={isLoading}
                autoComplete="email"
                {...register("email")}
              />
              {errors.email && (
                <p className="text-sm text-error">{errors.email.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Password</Label>
                <Link
                  href="/auth/forgot-password"
                  className="text-sm text-accent hover:underline"
                >
                  Forgot password?
                </Link>
              </div>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                disabled={isLoading}
                autoComplete="current-password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-sm text-error">{errors.password.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Signing in..." : "Sign in"}
            </Button>
          </form>

          {/* OAuth Section - Only show if at least one provider is configured */}
          {oauthProviders.hasAnyOAuth && (
            <>
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-border" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-foreground-secondary">
                    Or continue with
                  </span>
                </div>
              </div>

              <div className={`grid gap-4 ${oauthProviders.google && oauthProviders.github ? "grid-cols-2" : "grid-cols-1"}`}>
                {oauthProviders.google && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => handleOAuthSignIn("google")}
                    disabled={isLoading}
                  >
                    <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                      <path
                        fill="currentColor"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="currentColor"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Google
                  </Button>
                )}
                {oauthProviders.github && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => handleOAuthSignIn("github")}
                    disabled={isLoading}
                  >
                    <Github className="mr-2 h-4 w-4" />
                    GitHub
                  </Button>
                )}
              </div>
            </>
          )}
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <div className="text-sm text-foreground-secondary">
            Don&apos;t have an account?{" "}
            <Link href="/auth/signup" className="text-accent hover:underline">
              Sign up
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
