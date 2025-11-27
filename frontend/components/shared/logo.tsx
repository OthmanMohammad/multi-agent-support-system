import Link from 'next/link';

import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

const sizes = {
  sm: 'h-6 w-6',
  md: 'h-8 w-8',
  lg: 'h-10 w-10',
};

const textSizes = {
  sm: 'text-lg',
  md: 'text-xl',
  lg: 'text-2xl',
};

export function Logo({ className, size = 'md', showText = true }: LogoProps) {
  return (
    <Link href="/" className={cn('flex items-center gap-2', className)}>
      {/* Pixel Art Style Logo - Inspired by Mistral */}
      <div className={cn('relative', sizes[size])}>
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-full w-full"
        >
          {/* Pixel art M shape */}
          <rect x="2" y="8" width="4" height="20" fill="#FF8205" />
          <rect x="6" y="4" width="4" height="4" fill="#FA500F" />
          <rect x="10" y="8" width="4" height="4" fill="#FF8205" />
          <rect x="14" y="12" width="4" height="4" fill="#FFAF00" />
          <rect x="18" y="8" width="4" height="4" fill="#FF8205" />
          <rect x="22" y="4" width="4" height="4" fill="#FA500F" />
          <rect x="26" y="8" width="4" height="20" fill="#FF8205" />
        </svg>
      </div>
      {showText && (
        <span className={cn('font-bold text-text-primary', textSizes[size])}>
          Multi-Agent
        </span>
      )}
    </Link>
  );
}
