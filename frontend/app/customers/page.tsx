"use client";

import type { JSX } from "react";
import { useState } from "react";
import { useCustomers } from "@/lib/api/hooks";
import { Search, Mail, Building, Phone, Calendar } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import Link from "next/link";
import { format } from "date-fns";

/**
 * Customers Page
 * List and manage all customers
 */
export default function CustomersPage(): JSX.Element {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const limit = 20;

  const { data, isLoading } = useCustomers({
    limit,
    offset: page * limit,
    search: search || undefined,
  });

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="mx-auto max-w-7xl space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Customers</h1>
            <p className="mt-1 text-foreground-secondary">
              {data?.total || 0} total customers
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
        {isLoading ? (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-64 rounded-lg" />
            ))}
          </div>
        ) : data && data.customers && data.customers.length > 0 ? (
          <>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {data.customers.map((customer) => (
                <Link
                  key={customer.id}
                  href={`/customers/${customer.id}`}
                  className="group rounded-lg border border-border bg-surface p-6 transition-all hover:shadow-lg"
                >
                  <div className="mb-4 flex items-start justify-between">
                    <div>
                      <h3 className="text-lg font-semibold group-hover:text-accent">
                        {customer.name}
                      </h3>
                      <p className="mt-1 flex items-center gap-1.5 text-sm text-foreground-secondary">
                        <Mail className="h-3.5 w-3.5" />
                        {customer.email}
                      </p>
                    </div>
                  </div>

                  {customer.company && (
                    <p className="mb-2 flex items-center gap-1.5 text-sm text-foreground-secondary">
                      <Building className="h-3.5 w-3.5" />
                      {customer.company}
                    </p>
                  )}

                  {customer.phone && (
                    <p className="mb-2 flex items-center gap-1.5 text-sm text-foreground-secondary">
                      <Phone className="h-3.5 w-3.5" />
                      {customer.phone}
                    </p>
                  )}

                  <div className="mt-4 flex items-center justify-between border-t border-border pt-4">
                    <div>
                      <p className="text-xs text-foreground-secondary">
                        Interactions
                      </p>
                      <p className="text-lg font-semibold">
                        {customer.totalInteractions}
                      </p>
                    </div>
                    {customer.lastInteraction && (
                      <div className="text-right">
                        <p className="text-xs text-foreground-secondary">
                          Last Activity
                        </p>
                        <p className="text-sm font-medium">
                          {format(
                            new Date(customer.lastInteraction),
                            "MMM dd, yyyy"
                          )}
                        </p>
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-foreground-secondary">
                Showing {page * limit + 1} to{" "}
                {Math.min((page + 1) * limit, data.total)} of {data.total}{" "}
                customers
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => setPage(Math.max(0, page - 1))}
                  disabled={page === 0}
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setPage(page + 1)}
                  disabled={(page + 1) * limit >= data.total}
                >
                  Next
                </Button>
              </div>
            </div>
          </>
        ) : (
          <div className="rounded-lg border border-border bg-surface p-12 text-center">
            <p className="text-lg font-medium">No customers found</p>
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
