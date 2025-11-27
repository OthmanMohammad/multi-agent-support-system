import type { NextConfig } from "next";
import bundleAnalyzer from "@next/bundle-analyzer";

const nextConfig: NextConfig = {
  /* config options here */

  // Enable standalone output for Docker deployment
  output: "standalone",

  // Performance optimizations
  compress: true,
  poweredByHeader: false,

  // Production optimizations
  reactStrictMode: true,

  // Image optimization
  images: {
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
    // Allow images from the API domain
    remotePatterns: [
      {
        protocol: "https",
        hostname: "api.thatagentsproject.com",
      },
    ],
  },

  // Environment variables that should be available at build time
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_APP_URL: process.env.NEXT_PUBLIC_APP_URL,
  },
};

// Bundle analyzer - only enabled when ANALYZE=true
const withBundleAnalyzer = bundleAnalyzer({
  enabled: process.env.ANALYZE === "true",
});

export default withBundleAnalyzer(nextConfig);
