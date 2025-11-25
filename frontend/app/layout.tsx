import type { JSX } from "react";
import type { Metadata } from "next";
import { SessionProvider } from "next-auth/react";

import { ThemeProvider } from "@/components/theme-provider";
import { QueryProvider } from "@/lib/react-query/provider";
import { ToastProvider } from "@/components/providers/toast-provider";
import { CommandPalette } from "@/components/command-palette";
import { KeyboardShortcutsOverlay } from "@/components/keyboard-shortcuts-overlay";
import { PerformanceMonitor } from "@/components/performance-monitor";
import { siteConfig } from "@/config/site";

import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: siteConfig.name,
    template: `%s | ${siteConfig.name}`,
  },
  description: siteConfig.description,
  keywords: [
    "AI",
    "Customer Support",
    "Multi-Agent",
    "Chatbot",
    "Next.js",
    "React",
    "Tailwind CSS",
  ],
  authors: [
    {
      name: "Othman Mohammad",
      url: siteConfig.links.github,
    },
  ],
  creator: "Othman Mohammad",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: siteConfig.url,
    title: siteConfig.name,
    description: siteConfig.description,
    siteName: siteConfig.name,
  },
  twitter: {
    card: "summary_large_image",
    title: siteConfig.name,
    description: siteConfig.description,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>): JSX.Element {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="font-sans antialiased">
        <SessionProvider>
          <QueryProvider>
            <ThemeProvider>
              {children}
              <ToastProvider />
              <CommandPalette />
              <KeyboardShortcutsOverlay />
              <PerformanceMonitor showDebugPanel={false} />
            </ThemeProvider>
          </QueryProvider>
        </SessionProvider>
      </body>
    </html>
  );
}
