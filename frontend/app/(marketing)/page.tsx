'use client';

import { motion, useInView } from 'framer-motion';
import { ArrowRight, Cpu, MessageSquare, Shield, Zap } from 'lucide-react';
import Link from 'next/link';
import { useRef } from 'react';

import { Button } from '@/components/ui';

// =============================================================================
// Mistral-Style Rainbow Bar
// =============================================================================

function RainbowBar() {
  return (
    <div className="flex h-1 w-full">
      <div className="flex-1 bg-brand-red" />
      <div className="flex-1 bg-brand-orange-dark" />
      <div className="flex-1 bg-brand-orange" />
      <div className="flex-1 bg-brand-orange-light" />
      <div className="flex-1 bg-brand-yellow" />
    </div>
  );
}

// =============================================================================
// Hero Section - Mistral Style Large Typography
// =============================================================================

function HeroSection() {
  return (
    <section className="relative pt-20 pb-32 lg:pt-32 lg:pb-40">
      <div className="container">
        <div className="max-w-4xl">
          {/* Eyebrow */}
          <motion.p
            className="text-sm font-semibold text-brand-orange uppercase tracking-wider mb-6"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            Introducing That Agents Project
          </motion.p>

          {/* Main Headline */}
          <motion.h1
            className="text-5xl md:text-6xl lg:text-7xl font-black text-text-primary tracking-tight leading-[1.05]"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            AI agents for
            <br />
            <span className="text-brand-orange">customer support</span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            className="mt-8 text-xl md:text-2xl text-text-secondary max-w-2xl leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            Deploy specialized AI agents to handle support, sales, and customer success. Scale your
            operations without scaling your team.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="mt-10 flex flex-wrap items-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <Link href="/register">
              <Button size="lg" className="group">
                Get started
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link href="#technology">
              <Button size="lg" variant="outline">
                Learn more
              </Button>
            </Link>
          </motion.div>
        </div>
      </div>

      {/* Background gradient decoration */}
      <div className="absolute top-0 right-0 -z-10 w-1/2 h-full opacity-30 bg-gradient-to-l from-brand-yellow/20 via-brand-orange/10 to-transparent" />
    </section>
  );
}

// =============================================================================
// Features Section - Clean Grid
// =============================================================================

const features = [
  {
    icon: Zap,
    title: 'Instant responses',
    description: 'AI agents respond in seconds, not minutes. Handle peak loads effortlessly.',
  },
  {
    icon: MessageSquare,
    title: 'Multi-channel',
    description: 'Deploy across chat, email, and web. Meet customers where they are.',
  },
  {
    icon: Cpu,
    title: 'Smart routing',
    description: 'Automatically route conversations to the right agent or escalate to humans.',
  },
  {
    icon: Shield,
    title: 'Enterprise security',
    description: 'SOC 2 compliant with end-to-end encryption and role-based access control.',
  },
];

function FeaturesSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section id="technology" className="py-24 bg-background-secondary" ref={ref}>
      <div className="container">
        <div className="grid lg:grid-cols-2 gap-16 items-start">
          {/* Left - Text */}
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
              Built for scale
            </h2>
            <p className="mt-6 text-lg text-text-secondary max-w-md">
              Our platform handles millions of conversations daily with enterprise-grade reliability
              and performance.
            </p>
            <Link href="/register" className="inline-block mt-8">
              <Button>
                Start building
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </motion.div>

          {/* Right - Features Grid */}
          <div className="grid sm:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="group"
                initial={{ opacity: 0, y: 30 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <feature.icon className="h-6 w-6 text-brand-orange mb-4" />
                <h3 className="text-lg font-semibold text-text-primary mb-2">{feature.title}</h3>
                <p className="text-text-secondary text-sm leading-relaxed">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Agents Section - Showcase
// =============================================================================

const agents = [
  { name: 'Support Agent', description: 'Handle tickets and inquiries', color: 'bg-brand-red' },
  {
    name: 'Sales Agent',
    description: 'Qualify leads and book demos',
    color: 'bg-brand-orange-dark',
  },
  { name: 'Success Agent', description: 'Onboarding and retention', color: 'bg-brand-orange' },
  {
    name: 'Analytics Agent',
    description: 'Insights and reporting',
    color: 'bg-brand-orange-light',
  },
  { name: 'Security Agent', description: 'Threat detection', color: 'bg-brand-yellow' },
  { name: 'Custom Agent', description: 'Build your own', color: 'bg-text-primary' },
];

function AgentsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section id="agents" className="py-24" ref={ref}>
      <div className="container">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Specialized agents
          </h2>
          <p className="mt-4 text-lg text-text-secondary">
            Purpose-built for every customer interaction
          </p>
        </motion.div>

        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {agents.map((agent, index) => (
            <motion.div
              key={agent.name}
              className="group p-6 rounded-lg border border-border bg-surface hover:border-brand-orange transition-all duration-200 cursor-pointer"
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: index * 0.08 }}
              whileHover={{ y: -2 }}
            >
              <div className="flex items-start gap-4">
                <div className={`w-3 h-3 rounded-full ${agent.color} mt-1.5`} />
                <div>
                  <h3 className="font-semibold text-text-primary group-hover:text-brand-orange transition-colors">
                    {agent.name}
                  </h3>
                  <p className="text-sm text-text-secondary mt-1">{agent.description}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Stats Section - Bold Numbers
// =============================================================================

const stats = [
  { value: '99.9%', label: 'Uptime SLA' },
  { value: '<2s', label: 'Response time' },
  { value: '85%', label: 'Auto-resolution' },
  { value: '24/7', label: 'Availability' },
];

function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section className="py-20 bg-text-primary" ref={ref}>
      <div className="container">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              className="text-center"
              initial={{ opacity: 0, y: 20 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div className="text-4xl md:text-5xl font-black text-text-inverse tracking-tight">
                {stat.value}
              </div>
              <div className="mt-2 text-sm text-text-inverse/60">{stat.label}</div>
            </motion.div>
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
  { number: '01', title: 'Connect', description: 'Integrate with your existing tools in minutes.' },
  {
    number: '02',
    title: 'Train',
    description: 'Upload your knowledge base. AI learns your products.',
  },
  { number: '03', title: 'Deploy', description: 'Go live and watch AI handle customer inquiries.' },
];

function HowItWorksSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="py-24 bg-background-secondary" ref={ref}>
      <div className="container">
        <motion.div
          className="mb-16"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Up and running in minutes
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-12">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: index * 0.15 }}
            >
              <div className="text-6xl font-black text-brand-orange mb-4">{step.number}</div>
              <h3 className="text-2xl font-bold text-text-primary mb-2">{step.title}</h3>
              <p className="text-text-secondary">{step.description}</p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// CTA Section
// =============================================================================

function CTASection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="py-24" ref={ref}>
      <div className="container">
        <motion.div
          className="max-w-3xl mx-auto text-center"
          initial={{ opacity: 0, y: 30 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Ready to scale your support?
          </h2>
          <p className="mt-6 text-lg text-text-secondary">
            Join companies using AI-powered support to deliver better customer experiences.
          </p>

          <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
            <Link href="/register">
              <Button size="lg">
                Get started
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/login">
              <Button size="lg" variant="outline">
                Sign in
              </Button>
            </Link>
          </div>
        </motion.div>
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
      <FeaturesSection />
      <AgentsSection />
      <StatsSection />
      <HowItWorksSection />
      <CTASection />
      <RainbowBar />
    </>
  );
}
