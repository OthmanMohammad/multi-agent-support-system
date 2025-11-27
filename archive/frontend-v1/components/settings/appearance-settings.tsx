"use client";

import type { JSX } from "react";
import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Layout, Monitor, Moon, Palette, Sun, Type, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "@/lib/utils/toast";
import { cn } from "@/lib/utils";

type ThemeOption = "light" | "dark" | "system";
type FontSize = "sm" | "md" | "lg" | "xl";
type Density = "comfortable" | "compact" | "spacious";

const THEME_OPTIONS: Array<{
  value: ThemeOption;
  label: string;
  icon: typeof Sun;
}> = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Monitor },
];

const FONT_SIZES: Array<{ value: FontSize; label: string; size: string }> = [
  { value: "sm", label: "Small", size: "14px" },
  { value: "md", label: "Medium", size: "16px" },
  { value: "lg", label: "Large", size: "18px" },
  { value: "xl", label: "Extra Large", size: "20px" },
];

const DENSITY_OPTIONS: Array<{
  value: Density;
  label: string;
  description: string;
}> = [
  {
    value: "compact",
    label: "Compact",
    description: "More content, less spacing",
  },
  {
    value: "comfortable",
    label: "Comfortable",
    description: "Balanced spacing",
  },
  { value: "spacious", label: "Spacious", description: "More breathing room" },
];

const ACCENT_COLORS = [
  { name: "Blue", value: "#3b82f6" },
  { name: "Purple", value: "#8b5cf6" },
  { name: "Green", value: "#10b981" },
  { name: "Orange", value: "#f97316" },
  { name: "Pink", value: "#ec4899" },
  { name: "Teal", value: "#14b8a6" },
];

// Apply functions defined outside component to avoid hoisting issues
const applyFontSize = (size: FontSize): void => {
  const sizeMap = { sm: "14px", md: "16px", lg: "18px", xl: "20px" };
  document.documentElement.style.setProperty("--font-size-base", sizeMap[size]);
};

const applyDensity = (densityValue: Density): void => {
  const densityMap = { compact: "0.75", comfortable: "1", spacious: "1.25" };
  document.documentElement.style.setProperty(
    "--density-scale",
    densityMap[densityValue]
  );
};

const applyAccentColor = (color: string): void => {
  document.documentElement.style.setProperty("--color-accent", color);
};

const applyReducedMotion = (enabled: boolean): void => {
  if (enabled) {
    document.documentElement.style.setProperty("--transition-fast", "0ms");
    document.documentElement.style.setProperty("--transition-normal", "0ms");
    document.documentElement.style.setProperty("--transition-slow", "0ms");
  } else {
    document.documentElement.style.removeProperty("--transition-fast");
    document.documentElement.style.removeProperty("--transition-normal");
    document.documentElement.style.removeProperty("--transition-slow");
  }
};

/**
 * Appearance Settings Component
 * Customize the look and feel of the application
 */
