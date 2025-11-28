'use client';

import Link from 'next/link';
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
      <div className="min-h-screen flex items-center justify-center bg-beige-light">
        <div className="animate-pulse">
          <Logo size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col bg-beige-light">
      {/* Mistral Rainbow Bar */}
      <div className="flex h-1 w-full">
        <div className="flex-1 bg-mistral-red" />
        <div className="flex-1 bg-mistral-orange-dark" />
        <div className="flex-1 bg-mistral-orange" />
        <div className="flex-1 bg-mistral-orange-light" />
        <div className="flex-1 bg-mistral-yellow" />
      </div>

      {/* Header */}
      <header className="p-6 lg:p-8">
        <Link href="/">
          <Logo />
        </Link>
      </header>

      {/* Main Content */}
      <main className="flex-1 flex items-center justify-center px-6 pb-12">
        <div className="w-full max-w-sm">
          <div className="bg-white border border-border p-8">{children}</div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-sm text-text-tertiary">
        <p>&copy; {new Date().getFullYear()} That Agents Project. All rights reserved.</p>
      </footer>
    </div>
  );
}
