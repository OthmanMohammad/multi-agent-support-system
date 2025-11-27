# =============================================================================
# Multi-Agent Support System - Frontend Dockerfile
# Next.js 16 + React 19 Production Build
# Optimized for Oracle Cloud ARM64 (Ampere A1)
# =============================================================================

# Build arguments
ARG NODE_VERSION=22
ARG NEXT_PUBLIC_API_URL=https://api.thatagentsproject.com
ARG NEXT_PUBLIC_APP_URL=https://thatagentsproject.com

# =============================================================================
# Stage 1: Dependencies - Install all packages
# =============================================================================
FROM node:${NODE_VERSION}-alpine AS deps

# Install system dependencies
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10 --activate

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install dependencies
RUN pnpm install --frozen-lockfile --prod=false

# =============================================================================
# Stage 2: Builder - Build the application
# =============================================================================
FROM node:${NODE_VERSION}-alpine AS builder

WORKDIR /app

# Install pnpm
RUN corepack enable && corepack prepare pnpm@10 --activate

# Copy dependencies from deps stage
COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build arguments for Next.js
ARG NEXT_PUBLIC_API_URL
ARG NEXT_PUBLIC_APP_URL

# Set environment variables for build
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL}
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the application
RUN pnpm run build

# =============================================================================
# Stage 3: Runner - Production runtime
# =============================================================================
FROM node:${NODE_VERSION}-alpine AS runner

WORKDIR /app

# Set environment
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Install security updates
RUN apk update && apk upgrade && \
    rm -rf /var/cache/apk/*

# Copy built assets from builder
COPY --from=builder /app/public ./public

# Set correct permissions for Next.js cache
RUN mkdir .next && chown nextjs:nodejs .next

# Copy standalone build
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# Start the application
CMD ["node", "server.js"]
