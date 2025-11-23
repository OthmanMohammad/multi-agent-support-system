import type { JSX } from "react";
import { cn } from "@/lib/utils";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {}

/**
 * Skeleton Component
 * Animated loading placeholder for content
 */
export function Skeleton({ className, ...props }: SkeletonProps): JSX.Element {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-surface/50",
        className
      )}
      {...props}
    />
  );
}

/**
 * Shimmer Skeleton Component
 * Advanced skeleton with shimmer animation effect
 */
export function ShimmerSkeleton({
  className,
  ...props
}: SkeletonProps): JSX.Element {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-md bg-surface/50",
        "before:absolute before:inset-0",
        "before:-translate-x-full before:animate-[shimmer_2s_infinite]",
        "before:bg-gradient-to-r before:from-transparent before:via-white/10 before:to-transparent",
        className
      )}
      {...props}
    />
  );
}

/**
 * Skeleton Text Component
 * Pre-styled skeleton for text content
 */
export function SkeletonText({
  lines = 1,
  lastLineWidth = "60%",
  className,
}: {
  lines?: number;
  lastLineWidth?: string;
  className?: string;
}): JSX.Element {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className="h-4"
          style={{
            width: i === lines - 1 ? lastLineWidth : "100%",
          }}
        />
      ))}
    </div>
  );
}

/**
 * Skeleton Avatar Component
 * Pre-styled skeleton for avatar
 */
export function SkeletonAvatar({
  size = "md",
  className,
}: {
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}): JSX.Element {
  const sizeClasses = {
    sm: "h-8 w-8",
    md: "h-10 w-10",
    lg: "h-12 w-12",
    xl: "h-16 w-16",
  };

  return (
    <Skeleton className={cn("rounded-full", sizeClasses[size], className)} />
  );
}

/**
 * Skeleton Card Component
 * Pre-styled skeleton for card content
 */
export function SkeletonCard({
  showImage = true,
  showTitle = true,
  showDescription = true,
  descriptionLines = 2,
  className,
}: {
  showImage?: boolean;
  showTitle?: boolean;
  showDescription?: boolean;
  descriptionLines?: number;
  className?: string;
}): JSX.Element {
  return (
    <div className={cn("space-y-4", className)}>
      {showImage && <Skeleton className="h-48 w-full" />}
      {showTitle && <Skeleton className="h-6 w-2/3" />}
      {showDescription && (
        <SkeletonText lines={descriptionLines} lastLineWidth="80%" />
      )}
    </div>
  );
}

/**
 * Skeleton Table Component
 * Pre-styled skeleton for table rows
 */
export function SkeletonTable({
  rows = 5,
  columns = 4,
  className,
}: {
  rows?: number;
  columns?: number;
  className?: string;
}): JSX.Element {
  return (
    <div className={cn("space-y-2", className)}>
      {/* Header */}
      <div className="flex gap-4">
        {Array.from({ length: columns }).map((_, i) => (
          <Skeleton key={i} className="h-4 flex-1" />
        ))}
      </div>
      {/* Rows */}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={colIndex}
              className="h-8 flex-1"
              style={{
                width: colIndex === 0 ? "30%" : "auto",
              }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}

/**
 * Skeleton List Component
 * Pre-styled skeleton for list items
 */
export function SkeletonList({
  items = 5,
  showAvatar = true,
  showSecondaryText = true,
  className,
}: {
  items?: number;
  showAvatar?: boolean;
  showSecondaryText?: boolean;
  className?: string;
}): JSX.Element {
  return (
    <div className={cn("space-y-4", className)}>
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-4">
          {showAvatar && <SkeletonAvatar />}
          <div className="flex-1 space-y-2">
            <Skeleton className="h-4 w-full" />
            {showSecondaryText && <Skeleton className="h-3 w-3/4" />}
          </div>
        </div>
      ))}
    </div>
  );
}
