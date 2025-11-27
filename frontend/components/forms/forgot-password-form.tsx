'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Mail, ArrowLeft, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { Button, Input, Label } from '@/components/ui';
import { forgotPassword } from '@/lib/api/auth';
import { forgotPasswordSchema, type ForgotPasswordFormData } from '@/lib/validations/auth';

import { FieldError } from './field-error';

export function ForgotPasswordForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = async (data: ForgotPasswordFormData) => {
    setIsLoading(true);
    setError(null);
    try {
      await forgotPassword(data);
      setIsSuccess(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to send reset email';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  // Success State
  if (isSuccess) {
    return (
      <div className="w-full max-w-md space-y-6 text-center">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-success-light">
          <CheckCircle className="h-8 w-8 text-success" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-bold text-text-primary">Check your email</h1>
          <p className="text-text-secondary">
            If an account exists with that email, we&apos;ve sent you a password reset link.
          </p>
        </div>
        <Link href="/login">
          <Button variant="outline" className="w-full">
            <ArrowLeft className="h-4 w-4" />
            Back to sign in
          </Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold text-text-primary">Forgot your password?</h1>
        <p className="text-text-secondary">
          Enter your email and we&apos;ll send you a reset link
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Error */}
        {error && (
          <div className="rounded-md bg-error-light p-3 text-sm text-error">{error}</div>
        )}

        {/* Email Field */}
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <div className="relative">
            <Input
              id="email"
              type="email"
              placeholder="you@example.com"
              autoComplete="email"
              error={!!errors.email}
              {...register('email')}
            />
            <Mail className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-tertiary" />
          </div>
          <FieldError message={errors.email?.message} />
        </div>

        {/* Submit Button */}
        <Button type="submit" className="w-full" isLoading={isLoading}>
          Send reset link
        </Button>
      </form>

      {/* Back to Login */}
      <Link
        href="/login"
        className="flex items-center justify-center gap-2 text-sm text-text-secondary hover:text-text-primary transition-colors"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to sign in
      </Link>
    </div>
  );
}
