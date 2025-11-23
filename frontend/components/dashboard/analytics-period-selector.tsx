"use client";

import type { JSX } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

/**
 * Analytics Period Selector
 * Toggle between different time periods for analytics
 */

interface AnalyticsPeriodSelectorProps {
  value: "24h" | "7d" | "30d" | "90d";
  onChange: (value: "24h" | "7d" | "30d" | "90d") => void;
}

const periods: Array<{ value: "24h" | "7d" | "30d" | "90d"; label: string }> = [
  { value: "24h", label: "24 Hours" },
  { value: "7d", label: "7 Days" },
  { value: "30d", label: "30 Days" },
  { value: "90d", label: "90 Days" },
];

export function AnalyticsPeriodSelector({
  value,
  onChange,
}: AnalyticsPeriodSelectorProps): JSX.Element {
  return (
    <div className="inline-flex rounded-lg border border-border bg-surface p-1">
      {periods.map((period) => (
        <Button
          key={period.value}
          variant="ghost"
          size="sm"
          onClick={() => onChange(period.value)}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-medium transition-all",
            value === period.value
              ? "bg-accent text-accent-foreground shadow-sm"
              : "text-foreground-secondary hover:text-foreground"
          )}
        >
          {period.label}
        </Button>
      ))}
    </div>
  );
}
