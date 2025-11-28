import Link from 'next/link';

import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

const sizes = {
  sm: 'h-6 w-6',
  md: 'h-7 w-7',
  lg: 'h-9 w-9',
};

const textSizes = {
  sm: 'text-base',
  md: 'text-lg',
  lg: 'text-xl',
};

export function Logo({ className, size = 'md', showText = true }: LogoProps) {
  return (
    <Link href="/" className={cn('flex items-center gap-2.5', className)}>
      {/* Pixel Art Style Logo - Mistral Inspired */}
      <div className={cn('relative flex-shrink-0', sizes[size])}>
        <svg
          viewBox="0 0 32 32"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="h-full w-full"
          style={{ imageRendering: 'pixelated' }}
        >
          {/* Pixel art M shape with rainbow gradient */}
          <rect x="2" y="6" width="4" height="22" fill="#EE4B2B" />
          <rect x="6" y="2" width="4" height="4" fill="#FF5F1F" />
          <rect x="10" y="6" width="4" height="4" fill="#FF7000" />
          <rect x="14" y="10" width="4" height="4" fill="#FFA500" />
          <rect x="18" y="6" width="4" height="4" fill="#FF7000" />
          <rect x="22" y="2" width="4" height="4" fill="#FF5F1F" />
          <rect x="26" y="6" width="4" height="22" fill="#FFD700" />
        </svg>
      </div>
      {showText && (
        <span className={cn('font-bold tracking-tight text-text-primary', textSizes[size])}>
          That Agents
        </span>
      )}
    </Link>
  );
}
