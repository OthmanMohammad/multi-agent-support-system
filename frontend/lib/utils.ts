import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Utility function to merge Tailwind CSS classes
 * Combines clsx for conditional classes and tailwind-merge to resolve conflicts
 *
 * @example
 * cn("px-2 py-1", condition && "bg-blue-500", "px-4") // "py-1 bg-blue-500 px-4"
 */
export const cn = (...inputs: ClassValue[]): string => {
  return twMerge(clsx(inputs));
};

/**
 * Format date to relative time (e.g., "2 hours ago")
 */
export const formatRelativeTime = (date: Date): string => {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return "just now";
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} minute${diffInMinutes > 1 ? "s" : ""} ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours > 1 ? "s" : ""} ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 7) {
    return `${diffInDays} day${diffInDays > 1 ? "s" : ""} ago`;
  }

  const diffInWeeks = Math.floor(diffInDays / 7);
  if (diffInWeeks < 4) {
    return `${diffInWeeks} week${diffInWeeks > 1 ? "s" : ""} ago`;
  }

  const diffInMonths = Math.floor(diffInDays / 30);
  return `${diffInMonths} month${diffInMonths > 1 ? "s" : ""} ago`;
};

/**
 * Sleep for specified milliseconds (useful for testing/demos)
 */
export const sleep = (ms: number): Promise<void> => {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
};

/**
 * Debounce function execution
 */
export const debounce = <T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout | null = null;

  return (...args: Parameters<T>) => {
    if (timeout) {
      clearTimeout(timeout);
    }

    timeout = setTimeout(() => {
      func(...args);
    }, wait);
  };
};

/**
 * Truncate string to specified length
 */
export const truncate = (str: string, length: number): string => {
  if (str.length <= length) {
    return str;
  }
  return `${str.slice(0, length)}...`;
};

/**
 * Generate random ID (not cryptographically secure)
 */
export const generateId = (): string => {
  return Math.random().toString(36).substring(2, 15);
};
