"use client";

import type { JSX } from "react";
import { useCustomer, useCustomerInteractions } from "@/lib/api/hooks";
import {
  Activity,
  ArrowLeft,
  DollarSign,
  Mail,
  MessageSquare,
  Star,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { format } from "date-fns";
import { use } from "react";

/**
 * Customer Detail Page
 * View individual customer details and interaction history
 */
export default function CustomerDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}): JSX.Element {
  const { id } = use(params);
  const { data: customer, isLoading: customerLoading } = useCustomer(id);
  const { data: interactions, isLoading: interactionsLoading } =
    useCustomerInteractions(id);

  if (customerLoading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="mx-auto max-w-5xl space-y-8">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (!customer) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="mx-auto max-w-5xl">
          <Link href="/customers">
            <Button variant="ghost" className="mb-4">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Customers
            </Button>
          </Link>
          <div className="rounded-lg border border-border bg-surface p-12 text-center">
            <p className="text-lg font-medium">Customer not found</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-5xl space-y-8">
        {/* Header */}
        <div>
          <Link href="/customers">
            <Button variant="ghost" className="mb-4">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Customers
            </Button>
          </Link>
          <h1 className="text-3xl font-bold">
            {customer.name || customer.email}
          </h1>
          <p className="mt-1 text-foreground-secondary">
            Plan:{" "}
            <span className="font-medium capitalize">{customer.plan}</span>
          </p>
        </div>

        {/* Customer Info Card */}
        <div className="rounded-lg border border-border bg-surface p-6">
          <h2 className="mb-4 text-lg font-semibold">Customer Information</h2>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-foreground-secondary" />
              <div>
                <p className="text-xs text-foreground-secondary">Email</p>
                <p className="font-medium">{customer.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <MessageSquare className="h-5 w-5 text-foreground-secondary" />
              <div>
                <p className="text-xs text-foreground-secondary">
                  Total Conversations
                </p>
                <p className="font-medium">{customer.total_conversations}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-foreground-secondary" />
              <div>
                <p className="text-xs text-foreground-secondary">
                  Active Conversations
                </p>
                <p className="font-medium">{customer.active_conversations}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <DollarSign className="h-5 w-5 text-foreground-secondary" />
              <div>
                <p className="text-xs text-foreground-secondary">
                  Lifetime Value
                </p>
                <p className="font-medium">
                  ${customer.lifetime_value.toFixed(2)}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Health Score */}
        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-lg border border-border bg-surface p-6">
            <div className="flex items-center gap-2 text-foreground-secondary">
              <Star className="h-5 w-5" />
              <p className="text-sm font-medium">Health Score</p>
            </div>
            <p className="mt-2 flex items-baseline gap-1 text-3xl font-bold">
              {customer.health_score}
              <span className="text-lg font-normal text-foreground-secondary">
                /100
              </span>
            </p>
          </div>

          <div className="rounded-lg border border-border bg-surface p-6">
            <div className="flex items-center gap-2 text-foreground-secondary">
              <MessageSquare className="h-5 w-5" />
              <p className="text-sm font-medium">Member Since</p>
            </div>
            <p className="mt-2 text-xl font-bold">
              {format(new Date(customer.created_at), "MMMM dd, yyyy")}
            </p>
          </div>
        </div>

        {/* Conversation History Placeholder */}
        <div className="rounded-lg border border-border bg-surface p-6">
          <h2 className="mb-4 text-lg font-semibold">Conversation History</h2>

          {interactionsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : interactions &&
            Array.isArray(interactions) &&
            interactions.length > 0 ? (
            <div className="space-y-3">
              {interactions.map((_, index) => (
                <div
                  key={index}
                  className="rounded-lg border border-border p-4"
                >
                  <p className="text-sm text-foreground-secondary">
                    Interaction data placeholder
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <p className="py-8 text-center text-foreground-secondary">
              No conversations yet
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
