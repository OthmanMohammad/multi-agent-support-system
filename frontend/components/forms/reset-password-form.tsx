'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Eye, EyeOff, CheckCircle } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { useForm } from 'react-hook-form';

import { Button, Input, Label } from '@/components/ui';
import { resetPassword } from '@/lib/api/auth';
import { resetPasswordSchema, type ResetPasswordFormData } from '@/lib/validations/auth';

import { FieldError } from './field-error';

interface ResetPasswordFormProps {
  token: string;
}

export function ResetPasswordForm({ token }: ResetPasswordFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      token,
      new_password: '',
      confirm_password: '',
    },
  });

  const onSubmit = async (data: ResetPasswordFormData) => {
    setIsLoading(true);
    setError(null);
    try {
      await resetPassword({
        token: data.token,
        new_password: data.new_password,
      });
      setIsSuccess(true);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to reset password';
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
          <h1 className="text-2xl font-bold text-text-primary">Password reset successful</h1>
          <p className="text-text-secondary">
            Your password has been reset. You can now sign in with your new password.
          </p>
        </div>
        <Link href="/login">
          <Button className="w-full">Sign in</Button>
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold text-text-primary">Reset your password</h1>
        <p className="text-text-secondary">Enter your new password below</p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Error */}
        {error && (
          <div className="rounded-md bg-error-light p-3 text-sm text-error">{error}</div>
        )}

        {/* Hidden Token Field */}
        <input type="hidden" {...register('token')} />

        {/* Password Field */}
        <div className="space-y-2">
          <Label htmlFor="new_password">New Password</Label>
          <div className="relative">
            <Input
              id="new_password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Create a strong password"
              autoComplete="new-password"
              error={!!errors.new_password}
              {...register('new_password')}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <FieldError message={errors.new_password?.message} />
          <p className="text-xs text-text-tertiary">
            Must be 8+ characters with uppercase, lowercase, number, and special character
          </p>
        </div>

        {/* Confirm Password Field */}
        <div className="space-y-2">
          <Label htmlFor="confirm_password">Confirm Password</Label>
          <div className="relative">
            <Input
              id="confirm_password"
              type={showConfirmPassword ? 'text' : 'password'}
              placeholder="Confirm your password"
              autoComplete="new-password"
              error={!!errors.confirm_password}
              {...register('confirm_password')}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary transition-colors"
            >
              {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
          <FieldError message={errors.confirm_password?.message} />
        </div>

        {/* Submit Button */}
        <Button type="submit" className="w-full" isLoading={isLoading}>
          Reset password
        </Button>
      </form>
    </div>
  );
}
