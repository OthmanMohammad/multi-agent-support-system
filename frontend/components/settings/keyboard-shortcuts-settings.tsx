"use client";

import type { JSX } from "react";
import { Keyboard } from "lucide-react";
import {
  CHAT_SHORTCUTS,
  formatShortcut,
} from "@/lib/hooks/useKeyboardShortcuts";

/**
 * Keyboard Shortcuts Settings Component
 * View and customize keyboard shortcuts
 */
export function KeyboardShortcutsSettings(): JSX.Element {
  return (
    <div className="space-y-8">
      <div>
        <h2 className="text-2xl font-bold">Keyboard Shortcuts</h2>
        <p className="mt-1 text-sm text-foreground-secondary">
          Learn and customize keyboard shortcuts
        </p>
      </div>

      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Keyboard className="h-5 w-5" />
          <h3 className="font-semibold">Available Shortcuts</h3>
        </div>
        <div className="space-y-2">
          {Object.entries(CHAT_SHORTCUTS).map(([key, shortcut]) => (
            <div
              key={key}
              className="flex items-center justify-between rounded-lg border border-border p-3"
            >
              <span className="text-sm">
                {shortcut.description ?? key.replace(/_/g, " ").toLowerCase()}
              </span>
              <kbd className="rounded border border-border bg-background px-2 py-1 font-mono text-sm">
                {formatShortcut(shortcut)}
              </kbd>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
