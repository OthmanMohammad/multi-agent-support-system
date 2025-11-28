'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Turnstile } from '@marsidev/react-turnstile';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useCallback, useState } from 'react';
import { useForm } from 'react-hook-form';

import { Button, Icon, Input, Label, Separator } from '@/components/ui';
import { useAuthStore } from '@/lib/stores/auth-store';
import { registerSchema, type RegisterFormData } from '@/lib/validations/auth';

import { FieldError } from './field-error';
import { OAuthButtons } from './oauth-buttons';

const TURNSTILE_SITE_KEY = process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY || '1x00000000000000000000AA';

export function RegisterForm() {
  const router = useRouter();
  const { register: registerUser, isLoading, error, clearError } = useAuthStore();
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      full_name: '',
      organization: '',
      password: '',
      confirm_password: '',
      turnstile_token: '',
    },
  });

  const handleTurnstileSuccess = useCallback(
    (token: string) => {
      setValue('turnstile_token', token, { shouldValidate: true });
    },
    [setValue]
  );

  const onSubmit = async (data: RegisterFormData) => {
    clearError();
    try {
      await registerUser({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        organization: data.organization,
        turnstile_token: data.turnstile_token,
      });
      router.push('/chat');
    } catch {
      // Error is handled by the store
    }
  };

  return (
    <div className="w-full max-w-md space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold text-text-primary">Create an account</h1>
        <p className="text-text-secondary">Get started with your AI-powered support platform</p>
      </div>

      {/* OAuth Buttons */}
      <OAuthButtons />

      {/* Divider */}
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <Separator />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-surface px-2 text-text-tertiary">Or register with email</span>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        {/* Global Error */}
        {error && (
          <div className="rounded-lg bg-error-light p-3 text-sm text-error border border-error/20">
            {error}
          </div>
        )}

        {/* Full Name Field */}
        <div className="space-y-2">
          <Label htmlFor="full_name">Full Name</Label>
          <div className="relative">
            <Input
              id="full_name"
              type="text"
              placeholder="John Doe"
              autoComplete="name"
              error={!!errors.full_name}
              className="pr-10"
              {...register('full_name')}
            />
            <Icon name="user" size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          </div>
          <FieldError message={errors.full_name?.message} />
        </div>

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
              className="pr-10"
              {...register('email')}
            />
            <Icon name="mail" size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          </div>
          <FieldError message={errors.email?.message} />
        </div>

        {/* Organization Field (Optional) */}
        <div className="space-y-2">
          <Label htmlFor="organization">
            Organization <span className="text-text-tertiary">(optional)</span>
          </Label>
          <div className="relative">
            <Input
              id="organization"
              type="text"
              placeholder="Acme Corp"
              autoComplete="organization"
              className="pr-10"
              {...register('organization')}
            />
            <Icon name="building" size={16} className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          </div>
          <FieldError message={errors.organization?.message} />
        </div>

        {/* Password Field */}
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <div className="relative">
            <Input
              id="password"
              type={showPassword ? 'text' : 'password'}
              placeholder="Create a strong password"
              autoComplete="new-password"
              error={!!errors.password}
              className="pr-10"
              {...register('password')}
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary transition-colors"
            >
              <Icon name={showPassword ? 'eye-off' : 'eye'} size={16} />
            </button>
          </div>
          <FieldError message={errors.password?.message} />
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
              className="pr-10"
              {...register('confirm_password')}
            />
            <button
              type="button"
              onClick={() => setShowConfirmPassword(!showConfirmPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-secondary transition-colors"
            >
              <Icon name={showConfirmPassword ? 'eye-off' : 'eye'} size={16} />
            </button>
          </div>
          <FieldError message={errors.confirm_password?.message} />
        </div>

        {/* Turnstile Captcha */}
        <div className="space-y-2">
          <div className="flex justify-center">
            <Turnstile
              siteKey={TURNSTILE_SITE_KEY}
              onSuccess={handleTurnstileSuccess}
              options={{
                theme: 'dark',
                size: 'normal',
              }}
            />
          </div>
          <input type="hidden" {...register('turnstile_token')} />
          <FieldError message={errors.turnstile_token?.message} />
        </div>

        {/* Submit Button */}
        <Button type="submit" className="w-full" isLoading={isLoading}>
          Create account
        </Button>

        {/* Terms */}
        <p className="text-center text-xs text-text-tertiary">
          By creating an account, you agree to our{' '}
          <Link href="/terms" className="text-mistral-orange hover:text-mistral-orange-light transition-colors">
            Terms of Service
          </Link>{' '}
          and{' '}
          <Link href="/privacy" className="text-mistral-orange hover:text-mistral-orange-light transition-colors">
            Privacy Policy
          </Link>
        </p>
      </form>

      {/* Login Link */}
      <p className="text-center text-sm text-text-secondary">
        Already have an account?{' '}
        <Link
          href="/login"
          className="font-medium text-mistral-orange hover:text-mistral-orange-light transition-colors"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
