"use client";

import type { JSX } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  MessageSquare,
  Settings,
  Shield,
  Sparkles,
  Users,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/contexts/auth-context";

export default function Home(): JSX.Element {
  const { isAuthenticated, isInitialized, isNewUser } = useAuth();
  return (
    <div className="flex min-h-screen flex-col">
      {/* Hero Section */}
      <section className="flex flex-1 flex-col items-center justify-center px-4 py-20 text-center">
        <div className="mx-auto max-w-4xl space-y-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-2 text-sm">
            <Sparkles className="h-4 w-4 text-accent" />
            <span className="text-foreground-secondary">
              AI-Powered Multi-Agent Support System
            </span>
          </div>

          <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
            Customer Support,{" "}
            <span className="bg-gradient-to-r from-accent to-blue-500 bg-clip-text text-transparent">
              Reimagined
            </span>
          </h1>

          <p className="mx-auto max-w-2xl text-lg text-foreground-secondary sm:text-xl">
            Intelligent multi-agent system that handles customer conversations
            with AI precision. Monitor, analyze, and optimize your support
            workflow in real-time.
          </p>

          <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
            <Button asChild size="lg" className="gap-2">
              <Link href="/chat">
                <MessageSquare className="h-5 w-5" />
                Start Chatting
                <ArrowRight className="h-4 w-4" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="gap-2">
              <Link href="/dashboard">
                <BarChart3 className="h-5 w-5" />
                View Dashboard
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="border-t border-border bg-surface/50 px-4 py-20">
        <div className="mx-auto max-w-6xl">
          <h2 className="mb-12 text-center text-3xl font-bold">
            Everything you need to manage support
          </h2>

          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <Link
              href="/chat"
              className="group rounded-lg border border-border bg-background p-6 transition-all hover:border-accent hover:shadow-lg"
            >
              <MessageSquare className="mb-4 h-10 w-10 text-accent" />
              <h3 className="mb-2 text-xl font-semibold">AI Chat</h3>
              <p className="text-foreground-secondary">
                Multi-agent conversations with intelligent routing and context
                awareness
              </p>
              <div className="mt-4 flex items-center gap-2 text-sm text-accent">
                Try it now{" "}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </div>
            </Link>

            {/* Feature 2 */}
            <Link
              href="/dashboard"
              className="group rounded-lg border border-border bg-background p-6 transition-all hover:border-accent hover:shadow-lg"
            >
              <BarChart3 className="mb-4 h-10 w-10 text-accent" />
              <h3 className="mb-2 text-xl font-semibold">Analytics</h3>
              <p className="text-foreground-secondary">
                Real-time metrics, performance tracking, and detailed insights
              </p>
              <div className="mt-4 flex items-center gap-2 text-sm text-accent">
                View metrics{" "}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </div>
            </Link>

            {/* Feature 3 */}
            <Link
              href="/customers"
              className="group rounded-lg border border-border bg-background p-6 transition-all hover:border-accent hover:shadow-lg"
            >
              <Users className="mb-4 h-10 w-10 text-accent" />
              <h3 className="mb-2 text-xl font-semibold">
                Customer Management
              </h3>
              <p className="text-foreground-secondary">
                Complete customer profiles with conversation history and
                preferences
              </p>
              <div className="mt-4 flex items-center gap-2 text-sm text-accent">
                Manage customers{" "}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </div>
            </Link>

            {/* Feature 4 */}
            <Link
              href="/admin"
              className="group rounded-lg border border-border bg-background p-6 transition-all hover:border-accent hover:shadow-lg"
            >
              <Shield className="mb-4 h-10 w-10 text-accent" />
              <h3 className="mb-2 text-xl font-semibold">Admin Panel</h3>
              <p className="text-foreground-secondary">
                System health monitoring, cost tracking, and agent management
              </p>
              <div className="mt-4 flex items-center gap-2 text-sm text-accent">
                Admin tools{" "}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </div>
            </Link>

            {/* Feature 5 */}
            <Link
              href="/settings"
              className="group rounded-lg border border-border bg-background p-6 transition-all hover:border-accent hover:shadow-lg"
            >
              <Settings className="mb-4 h-10 w-10 text-accent" />
              <h3 className="mb-2 text-xl font-semibold">Settings</h3>
              <p className="text-foreground-secondary">
                Customize your experience with theme, preferences, and
                integrations
              </p>
              <div className="mt-4 flex items-center gap-2 text-sm text-accent">
                Configure{" "}
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </div>
            </Link>

            {/* Feature 6 */}
            <div className="rounded-lg border border-border bg-background p-6">
              <Sparkles className="mb-4 h-10 w-10 text-accent" />
              <h3 className="mb-2 text-xl font-semibold">Advanced Features</h3>
              <p className="text-foreground-secondary">
                Voice input, smart search, command palette (⌘K), and performance
                monitoring
              </p>
              <div className="mt-4 text-sm text-foreground-secondary">
                Press{" "}
                <kbd className="rounded border border-border bg-surface px-2 py-1 font-mono">
                  ?
                </kbd>{" "}
                for shortcuts
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section - Show different content based on auth state */}
      <section className="border-t border-border px-4 py-20 text-center">
        <div className="mx-auto max-w-2xl space-y-6">
          {/* eslint-disable-next-line no-nested-ternary -- Auth state conditional */}
          {isInitialized && isAuthenticated ? (
            // Authenticated: Show different CTAs for new vs returning users
            isNewUser ? (
              // New user just registered - show onboarding message
              <>
                <h2 className="text-3xl font-bold">Welcome to the team!</h2>
                <p className="text-lg text-foreground-secondary">
                  Your account is ready. Start your first conversation with our
                  AI support agents.
                </p>
                <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
                  <Button asChild size="lg">
                    <Link href="/chat">Start Your First Chat</Link>
                  </Button>
                  <Button asChild variant="outline" size="lg">
                    <Link href="/dashboard">Explore Dashboard</Link>
                  </Button>
                </div>
              </>
            ) : (
              // Returning user - show welcome back message
              <>
                <h2 className="text-3xl font-bold">Welcome back!</h2>
                <p className="text-lg text-foreground-secondary">
                  Continue where you left off
                </p>
                <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
                  <Button asChild size="lg">
                    <Link href="/chat">Go to Chat</Link>
                  </Button>
                  <Button asChild variant="outline" size="lg">
                    <Link href="/dashboard">View Dashboard</Link>
                  </Button>
                </div>
              </>
            )
          ) : (
            // Not authenticated: Show sign up/sign in CTAs
            <>
              <h2 className="text-3xl font-bold">Ready to get started?</h2>
              <p className="text-lg text-foreground-secondary">
                Create an account or sign in to access all features
              </p>
              <div className="flex flex-col gap-4 sm:flex-row sm:justify-center">
                <Button asChild size="lg">
                  <Link href="/auth/signup">Create Account</Link>
                </Button>
                <Button asChild variant="outline" size="lg">
                  <Link href="/auth/signin">Sign In</Link>
                </Button>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
