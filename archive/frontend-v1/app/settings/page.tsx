"use client";

import type { JSX } from "react";
import { useState } from "react";
import {
  Bell,
  Database,
  Download,
  Keyboard,
  Palette,
  Shield,
  Upload,
  User,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ProfileSettings } from "@/components/settings/profile-settings";
import { AppearanceSettings } from "@/components/settings/appearance-settings";
import { NotificationSettings } from "@/components/settings/notification-settings";
import { PrivacySettings } from "@/components/settings/privacy-settings";
import { KeyboardShortcutsSettings } from "@/components/settings/keyboard-shortcuts-settings";
import { DataSettings } from "@/components/settings/data-settings";
import { AuthGuard } from "@/components/auth/auth-guard";
import { cn } from "@/lib/utils";

type SettingsTab =
  | "profile"
  | "appearance"
  | "notifications"
  | "privacy"
  | "keyboard"
  | "data";

interface SettingsTabConfig {
  id: SettingsTab;
  label: string;
  icon: typeof User;
  description: string;
}

const SETTINGS_TABS: SettingsTabConfig[] = [
  {
    id: "profile",
    label: "Profile",
    icon: User,
    description: "Manage your personal information and account details",
  },
  {
    id: "appearance",
    label: "Appearance",
    icon: Palette,
    description: "Customize the look and feel of the application",
  },
  {
    id: "notifications",
    label: "Notifications",
    icon: Bell,
    description: "Configure notification preferences and alerts",
  },
  {
    id: "privacy",
    label: "Privacy & Security",
    icon: Shield,
    description: "Manage privacy settings and security options",
  },
  {
    id: "keyboard",
    label: "Keyboard Shortcuts",
    icon: Keyboard,
    description: "View and customize keyboard shortcuts",
  },
  {
    id: "data",
    label: "Data Management",
    icon: Database,
    description: "Export, import, and manage your data",
  },
];

/**
 * Settings Page Component
 *
 * Protected route requiring authentication.
 * Comprehensive settings interface with multiple categories.
 */
export default function SettingsPage(): JSX.Element {
  return (
    <AuthGuard>
      <SettingsContent />
    </AuthGuard>
  );
}

/**
 * Settings Content Component
 *
 * Contains the actual settings UI, rendered only when authenticated.
 *
 * Features:
 * - Profile management
 * - Appearance customization
 * - Notification preferences
 * - Privacy & security settings
 * - Keyboard shortcuts
 * - Data export/import
 */
function SettingsContent(): JSX.Element {
  const [activeTab, setActiveTab] = useState<SettingsTab>("profile");

  const renderContent = (): JSX.Element => {
    switch (activeTab) {
      case "profile":
        return <ProfileSettings />;
      case "appearance":
        return <AppearanceSettings />;
      case "notifications":
        return <NotificationSettings />;
      case "privacy":
        return <PrivacySettings />;
      case "keyboard":
        return <KeyboardShortcutsSettings />;
      case "data":
        return <DataSettings />;
      default:
        return <ProfileSettings />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      {/* Settings Sidebar */}
      <aside className="w-80 border-r border-border bg-surface">
        <div className="flex h-full flex-col">
          {/* Header */}
          <div className="border-b border-border p-6">
            <h1 className="text-2xl font-bold">Settings</h1>
            <p className="mt-1 text-sm text-foreground-secondary">
              Manage your account and preferences
            </p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto p-4">
            <div className="space-y-1">
              {SETTINGS_TABS.map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;

                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={cn(
                      "flex w-full items-start gap-3 rounded-lg p-3 text-left transition-colors",
                      isActive
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-surface-hover"
                    )}
                  >
                    <Icon
                      className={cn(
                        "mt-0.5 h-5 w-5 shrink-0",
                        isActive && "text-accent-foreground"
                      )}
                    />
                    <div className="flex-1 min-w-0">
                      <div
                        className={cn(
                          "font-medium",
                          isActive && "text-accent-foreground"
                        )}
                      >
                        {tab.label}
                      </div>
                      <div className="mt-0.5 text-xs text-foreground-secondary line-clamp-2">
                        {tab.description}
                      </div>
                    </div>
                  </button>
                );
              })}
            </div>
          </nav>

          {/* Footer */}
          <div className="border-t border-border p-4">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" className="flex-1">
                <Upload className="mr-2 h-4 w-4" />
                Import
              </Button>
              <Button variant="outline" size="sm" className="flex-1">
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
            </div>
          </div>
        </div>
      </aside>

      {/* Settings Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-4xl p-8">{renderContent()}</div>
      </main>
    </div>
  );
}
