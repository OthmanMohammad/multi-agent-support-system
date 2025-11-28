import {
  Zap,
  Shield,
  BarChart3,
  Users,
  MessageSquare,
  Cpu,
  ArrowRight,
  CheckCircle,
} from 'lucide-react';
import Link from 'next/link';

import { Button, Card, CardContent } from '@/components/ui';

// =============================================================================
// Hero Section
// =============================================================================

function HeroSection() {
  return (
    <section className="relative overflow-hidden py-20 md:py-32">
      {/* Background gradient */}
      <div className="absolute inset-0 -z-10">
        <div className="absolute inset-0 bg-gradient-to-b from-background-secondary/50 to-background" />
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-brand-orange/10 rounded-full blur-3xl" />
      </div>

      <div className="container">
        <div className="mx-auto max-w-3xl text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 rounded-full bg-background-secondary px-4 py-1.5 text-sm font-medium text-text-secondary mb-6">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-brand-orange opacity-75" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-brand-orange" />
            </span>
            243+ Specialized AI Agents
          </div>

          {/* Headline */}
          <h1 className="text-4xl md:text-6xl font-bold text-text-primary tracking-tight text-balance">
            Customer support that <span className="gradient-text">actually scales</span>
          </h1>

          {/* Subheadline */}
          <p className="mt-6 text-lg md:text-xl text-text-secondary max-w-2xl mx-auto">
            Deploy an army of AI agents trained for support, sales, and customer success. Handle 10x
            more requests without hiring 10x more people.
          </p>

          {/* CTA Buttons */}
          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg" className="px-8">
                Start Free Trial
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="#how-it-works">
              <Button size="lg" variant="outline">
                See How It Works
              </Button>
            </Link>
          </div>

          {/* Social Proof */}
          <p className="mt-8 text-sm text-text-tertiary">Trusted by 500+ companies worldwide</p>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Features Section
// =============================================================================

const features = [
  {
    icon: Cpu,
    title: '243+ Specialized Agents',
    description:
      'Purpose-built AI agents for every scenario: billing, technical support, sales, onboarding, and more.',
  },
  {
    icon: Zap,
    title: 'Instant Responses',
    description:
      'AI agents respond in seconds, not minutes. Handle peak loads without breaking a sweat.',
  },
  {
    icon: MessageSquare,
    title: 'Multi-Channel Support',
    description: 'Deploy across chat, email, and web. Your customers get help wherever they are.',
  },
  {
    icon: BarChart3,
    title: 'Real-Time Analytics',
    description:
      'Track agent performance, customer satisfaction, and identify improvement opportunities.',
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'SOC 2 compliant, end-to-end encryption, and role-based access control built-in.',
  },
  {
    icon: Users,
    title: 'Human Escalation',
    description:
      'Complex issues automatically escalate to your team. AI handles the volume, humans handle the edge cases.',
  },
];

function FeaturesSection() {
  return (
    <section id="features" className="py-20 bg-background-secondary/30">
      <div className="container">
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-text-primary">
            Everything you need to scale support
          </h2>
          <p className="mt-4 text-lg text-text-secondary">
            A complete platform that grows with your business
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card key={feature.title} className="group hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-brand-orange/10 text-brand-orange mb-4 group-hover:bg-brand-orange group-hover:text-white transition-colors">
                  <feature.icon className="h-6 w-6" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">{feature.title}</h3>
                <p className="text-text-secondary">{feature.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// How It Works Section
// =============================================================================

const steps = [
  {
    step: '01',
    title: 'Connect Your Channels',
    description: 'Integrate with your existing support channels in minutes. No code required.',
  },
  {
    step: '02',
    title: 'Train Your Agents',
    description: 'Upload your knowledge base and FAQs. Our AI learns your products and processes.',
  },
  {
    step: '03',
    title: 'Go Live',
    description:
      'Deploy AI agents to handle customer inquiries. Monitor and optimize in real-time.',
  },
];

function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-20">
      <div className="container">
        {/* Section Header */}
        <div className="mx-auto max-w-2xl text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-text-primary">
            Up and running in minutes
          </h2>
          <p className="mt-4 text-lg text-text-secondary">
            Three simple steps to transform your customer support
          </p>
        </div>

        {/* Steps */}
        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((step, index) => (
            <div key={step.step} className="relative">
              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-8 left-1/2 w-full h-0.5 bg-border" />
              )}
              <div className="relative bg-background p-6 rounded-xl text-center">
                <div className="inline-flex h-16 w-16 items-center justify-center rounded-full bg-brand-orange text-white text-2xl font-bold mb-4">
                  {step.step}
                </div>
                <h3 className="text-xl font-semibold text-text-primary mb-2">{step.title}</h3>
                <p className="text-text-secondary">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Stats Section
// =============================================================================

const stats = [
  { value: '243+', label: 'AI Agents' },
  { value: '99.9%', label: 'Uptime SLA' },
  { value: '<2s', label: 'Response Time' },
  { value: '85%', label: 'Auto-Resolution' },
];

function StatsSection() {
  return (
    <section className="py-16 bg-brand-orange">
      <div className="container">
        <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
          {stats.map((stat) => (
            <div key={stat.label} className="text-center">
              <div className="text-4xl md:text-5xl font-bold text-white">{stat.value}</div>
              <div className="mt-2 text-white/80">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// CTA Section
// =============================================================================

const benefits = ['No credit card required', '14-day free trial', 'Cancel anytime'];

function CTASection() {
  return (
    <section id="pricing" className="py-20 bg-background-secondary/50">
      <div className="container">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-text-primary">
            Ready to transform your support?
          </h2>
          <p className="mt-4 text-lg text-text-secondary">
            Join hundreds of companies already using Multi-Agent Support to deliver better customer
            experiences at scale.
          </p>

          <div className="mt-8">
            <Link href="/register">
              <Button size="lg" className="px-8">
                Start Your Free Trial
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {/* Benefits */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-6">
            {benefits.map((benefit) => (
              <div key={benefit} className="flex items-center gap-2 text-sm text-text-secondary">
                <CheckCircle className="h-4 w-4 text-success" />
                {benefit}
              </div>
            ))}
          </div>
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
      <HeroSection />
      <FeaturesSection />
      <HowItWorksSection />
      <StatsSection />
      <CTASection />
    </>
  );
}
