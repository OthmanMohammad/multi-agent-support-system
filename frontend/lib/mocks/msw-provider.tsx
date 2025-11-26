"use client";

import type { JSX } from "react";
import { useEffect, useState } from "react";

/**
 * MSW Provider
 * Conditionally enables Mock Service Worker in development
 */

interface MSWProviderProps {
  children: React.ReactNode;
}

export function MSWProvider({ children }: MSWProviderProps): JSX.Element {
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Only enable MSW in development and if explicitly enabled
    const enableMSW =
      process.env.NODE_ENV === "development" &&
      process.env.NEXT_PUBLIC_ENABLE_MSW === "true";

    if (!enableMSW) {
      setIsReady(true);
      return;
    }

    // Dynamically import MSW browser worker
    import("./browser")
      .then(({ worker }) => {
        return worker.start({
          onUnhandledRequest: "bypass", // Don't warn about unhandled requests
          quiet: false, // Log mocked requests
        });
      })
      .then(() => {
        // eslint-disable-next-line no-console -- intentional MSW debug logging
        console.log("[MSW] Mock Service Worker started");
        setIsReady(true);
      })
      .catch((error) => {
        console.error("[MSW] Failed to start Mock Service Worker:", error);
        setIsReady(true); // Continue even if MSW fails
      });
  }, []);

  // Show loading state while MSW is initializing
  if (!isReady) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-accent border-t-transparent" />
          <p className="mt-2 text-sm text-foreground-secondary">
            Initializing development environment...
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
