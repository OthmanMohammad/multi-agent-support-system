"use client";

import type { JSX } from "react";
import { useState } from "react";
import { Keyboard, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  useKeyboardShortcuts,
  CHAT_SHORTCUTS,
  formatShortcut,
} from "@/lib/hooks/useKeyboardShortcuts";
import { cn } from "@/lib/utils";

interface ShortcutGroup {
  title: string;
  shortcuts: Array<{
    name: string;
    shortcut: typeof CHAT_SHORTCUTS[keyof typeof CHAT_SHORTCUTS];
  }>;
}

const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    title: "General",
    shortcuts: [
      { name: "New conversation", shortcut: CHAT_SHORTCUTS.NEW_CONVERSATION },
      { name: "Search conversations", shortcut: CHAT_SHORTCUTS.SEARCH },
      { name: "Toggle sidebar", shortcut: CHAT_SHORTCUTS.TOGGLE_SIDEBAR },
      { name: "Focus message input", shortcut: CHAT_SHORTCUTS.FOCUS_INPUT },
    ],
  },
  {
    title: "Actions",
    shortcuts: [
      { name: "Export conversation", shortcut: CHAT_SHORTCUTS.EXPORT },
      {
        name: "Delete conversation",
        shortcut: CHAT_SHORTCUTS.DELETE_CONVERSATION,
      },
      { name: "Open settings", shortcut: CHAT_SHORTCUTS.SETTINGS },
    ],
  },
];

/**
 * Keyboard Shortcuts Help Component
 * Modal showing all available keyboard shortcuts
 */
export function KeyboardShortcutsHelp(): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);

  // Register shortcut to open help (? key)
  useKeyboardShortcuts({
    shortcuts: [
      {
        key: "?",
        shiftKey: true,
        handler: () => setIsOpen(true),
        description: "Show keyboard shortcuts",
      },
      {
        key: "Escape",
        handler: () => setIsOpen(false),
        description: "Close modal",
        preventDefault: false,
      },
    ],
    enabled: true,
  });

  if (!isOpen) {
    return (
      <Button
        size="icon"
        variant="ghost"
        onClick={() => setIsOpen(true)}
        title="Keyboard shortcuts (?)"
        className="fixed bottom-4 right-4 z-50 h-10 w-10 rounded-full shadow-lg"
      >
        <Keyboard className="h-5 w-5" />
      </Button>
    );
  }

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm"
        onClick={() => setIsOpen(false)}
      />

      {/* Modal */}
      <div className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl -translate-x-1/2 -translate-y-1/2 rounded-lg border border-border bg-background p-6 shadow-lg">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold">Keyboard Shortcuts</h2>
            <p className="mt-1 text-sm text-foreground-secondary">
              Speed up your workflow with these shortcuts
            </p>
          </div>
          <Button
            size="icon"
            variant="ghost"
            onClick={() => setIsOpen(false)}
            title="Close (Esc)"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Shortcuts List */}
        <div className="space-y-6">
          {SHORTCUT_GROUPS.map((group) => (
            <div key={group.title}>
              <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-foreground-secondary">
                {group.title}
              </h3>
              <div className="space-y-2">
                {group.shortcuts.map((item) => (
                  <div
                    key={item.name}
                    className="flex items-center justify-between rounded-lg border border-border bg-surface px-4 py-3"
                  >
                    <span className="text-sm font-medium">{item.name}</span>
                    <kbd className="rounded border border-border bg-background px-2 py-1 text-xs font-mono font-semibold">
                      {formatShortcut(item.shortcut)}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="mt-6 rounded-lg bg-surface p-4 text-center text-sm text-foreground-secondary">
          Press <kbd className="rounded border border-border bg-background px-2 py-1 font-mono">?</kbd> to toggle this help
        </div>
      </div>
    </>
  );
}
