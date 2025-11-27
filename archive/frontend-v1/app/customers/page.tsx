"use client";

import type { JSX } from "react";
import { useMemo, useState } from "react";
import { useCustomers } from "@/lib/api/hooks";
import { Mail, Search, Users } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { format } from "date-fns";

/**
 * Get plan badge classes based on plan type
 */
function getPlanBadgeClasses(plan: string): string {
  switch (plan) {
    case "enterprise":
      return "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300";
    case "premium":
      return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300";
    case "basic":
      return "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300";
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-300";
  }
}

/**
 * Customers Page
 * List and manage all customers
 */
export default function CustomersPage(): JSX.Element {
  const [search, setSearch] = useState("");

  const { customers, isLoading } = useCustomers();

  // Filter customers by search term
  const filteredCustomers = useMemo(() => {
    if (!customers) {
      return [];
    }
    if (!search) {
      return customers;
    }

    const searchLower = search.toLowerCase();
    return customers.filter(
      (c) =>
        c.email.toLowerCase().includes(searchLower) ||
        (c.name && c.name.toLowerCase().includes(searchLower))
    );
  }, [customers, search]);

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Customers</h1>
            <p className="mt-1 text-foreground-secondary">
              {customers?.length || 0} total customers
            </p>
          </div>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
            <input
              type="text"
              placeholder="Search customers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-10 w-80 rounded-lg border border-border bg-surface pl-9 pr-4 text-sm placeholder:text-foreground-secondary focus:outline-none focus:ring-2 focus:ring-accent"
            />
          </div>
        </div>

        {/* Customers Grid */}
        {/* eslint-disable-next-line no-nested-ternary -- Loading/data/empty conditional */}
        {isLoading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-48 rounded-lg" />
            ))}
          </div>
        ) : filteredCustomers.length > 0 ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filteredCustomers.map((customer) => (
              <Link
                key={customer.customer_id}
                href={`/customers/${customer.customer_id}`}
                className="group rounded-lg border border-border bg-surface p-6 transition-all hover:shadow-lg"
              >
                <div className="mb-4 flex items-start justify-between">
                  <div>
                    <h3 className="text-lg font-semibold group-hover:text-accent">
                      {customer.name || "Unnamed Customer"}
                    </h3>
                    <p className="mt-1 flex items-center gap-1.5 text-sm text-foreground-secondary">
                      <Mail className="h-3.5 w-3.5" />
                      {customer.email}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2 py-1 text-xs font-medium capitalize ${getPlanBadgeClasses(customer.plan)}`}
                  >
                    {customer.plan}
                  </span>
                </div>

                <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
                  <div>
                    <p className="text-xs text-foreground-secondary">Plan</p>
                    <p className="text-sm font-medium capitalize">
                      {customer.plan}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xs text-foreground-secondary">Joined</p>
                    <p className="text-sm font-medium">
                      {format(new Date(customer.created_at), "MMM dd, yyyy")}
                    </p>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-surface p-12 text-center">
            <Users className="mx-auto h-12 w-12 text-foreground-secondary" />
            <p className="mt-4 text-lg font-medium">No customers found</p>
            <p className="mt-2 text-foreground-secondary">
              {search
                ? "Try adjusting your search"
                : "Customers will appear here once they interact with the system"}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
