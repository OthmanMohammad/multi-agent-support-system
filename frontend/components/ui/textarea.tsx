'use client';

import { forwardRef, type TextareaHTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

export interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean;
}

const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, error, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          'flex min-h-[80px] w-full rounded-md border bg-surface px-3 py-2 text-sm text-text-primary',
          'placeholder:text-text-tertiary',
          'transition-colors duration-150',
          'focus:outline-none focus:ring-2 focus:ring-brand-orange focus:ring-offset-1',
          'disabled:cursor-not-allowed disabled:opacity-50',
          'resize-none',
          error
            ? 'border-error focus:ring-error'
            : 'border-border hover:border-border-strong focus:border-brand-orange',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);

Textarea.displayName = 'Textarea';

export { Textarea };
