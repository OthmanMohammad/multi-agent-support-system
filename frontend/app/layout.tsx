import type { Metadata, Viewport } from 'next';
import { Toaster } from 'sonner';

import { Providers } from '@/components/shared/providers';

import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'Multi-Agent Support | AI-Powered Customer Support',
    template: '%s | Multi-Agent Support',
  },
  description:
    'Enterprise-grade AI-powered customer support platform with 243+ specialized agents. Handle support, sales, and success at scale.',
  keywords: ['AI', 'customer support', 'multi-agent', 'chatbot', 'enterprise'],
  authors: [{ name: 'Multi-Agent Support' }],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://thatagentsproject.com',
    siteName: 'Multi-Agent Support',
    title: 'Multi-Agent Support | AI-Powered Customer Support',
    description:
      'Enterprise-grade AI-powered customer support platform with 243+ specialized agents.',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Multi-Agent Support | AI-Powered Customer Support',
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
    <html lang="en">
      <body className="min-h-screen bg-background antialiased">
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
