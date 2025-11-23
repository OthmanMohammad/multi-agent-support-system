"use client";

import type { JSX } from "react";
import { useState, useEffect } from "react";
import { Keyboard, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

/**
 * Keyboard Shortcuts Overlay
 * Visual guide to all keyboard shortcuts in the application
 * Press '?' to toggle
 */

interface Shortcut {
  keys: string[];
  description: string;
  category: string;
}

const shortcuts: Shortcut[] = [
  // Navigation
  {
    keys: ["⌘", "K"],
    description: "Open command palette",
    category: "Navigation",
  },
  {
    keys: ["G", "H"],
    description: "Go to home",
    category: "Navigation",
  },
  {
    keys: ["G", "C"],
    description: "Go to chat",
    category: "Navigation",
  },
  {
    keys: ["G", "D"],
    description: "Go to dashboard",
    category: "Navigation",
  },
  {
    keys: ["G", "A"],
    description: "Go to admin",
    category: "Navigation",
  },
  {
    keys: ["G", "S"],
    description: "Go to settings",
    category: "Navigation",
  },

  // Chat Actions
  {
    keys: ["⌘", "Enter"],
    description: "Send message",
    category: "Chat",
  },
  {
    keys: ["⌘", "N"],
    description: "New conversation",
    category: "Chat",
  },
  {
    keys: ["⌘", "/"],
    description: "Focus message input",
    category: "Chat",
  },
  {
    keys: ["↑"],
    description: "Edit last message",
    category: "Chat",
  },
  {
    keys: ["Esc"],
    description: "Cancel editing",
    category: "Chat",
  },

  // Search & Filter
  {
    keys: ["⌘", "F"],
    description: "Search conversations",
    category: "Search",
  },
  {
    keys: ["⌘", "Shift", "F"],
    description: "Advanced search",
    category: "Search",
  },

  // Voice
  {
    keys: ["⌘", "Shift", "V"],
    description: "Toggle voice input",
    category: "Voice",
  },
  {
    keys: ["⌘", "Shift", "S"],
    description: "Read message aloud",
    category: "Voice",
  },

  // Export
  {
    keys: ["⌘", "E"],
    description: "Export conversation",
    category: "Export",
  },
  {
    keys: ["⌘", "Shift", "E"],
    description: "Export to PDF",
    category: "Export",
  },

  // Theme
  {
    keys: ["⌘", "Shift", "L"],
    description: "Toggle light mode",
    category: "Appearance",
  },
  {
    keys: ["⌘", "Shift", "D"],
    description: "Toggle dark mode",
    category: "Appearance",
  },

  // Performance
  {
    keys: ["Shift", "Alt", "P"],
    description: "Toggle performance monitor",
    category: "Debug",
  },

  // Help
  {
    keys: ["?"],
    description: "Show keyboard shortcuts",
    category: "Help",
  },
];

export function KeyboardShortcutsOverlay(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Open with '?'
      if (e.key === "?" && !e.metaKey && !e.ctrlKey && !e.shiftKey) {
        const target = e.target as HTMLElement;
        // Don't trigger in input fields
        if (
          target.tagName !== "INPUT" &&
          target.tagName !== "TEXTAREA" &&
          !target.isContentEditable
        ) {
          e.preventDefault();
          setIsOpen(true);
        }
      }

      // Close with Escape
      if (e.key === "Escape" && isOpen) {
        setIsOpen(false);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen]);

  if (!isOpen) return <></>;

  const categories = Array.from(
    new Set(shortcuts.map((s) => s.category))
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative max-h-[90vh] w-full max-w-4xl overflow-hidden rounded-xl border border-border bg-surface shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border bg-surface p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-accent text-accent-foreground">
              <Keyboard className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold">Keyboard Shortcuts</h2>
              <p className="text-sm text-foreground-secondary">
                Navigate faster with these shortcuts
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsOpen(false)}
            className="h-8 w-8 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        <div className="max-h-[calc(90vh-120px)] overflow-y-auto p-6">
          <div className="grid gap-8 md:grid-cols-2">
            {categories.map((category) => (
              <div key={category}>
                <h3 className="mb-4 text-sm font-semibold text-foreground-secondary">
                  {category}
                </h3>
                <div className="space-y-3">
                  {shortcuts
                    .filter((s) => s.category === category)
                    .map((shortcut, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between rounded-lg border border-border bg-background p-3"
                      >
                        <span className="text-sm">{shortcut.description}</span>
                        <div className="flex items-center gap-1">
                          {shortcut.keys.map((key, i) => (
                            <kbd
                              key={i}
                              className="inline-flex h-7 min-w-7 items-center justify-center rounded border border-border bg-surface px-2 font-mono text-xs font-semibold shadow-sm"
                            >
                              {key}
                            </kbd>
                          ))}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-border bg-surface px-6 py-4">
          <p className="text-xs text-foreground-secondary">
            Press <kbd className="rounded border border-border bg-background px-1.5 py-0.5 font-mono text-xs">ESC</kbd> or{" "}
            <kbd className="rounded border border-border bg-background px-1.5 py-0.5 font-mono text-xs">?</kbd> to close
          </p>
          <Button variant="outline" size="sm" onClick={() => setIsOpen(false)}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
