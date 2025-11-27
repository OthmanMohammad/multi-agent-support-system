"use client";

/* eslint-disable react-hooks/incompatible-library -- TanStack Virtual is a known incompatible library */
import type { JSX } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { useRef } from "react";

/**
 * Virtual List Component
 * High-performance list rendering for thousands of items
 * Uses @tanstack/react-virtual for windowing
 */

interface VirtualListProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => JSX.Element;
  estimateSize?: number;
  overscan?: number;
  className?: string;
}

export function VirtualList<T>({
  items,
  renderItem,
  estimateSize = 80,
  overscan = 5,
  className,
}: VirtualListProps<T>): JSX.Element {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateSize,
    overscan,
  });

  const virtualItems = virtualizer.getVirtualItems();

  return (
    <div
      ref={parentRef}
      className={className}
      style={{
        height: "100%",
        overflow: "auto",
      }}
    >
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {virtualItems.map((virtualRow) => {
          const item = items[virtualRow.index];
          if (item === undefined) {
            return null;
          }
          return (
            <div
              key={virtualRow.key}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              {renderItem(item, virtualRow.index)}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Virtual Grid Component
 * High-performance grid rendering
 */
interface VirtualGridProps<T> {
  items: T[];
  renderItem: (item: T, index: number) => JSX.Element;
  columns: number;
  estimateRowSize?: number;
  estimateColumnSize?: number;
  gap?: number;
  className?: string;
}

export function VirtualGrid<T>({
  items,
  renderItem,
  columns,
  estimateRowSize = 200,
  gap = 16,
  className,
}: VirtualGridProps<T>): JSX.Element {
  const parentRef = useRef<HTMLDivElement>(null);

  const rows = Math.ceil(items.length / columns);

  const rowVirtualizer = useVirtualizer({
    count: rows,
    getScrollElement: () => parentRef.current,
    estimateSize: () => estimateRowSize,
    overscan: 3,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();

  return (
    <div
      ref={parentRef}
      className={className}
      style={{
        height: "100%",
        overflow: "auto",
      }}
    >
      <div
        style={{
          height: `${rowVirtualizer.getTotalSize()}px`,
          width: "100%",
          position: "relative",
        }}
      >
        {virtualRows.map((virtualRow) => {
          const rowItems = items.slice(
            virtualRow.index * columns,
            (virtualRow.index + 1) * columns
          );

          return (
            <div
              key={virtualRow.key}
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: `${virtualRow.size}px`,
                transform: `translateY(${virtualRow.start}px)`,
              }}
            >
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: `repeat(${columns}, 1fr)`,
                  gap: `${gap}px`,
                  height: "100%",
                }}
              >
                {rowItems.map((item, colIndex) => {
                  const index = virtualRow.index * columns + colIndex;
                  return <div key={index}>{renderItem(item, index)}</div>;
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
