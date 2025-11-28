'use client';

import Link from 'next/link';

import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
  animated?: boolean;
}

const sizes = {
  sm: 'h-6 w-6',
  md: 'h-8 w-8',
  lg: 'h-10 w-10',
  xl: 'h-12 w-12',
};

const textSizes = {
  sm: 'text-sm',
  md: 'text-base',
  lg: 'text-lg',
  xl: 'text-xl',
};

// =============================================================================
// TAP Logo Component - Pixel Art Style (Mistral Inspired)
// =============================================================================
export function Logo({ className, size = 'md', showText = true, animated = false }: LogoProps) {
  return (
    <Link href="/" className={cn('flex items-center gap-2.5', className)}>
      {/* Pixel Art Logo - "T" with network nodes (like Mistral's M) */}
      <div className={cn('relative flex-shrink-0', sizes[size])}>
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className={cn('h-full w-full', animated && 'animate-pulse')}
          style={{ imageRendering: 'pixelated' }}
        >
          {/* Rainbow gradient "T" shape */}
          {/* Top bar - gradient from left to right */}
          <rect x="2" y="4" width="6" height="6" fill="#EF4444" />
          <rect x="8" y="4" width="5" height="6" fill="#EA580C" />
          <rect x="13" y="4" width="6" height="6" fill="#F97316" />
          <rect x="19" y="4" width="5" height="6" fill="#FB923C" />
          <rect x="24" y="4" width="6" height="6" fill="#FACC15" />

          {/* Stem of T - gradient from top to bottom */}
          <rect x="12" y="10" width="8" height="5" fill="#F97316" />
          <rect x="12" y="15" width="8" height="5" fill="#FB923C" />
          <rect x="12" y="20" width="8" height="8" fill="#FACC15" />

          {/* Network nodes - representing agents */}
          <rect x="0" y="6" width="3" height="3" fill="#A3A3A3" opacity="0.7" />
          <rect x="29" y="6" width="3" height="3" fill="#A3A3A3" opacity="0.7" />
          <rect x="4" y="18" width="3" height="3" fill="#A3A3A3" opacity="0.7" />
          <rect x="25" y="18" width="3" height="3" fill="#A3A3A3" opacity="0.7" />
        </svg>
      </div>

      {showText && (
        <div className="flex flex-col">
          <span className={cn('font-bold tracking-tight text-text-primary', textSizes[size])}>
            That Agents
          </span>
          {size !== 'sm' && (
            <span className="text-xs text-text-secondary tracking-wide">Project</span>
          )}
        </div>
      )}
    </Link>
  );
}

// =============================================================================
// Compact Logo (Icon Only)
// =============================================================================
export function LogoIcon({ className, size = 'md' }: Omit<LogoProps, 'showText'>) {
  return (
    <div className={cn('relative flex-shrink-0', sizes[size], className)}>
      <svg
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className="h-full w-full"
        style={{ imageRendering: 'pixelated' }}
      >
        {/* Simplified T with gradient */}
        <rect x="4" y="4" width="24" height="6" fill="url(#tap-gradient)" />
        <rect x="12" y="10" width="8" height="18" fill="url(#tap-gradient-vertical)" />

        <defs>
          <linearGradient id="tap-gradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#EF4444" />
            <stop offset="25%" stopColor="#EA580C" />
            <stop offset="50%" stopColor="#F97316" />
            <stop offset="75%" stopColor="#FB923C" />
            <stop offset="100%" stopColor="#FACC15" />
          </linearGradient>
          <linearGradient id="tap-gradient-vertical" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#F97316" />
            <stop offset="100%" stopColor="#FACC15" />
          </linearGradient>
        </defs>
      </svg>
    </div>
  );
}
