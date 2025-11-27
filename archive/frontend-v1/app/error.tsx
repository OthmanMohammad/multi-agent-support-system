"use client";

import type { JSX } from "react";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Error UI for Next.js App Router
 * Automatically shown when errors occur in page components
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): JSX.Element {
  useEffect(() => {
    // Log the error to error reporting service
    console.error("Page error:", error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-error">Something went wrong</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-foreground-secondary">
            {error.message || "An unexpected error occurred"}
          </p>

          {error.digest && (
            <p className="text-xs text-foreground-secondary">
              Error ID: {error.digest}
            </p>
          )}

          {process.env.NODE_ENV === "development" && error.stack && (
            <details className="rounded-md bg-surface p-4 text-xs">
              <summary className="cursor-pointer font-semibold">
                Stack Trace
              </summary>
              <pre className="mt-2 overflow-auto whitespace-pre-wrap">
                {error.stack}
              </pre>
            </details>
          )}

          <div className="flex gap-2">
            <Button onClick={reset} variant="default">
              Try again
            </Button>
            <Button
              onClick={() => (window.location.href = "/")}
              variant="outline"
            >
              Go home
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
