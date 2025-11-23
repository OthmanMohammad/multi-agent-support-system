import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */

  // Performance optimizations
  compress: true,
  poweredByHeader: false,

  // Production optimizations
  reactStrictMode: true,
  swcMinify: true,

  // Image optimization
  images: {
    formats: ["image/avif", "image/webp"],
    deviceSizes: [640, 750, 828, 1080, 1200, 1920, 2048, 3840],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
};

// Bundle analyzer - only enabled when ANALYZE=true
const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

export default withBundleAnalyzer(nextConfig);
