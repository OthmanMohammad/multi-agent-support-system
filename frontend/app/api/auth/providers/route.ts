import { NextResponse } from "next/server";
import { isGoogleConfigured, isGitHubConfigured } from "@/auth.config";

/**
 * GET /api/auth/providers
 *
 * Returns which OAuth providers are configured and available.
 * This allows the frontend to dynamically show/hide OAuth buttons.
 */
export async function GET() {
  return NextResponse.json({
    google: isGoogleConfigured,
    github: isGitHubConfigured,
  });
}
