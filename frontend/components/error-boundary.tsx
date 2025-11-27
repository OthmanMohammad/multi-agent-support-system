'use client';

import { Component, type ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

import { Button, Card, CardContent } from '@/components/ui';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <Card className="m-4">
          <CardContent className="p-8 text-center">
            <div className="flex justify-center mb-4">
              <div className="p-3 rounded-full bg-error/10">
                <AlertTriangle className="h-8 w-8 text-error" />
              </div>
            </div>
            <h2 className="text-xl font-semibold text-text-primary mb-2">Something went wrong</h2>
            <p className="text-text-secondary mb-6 max-w-md mx-auto">
              An unexpected error occurred. Please try refreshing the page or contact support if the
              problem persists.
            </p>
            <div className="flex gap-3 justify-center">
              <Button onClick={this.handleReset} variant="outline">
                <RefreshCw className="h-4 w-4 mr-2" />
                Try Again
              </Button>
              <Button onClick={() => window.location.reload()}>Refresh Page</Button>
            </div>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <pre className="mt-6 p-4 bg-background-secondary rounded-lg text-left text-sm overflow-auto max-h-48">
                {this.state.error.message}
                {'\n\n'}
                {this.state.error.stack}
              </pre>
            )}
          </CardContent>
        </Card>
      );
    }

    return this.props.children;
  }
}

// Page-level error component (for Next.js error.tsx files)
interface PageErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export function PageError({ error, reset }: PageErrorProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <Card className="max-w-lg w-full">
        <CardContent className="p-8 text-center">
          <div className="flex justify-center mb-4">
            <div className="p-3 rounded-full bg-error/10">
              <AlertTriangle className="h-8 w-8 text-error" />
            </div>
          </div>
          <h2 className="text-xl font-semibold text-text-primary mb-2">Something went wrong</h2>
          <p className="text-text-secondary mb-6">
            An error occurred while loading this page. Please try again.
          </p>
          <div className="flex gap-3 justify-center">
            <Button onClick={reset} variant="outline">
              <RefreshCw className="h-4 w-4 mr-2" />
              Try Again
            </Button>
            <Button onClick={() => (window.location.href = '/')}>Go Home</Button>
          </div>
          {process.env.NODE_ENV === 'development' && (
            <pre className="mt-6 p-4 bg-background-secondary rounded-lg text-left text-sm overflow-auto max-h-48">
              {error.message}
              {error.digest && `\n\nDigest: ${error.digest}`}
            </pre>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
