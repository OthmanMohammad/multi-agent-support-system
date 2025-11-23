"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useHealthCheck, useCostTracking, useSwitchBackend } from "@/lib/api/hooks";
import { HealthStatus } from "@/components/admin/health-status";
import { CostTracking } from "@/components/admin/cost-tracking";
import { BackendSwitcher } from "@/components/admin/backend-switcher";
import { AgentManagement } from "@/components/admin/agent-management";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Shield, DollarSign, Bot, Activity } from "lucide-react";

/**
 * Admin Panel Page
 * System health, cost tracking, and configuration
 */
export default function AdminPage(): JSX.Element {
  const [activeTab, setActiveTab] = useState("health");

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-accent text-accent-foreground">
            <Shield className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Admin Panel</h1>
            <p className="text-foreground-secondary">
              System health, costs, and configuration
            </p>
          </div>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4 lg:w-auto">
            <TabsTrigger value="health" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              <span>Health</span>
            </TabsTrigger>
            <TabsTrigger value="costs" className="flex items-center gap-2">
              <DollarSign className="h-4 w-4" />
              <span>Costs</span>
            </TabsTrigger>
            <TabsTrigger value="agents" className="flex items-center gap-2">
              <Bot className="h-4 w-4" />
              <span>Agents</span>
            </TabsTrigger>
            <TabsTrigger value="backend" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              <span>Backend</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="health" className="space-y-6">
            <HealthStatus />
          </TabsContent>

          <TabsContent value="costs" className="space-y-6">
            <CostTracking />
          </TabsContent>

          <TabsContent value="agents" className="space-y-6">
            <AgentManagement />
          </TabsContent>

          <TabsContent value="backend" className="space-y-6">
            <BackendSwitcher />
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
