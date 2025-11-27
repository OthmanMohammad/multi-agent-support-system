/**
 * Authentication Guard Component
 *
 * Enterprise-grade route protection with:
 * - Automatic redirect for unauthenticated users
 * - Loading states with skeleton UI
 * - Role-based access control support
 * - Callback URL preservation for post-login redirect
 */

"use client";

import { type ReactNode, useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/contexts/auth-context";
import { Skeleton } from "@/components/ui/skeleton";

// =============================================================================
// TYPES
// =============================================================================

interface AuthGuardProps {
  children: ReactNode;
  /** Required roles for access (optional - defaults to any authenticated user) */
  requiredRoles?: Array<"user" | "admin" | "moderator">;
  /** Custom redirect path (defaults to /auth/signin) */
  redirectTo?: string;
  /** Show loading skeleton while checking auth */
  showSkeleton?: boolean;
  /** Custom fallback component during loading */
  fallback?: ReactNode;
}

// =============================================================================
// LOADING SKELETON
// =============================================================================

function AuthLoadingSkeleton() {
  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header skeleton */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-72" />
          </div>
          <Skeleton className="h-10 w-32" />
        </div>

        {/* Content skeleton */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>

        {/* Charts skeleton */}
        <div className="grid gap-6 lg:grid-cols-2">
          <Skeleton className="h-64 rounded-lg" />
          <Skeleton className="h-64 rounded-lg" />
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// COMPONENT
// =============================================================================

export function AuthGuard({
  children,
  requiredRoles,
  redirectTo = "/auth/signin",
  showSkeleton = true,
  fallback,
}: AuthGuardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading, isInitialized, user } = useAuth();

  useEffect(() => {
    // Wait for auth to initialize
    if (!isInitialized) {
      return;
    }

    // Redirect if not authenticated
    if (!isAuthenticated) {
      // Build callback URL for post-login redirect
      const callbackUrl = encodeURIComponent(pathname);
      router.replace(`${redirectTo}?callbackUrl=${callbackUrl}`);
      return;
    }

    // Check role-based access
    if (requiredRoles && requiredRoles.length > 0 && user) {
      const hasRequiredRole = requiredRoles.includes(user.role);
      if (!hasRequiredRole) {
        // Redirect to unauthorized page or dashboard
        router.replace("/unauthorized");
        return;
      }
    }
  }, [
    isAuthenticated,
    isInitialized,
    user,
    requiredRoles,
    router,
    pathname,
    redirectTo,
  ]);

  // Show loading state
  if (isLoading || !isInitialized) {
    if (fallback) {
      return <>{fallback}</>;
    }
    if (showSkeleton) {
      return <AuthLoadingSkeleton />;
    }
    return null;
  }

  // Not authenticated - will redirect, show nothing
  if (!isAuthenticated) {
    return showSkeleton ? <AuthLoadingSkeleton /> : null;
  }

  // Check role access
  if (requiredRoles && requiredRoles.length > 0 && user) {
    const hasRequiredRole = requiredRoles.includes(user.role);
    if (!hasRequiredRole) {
      return null; // Will redirect
    }
  }

  // Authenticated and authorized
  return <>{children}</>;
}

// =============================================================================
// HIGHER-ORDER COMPONENT (ALTERNATIVE)
// =============================================================================

type WithAuthOptions = Omit<AuthGuardProps, "children">;

export function withAuth<P extends object>(
  Component: React.ComponentType<P>,
  options?: WithAuthOptions
) {
  const displayName = Component.displayName || Component.name || "Component";

  function WithAuthComponent(props: P) {
    return (
      <AuthGuard {...options}>
        <Component {...props} />
      </AuthGuard>
    );
  }

  WithAuthComponent.displayName = `withAuth(${displayName})`;

  return WithAuthComponent;
}

// =============================================================================
// REDIRECT IF AUTHENTICATED (FOR AUTH PAGES)
// =============================================================================

interface RedirectIfAuthenticatedProps {
  children: ReactNode;
  /** Redirect destination (defaults to /dashboard) */
  redirectTo?: string;
}

export function RedirectIfAuthenticated({
  children,
  redirectTo = "/dashboard",
}: RedirectIfAuthenticatedProps) {
  const router = useRouter();
  const { isAuthenticated, isLoading, isInitialized } = useAuth();

  useEffect(() => {
    if (isInitialized && !isLoading && isAuthenticated) {
      router.replace(redirectTo);
    }
  }, [isAuthenticated, isLoading, isInitialized, router, redirectTo]);

  // Show loading while checking auth
  if (isLoading || !isInitialized) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // Already authenticated - will redirect
  if (isAuthenticated) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
      </div>
    );
  }

  // Not authenticated - show auth page
  return <>{children}</>;
}

// =============================================================================
// EXPORTS
// =============================================================================

export { AuthLoadingSkeleton };
