'use client';

import { ChevronDown, Menu, X } from 'lucide-react';
import Link from 'next/link';
import { useEffect, useState } from 'react';

import { Logo } from '@/components/shared';
import { Button } from '@/components/ui';
import { useAuthStore } from '@/lib/stores/auth-store';
import { cn } from '@/lib/utils';

const navLinks = [
  { href: '#technology', label: 'Technology' },
  { href: '#agents', label: 'Agents' },
  { href: '/docs', label: 'Docs' },
];

export function MarketingHeader() {
  const { isAuthenticated } = useAuthStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  // Handle scroll effect
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
        'sticky top-0 z-50 transition-all duration-200',
        scrolled ? 'bg-background/95 backdrop-blur-md border-b border-border' : 'bg-transparent'
      )}
    >
      <div className="container">
        <nav className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Logo />

          {/* Desktop Navigation - Center */}
          <div className="hidden md:flex md:items-center md:gap-1">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors rounded-md hover:bg-background-secondary"
              >
                {link.label}
              </Link>
            ))}
            {/* Dropdown example - like Mistral */}
            <div className="relative group">
              <button className="flex items-center gap-1 px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary transition-colors rounded-md hover:bg-background-secondary">
                Company
                <ChevronDown className="h-4 w-4 transition-transform group-hover:rotate-180" />
              </button>
              <div className="absolute top-full left-0 pt-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
                <div className="bg-surface border border-border rounded-lg shadow-lg py-2 min-w-[160px]">
                  <Link
                    href="/about"
                    className="block px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-background-secondary"
                  >
                    About
                  </Link>
                  <Link
                    href="/blog"
                    className="block px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-background-secondary"
                  >
                    Blog
                  </Link>
                  <Link
                    href="/careers"
                    className="block px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-background-secondary"
                  >
                    Careers
                  </Link>
                </div>
              </div>
            </div>
          </div>

          {/* CTA Buttons - Right */}
          <div className="hidden md:flex md:items-center md:gap-3">
            {isAuthenticated ? (
              <Link href="/chat">
                <Button size="sm">Dashboard</Button>
              </Link>
            ) : (
              <>
                <Link href="/login">
                  <Button variant="ghost" size="sm">
                    Sign in
                  </Button>
                </Link>
                <Link href="/register">
                  <Button size="sm">Get started</Button>
                </Link>
              </>
            )}
          </div>

          {/* Mobile Menu Button */}
          <button
            type="button"
            className="md:hidden p-2 text-text-secondary hover:text-text-primary transition-colors"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </nav>

        {/* Mobile Menu */}
        <div
          className={cn(
            'md:hidden overflow-hidden transition-all duration-300 ease-out',
            mobileMenuOpen ? 'max-h-[400px] opacity-100' : 'max-h-0 opacity-0'
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
            <Link
              href="/about"
              className="py-3 text-base font-medium text-text-secondary hover:text-text-primary transition-colors"
              onClick={() => setMobileMenuOpen(false)}
            >
              About
            </Link>

            <div className="flex flex-col gap-2 pt-4 mt-4 border-t border-border">
              {isAuthenticated ? (
                <Link href="/chat" onClick={() => setMobileMenuOpen(false)}>
                  <Button className="w-full">Dashboard</Button>
                </Link>
              ) : (
                <>
                  <Link href="/login" onClick={() => setMobileMenuOpen(false)}>
                    <Button variant="outline" className="w-full">
                      Sign in
                    </Button>
                  </Link>
                  <Link href="/register" onClick={() => setMobileMenuOpen(false)}>
                    <Button className="w-full">Get started</Button>
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
