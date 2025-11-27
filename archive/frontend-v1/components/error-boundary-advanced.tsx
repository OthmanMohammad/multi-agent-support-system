"use client";

import React, { Component, type ErrorInfo, type ReactNode } from "react";
import { AlertTriangle, Bug, Home, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, reset: () => void) => ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
  showDetails?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  errorCount: number;
}

/**
 * Advanced Error Boundary Component
 * Catches errors, logs them, and provides recovery options
 *
 * Features:
 * - Custom fallback UI
 * - Error logging hooks
 * - Automatic retry mechanism
 * - Error details toggle (dev mode)
 * - Error reporting integration ready
 */
export class ErrorBoundaryAdvanced extends Component<
  ErrorBoundaryProps,
  ErrorBoundaryState
> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      errorCount: 0,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return {
      hasError: true,
      error,
    };
  }

  override componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console
    console.error("Error Boundary caught an error:", error, errorInfo);

    // Update state with error details
    this.setState((prevState) => ({
      errorInfo,
      errorCount: prevState.errorCount + 1,
    }));

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }

    // TODO: Send error to logging service (e.g., Sentry, LogRocket)
    /*
    if (typeof window !== 'undefined' && window.Sentry) {
      window.Sentry.captureException(error, {
        contexts: {
          react: {
            componentStack: errorInfo.componentStack,
          },
        },
      });
    }
    */
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = (): void => {
    if (typeof window !== "undefined") {
      window.location.reload();
    }
  };

  handleGoHome = (): void => {
    if (typeof window !== "undefined") {
      window.location.href = "/";
    }
  };

  handleReportError = (): void => {
    const { error, errorInfo } = this.state;

    // Create error report
    const report = {
      message: error?.message || "Unknown error",
      stack: error?.stack || "",
      componentStack: errorInfo?.componentStack || "",
      timestamp: new Date().toISOString(),
      userAgent: typeof navigator !== "undefined" ? navigator.userAgent : "",
      url: typeof window !== "undefined" ? window.location.href : "",
    };

    // TODO: Send to error reporting service

    console.error("Error Report:", report);

    // For now, copy to clipboard
    if (typeof navigator !== "undefined" && navigator.clipboard) {
      navigator.clipboard.writeText(JSON.stringify(report, null, 2));
      // eslint-disable-next-line no-alert -- Simple user notification
      alert("Error details copied to clipboard");
    }
  };

  override render(): ReactNode {
    const { hasError, error, errorInfo, errorCount } = this.state;
    const {
      children,
      fallback,
      showDetails = process.env.NODE_ENV === "development",
    } = this.props;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback(error, this.handleReset);
      }

      // Default fallback UI
      return (
        <div className="flex min-h-screen items-center justify-center bg-background p-4">
          <div className="w-full max-w-2xl">
            {/* Error Card */}
            <div className="rounded-lg border border-destructive bg-destructive/5 p-8">
              {/* Icon */}
              <div className="mb-6 flex justify-center">
                <div className="rounded-full bg-destructive/10 p-4">
                  <AlertTriangle className="h-12 w-12 text-destructive" />
                </div>
              </div>

              {/* Title */}
              <h1 className="mb-2 text-center text-2xl font-bold text-destructive">
                Oops! Something went wrong
              </h1>

              {/* Description */}
              <p className="mb-6 text-center text-foreground-secondary">
                We apologize for the inconvenience. The application encountered
                an unexpected error.
              </p>

              {/* Error Message */}
              {showDetails && (
                <div className="mb-6 rounded-lg border border-border bg-surface p-4">
                  <div className="mb-2 flex items-center gap-2 text-sm font-semibold">
                    <Bug className="h-4 w-4" />
                    Error Details
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-mono text-destructive">
                      {error.message}
                    </p>
                    {errorCount > 1 && (
                      <p className="text-xs text-foreground-secondary">
                        This error has occurred {errorCount} time
                        {errorCount > 1 ? "s" : ""}.
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* Stack Trace (Dev Mode Only) */}
              {showDetails && error.stack && (
                <details className="mb-6 rounded-lg border border-border bg-surface">
                  <summary className="cursor-pointer p-4 text-sm font-semibold hover:bg-surface/80">
                    Stack Trace
                  </summary>
                  <div className="border-t border-border p-4">
                    <pre className="overflow-x-auto text-xs text-foreground-secondary">
                      {error.stack}
                    </pre>
                  </div>
                </details>
              )}

              {/* Component Stack (Dev Mode Only) */}
              {showDetails && errorInfo?.componentStack && (
                <details className="mb-6 rounded-lg border border-border bg-surface">
                  <summary className="cursor-pointer p-4 text-sm font-semibold hover:bg-surface/80">
                    Component Stack
                  </summary>
                  <div className="border-t border-border p-4">
                    <pre className="overflow-x-auto text-xs text-foreground-secondary">
                      {errorInfo.componentStack}
                    </pre>
                  </div>
                </details>
              )}

              {/* Actions */}
              <div className="flex flex-col gap-3 sm:flex-row">
                <Button
                  onClick={this.handleReset}
                  className="flex-1"
                  variant="default"
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Try Again
                </Button>

                <Button
                  onClick={this.handleReload}
                  className="flex-1"
                  variant="outline"
                >
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Reload Page
                </Button>

                <Button
                  onClick={this.handleGoHome}
                  className="flex-1"
                  variant="outline"
                >
                  <Home className="mr-2 h-4 w-4" />
                  Go Home
                </Button>
              </div>

              {/* Report Button (Dev Mode) */}
              {showDetails && (
                <div className="mt-3">
                  <Button
                    onClick={this.handleReportError}
                    className="w-full"
                    variant="ghost"
                  >
                    <Bug className="mr-2 h-4 w-4" />
                    Copy Error Details
                  </Button>
                </div>
              )}

              {/* Help Text */}
              <div className="mt-6 text-center text-sm text-foreground-secondary">
                If this problem persists, please contact support.
              </div>
            </div>
          </div>
        </div>
      );
    }

    return children;
  }
}

/**
 * Functional wrapper for Error Boundary
 * Use this in app router where class components aren't ideal
 */
export function withErrorBoundary<P extends object>(
  Component: React.ComponentType<P>,
  errorBoundaryProps?: Omit<ErrorBoundaryProps, "children">
): React.ComponentType<P> {
  const WrappedComponent = (props: P) => (
    <ErrorBoundaryAdvanced {...errorBoundaryProps}>
      <Component {...props} />
    </ErrorBoundaryAdvanced>
  );

  WrappedComponent.displayName = `withErrorBoundary(${Component.displayName || Component.name || "Component"})`;

  return WrappedComponent;
}
