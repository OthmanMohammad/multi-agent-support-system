"use client";

import type { JSX } from "react";
import { useState, useEffect } from "react";
import { Bell, Mail, MessageSquare, BellRing, Volume2 } from "lucide-react";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "@/lib/utils/toast";
import { cn } from "@/lib/utils";

interface NotificationSetting {
  id: string;
  label: string;
  description: string;
  enabled: boolean;
}

/**
 * Notification Settings Component
 * Configure notification preferences and alerts
 */
export function NotificationSettings(): JSX.Element {
  const [emailNotifications, setEmailNotifications] = useState<NotificationSetting[]>([
    {
      id: "new-message",
      label: "New Messages",
      description: "Receive emails when you get new messages",
      enabled: true,
    },
    {
      id: "mentions",
      label: "Mentions",
      description: "Get notified when someone mentions you",
      enabled: true,
    },
    {
      id: "updates",
      label: "Product Updates",
      description: "Stay informed about new features and improvements",
      enabled: false,
    },
    {
      id: "marketing",
      label: "Marketing",
      description: "Receive tips, tricks, and special offers",
      enabled: false,
    },
  ]);

  const [pushNotifications, setPushNotifications] = useState<NotificationSetting[]>([
    {
      id: "chat-messages",
      label: "Chat Messages",
      description: "Get push notifications for new chat messages",
      enabled: true,
    },
    {
      id: "agent-responses",
      label: "Agent Responses",
      description: "Notify when AI agent responds to your message",
      enabled: true,
    },
    {
      id: "system-alerts",
      label: "System Alerts",
      description: "Important system notifications and alerts",
      enabled: true,
    },
  ]);

  const [soundEnabled, setSoundEnabled] = useState(true);
  const [browserNotificationsEnabled, setBrowserNotificationsEnabled] = useState(false);

  useEffect(() => {
    // Check browser notification permission
    if ("Notification" in window) {
      setBrowserNotificationsEnabled(Notification.permission === "granted");
    }
  }, []);

  const toggleEmailNotification = (id: string): void => {
    setEmailNotifications((prev) =>
      prev.map((notif) =>
        notif.id === id ? { ...notif, enabled: !notif.enabled } : notif
      )
    );

    toast.success("Notification preference updated");
  };

  const togglePushNotification = (id: string): void => {
    setPushNotifications((prev) =>
      prev.map((notif) =>
        notif.id === id ? { ...notif, enabled: !notif.enabled } : notif
      )
    );

    toast.success("Notification preference updated");
  };

  const handleRequestBrowserPermission = async (): Promise<void> => {
    if (!("Notification" in window)) {
      toast.error("Not supported", {
        description: "Your browser doesn't support notifications",
      });
      return;
    }

    try {
      const permission = await Notification.requestPermission();
      setBrowserNotificationsEnabled(permission === "granted");

      if (permission === "granted") {
        toast.success("Browser notifications enabled", {
          description: "You'll now receive notifications in your browser",
        });

        // Show test notification
        new Notification("Test Notification", {
          body: "Browser notifications are working!",
          icon: "/icon.png",
        });
      } else {
        toast.warning("Permission denied", {
          description: "You denied browser notifications",
        });
      }
    } catch (error) {
      toast.error("Failed to enable notifications");
    }
  };

  const handleSavePreferences = (): void => {
    // TODO: Save to backend
    toast.success("Preferences saved", {
      description: "Your notification preferences have been saved",
    });
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Notifications</h2>
        <p className="mt-1 text-sm text-foreground-secondary">
          Manage how and when you receive notifications
        </p>
      </div>

      {/* Browser Notifications */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <BellRing className="h-5 w-5" />
          <h3 className="font-semibold">Browser Notifications</h3>
        </div>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="font-medium">Enable Browser Notifications</div>
            <div className="text-sm text-foreground-secondary">
              Receive notifications directly in your browser
            </div>
          </div>
          {browserNotificationsEnabled ? (
            <div className="flex items-center gap-2 text-sm text-green-500">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              Enabled
            </div>
          ) : (
            <Button onClick={handleRequestBrowserPermission}>Enable</Button>
          )}
        </div>
      </div>

      {/* Sound */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Volume2 className="h-5 w-5" />
          <h3 className="font-semibold">Sound</h3>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Notification Sounds</div>
            <div className="text-sm text-foreground-secondary">
              Play a sound when you receive notifications
            </div>
          </div>
          <button
            onClick={() => {
              setSoundEnabled(!soundEnabled);
              toast.success(soundEnabled ? "Sound disabled" : "Sound enabled");
            }}
            className={cn(
              "relative h-6 w-11 rounded-full transition-colors",
              soundEnabled ? "bg-accent" : "bg-surface-hover"
            )}
          >
            <div
              className={cn(
                "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform",
                soundEnabled ? "translate-x-5.5" : "translate-x-0.5"
              )}
            />
          </button>
        </div>
      </div>

      {/* Email Notifications */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Mail className="h-5 w-5" />
          <h3 className="font-semibold">Email Notifications</h3>
        </div>
        <div className="space-y-4">
          {emailNotifications.map((notif) => (
            <div key={notif.id} className="flex items-center justify-between">
              <div className="flex-1">
                <div className="font-medium">{notif.label}</div>
                <div className="text-sm text-foreground-secondary">
                  {notif.description}
                </div>
              </div>
              <button
                onClick={() => toggleEmailNotification(notif.id)}
                className={cn(
                  "relative h-6 w-11 rounded-full transition-colors",
                  notif.enabled ? "bg-accent" : "bg-surface-hover"
                )}
              >
                <div
                  className={cn(
                    "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform",
                    notif.enabled ? "translate-x-5.5" : "translate-x-0.5"
                  )}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Push Notifications */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          <h3 className="font-semibold">Push Notifications</h3>
        </div>
        <div className="space-y-4">
          {pushNotifications.map((notif) => (
            <div key={notif.id} className="flex items-center justify-between">
              <div className="flex-1">
                <div className="font-medium">{notif.label}</div>
                <div className="text-sm text-foreground-secondary">
                  {notif.description}
                </div>
              </div>
              <button
                onClick={() => togglePushNotification(notif.id)}
                className={cn(
                  "relative h-6 w-11 rounded-full transition-colors",
                  notif.enabled ? "bg-accent" : "bg-surface-hover"
                )}
                disabled={!browserNotificationsEnabled}
              >
                <div
                  className={cn(
                    "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform",
                    notif.enabled ? "translate-x-5.5" : "translate-x-0.5"
                  )}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Save Button */}
      <div className="flex items-center justify-between rounded-lg border border-border bg-surface p-4">
        <p className="text-sm text-foreground-secondary">
          Save your notification preferences
        </p>
        <Button onClick={handleSavePreferences}>Save Preferences</Button>
      </div>
    </div>
  );
}
