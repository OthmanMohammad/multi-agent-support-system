"use client";

import type { JSX } from "react";
import { Toaster } from "sonner";
import { useTheme } from "next-themes";

/**
 * Toast Provider Component
 * Provides global toast notifications using Sonner
 * Automatically adapts to theme (light/dark)
 */
export function ToastProvider(): JSX.Element {
  const { theme } = useTheme();

  return (
    <Toaster
      theme={(theme as "light" | "dark" | "system") || "system"}
      position="bottom-right"
      expand={false}
      richColors
      closeButton
      duration={4000}
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg",
          description: "group-[.toast]:text-foreground-secondary",
          actionButton:
            "group-[.toast]:bg-accent group-[.toast]:text-accent-foreground",
          cancelButton:
            "group-[.toast]:bg-surface group-[.toast]:text-foreground-secondary",
          error:
            "group-[.toaster]:bg-destructive group-[.toaster]:text-destructive-foreground group-[.toaster]:border-destructive",
          success:
            "group-[.toaster]:bg-green-500 group-[.toaster]:text-white group-[.toaster]:border-green-600",
          warning:
            "group-[.toaster]:bg-yellow-500 group-[.toaster]:text-white group-[.toaster]:border-yellow-600",
          info: "group-[.toaster]:bg-blue-500 group-[.toaster]:text-white group-[.toaster]:border-blue-600",
        },
      }}
    />
  );
}
