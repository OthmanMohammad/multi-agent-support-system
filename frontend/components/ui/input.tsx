'use client';

import { forwardRef, type InputHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

// =============================================================================
// TAP Input Component - Mistral.ai Dark Mode Style
// =============================================================================

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, error, leftIcon, rightIcon, ...props }, ref) => {
    return (
      <div className="relative w-full">
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary">{leftIcon}</div>
        )}
        <input
          type={type}
          className={cn(
            // Base styles
            'flex h-11 w-full rounded-lg border bg-surface px-4 text-base text-text-primary',
            'placeholder:text-text-tertiary',
            'transition-all duration-200',
            // Focus styles
            'focus:outline-none focus:ring-2 focus:ring-mistral-orange/20',
            // Default border
            'border-border focus:border-mistral-orange',
            // Error state
            error && 'border-error focus:border-error focus:ring-error/20',
            // Disabled state
            'disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-surface-elevated',
            // File input
            'file:border-0 file:bg-transparent file:text-sm file:font-medium',
            // Icon padding
            leftIcon && 'pl-10',
            rightIcon && 'pr-10',
            className
          )}
          ref={ref}
          {...props}
        />
        {rightIcon && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2 text-text-tertiary">{rightIcon}</div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

// =============================================================================
// Search Input - Specialized input with search icon
// =============================================================================
const SearchInput = forwardRef<HTMLInputElement, Omit<InputProps, 'leftIcon'>>(
  ({ className, ...props }, ref) => {
    return (
      <Input
        ref={ref}
        type="search"
        leftIcon={
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            style={{ imageRendering: 'pixelated' }}
          >
            {/* Pixel search icon */}
            <rect x="6" y="4" width="8" height="2" fill="currentColor" />
            <rect x="4" y="6" width="2" height="8" fill="currentColor" />
            <rect x="14" y="6" width="2" height="8" fill="currentColor" />
            <rect x="6" y="14" width="8" height="2" fill="currentColor" />
            <rect x="14" y="14" width="2" height="2" fill="currentColor" />
            <rect x="16" y="16" width="2" height="2" fill="currentColor" />
            <rect x="18" y="18" width="2" height="2" fill="currentColor" />
          </svg>
        }
        className={cn('', className)}
        {...props}
      />
    );
  }
);

SearchInput.displayName = 'SearchInput';

export { Input, SearchInput };
