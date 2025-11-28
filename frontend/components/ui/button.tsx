'use client';

import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { forwardRef, type ButtonHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

// =============================================================================
// TAP Button Component - Mistral.ai Style
// SHARP CORNERS - 0 border radius on all buttons
// =============================================================================

const buttonVariants = cva(
  // Base styles - SHARP CORNERS (no rounded-lg!)
  'inline-flex items-center justify-center gap-2 whitespace-nowrap font-semibold transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-mistral-orange focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50',
  {
    variants: {
      variant: {
        // Primary: Orange background (Mistral's signature #FF8205)
        primary:
          'bg-mistral-orange text-white hover:bg-mistral-orange-dark active:scale-[0.98]',

        // Secondary: White background with dark text
        secondary:
          'bg-white text-mistral-brown hover:bg-beige-light active:scale-[0.98] border border-border',

        // Outline: Transparent with border
        outline:
          'border border-border bg-transparent text-text-primary hover:border-mistral-tan hover:bg-beige-light',

        // Ghost: No background, subtle hover
        ghost: 'text-text-secondary hover:text-text-primary hover:bg-beige-light',

        // Danger: Red for destructive actions
        danger: 'bg-mistral-red text-white hover:bg-[#c00400] active:scale-[0.98]',

        // Link: Text only, underline on hover
        link: 'text-mistral-orange underline-offset-4 hover:underline p-0 h-auto font-normal',

        // Dark: Black button
        dark: 'bg-black text-white hover:bg-black-tinted active:scale-[0.98]',

        // Orange outline
        'orange-outline':
          'border border-mistral-orange bg-transparent text-mistral-orange hover:bg-mistral-orange/10',
      },
      size: {
        sm: 'h-9 px-4 text-sm',
        md: 'h-10 px-5 text-sm',
        lg: 'h-11 px-6 text-base',
        xl: 'h-12 px-8 text-base',
        '2xl': 'h-14 px-10 text-lg',
        icon: 'h-10 w-10',
        'icon-sm': 'h-8 w-8',
        'icon-lg': 'h-12 w-12',
      },
    },
    defaultVariants: {
      variant: 'primary',
      size: 'md',
    },
  }
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant,
      size,
      asChild = false,
      isLoading,
      leftIcon,
      rightIcon,
      children,
      disabled,
      ...props
    },
    ref
  ) => {
    const Comp = asChild ? Slot : 'button';

    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading ? (
          <>
            {/* Pixel-art style loading spinner */}
            <svg
              className="h-4 w-4 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
              style={{ imageRendering: 'pixelated' }}
            >
              <rect x="11" y="2" width="2" height="4" fill="currentColor" />
              <rect x="16" y="4" width="2" height="2" fill="currentColor" opacity="0.8" />
              <rect x="18" y="8" width="4" height="2" fill="currentColor" opacity="0.6" />
              <rect x="18" y="14" width="2" height="2" fill="currentColor" opacity="0.4" />
              <rect x="11" y="18" width="2" height="4" fill="currentColor" opacity="0.3" />
              <rect x="4" y="14" width="2" height="2" fill="currentColor" opacity="0.4" />
              <rect x="2" y="8" width="4" height="2" fill="currentColor" opacity="0.6" />
              <rect x="4" y="4" width="2" height="2" fill="currentColor" opacity="0.8" />
            </svg>
            <span>Loading...</span>
          </>
        ) : (
          <>
            {leftIcon && <span className="flex-shrink-0">{leftIcon}</span>}
            {children}
            {rightIcon && <span className="flex-shrink-0">{rightIcon}</span>}
          </>
        )}
      </Comp>
    );
  }
);

Button.displayName = 'Button';

export { Button, buttonVariants };
