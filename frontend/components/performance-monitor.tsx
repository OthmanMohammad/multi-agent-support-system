"use client";

import type { JSX } from "react";
import { useEffect, useState } from "react";
import { Activity, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Performance Monitor Component
 * Real-time performance metrics using Performance API
 * Shows FPS, memory usage, render time, and core web vitals
 */

interface PerformanceMetrics {
  fps: number;
  memory: {
    used: number;
    total: number;
    percentage: number;
  } | null;
  renderTime: number;
  navigationTiming: {
    domContentLoaded: number;
    loadComplete: number;
  };
  vitals: {
    fcp: number | null; // First Contentful Paint
    lcp: number | null; // Largest Contentful Paint
    fid: number | null; // First Input Delay
    cls: number | null; // Cumulative Layout Shift
  };
}

interface PerformanceMonitorProps {
  className?: string;
  showDebugPanel?: boolean;
}

export function PerformanceMonitor({
  className,
  showDebugPanel = true,
}: PerformanceMonitorProps): JSX.Element | null {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 0,
    memory: null,
    renderTime: 0,
    navigationTiming: { domContentLoaded: 0, loadComplete: 0 },
    vitals: { fcp: null, lcp: null, fid: null, cls: null },
  });
  const [isVisible, setIsVisible] = useState(false);

  // Calculate FPS
  useEffect(() => {
    let frameCount = 0;
    let lastTime = performance.now();
    let animationFrameId: number;

    const measureFPS = () => {
      frameCount++;
      const currentTime = performance.now();
      const elapsed = currentTime - lastTime;

      if (elapsed >= 1000) {
        const fps = Math.round((frameCount * 1000) / elapsed);
        setMetrics((prev) => ({ ...prev, fps }));
        frameCount = 0;
        lastTime = currentTime;
      }

      animationFrameId = requestAnimationFrame(measureFPS);
    };

    measureFPS();

    return () => cancelAnimationFrame(animationFrameId);
  }, []);

  // Measure memory usage (Chrome only)
  useEffect(() => {
    const measureMemory = () => {
      if ("memory" in performance) {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const mem = (performance as any).memory;
        setMetrics((prev) => ({
          ...prev,
          memory: {
            used: Math.round(mem.usedJSHeapSize / 1048576), // Convert to MB
            total: Math.round(mem.totalJSHeapSize / 1048576),
            percentage: Math.round(
              (mem.usedJSHeapSize / mem.jsHeapSizeLimit) * 100
            ),
          },
        }));
      }
    };

    const interval = setInterval(measureMemory, 1000);
    measureMemory();

    return () => clearInterval(interval);
  }, []);

  // Measure navigation timing
  useEffect(() => {
    const timing = performance.timing;
    const domContentLoaded =
      timing.domContentLoadedEventEnd - timing.navigationStart;
    const loadComplete = timing.loadEventEnd - timing.navigationStart;

    setMetrics((prev) => ({
      ...prev,
      navigationTiming: {
        domContentLoaded: Math.round(domContentLoaded),
        loadComplete: Math.round(loadComplete),
      },
    }));

    // Measure Core Web Vitals
    if ("PerformanceObserver" in window) {
      // LCP
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const lastEntry = entries[entries.length - 1] as any;
        setMetrics((prev) => ({
          ...prev,
          vitals: { ...prev.vitals, lcp: Math.round(lastEntry.renderTime) },
        }));
      });
      lcpObserver.observe({ type: "largest-contentful-paint", buffered: true });

      // FID
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const firstEntry = entries[0] as any;
        setMetrics((prev) => ({
          ...prev,
          vitals: {
            ...prev.vitals,
            fid: Math.round(firstEntry.processingStart - firstEntry.startTime),
          },
        }));
      });
      fidObserver.observe({ type: "first-input", buffered: true });

      return () => {
        lcpObserver.disconnect();
        fidObserver.disconnect();
      };
    }
    return;
  }, []);

  // Keyboard shortcut to toggle (Shift+Alt+P)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.shiftKey && e.altKey && e.key === "P") {
        setIsVisible((prev) => !prev);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!showDebugPanel && !isVisible) {
    return null;
  }

  const getFPSColor = (fps: number) => {
    if (fps >= 55) {
      return "text-green-500";
    }
    if (fps >= 30) {
      return "text-yellow-500";
    }
    return "text-red-500";
  };

  const getMemoryColor = (percentage: number) => {
    if (percentage < 60) {
      return "text-green-500";
    }
    if (percentage < 80) {
      return "text-yellow-500";
    }
    return "text-red-500";
  };

  return (
    <div
      className={cn(
        "fixed bottom-4 right-4 z-50 w-80 rounded-lg border border-border bg-surface/95 p-4 shadow-2xl backdrop-blur-sm",
        className
      )}
    >
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-4 w-4 text-accent" />
          <h3 className="text-sm font-semibold">Performance</h3>
        </div>
        <button
          onClick={() => setIsVisible(false)}
          className="text-xs text-foreground-secondary hover:text-foreground"
        >
          Hide (Shift+Alt+P)
        </button>
      </div>

      <div className="space-y-3">
        {/* FPS */}
        <div className="flex items-center justify-between rounded-lg bg-background p-2">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-foreground-secondary" />
            <span className="text-sm">FPS</span>
          </div>
          <span className={cn("text-lg font-bold", getFPSColor(metrics.fps))}>
            {metrics.fps}
          </span>
        </div>

        {/* Memory */}
        {metrics.memory && (
          <div className="rounded-lg bg-background p-2">
            <div className="mb-1 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Activity className="h-4 w-4 text-foreground-secondary" />
                <span className="text-sm">Memory</span>
              </div>
              <span
                className={cn(
                  "text-sm font-semibold",
                  getMemoryColor(metrics.memory.percentage)
                )}
              >
                {metrics.memory.percentage}%
              </span>
            </div>
            <div className="h-1.5 overflow-hidden rounded-full bg-surface">
              <div
                className={cn(
                  "h-full transition-all",
                  getMemoryColor(metrics.memory.percentage).replace(
                    "text-",
                    "bg-"
                  )
                )}
                style={{ width: `${metrics.memory.percentage}%` }}
              />
            </div>
            <p className="mt-1 text-xs text-foreground-secondary">
              {metrics.memory.used} MB / {metrics.memory.total} MB
            </p>
          </div>
        )}

        {/* Load Times */}
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-foreground-secondary">DOM Ready</span>
            <span className="font-mono">
              {(metrics.navigationTiming.domContentLoaded / 1000).toFixed(2)}s
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-foreground-secondary">Load Complete</span>
            <span className="font-mono">
              {(metrics.navigationTiming.loadComplete / 1000).toFixed(2)}s
            </span>
          </div>
        </div>

        {/* Core Web Vitals */}
        {(metrics.vitals.lcp || metrics.vitals.fid) && (
          <div className="rounded-lg border border-border bg-background p-2">
            <h4 className="mb-2 text-xs font-semibold text-foreground-secondary">
              Core Web Vitals
            </h4>
            <div className="space-y-1.5">
              {metrics.vitals.lcp && (
                <div className="flex items-center justify-between text-xs">
                  <span>LCP</span>
                  <span className="font-mono">
                    {(metrics.vitals.lcp / 1000).toFixed(2)}s
                  </span>
                </div>
              )}
              {metrics.vitals.fid && (
                <div className="flex items-center justify-between text-xs">
                  <span>FID</span>
                  <span className="font-mono">{metrics.vitals.fid}ms</span>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
