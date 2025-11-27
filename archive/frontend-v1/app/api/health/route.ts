/**
 * Frontend Health Check Endpoint
 * Used by Docker health checks and load balancers
 */

import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export async function GET() {
  const health = {
    status: "healthy",
    timestamp: new Date().toISOString(),
    service: "frontend",
    version: process.env.npm_package_version || "1.0.0",
    environment: process.env.NODE_ENV || "development",
    uptime: process.uptime(),
  };

  return NextResponse.json(health, {
    status: 200,
    headers: {
      "Cache-Control": "no-store, no-cache, must-revalidate",
      Pragma: "no-cache",
    },
  });
}
