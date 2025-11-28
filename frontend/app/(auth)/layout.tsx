'use client';

import { redirect } from 'next/navigation';
import { useEffect, type ReactNode } from 'react';

import { Logo } from '@/components/shared';
import { useAuthStore } from '@/lib/stores/auth-store';

interface AuthLayoutProps {
  children: ReactNode;
}

export default function AuthLayout({ children }: AuthLayoutProps) {
  const { isAuthenticated, isInitialized, isLoading } = useAuthStore();

  useEffect(() => {
    // Redirect to dashboard if already authenticated
    if (isInitialized && isAuthenticated) {
      redirect('/chat');
    }
  }, [isAuthenticated, isInitialized]);

  // Show nothing while checking auth
  if (!isInitialized || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="animate-pulse">
          <Logo size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-background">
      {/* Rainbow bar */}
      <div className="flex h-1 w-full">
        <div className="flex-1 bg-brand-red" />
        <div className="flex-1 bg-brand-orange-dark" />
        <div className="flex-1 bg-brand-orange" />
        <div className="flex-1 bg-brand-orange-light" />
        <div className="flex-1 bg-brand-yellow" />
      </div>

      {/* Header */}
      <header className="p-6 lg:p-8">
        <Logo />
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6 pb-12">
        <div className="w-full max-w-sm">
          <div className="bg-surface rounded-lg border border-border p-8">{children}</div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-sm text-text-tertiary">
        <p>{new Date().getFullYear()} That Agents Project</p>
      </footer>
    </div>
  );
}
