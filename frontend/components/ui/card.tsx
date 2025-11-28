'use client';

import { forwardRef, type HTMLAttributes } from 'react';

import { cn } from '@/lib/utils';

// =============================================================================
// TAP Card Component - Mistral.ai Dark Mode Style
// =============================================================================

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'elevated' | 'ghost' | 'gradient';
  interactive?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant = 'default', interactive = false, padding = 'md', ...props }, ref) => {
    const variants = {
      default: 'bg-surface border border-border',
      elevated: 'bg-surface-elevated border border-border shadow-card',
      ghost: 'bg-transparent border-0',
      gradient: 'bg-gradient-to-br from-surface to-background-secondary border border-border',
    };

    const paddings = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'transition-all duration-200', // Sharp corners - no rounded!
          variants[variant],
          paddings[padding],
          interactive &&
            'cursor-pointer hover:border-border-strong hover:-translate-y-1 hover:shadow-lg',
          className
        )}
        {...props}
      />
    );
  }
);

Card.displayName = 'Card';

// =============================================================================
// Card Header
// =============================================================================
const CardHeader = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex flex-col space-y-1.5', className)} {...props} />
  )
);
CardHeader.displayName = 'CardHeader';

// =============================================================================
// Card Title
// =============================================================================
const CardTitle = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLHeadingElement>>(
  ({ className, ...props }, ref) => (
    <h3
      ref={ref}
      className={cn('text-xl font-semibold text-text-primary tracking-tight', className)}
      {...props}
    />
  )
);
CardTitle.displayName = 'CardTitle';

// =============================================================================
// Card Description
// =============================================================================
const CardDescription = forwardRef<HTMLParagraphElement, HTMLAttributes<HTMLParagraphElement>>(
  ({ className, ...props }, ref) => (
    <p
      ref={ref}
      className={cn('text-sm text-text-secondary leading-relaxed', className)}
      {...props}
    />
  )
);
CardDescription.displayName = 'CardDescription';

// =============================================================================
// Card Content
// =============================================================================
const CardContent = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => <div ref={ref} className={cn('', className)} {...props} />
);
CardContent.displayName = 'CardContent';

// =============================================================================
// Card Footer
// =============================================================================
const CardFooter = forwardRef<HTMLDivElement, HTMLAttributes<HTMLDivElement>>(
  ({ className, ...props }, ref) => (
    <div ref={ref} className={cn('flex items-center pt-4', className)} {...props} />
  )
);
CardFooter.displayName = 'CardFooter';

// =============================================================================
// Feature Card - Specialized card for features section
// =============================================================================
export interface FeatureCardProps extends HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description: string;
}

const FeatureCard = forwardRef<HTMLDivElement, FeatureCardProps>(
  ({ className, icon, title, description, ...props }, ref) => (
    <Card ref={ref} variant="default" interactive className={cn('group', className)} {...props}>
      {icon && (
        <div className="mb-4 text-mistral-orange group-hover:text-mistral-yellow transition-colors">
          {icon}
        </div>
      )}
      <h3 className="text-lg font-semibold text-text-primary mb-2 group-hover:text-mistral-orange transition-colors">
        {title}
      </h3>
      <p className="text-sm text-text-secondary leading-relaxed">{description}</p>
    </Card>
  )
);
FeatureCard.displayName = 'FeatureCard';

export { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, FeatureCard };
