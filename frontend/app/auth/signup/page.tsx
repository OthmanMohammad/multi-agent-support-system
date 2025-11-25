"use client";

import type { JSX } from "react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { z } from "zod";
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
import { useAuth } from "@/lib/contexts/auth-context";
import { useOAuthProviders } from "@/lib/hooks/use-oauth-providers";

/**
 * Sign Up Page
 *
 * Enterprise-grade registration page with:
 * - Form validation with Zod
 * - Password strength requirements
 * - Auto-login after successful registration
 * - OAuth registration support
 * - Auto-redirect if already authenticated
 */

const signUpSchema = z
  .object({
    name: z.string().min(2, "Name must be at least 2 characters"),
    email: z.string().email("Please enter a valid email address"),
    password: z
      .string()
      .min(8, "Password must be at least 8 characters")
      .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
      .regex(/[a-z]/, "Password must contain at least one lowercase letter")
      .regex(/[0-9]/, "Password must contain at least one number")
      .regex(
        /[^A-Za-z0-9]/,
        "Password must contain at least one special character"
      ),
    confirmPassword: z.string(),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: "Passwords do not match",
    path: ["confirmPassword"],
  });

type SignUpFormData = z.infer<typeof signUpSchema>;

export default function SignUpPage(): JSX.Element {
  const router = useRouter();

  // Use the auth context for registration
  const {
    register: registerUser,
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
  } = useForm<SignUpFormData>({
    resolver: zodResolver(signUpSchema),
  });

  // Redirect if already authenticated
  useEffect(() => {
    if (isInitialized && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isInitialized, isAuthenticated, router]);

  // Handle form submission
  const onSubmit = async (data: SignUpFormData): Promise<void> => {
    const result = await registerUser({
      email: data.email,
      password: data.password,
      full_name: data.name,
    });

    if (!result.success) {
      setError("root", {
        type: "manual",
        message: "Failed to create account. Please try again.",
      });
    }
    // Success case: registerUser() handles redirect to dashboard
  };

  // Handle OAuth sign up
  const handleOAuthSignUp = (provider: "google" | "github"): void => {
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
          <CardTitle className="text-2xl font-bold">Create an account</CardTitle>
          <CardDescription>
            Enter your details to get started
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Error message */}
          {errors.root && (
            <div className="rounded-md bg-error/10 p-3 text-sm text-error">
              {errors.root.message}
            </div>
          )}

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                disabled={isLoading}
                autoComplete="name"
                {...register("name")}
              />
              {errors.name && (
                <p className="text-sm text-error">{errors.name.message}</p>
              )}
            </div>

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
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Create a strong password"
                disabled={isLoading}
                autoComplete="new-password"
                {...register("password")}
              />
              {errors.password && (
                <p className="text-sm text-error">{errors.password.message}</p>
              )}
              <p className="text-xs text-foreground-secondary">
                Must be 8+ characters with uppercase, lowercase, number, and special character
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Confirm your password"
                disabled={isLoading}
                autoComplete="new-password"
                {...register("confirmPassword")}
              />
              {errors.confirmPassword && (
                <p className="text-sm text-error">{errors.confirmPassword.message}</p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? "Creating account..." : "Create account"}
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
                    onClick={() => handleOAuthSignUp("google")}
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
                    onClick={() => handleOAuthSignUp("github")}
                    disabled={isLoading}
                  >
                    <Github className="mr-2 h-4 w-4" />
                    GitHub
                  </Button>
                )}
              </div>
            </>
          )}

          <p className="text-center text-xs text-foreground-secondary">
            By creating an account, you agree to our{" "}
            <Link href="/terms" className="text-accent hover:underline">
              Terms of Service
            </Link>{" "}
            and{" "}
            <Link href="/privacy" className="text-accent hover:underline">
              Privacy Policy
            </Link>
          </p>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4">
          <div className="text-sm text-foreground-secondary">
            Already have an account?{" "}
            <Link href="/auth/signin" className="text-accent hover:underline">
              Sign in
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  );
}
