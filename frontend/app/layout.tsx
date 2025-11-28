import type { Metadata, Viewport } from 'next';
import { DM_Sans } from 'next/font/google';
import { Toaster } from 'sonner';

import { Providers } from '@/components/shared/providers';

import './globals.css';

const dmSans = DM_Sans({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
  variable: '--font-dm-sans',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'That Agents Project | AI-Powered Customer Support',
    template: '%s | That Agents Project',
  },
  description:
    'Enterprise-grade AI-powered customer support platform with 243+ specialized agents. Handle support, sales, and success at scale.',
  keywords: ['AI', 'customer support', 'multi-agent', 'chatbot', 'enterprise', 'that agents project'],
  authors: [{ name: 'That Agents Project' }],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://thatagentsproject.com',
    siteName: 'That Agents Project',
    title: 'That Agents Project | AI-Powered Customer Support',
    description:
      'Enterprise-grade AI-powered customer support platform with 243+ specialized agents.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'That Agents Project | AI-Powered Customer Support',
    description:
      'Enterprise-grade AI-powered customer support platform with 243+ specialized agents.',
  },
  robots: {
    index: true,
    follow: true,
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#FF8205',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={dmSans.variable}>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: 'var(--surface)',
                border: '1px solid var(--border)',
                color: 'var(--text-primary)',
              },
            }}
          />
        </Providers>
      </body>
    </html>
  );
}