export function AppearanceSettings(): JSX.Element {
  const { theme, setTheme } = useTheme();
  const [fontSize, setFontSize] = useState<FontSize>("md");
  const [density, setDensity] = useState<Density>("comfortable");
  const [accentColor, setAccentColor] = useState(
    ACCENT_COLORS[0]?.value ?? "#3b82f6"
  );
  const [reducedMotion, setReducedMotion] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Wait for client-side mounting to prevent hydration mismatch
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: required for hydration safety
    setMounted(true);

    // Load preferences from localStorage
    const savedFontSize = localStorage.getItem("fontSize") as FontSize;
    const savedDensity = localStorage.getItem("density") as Density;
    const savedAccentColor = localStorage.getItem("accentColor");
    const savedReducedMotion = localStorage.getItem("reducedMotion") === "true";

    if (savedFontSize) {
      setFontSize(savedFontSize);
    }
    if (savedDensity) {
      setDensity(savedDensity);
    }
    if (savedAccentColor) {
      setAccentColor(savedAccentColor);
    }
    setReducedMotion(savedReducedMotion);

    // Apply settings
    applyFontSize(savedFontSize || "md");
    applyDensity(savedDensity || "comfortable");
    applyAccentColor(savedAccentColor || ACCENT_COLORS[0]?.value || "#3b82f6");
    applyReducedMotion(savedReducedMotion);
  }, []);

  const handleThemeChange = (newTheme: ThemeOption): void => {
    setTheme(newTheme);
    toast.success("Theme updated", {
      description: `Switched to ${newTheme} theme`,
    });
  };

  const handleFontSizeChange = (size: FontSize): void => {
    setFontSize(size);
    localStorage.setItem("fontSize", size);
    applyFontSize(size);
    toast.success("Font size updated");
  };

  const handleDensityChange = (densityValue: Density): void => {
    setDensity(densityValue);
    localStorage.setItem("density", densityValue);
    applyDensity(densityValue);
    toast.success("Density updated");
  };

  const handleAccentColorChange = (color: string): void => {
    setAccentColor(color);
    localStorage.setItem("accentColor", color);
    applyAccentColor(color);
    toast.success("Accent color updated");
  };

  const handleReducedMotionToggle = (): void => {
    const newValue = !reducedMotion;
    setReducedMotion(newValue);
    localStorage.setItem("reducedMotion", String(newValue));
    applyReducedMotion(newValue);
    toast.success(
      newValue ? "Reduced motion enabled" : "Reduced motion disabled"
    );
  };

  const handleResetToDefaults = (): void => {
    setTheme("system");
    setFontSize("md");
    setDensity("comfortable");
    setAccentColor(ACCENT_COLORS[0]?.value ?? "#3b82f6");
    setReducedMotion(false);

    localStorage.removeItem("fontSize");
    localStorage.removeItem("density");
    localStorage.removeItem("accentColor");
    localStorage.removeItem("reducedMotion");

    applyFontSize("md");
    applyDensity("comfortable");
    applyAccentColor(ACCENT_COLORS[0]?.value ?? "#3b82f6");
    applyReducedMotion(false);

    toast.success("Reset to defaults", {
      description: "All appearance settings have been reset",
    });
  };

  if (!mounted) {
    return <div className="animate-pulse">Loading...</div>;
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Appearance</h2>
        <p className="mt-1 text-sm text-foreground-secondary">
          Customize how the application looks and feels
        </p>
      </div>

      {/* Theme Selection */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Palette className="h-5 w-5" />
          <h3 className="font-semibold">Theme</h3>
        </div>
        <div className="grid grid-cols-3 gap-3">
          {THEME_OPTIONS.map((option) => {
            const Icon = option.icon;
            const isActive = theme === option.value;

            return (
              <button
                key={option.value}
                onClick={() => handleThemeChange(option.value)}
                className={cn(
                  "flex flex-col items-center gap-3 rounded-lg border-2 p-4 transition-all hover:bg-surface-hover",
                  isActive ? "border-accent bg-accent/10" : "border-border"
                )}
              >
                <Icon className={cn("h-6 w-6", isActive && "text-accent")} />
                <span
                  className={cn(
                    "text-sm font-medium",
                    isActive && "text-accent"
                  )}
                >
                  {option.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Font Size */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Type className="h-5 w-5" />
          <h3 className="font-semibold">Font Size</h3>
        </div>
        <div className="grid grid-cols-4 gap-3">
          {FONT_SIZES.map((option) => {
            const isActive = fontSize === option.value;

            return (
              <button
                key={option.value}
                onClick={() => handleFontSizeChange(option.value)}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-lg border-2 p-4 transition-all hover:bg-surface-hover",
                  isActive ? "border-accent bg-accent/10" : "border-border"
                )}
              >
                <span
                  className={cn("font-medium", isActive && "text-accent")}
                  style={{ fontSize: option.size }}
                >
                  Aa
                </span>
                <span className={cn("text-xs", isActive && "text-accent")}>
                  {option.label}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Density */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Layout className="h-5 w-5" />
          <h3 className="font-semibold">Density</h3>
        </div>
        <div className="space-y-2">
          {DENSITY_OPTIONS.map((option) => {
            const isActive = density === option.value;

            return (
              <button
                key={option.value}
                onClick={() => handleDensityChange(option.value)}
                className={cn(
                  "flex w-full items-center justify-between rounded-lg border-2 p-4 text-left transition-all hover:bg-surface-hover",
                  isActive ? "border-accent bg-accent/10" : "border-border"
                )}
              >
                <div>
                  <div className={cn("font-medium", isActive && "text-accent")}>
                    {option.label}
                  </div>
                  <div className="text-sm text-foreground-secondary">
                    {option.description}
                  </div>
                </div>
                {isActive && <div className="h-4 w-4 rounded-full bg-accent" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Accent Color */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Palette className="h-5 w-5" />
          <h3 className="font-semibold">Accent Color</h3>
        </div>
        <div className="grid grid-cols-6 gap-3">
          {ACCENT_COLORS.map((color) => {
            const isActive = accentColor === color.value;

            return (
              <button
                key={color.value}
                onClick={() => handleAccentColorChange(color.value)}
                className={cn(
                  "flex flex-col items-center gap-2 rounded-lg border-2 p-3 transition-all hover:scale-105",
                  isActive ? "border-foreground" : "border-border"
                )}
              >
                <div
                  className="h-8 w-8 rounded-full"
                  style={{ backgroundColor: color.value }}
                />
                <span className="text-xs">{color.name}</span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Accessibility */}
      <div className="rounded-lg border border-border bg-surface p-6">
        <div className="mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5" />
          <h3 className="font-semibold">Accessibility</h3>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <div className="font-medium">Reduced Motion</div>
            <div className="text-sm text-foreground-secondary">
              Minimize animations and transitions
            </div>
          </div>
          <button
            onClick={handleReducedMotionToggle}
            className={cn(
              "relative h-6 w-11 rounded-full transition-colors",
              reducedMotion ? "bg-accent" : "bg-surface-hover"
            )}
          >
            <div
              className={cn(
                "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform",
                reducedMotion ? "translate-x-5.5" : "translate-x-0.5"
              )}
            />
          </button>
        </div>
      </div>

      {/* Reset */}
      <div className="flex items-center justify-between rounded-lg border border-border bg-surface p-4">
        <p className="text-sm text-foreground-secondary">
          Reset all appearance settings to defaults
        </p>
        <Button variant="outline" onClick={handleResetToDefaults}>
          Reset to Defaults
        </Button>
      </div>
    </div>
  );
}
