'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Logo } from '@/components/shared';
import { Button, Icon } from '@/components/ui';
import { useAuthStore } from '@/lib/stores/auth-store';
import { cn } from '@/lib/utils';

// =============================================================================
// TAP Marketing Header - Mistral.ai Inspired Dark Navigation
// =============================================================================

const navLinks = [
  { href: '/#technology', label: 'Technology' },
  { href: '/#agents', label: 'Agents' },
  { href: '/docs', label: 'Documentation' },
];

const companyLinks = [
  { href: '/about', label: 'About' },
  { href: '/blog', label: 'Blog' },
  { href: '/careers', label: 'Careers' },
];

export function MarketingHeader() {
  const { isAuthenticated } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll effect for background blur
  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 10);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        scrolled
          ? 'bg-beige-light/95 backdrop-blur-xl border-b border-border'
          : 'bg-transparent'
      )}
    >
      <div className="container">
        <nav className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Logo size="md" />

          {/* Desktop Navigation - Center */}
          <div className="hidden md:flex md:items-center md:gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors hover:bg-beige-medium"
              >
                {link.label}
              </Link>
            ))}

            {/* Company Dropdown */}
            <div className="relative group">
              <button className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors hover:bg-beige-medium">
                Company
                <Icon name="chevron-down" size={14} className="transition-transform group-hover:rotate-180" />
              </button>

              {/* Dropdown Menu */}
              <div className="absolute top-full left-0 pt-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 transform group-hover:translate-y-0 translate-y-2">
                <div className="bg-white border border-border shadow-xl py-2 min-w-[180px]">
                  {companyLinks.map((link) => (
                    <Link
                      key={link.href}
                      href={link.href}
                      className="flex items-center gap-3 px-4 py-2.5 text-sm text-text-secondary hover:text-text-primary hover:bg-beige-light transition-colors"
                    >
                      {link.label}
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* CTA Buttons - Right */}
          <div className="hidden md:flex md:items-center md:gap-3">
            {isAuthenticated ? (
              <Link href="/chat">
                <Button size="sm">
                  Dashboard
                  <Icon name="arrow-right" size={14} />
                </Button>
              </Link>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Sign in
                  </Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">
                    Get started
                    <Icon name="arrow-right" size={14} />
                  </Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            type="button"
            className="md:hidden p-2 text-text-secondary hover:text-text-primary transition-colors hover:bg-beige-medium"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            <Icon name={mobileMenuOpen ? 'close' : 'menu'} size={20} />
          </button>
        </nav>

        {/* Mobile Menu */}
        <div
          className={cn(
            'md:hidden overflow-hidden transition-all duration-300 ease-out',
            mobileMenuOpen ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
          )}
        >
          <div className="flex flex-col py-4 border-t border-border">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="py-3 text-base font-medium text-text-secondary hover:text-text-primary transition-colors"
                onClick={() => setMobileMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}

            {/* Company links in mobile */}
            <div className="py-3 border-t border-border mt-3">
              <p className="text-xs font-medium text-text-tertiary uppercase tracking-wider mb-2">
                Company
              </p>
              {companyLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="block py-2 text-base font-medium text-text-secondary hover:text-text-primary transition-colors"
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
            </div>

            {/* Mobile CTAs */}
            <div className="flex flex-col gap-3 pt-4 mt-3 border-t border-border">
              {isAuthenticated ? (
                <Link href="/chat" onClick={() => setMobileMenuOpen(false)}>
                  <Button className="w-full">
                    Dashboard
                    <Icon name="arrow-right" size={14} />
                  </Button>
                </Link>
              ) : (
                <>
                  <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="outline" className="w-full">
                      Sign in
                    </Button>
                  </Link>
                  <Link href="/register" onClick={() => setMobileMenuOpen(false)}>
                    <Button className="w-full">
                      Get started
                      <Icon name="arrow-right" size={14} />
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
