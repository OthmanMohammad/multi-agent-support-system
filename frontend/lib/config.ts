/**
 * Application Configuration
 *
 * Centralized configuration with environment variable validation.
 * Fails fast if required variables are missing.
 */

import { z } from "zod";

// =============================================================================
// ENVIRONMENT SCHEMA
// =============================================================================

const envSchema = z.object({
  // API Configuration
  NEXT_PUBLIC_API_URL: z.string().url().default("http://localhost:8000"),

  // NextAuth Configuration
  NEXTAUTH_URL: z.string().url().optional(),
  NEXTAUTH_SECRET: z.string().min(32).optional(),

  // OAuth (optional)
  GOOGLE_CLIENT_ID: z.string().optional(),
  GOOGLE_CLIENT_SECRET: z.string().optional(),
  GITHUB_CLIENT_ID: z.string().optional(),
  GITHUB_CLIENT_SECRET: z.string().optional(),

  // Feature Flags
  NEXT_PUBLIC_ENABLE_MSW: z.string().optional().default("false"),

  // Environment
  NODE_ENV: z
    .enum(["development", "production", "test"])
    .default("development"),
});

// =============================================================================
// PARSE AND VALIDATE ENVIRONMENT
// =============================================================================

function getEnv() {
  // In test environment, use defaults for all variables
  const isTest = process.env.NODE_ENV === "test";

  const parsed = envSchema.safeParse({
    NEXT_PUBLIC_API_URL:
      process.env.NEXT_PUBLIC_API_URL ||
      (isTest ? "http://localhost:8000" : undefined),
    NEXTAUTH_URL: process.env.NEXTAUTH_URL,
    NEXTAUTH_SECRET:
      process.env.NEXTAUTH_SECRET ||
      (isTest ? "test-secret-for-testing-only-minimum-32-chars" : undefined),
    GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET: process.env.GOOGLE_CLIENT_SECRET,
    GITHUB_CLIENT_ID: process.env.GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET: process.env.GITHUB_CLIENT_SECRET,
    NEXT_PUBLIC_ENABLE_MSW: process.env.NEXT_PUBLIC_ENABLE_MSW,
    NODE_ENV: process.env.NODE_ENV,
  });

  if (!parsed.success) {
    // In test mode, log warning instead of throwing
    if (isTest) {
      console.warn(
        "⚠️ Environment variable validation issues in test mode:",
        parsed.error.flatten().fieldErrors
      );
      // Return defaults for testing
      return {
        NEXT_PUBLIC_API_URL: "http://localhost:8000",
        NEXTAUTH_URL: undefined,
        NEXTAUTH_SECRET: "test-secret-for-testing-only-minimum-32-chars",
        GOOGLE_CLIENT_ID: undefined,
        GOOGLE_CLIENT_SECRET: undefined,
        GITHUB_CLIENT_ID: undefined,
        GITHUB_CLIENT_SECRET: undefined,
        NEXT_PUBLIC_ENABLE_MSW: "false",
        NODE_ENV: "test" as const,
      };
    }

    console.error(
      "❌ Invalid environment variables:",
      parsed.error.flatten().fieldErrors
    );
    throw new Error("Invalid environment variables");
  }

  return parsed.data;
}

export const env = getEnv();

// =============================================================================
// APPLICATION CONFIG
// =============================================================================

export const config = {
  // API Configuration
  api: {
    baseURL: env.NEXT_PUBLIC_API_URL,
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
    retryDelay: 1000, // 1 second
  },

  // Feature Flags
  features: {
    enableMSW: env.NEXT_PUBLIC_ENABLE_MSW === "true",
    enableOAuth: !!(env.GOOGLE_CLIENT_ID || env.GITHUB_CLIENT_ID),
  },

  // Environment
  isDevelopment: env.NODE_ENV === "development",
  isProduction: env.NODE_ENV === "production",
  isTest: env.NODE_ENV === "test",
} as const;

// Type-safe config
export type Config = typeof config;
