"use client";

import type { JSX } from "react";
import { useState, useMemo, useEffect } from "react";
import Fuse from "fuse.js";
import { Search, X, Filter } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

/**
 * Smart Search Component
 * Fuzzy search with advanced filtering and ranking
 * Uses Fuse.js for semantic matching
 */

interface SmartSearchProps<T> {
  data: T[];
  keys: string[];
  onResults: (results: T[]) => void;
  placeholder?: string;
  threshold?: number;
  className?: string;
  showFilters?: boolean;
  filters?: SearchFilter[];
}

interface SearchFilter {
  key: string;
  label: string;
  values: Array<{ value: string; label: string }>;
}

export function SmartSearch<T extends Record<string, any>>({
  data,
  keys,
  onResults,
  placeholder = "Search...",
  threshold = 0.4,
  className,
  showFilters = false,
  filters = [],
}: SmartSearchProps<T>): JSX.Element {
  const [query, setQuery] = useState("");
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [showFilterPanel, setShowFilterPanel] = useState(false);

  // Initialize Fuse instance
  const fuse = useMemo(
    () =>
      new Fuse(data, {
        keys,
        threshold,
        includeScore: true,
        includeMatches: true,
        minMatchCharLength: 2,
        ignoreLocation: true,
        useExtendedSearch: true,
      }),
    [data, keys, threshold]
  );

  // Perform search
  useEffect(() => {
    let results = data;

    // Apply text search
    if (query.trim()) {
      const fuseResults = fuse.search(query);
      results = fuseResults.map((result) => result.item);
    }

    // Apply filters
    if (Object.keys(activeFilters).length > 0) {
      results = results.filter((item) => {
        return Object.entries(activeFilters).every(([key, value]) => {
          if (!value) return true;
          return String(item[key]) === value;
        });
      });
    }

    onResults(results);
  }, [query, activeFilters, fuse, data, onResults]);

  const handleFilterChange = (key: string, value: string) => {
    setActiveFilters((prev) => {
      if (value === "") {
        const newFilters = { ...prev };
        delete newFilters[key];
        return newFilters;
      }
      return { ...prev, [key]: value };
    });
  };

  const clearFilters = () => {
    setActiveFilters({});
    setQuery("");
  };

  const hasActiveFilters = query || Object.keys(activeFilters).length > 0;

  return (
    <div className={cn("space-y-3", className)}>
      {/* Search Input */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-foreground-secondary" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholder}
            className="h-10 w-full rounded-lg border border-border bg-surface pl-10 pr-10 text-sm placeholder:text-foreground-secondary focus:outline-none focus:ring-2 focus:ring-accent"
          />
          {query && (
            <button
              onClick={() => setQuery("")}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-foreground-secondary hover:text-foreground"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>

        {showFilters && (
          <Button
            variant={showFilterPanel ? "default" : "outline"}
            size="sm"
            onClick={() => setShowFilterPanel(!showFilterPanel)}
            className="h-10"
          >
            <Filter className="h-4 w-4" />
            {Object.keys(activeFilters).length > 0 && (
              <span className="ml-2">({Object.keys(activeFilters).length})</span>
            )}
          </Button>
        )}

        {hasActiveFilters && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearFilters}
            className="h-10"
          >
            Clear
          </Button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilterPanel && filters.length > 0 && (
        <div className="rounded-lg border border-border bg-surface p-4">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-sm font-semibold">Filters</h3>
            {Object.keys(activeFilters).length > 0 && (
              <button
                onClick={() => setActiveFilters({})}
                className="text-xs text-accent hover:underline"
              >
                Clear all
              </button>
            )}
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {filters.map((filter) => (
              <div key={filter.key}>
                <label className="mb-1.5 block text-xs font-medium text-foreground-secondary">
                  {filter.label}
                </label>
                <select
                  value={activeFilters[filter.key] || ""}
                  onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                  className="h-9 w-full rounded-lg border border-border bg-background px-3 text-sm focus:outline-none focus:ring-2 focus:ring-accent"
                >
                  <option value="">All</option>
                  {filter.values.map((v) => (
                    <option key={v.value} value={v.value}>
                      {v.label}
                    </option>
                  ))}
                </select>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search Info */}
      {(query || Object.keys(activeFilters).length > 0) && (
        <div className="flex items-center gap-2 text-xs text-foreground-secondary">
          <span>Active filters:</span>
          {query && (
            <span className="rounded-full bg-accent/10 px-2 py-0.5 font-medium text-accent">
              Search: "{query}"
            </span>
          )}
          {Object.entries(activeFilters).map(([key, value]) => {
            const filter = filters.find((f) => f.key === key);
            const valueLabel =
              filter?.values.find((v) => v.value === value)?.label || value;
            return (
              <span
                key={key}
                className="rounded-full bg-accent/10 px-2 py-0.5 font-medium text-accent"
              >
                {filter?.label || key}: {valueLabel}
              </span>
            );
          })}
        </div>
      )}
    </div>
  );
}
