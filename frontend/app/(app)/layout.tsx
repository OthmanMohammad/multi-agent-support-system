'use client';

import { redirect } from 'next/navigation';
import { useEffect, type ReactNode } from 'react';

import { AppSidebar } from '@/components/layout/app-sidebar';
import { AppHeader } from '@/components/layout/app-header';
import { Spinner } from '@/components/ui';
import { useAuthStore } from '@/lib/stores/auth-store';

interface AppLayoutProps {
  children: ReactNode;
}

export default function AppLayout({ children }: AppLayoutProps) {
  const { isAuthenticated, isInitialized, isLoading, user } = useAuthStore();

  useEffect(() => {
    // Redirect to login if not authenticated
    if (isInitialized && !isAuthenticated) {
      redirect('/login');
    }
  }, [isAuthenticated, isInitialized]);

  // Show loading while checking auth
  if (!isInitialized || isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Spinner size="lg" />
      </div>
    );
  }

  // Don't render if not authenticated (redirect will happen)
  if (!isAuthenticated || !user) {
    return null;
  }

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      {/* Sidebar */}
      <AppSidebar />

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <AppHeader />

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
