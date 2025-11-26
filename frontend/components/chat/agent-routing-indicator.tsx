"use client";

import type { JSX } from "react";
import { useEffect, useState } from "react";
import type { Bot } from "lucide-react";
import {
  Brain,
  CheckCircle,
  Code,
  Database,
  HelpCircle,
  Network,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type AgentType =
  | "router"
  | "technical"
  | "billing"
  | "general"
  | "code"
  | "database";

interface AgentInfo {
  type: AgentType;
  name: string;
  description: string;
  icon: typeof Bot;
  color: string;
}

const AGENT_INFO: Record<AgentType, AgentInfo> = {
  router: {
    type: "router",
    name: "Router Agent",
    description: "Analyzing your query...",
    icon: Network,
    color: "text-purple-500",
  },
  technical: {
    type: "technical",
    name: "Technical Support",
    description: "Handling technical issues",
    icon: Zap,
    color: "text-blue-500",
  },
  billing: {
    type: "billing",
    name: "Billing Support",
    description: "Managing billing questions",
    icon: Database,
    color: "text-green-500",
  },
  general: {
    type: "general",
    name: "General Support",
    description: "Providing general assistance",
    icon: HelpCircle,
    color: "text-yellow-500",
  },
  code: {
    type: "code",
    name: "Code Assistant",
    description: "Helping with code issues",
    icon: Code,
    color: "text-cyan-500",
  },
  database: {
    type: "database",
    name: "Database Expert",
    description: "Assisting with database queries",
    icon: Database,
    color: "text-indigo-500",
  },
};

interface AgentRoutingIndicatorProps {
  currentAgent?: AgentType;
  isRouting?: boolean;
  confidence?: number;
}

/**
 * Agent Routing Indicator Component
 * Shows which AI agent is handling the current request
 * Provides visual feedback on the multi-agent routing system
 */
export function AgentRoutingIndicator({
  currentAgent = "router",
  isRouting = false,
  confidence = 0,
}: AgentRoutingIndicatorProps): JSX.Element | null {
  const [showIndicator, setShowIndicator] = useState(false);

  useEffect(() => {
    if (isRouting) {
      // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional: show immediately when routing starts
      setShowIndicator(true);
      return;
    }
    // Keep showing for 2 seconds after routing completes
    const timer = setTimeout(() => setShowIndicator(false), 2000);
    return () => clearTimeout(timer);
  }, [isRouting]);

  if (!showIndicator && !isRouting) {
    return null;
  }

  const agent = AGENT_INFO[currentAgent];
  const Icon = agent.icon;

  return (
    <div
      className={cn(
        "mb-4 flex items-center gap-3 rounded-lg border border-border bg-surface px-4 py-3 transition-all",
        isRouting && "animate-pulse"
      )}
    >
      {/* Icon */}
      <div
        className={cn(
          "flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-background",
          isRouting && "animate-spin-slow"
        )}
      >
        <Icon className={cn("h-5 w-5", agent.color)} />
      </div>

      {/* Info */}
      <div className="flex-1">
        <div className="flex items-center gap-2">
          <p className="font-medium">{agent.name}</p>
          {!isRouting && confidence > 0 && (
            <span className="rounded-full bg-accent px-2 py-0.5 text-xs text-accent-foreground">
              {Math.round(confidence * 100)}% confidence
            </span>
          )}
        </div>
        <p className="text-sm text-foreground-secondary">
          {isRouting ? "Routing your request..." : agent.description}
        </p>
      </div>

      {/* Status Icon */}
      {!isRouting && (
        <CheckCircle className="h-5 w-5 shrink-0 text-green-500" />
      )}
    </div>
  );
}

/**
 * Agent Routing Steps Component
 * Shows the step-by-step routing process
 */
interface RoutingStep {
  label: string;
  status: "pending" | "active" | "complete";
}

interface AgentRoutingStepsProps {
  steps: RoutingStep[];
  isVisible: boolean;
}

export function AgentRoutingSteps({
  steps,
  isVisible,
}: AgentRoutingStepsProps): JSX.Element | null {
  if (!isVisible) {
    return null;
  }

  return (
    <div className="mb-4 rounded-lg border border-border bg-surface p-4">
      <div className="mb-3 flex items-center gap-2">
        <Brain className="h-4 w-4 text-purple-500" />
        <p className="text-sm font-semibold">Agent Routing Process</p>
      </div>

      <div className="space-y-2">
        {steps.map((step, index) => (
          <div key={index} className="flex items-center gap-3">
            {/* Status Indicator */}
            <div
              className={cn(
                "flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2",
                step.status === "complete" &&
                  "border-green-500 bg-green-500 text-white",
                step.status === "active" &&
                  "animate-pulse border-blue-500 bg-blue-500 text-white",
                step.status === "pending" && "border-border bg-background"
              )}
            >
              {/* eslint-disable-next-line no-nested-ternary -- Status icon conditional */}
              {step.status === "complete" ? (
                <CheckCircle className="h-4 w-4" />
              ) : step.status === "active" ? (
                <div className="h-2 w-2 rounded-full bg-white" />
              ) : (
                <div className="h-2 w-2 rounded-full bg-foreground-secondary/30" />
              )}
            </div>

            {/* Step Label */}
            <p
              className={cn(
                "text-sm",
                step.status === "pending" && "text-foreground-secondary",
                step.status === "active" && "font-medium",
                step.status === "complete" && "text-green-500"
              )}
            >
              {step.label}
            </p>

            {/* Connector Line */}
            {index < steps.length - 1 && (
              <div
                className={cn(
                  "absolute left-[11px] mt-8 h-6 w-0.5",
                  step.status === "complete" ? "bg-green-500" : "bg-border"
                )}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
