"use client";

import type { JSX } from "react";
import { useCustomer, useCustomerInteractions } from "@/lib/api/hooks";
import { ArrowLeft, Mail, Building, Phone, Clock, Star, MessageSquare } from "lucide-react";
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
          <h1 className="text-3xl font-bold">{customer.name}</h1>
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

            {customer.company && (
              <div className="flex items-center gap-3">
                <Building className="h-5 w-5 text-foreground-secondary" />
                <div>
                  <p className="text-xs text-foreground-secondary">Company</p>
                  <p className="font-medium">{customer.company}</p>
                </div>
              </div>
            )}

            {customer.phone && (
              <div className="flex items-center gap-3">
                <Phone className="h-5 w-5 text-foreground-secondary" />
                <div>
                  <p className="text-xs text-foreground-secondary">Phone</p>
                  <p className="font-medium">{customer.phone}</p>
                </div>
              </div>
            )}

            <div className="flex items-center gap-3">
              <MessageSquare className="h-5 w-5 text-foreground-secondary" />
              <div>
                <p className="text-xs text-foreground-secondary">
                  Total Interactions
                </p>
                <p className="font-medium">{customer.totalInteractions}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Interaction Stats */}
        {interactionsLoading ? (
          <Skeleton className="h-32 w-full" />
        ) : interactions ? (
          <div className="grid gap-6 md:grid-cols-3">
            <div className="rounded-lg border border-border bg-surface p-6">
              <div className="flex items-center gap-2 text-foreground-secondary">
                <MessageSquare className="h-5 w-5" />
                <p className="text-sm font-medium">Total Interactions</p>
              </div>
              <p className="mt-2 text-3xl font-bold">
                {interactions.totalInteractions}
              </p>
            </div>

            <div className="rounded-lg border border-border bg-surface p-6">
              <div className="flex items-center gap-2 text-foreground-secondary">
                <Clock className="h-5 w-5" />
                <p className="text-sm font-medium">Avg Response Time</p>
              </div>
              <p className="mt-2 text-3xl font-bold">
                {interactions.avgResponseTime.toFixed(1)}s
              </p>
            </div>

            {interactions.satisfactionScore && (
              <div className="rounded-lg border border-border bg-surface p-6">
                <div className="flex items-center gap-2 text-foreground-secondary">
                  <Star className="h-5 w-5" />
                  <p className="text-sm font-medium">Satisfaction Score</p>
                </div>
                <p className="mt-2 flex items-baseline gap-1 text-3xl font-bold">
                  {interactions.satisfactionScore.toFixed(1)}
                  <span className="text-lg font-normal text-foreground-secondary">
                    /5.0
                  </span>
                </p>
              </div>
            )}
          </div>
        ) : null}

        {/* Conversation History */}
        <div className="rounded-lg border border-border bg-surface p-6">
          <h2 className="mb-4 text-lg font-semibold">Conversation History</h2>

          {interactionsLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : interactions && interactions.conversations.length > 0 ? (
            <div className="space-y-3">
              {interactions.conversations.map((conversation) => (
                <Link
                  key={conversation.id}
                  href={`/chat?id=${conversation.id}`}
                  className="block rounded-lg border border-border p-4 transition-colors hover:bg-surface-hover"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-medium hover:text-accent">
                        {conversation.title}
                      </h3>
                      <p className="mt-1 text-sm text-foreground-secondary">
                        Created{" "}
                        {format(
                          new Date(conversation.createdAt),
                          "MMM dd, yyyy 'at' HH:mm"
                        )}
                      </p>
                    </div>
                    <Button variant="ghost" size="sm">
                      View
                    </Button>
                  </div>
                </Link>
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
