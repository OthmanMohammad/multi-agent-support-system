/**
 * Keyboard Shortcuts Hook
 *
 * Provides keyboard shortcut handling for the application.
 */

"use client";

import { useCallback, useEffect } from "react";

// =============================================================================
// TYPES
// =============================================================================

export interface Shortcut {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  shiftKey?: boolean; // Alias for shift
  ctrlKey?: boolean; // Alias for ctrl
  metaKey?: boolean; // Alias for meta
  altKey?: boolean; // Alias for alt
  handler: () => void;
  description?: string;
  preventDefault?: boolean;
}

export interface ShortcutDefinition {
  key: string;
  ctrl?: boolean;
  meta?: boolean;
  shift?: boolean;
  alt?: boolean;
  description?: string;
}

export interface UseKeyboardShortcutsOptions {
  shortcuts: Shortcut[];
  enabled?: boolean;
}

// =============================================================================
// CHAT SHORTCUTS DEFINITIONS
// =============================================================================

export const CHAT_SHORTCUTS = {
  NEW_CONVERSATION: {
    key: "n",
    ctrl: true,
    description: "New Conversation",
  } as ShortcutDefinition,
  SEARCH: {
    key: "k",
    ctrl: true,
    description: "Search",
  } as ShortcutDefinition,
  TOGGLE_SIDEBAR: {
    key: "b",
    ctrl: true,
    description: "Toggle Sidebar",
  } as ShortcutDefinition,
  FOCUS_INPUT: {
    key: "/",
    description: "Focus Input",
  } as ShortcutDefinition,
  EXPORT: {
    key: "e",
    ctrl: true,
    description: "Export Conversation",
  } as ShortcutDefinition,
  DELETE_CONVERSATION: {
    key: "Delete",
    ctrl: true,
    description: "Delete Conversation",
  } as ShortcutDefinition,
  SETTINGS: {
    key: ",",
    ctrl: true,
    description: "Open Settings",
  } as ShortcutDefinition,
  SEND_MESSAGE: {
    key: "Enter",
    description: "Send Message",
  } as ShortcutDefinition,
  NEW_LINE: {
    key: "Enter",
    shift: true,
    description: "New Line",
  } as ShortcutDefinition,
} as const;

// =============================================================================
// FORMAT SHORTCUT HELPER
// =============================================================================

/**
 * Format a shortcut definition to a human-readable string
 */
export function formatShortcut(shortcut: ShortcutDefinition): string {
  const parts: string[] = [];
  const isMac =
    typeof navigator !== "undefined" && navigator.platform.includes("Mac");

  if (shortcut.ctrl) {
    parts.push(isMac ? "⌘" : "Ctrl");
  }
  if (shortcut.meta) {
    parts.push(isMac ? "⌘" : "Win");
  }
  if (shortcut.alt) {
    parts.push(isMac ? "⌥" : "Alt");
  }
  if (shortcut.shift) {
    parts.push(isMac ? "⇧" : "Shift");
  }

  // Format special keys
  let keyDisplay = shortcut.key;
  switch (shortcut.key.toLowerCase()) {
    case "enter":
      keyDisplay = isMac ? "↩" : "Enter";
      break;
    case "escape":
      keyDisplay = "Esc";
      break;
    case "delete":
      keyDisplay = isMac ? "⌫" : "Del";
      break;
    case "arrowup":
      keyDisplay = "↑";
      break;
    case "arrowdown":
      keyDisplay = "↓";
      break;
    case "arrowleft":
      keyDisplay = "←";
      break;
    case "arrowright":
      keyDisplay = "→";
      break;
    case " ":
      keyDisplay = "Space";
      break;
    default:
      keyDisplay = shortcut.key.toUpperCase();
  }

  parts.push(keyDisplay);

  return parts.join(isMac ? "" : "+");
}

// =============================================================================
// USE KEYBOARD SHORTCUTS HOOK
// =============================================================================

/**
 * Hook to handle keyboard shortcuts
 */
export function useKeyboardShortcuts(
  options: UseKeyboardShortcutsOptions
): void {
  const { shortcuts, enabled = true } = options;

  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      if (!enabled) {
        return;
      }

      // Don't trigger shortcuts when typing in inputs (unless it's Escape)
      const target = event.target as HTMLElement;
      const isInput = ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName);
      const isContentEditable = target.isContentEditable;

      for (const shortcut of shortcuts) {
        const ctrl = shortcut.ctrl ?? shortcut.ctrlKey ?? false;
        const meta = shortcut.meta ?? shortcut.metaKey ?? false;
        const shift = shortcut.shift ?? shortcut.shiftKey ?? false;
        const alt = shortcut.alt ?? shortcut.altKey ?? false;

        // For special keys like Escape, allow them even in inputs
        const isSpecialKey = ["Escape", "F1", "F2", "F3"].includes(
          shortcut.key
        );

        // Skip if in input and not a special key
        if ((isInput || isContentEditable) && !isSpecialKey && !ctrl && !meta) {
          continue;
        }

        // Check if modifiers match
        const modifiersMatch =
          event.ctrlKey === ctrl &&
          event.metaKey === meta &&
          event.shiftKey === shift &&
          event.altKey === alt;

        // Check if key matches (case-insensitive)
        const keyMatches =
          event.key.toLowerCase() === shortcut.key.toLowerCase();

        if (modifiersMatch && keyMatches) {
          if (shortcut.preventDefault !== false) {
            event.preventDefault();
          }
          shortcut.handler();
          return;
        }
      }
    },
    [shortcuts, enabled]
  );

  useEffect(() => {
    if (!enabled) {
      return;
    }

    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown, enabled]);
}
