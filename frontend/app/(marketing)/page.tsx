'use client';

import { ArrowRight } from 'lucide-react';
import Link from 'next/link';

import {
  PixelAgentIcon,
  PixelChartIcon,
  PixelChatIcon,
  PixelLightningIcon,
  PixelMLogoIcon,
  PixelShieldIcon,
  PixelSparkleIcon,
  PixelUsersIcon,
} from '@/components/icons';
import { Button } from '@/components/ui';

// =============================================================================
// Rainbow Gradient Bar - Mistral signature element
// =============================================================================

function RainbowBar() {
  return (
    <div className="flex h-1 w-full overflow-hidden">
      <div className="flex-1 bg-brand-red" />
      <div className="flex-1 bg-brand-orange-dark" />
      <div className="flex-1 bg-brand-orange" />
      <div className="flex-1 bg-brand-orange-light" />
      <div className="flex-1 bg-brand-yellow" />
    </div>
  );
}

// =============================================================================
// Hero Section - Mistral Style
// =============================================================================

function HeroSection() {
  return (
    <section className="relative py-24 md:py-32 lg:py-40">
      <div className="container">
        <div className="mx-auto max-w-4xl">
          {/* Headline - Large, bold, tight tracking */}
          <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold text-text-primary tracking-tight leading-[0.95]">
            AI agents for
            <br />
            <span className="text-brand-orange">customer support</span>
          </h1>

          {/* Subheadline - Clean and simple */}
          <p className="mt-8 text-xl md:text-2xl text-text-secondary max-w-2xl leading-relaxed">
            Deploy 243+ specialized AI agents to handle support, sales, and success. Scale without
            limits.
          </p>

          {/* CTA Buttons - Mistral style */}
          <div className="mt-12 flex flex-wrap items-center gap-4">
            <Link href="/register">
              <Button size="lg" className="group">
                Get started free
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
                Sign in
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Models/Agents Section - Pixelated icons grid
// =============================================================================

const agents = [
  {
    icon: PixelChatIcon,
    name: 'Support Agent',
    description: 'Handle tickets and inquiries',
    color: 'text-brand-red',
  },
  {
    icon: PixelLightningIcon,
    name: 'Speed Agent',
    description: 'Instant response times',
    color: 'text-brand-orange-dark',
  },
  {
    icon: PixelAgentIcon,
    name: 'Smart Agent',
    description: 'Context-aware responses',
    color: 'text-brand-orange',
  },
  {
    icon: PixelShieldIcon,
    name: 'Security Agent',
    description: 'Enterprise-grade protection',
    color: 'text-brand-orange-light',
  },
  {
    icon: PixelChartIcon,
    name: 'Analytics Agent',
    description: 'Real-time insights',
    color: 'text-brand-yellow',
  },
  {
    icon: PixelUsersIcon,
    name: 'Team Agent',
    description: 'Human escalation built-in',
    color: 'text-brand-orange',
  },
];

function AgentsSection() {
  return (
    <section className="py-24 bg-surface">
      <div className="container">
        {/* Section Header */}
        <div className="mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Specialized agents
          </h2>
          <p className="mt-4 text-xl text-text-secondary">
            Purpose-built for every customer interaction
          </p>
        </div>

        {/* Agents Grid */}
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {agents.map((agent) => (
            <div
              key={agent.name}
              className="group p-6 rounded-xl border border-border bg-background hover:border-brand-orange transition-colors cursor-pointer"
            >
              <agent.icon size={48} className={`${agent.color} mb-4`} />
              <h3 className="text-lg font-semibold text-text-primary mb-1">{agent.name}</h3>
              <p className="text-text-secondary">{agent.description}</p>
            </div>
          ))}
        </div>

        {/* View all link */}
        <div className="mt-12">
          <Link
            href="#features"
            className="inline-flex items-center gap-2 text-text-primary font-medium hover:text-brand-orange transition-colors"
          >
            View all 243 agents
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Features Section - Clean cards
// =============================================================================

const features = [
  {
    icon: PixelSparkleIcon,
    title: 'Instant responses',
    description: 'AI agents respond in seconds, not minutes. Handle peak loads effortlessly.',
  },
  {
    icon: PixelChatIcon,
    title: 'Multi-channel',
    description: 'Deploy across chat, email, and web. Meet customers where they are.',
  },
  {
    icon: PixelChartIcon,
    title: 'Real-time analytics',
    description: 'Track performance, satisfaction, and identify improvement opportunities.',
  },
  {
    icon: PixelShieldIcon,
    title: 'Enterprise security',
    description: 'SOC 2 compliant with end-to-end encryption and role-based access.',
  },
];

function FeaturesSection() {
  return (
    <section id="features" className="py-24">
      <div className="container">
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left column - Header */}
          <div>
            <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
              Built for scale
            </h2>
            <p className="mt-4 text-xl text-text-secondary max-w-md">
              Everything you need to transform customer support
            </p>

            <div className="mt-8">
              <Link href="/register">
                <Button>
                  Start building
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>

          {/* Right column - Features */}
          <div className="grid gap-6 sm:grid-cols-2">
            {features.map((feature) => (
              <div key={feature.title} className="p-6">
                <feature.icon size={32} className="text-brand-orange mb-4" />
                <h3 className="text-lg font-semibold text-text-primary mb-2">{feature.title}</h3>
                <p className="text-text-secondary text-sm">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Stats Section - Bold numbers
// =============================================================================

const stats = [
  { value: '243+', label: 'Specialized agents' },
  { value: '99.9%', label: 'Uptime SLA' },
  { value: '<2s', label: 'Response time' },
  { value: '85%', label: 'Auto-resolution' },
];

function StatsSection() {
  return (
    <section className="py-24 bg-text-primary">
      <div className="container">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-5xl md:text-6xl font-bold text-white tracking-tight">
                {stat.value}
              </div>
              <div className="mt-2 text-white/60 text-sm">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// How it Works Section - Steps
// =============================================================================

const steps = [
  {
    number: '1',
    title: 'Connect',
    description: 'Integrate with your existing support channels in minutes.',
  },
  {
    number: '2',
    title: 'Train',
    description: 'Upload your knowledge base. AI learns your products.',
  },
  {
    number: '3',
    title: 'Deploy',
    description: 'Go live and watch AI handle customer inquiries.',
  },
];

function HowItWorksSection() {
  return (
    <section className="py-24">
      <div className="container">
        <div className="mb-16">
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Up and running in minutes
          </h2>
        </div>

        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((step) => (
            <div key={step.number} className="relative">
              <div className="text-8xl font-bold text-background-tertiary leading-none">
                {step.number}
              </div>
              <div className="mt-4">
                <h3 className="text-2xl font-semibold text-text-primary">{step.title}</h3>
                <p className="mt-2 text-text-secondary">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// CTA Section - Final call to action
// =============================================================================

function CTASection() {
  return (
    <section className="py-24 bg-background-secondary">
      <div className="container">
        <div className="mx-auto max-w-3xl text-center">
          <PixelMLogoIcon size={64} className="mx-auto mb-8" />

          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Ready to scale?
          </h2>
          <p className="mt-4 text-xl text-text-secondary">
            Join hundreds of companies using AI-powered support
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg">
                Start free trial
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
                Talk to sales
              </Button>
            </Link>
          </div>

          <p className="mt-6 text-sm text-text-tertiary">
            No credit card required · 14-day free trial · Cancel anytime
          </p>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Page Export
// =============================================================================

export default function HomePage() {
  return (
    <>
      <RainbowBar />
      <HeroSection />
      <AgentsSection />
      <FeaturesSection />
      <StatsSection />
      <HowItWorksSection />
      <CTASection />
      <RainbowBar />
    </>
  );
}
