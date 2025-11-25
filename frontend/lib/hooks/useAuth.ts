/**
 * Authentication Hook
 *
 * Re-exports the useAuth hook from the auth context.
 * This file exists for backwards compatibility.
 *
 * @deprecated Import from '@/lib/contexts/auth-context' instead
 */

"use client";

export { useAuth } from "../contexts/auth-context";
export type { AuthContextValue, AuthState } from "../contexts/auth-context";
