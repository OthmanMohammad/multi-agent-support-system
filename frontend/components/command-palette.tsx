"use client";

import type { JSX } from "react";
import { useEffect, useState, useCallback } from "react";
import { Command } from "cmdk";
import { useRouter } from "next/navigation";
import {
  Search,
  Home,
  MessageSquare,
  BarChart3,
  Users,
  Settings,
  Shield,
  Moon,
  Sun,
  Keyboard,
  FileText,
  Download,
  Upload,
  Trash2,
  Plus,
  Edit,
  Copy,
  Eye,
} from "lucide-react";
import { useTheme } from "next-themes";
import { cn } from "@/lib/utils";

/**
 * Command Palette Component
 * Global keyboard-first navigation and actions (Cmd+K)
 * Inspired by VSCode, Raycast, and Linear
 */

interface CommandItem {
  id: string;
  label: string;
  description?: string;
  icon: React.ComponentType<{ className?: string }>;
  action: () => void;
  keywords?: string[];
  category: "navigation" | "actions" | "settings" | "themes";
}

export function CommandPalette(): JSX.Element {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const router = useRouter();
  const { setTheme } = useTheme();

  // Toggle with Cmd+K or Ctrl+K
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === "k" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener("keydown", down);
    return () => document.removeEventListener("keydown", down);
  }, []);

  // Close on escape
  useEffect(() => {
    if (!open) setSearch("");
  }, [open]);

  const commands: CommandItem[] = [
    // Navigation
    {
      id: "nav-home",
      label: "Go to Home",
      description: "Navigate to home page",
      icon: Home,
      action: () => router.push("/"),
      keywords: ["home", "main", "index"],
      category: "navigation",
    },
    {
      id: "nav-chat",
      label: "Go to Chat",
      description: "Open chat interface",
      icon: MessageSquare,
      action: () => router.push("/chat"),
      keywords: ["chat", "conversations", "messages"],
      category: "navigation",
    },
    {
      id: "nav-dashboard",
      label: "Go to Dashboard",
      description: "View analytics and metrics",
      icon: BarChart3,
      action: () => router.push("/dashboard"),
      keywords: ["dashboard", "analytics", "metrics", "stats"],
      category: "navigation",
    },
    {
      id: "nav-customers",
      label: "Go to Customers",
      description: "Manage customers",
      icon: Users,
      action: () => router.push("/customers"),
      keywords: ["customers", "users", "clients"],
      category: "navigation",
    },
    {
      id: "nav-admin",
      label: "Go to Admin Panel",
      description: "System administration",
      icon: Shield,
      action: () => router.push("/admin"),
      keywords: ["admin", "settings", "system", "health"],
      category: "navigation",
    },
    {
      id: "nav-settings",
      label: "Go to Settings",
      description: "Configure preferences",
      icon: Settings,
      action: () => router.push("/settings"),
      keywords: ["settings", "preferences", "config"],
      category: "navigation",
    },

    // Actions
    {
      id: "action-new-chat",
      label: "New Conversation",
      description: "Start a new chat",
      icon: Plus,
      action: () => {
        router.push("/chat");
        // TODO: Trigger new conversation
      },
      keywords: ["new", "create", "conversation", "chat"],
      category: "actions",
    },
    {
      id: "action-export",
      label: "Export Data",
      description: "Export to PDF, CSV, or Excel",
      icon: Download,
      action: () => {
        // TODO: Open export dialog
      },
      keywords: ["export", "download", "save", "pdf", "csv"],
      category: "actions",
    },
    {
      id: "action-shortcuts",
      label: "Show Keyboard Shortcuts",
      description: "View all shortcuts",
      icon: Keyboard,
      action: () => {
        // TODO: Open shortcuts modal
      },
      keywords: ["keyboard", "shortcuts", "hotkeys", "help"],
      category: "actions",
    },

    // Themes
    {
      id: "theme-light",
      label: "Switch to Light Mode",
      description: "Use light color scheme",
      icon: Sun,
      action: () => setTheme("light"),
      keywords: ["light", "theme", "bright"],
      category: "themes",
    },
    {
      id: "theme-dark",
      label: "Switch to Dark Mode",
      description: "Use dark color scheme",
      icon: Moon,
      action: () => setTheme("dark"),
      keywords: ["dark", "theme", "night"],
      category: "themes",
    },
  ];

  const handleSelect = useCallback((item: CommandItem) => {
    setOpen(false);
    item.action();
  }, []);

  const categories = {
    navigation: "Navigation",
    actions: "Actions",
    themes: "Appearance",
    settings: "Settings",
  };

  return (
    <Command.Dialog
      open={open}
      onOpenChange={setOpen}
      label="Command Menu"
      className="fixed left-1/2 top-1/2 z-50 w-full max-w-2xl -translate-x-1/2 -translate-y-1/2 overflow-hidden rounded-xl border border-border bg-surface shadow-2xl"
    >
      <div className="flex items-center border-b border-border px-4">
        <Search className="mr-2 h-5 w-5 text-foreground-secondary" />
        <Command.Input
          value={search}
          onValueChange={setSearch}
          placeholder="Type a command or search..."
          className="flex h-14 w-full bg-transparent py-3 text-base outline-none placeholder:text-foreground-secondary"
        />
        <kbd className="pointer-events-none ml-auto inline-flex h-6 select-none items-center gap-1 rounded border border-border bg-background px-2 font-mono text-xs font-medium text-foreground-secondary">
          ESC
        </kbd>
      </div>

      <Command.List className="max-h-96 overflow-y-auto p-2">
        <Command.Empty className="py-12 text-center text-sm text-foreground-secondary">
          No results found.
        </Command.Empty>

        {Object.entries(categories).map(([key, label]) => {
          const categoryCommands = commands.filter((cmd) => cmd.category === key);
          if (categoryCommands.length === 0) return null;

          return (
            <Command.Group
              key={key}
              heading={label}
              className="mb-2 [&_[cmdk-group-heading]]:px-2 [&_[cmdk-group-heading]]:py-2 [&_[cmdk-group-heading]]:text-xs [&_[cmdk-group-heading]]:font-semibold [&_[cmdk-group-heading]]:text-foreground-secondary"
            >
              {categoryCommands.map((command) => {
                const Icon = command.icon;
                return (
                  <Command.Item
                    key={command.id}
                    value={`${command.label} ${command.description} ${command.keywords?.join(" ")}`}
                    onSelect={() => handleSelect(command)}
                    className="group relative flex cursor-pointer items-center gap-3 rounded-lg px-3 py-2.5 text-sm aria-selected:bg-accent aria-selected:text-accent-foreground"
                  >
                    <Icon className="h-4 w-4 text-foreground-secondary group-aria-selected:text-accent-foreground" />
                    <div className="flex flex-1 flex-col gap-0.5">
                      <span className="font-medium">{command.label}</span>
                      {command.description && (
                        <span className="text-xs text-foreground-secondary group-aria-selected:text-accent-foreground/70">
                          {command.description}
                        </span>
                      )}
                    </div>
                  </Command.Item>
                );
              })}
            </Command.Group>
          );
        })}
      </Command.List>

      <div className="flex items-center justify-between border-t border-border px-4 py-2.5 text-xs text-foreground-secondary">
        <div className="flex items-center gap-4">
          <span>Navigate with ↑↓</span>
          <span>Select with ↵</span>
        </div>
        <div className="flex items-center gap-1">
          <kbd className="rounded border border-border bg-background px-1.5 py-0.5 font-mono">
            ⌘K
          </kbd>
          <span>to toggle</span>
        </div>
      </div>
    </Command.Dialog>
  );
}
