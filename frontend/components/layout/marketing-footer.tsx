'use client';

import Link from 'next/link';

import { Logo } from '@/components/shared';
import { Icon } from '@/components/ui';

// =============================================================================
// TAP Marketing Footer - Mistral.ai Inspired Dark Design
// =============================================================================

const footerLinks = {
  product: [
    { href: '/#technology', label: 'Technology' },
    { href: '/#agents', label: 'Agents' },
    { href: '/docs', label: 'Documentation' },
    { href: '/changelog', label: 'Changelog' },
  ],
  company: [
    { href: '/about', label: 'About' },
    { href: '/blog', label: 'Blog' },
    { href: '/careers', label: 'Careers' },
    { href: '/contact', label: 'Contact' },
  ],
  resources: [
    { href: '/docs', label: 'API Reference' },
    { href: '/guides', label: 'Guides' },
    { href: '/status', label: 'System Status' },
    { href: '/support', label: 'Support' },
  ],
  legal: [
    { href: '/privacy', label: 'Privacy Policy' },
    { href: '/terms', label: 'Terms of Service' },
    { href: '/security', label: 'Security' },
  ],
};

const socialLinks = [
  { href: 'https://twitter.com', label: 'Twitter', icon: 'twitter' },
  { href: 'https://github.com', label: 'GitHub', icon: 'github' },
  { href: 'https://linkedin.com', label: 'LinkedIn', icon: 'linkedin' },
  { href: 'https://discord.com', label: 'Discord', icon: 'discord' },
];

export function MarketingFooter() {
  return (
    <footer className="border-t border-border bg-white">
      {/* Main Footer Content */}
      <div className="container py-16 lg:py-20">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-6 lg:gap-12">
          {/* Brand Column */}
          <div className="col-span-2">
            <Logo size="lg" showText={true} />
            <p className="mt-4 text-sm text-text-secondary leading-relaxed max-w-xs">
              AI-powered customer support platform with 243+ specialized agents for enterprise teams.
            </p>

            {/* Social Links */}
            <div className="flex items-center gap-4 mt-6">
              {socialLinks.map((link) => (
                <a
                  key={link.label}
                  href={link.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-text-tertiary hover:text-text-primary transition-colors"
                  aria-label={link.label}
                >
                  <Icon name={link.icon} size={20} />
                </a>
              ))}
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-4">Product</h3>
            <ul className="space-y-3">
              {footerLinks.product.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-4">Company</h3>
            <ul className="space-y-3">
              {footerLinks.company.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-4">Resources</h3>
            <ul className="space-y-3">
              {footerLinks.resources.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal Links */}
          <div>
            <h3 className="text-sm font-semibold text-text-primary mb-4">Legal</h3>
            <ul className="space-y-3">
              {footerLinks.legal.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-sm text-text-secondary hover:text-text-primary transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* Rainbow Bar */}
      <div className="flex h-1 w-full">
        <div className="flex-1 bg-mistral-red" />
        <div className="flex-1 bg-mistral-orange-dark" />
        <div className="flex-1 bg-mistral-orange" />
        <div className="flex-1 bg-mistral-orange-light" />
        <div className="flex-1 bg-mistral-yellow" />
      </div>

      {/* Bottom Bar */}
      <div className="border-t border-border">
        <div className="container py-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-sm text-text-tertiary">
              {new Date().getFullYear()} That Agents Project. All rights reserved.
            </p>
            <div className="flex items-center gap-6">
              <Link
                href="/privacy"
                className="text-sm text-text-tertiary hover:text-text-primary transition-colors"
              >
                Privacy
              </Link>
              <Link
                href="/terms"
                className="text-sm text-text-tertiary hover:text-text-primary transition-colors"
              >
                Terms
              </Link>
              <Link
                href="/cookies"
                className="text-sm text-text-tertiary hover:text-text-primary transition-colors"
              >
                Cookies
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
