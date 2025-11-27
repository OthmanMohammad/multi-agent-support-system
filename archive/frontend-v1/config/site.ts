/**
 * Site-wide configuration
 * Centralized place for app metadata, URLs, and constants
 */

export const siteConfig = {
  name: "Multi-Agent Support System",
  description:
    "AI-powered customer support with intelligent multi-agent routing and context-aware responses",
  url: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
  apiUrl: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  links: {
    github: "https://github.com/OthmanMohammad/multi-agent-support-system",
    docs: "/docs",
  },
} as const;

export const navConfig = {
  mainNav: [
    {
      title: "Dashboard",
      href: "/",
    },
    {
      title: "Chat",
      href: "/chat",
    },
    {
      title: "Analytics",
      href: "/analytics",
    },
    {
      title: "Settings",
      href: "/settings",
    },
  ],
} as const;
