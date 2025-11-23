import type { JSX } from "react";

/**
 * Loading UI for Next.js App Router
 * Automatically shown while pages are loading
 */
export default function Loading(): JSX.Element {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-12 w-12 animate-spin rounded-full border-4 border-border border-t-accent"></div>
        <p className="text-sm text-foreground-secondary">Loading...</p>
      </div>
    </div>
  );
}
