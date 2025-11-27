'use client';

import { useSearchParams } from 'next/navigation';
import { Suspense } from 'react';

import { ResetPasswordForm } from '@/components/forms';
import { Spinner } from '@/components/ui';

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token');

  if (!token) {
    return (
      <div className="w-full max-w-md space-y-4 text-center">
        <h1 className="text-2xl font-bold text-text-primary">Invalid Link</h1>
        <p className="text-text-secondary">
          This password reset link is invalid or has expired. Please request a new one.
        </p>
      </div>
    );
  }

  return <ResetPasswordForm token={token} />;
}

export default function ResetPasswordPage() {
  return (
    <Suspense
      fallback={
        <div className="flex justify-center">
          <Spinner size="lg" />
        </div>
      }
    >
      <ResetPasswordContent />
    </Suspense>
  );
}
