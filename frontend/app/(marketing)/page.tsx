'use client';

import { motion, useInView } from 'framer-motion';
import Link from 'next/link';
import { useEffect, useRef, useState } from 'react';

import { Button, Icon } from '@/components/ui';

// =============================================================================
// Mistral-Style Animated Rainbow Bar
// =============================================================================

function RainbowBar() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true });

  return (
    <div ref={ref} className="flex h-1 w-full overflow-hidden">
      {['mistral-red', 'mistral-orange-dark', 'mistral-orange', 'mistral-orange-light', 'mistral-yellow'].map((color, i) => (
        <motion.div
          key={color}
          className={`flex-1 bg-${color}`}
          initial={{ scaleX: 0 }}
          animate={isInView ? { scaleX: 1 } : { scaleX: 0 }}
          transition={{ duration: 0.4, delay: i * 0.1, ease: 'easeOut' }}
          style={{ transformOrigin: 'left' }}
        />
      ))}
    </div>
  );
}

// =============================================================================
// Typewriter Effect Hook
// =============================================================================

function useTypewriter(text: string, speed: number = 80, delay: number = 500) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);

  useEffect(() => {
    const timeout = setTimeout(() => {
      let currentIndex = 0;
      const interval = setInterval(() => {
        if (currentIndex <= text.length) {
          setDisplayedText(text.slice(0, currentIndex));
          currentIndex++;
        } else {
          clearInterval(interval);
          setIsComplete(true);
        }
      }, speed);

      return () => clearInterval(interval);
    }, delay);

    return () => clearTimeout(timeout);
  }, [text, speed, delay]);

  return { displayedText, isComplete };
}

// =============================================================================
// Hero Section - Mistral Style with Typewriter
// =============================================================================

function HeroSection() {
  const { displayedText, isComplete } = useTypewriter('customer support', 60, 800);

  return (
    <section className="relative pt-24 pb-32 lg:pt-36 lg:pb-48 overflow-hidden">
      <div className="container">
        <div className="max-w-5xl">
          {/* Eyebrow Badge */}
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface border border-border mb-8"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <Icon name="logo" size={16} className="text-mistral-orange" />
            <span className="text-sm font-medium text-text-secondary">
              Introducing That Agents Project
            </span>
          </motion.div>

          {/* Main Headline with Typewriter */}
          <motion.h1
            className="text-5xl md:text-6xl lg:text-8xl font-black text-text-primary tracking-tighter leading-[0.95]"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            AI agents for
            <br />
            <span className="text-mistral-orange">
              {displayedText}
              <span className={`inline-block w-[3px] h-[0.9em] bg-mistral-orange ml-1 ${isComplete ? 'animate-pulse' : ''}`} />
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            className="mt-8 text-xl md:text-2xl text-text-secondary max-w-2xl leading-relaxed"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
          >
            Deploy 243+ specialized AI agents to handle support, sales, and customer success.
            Scale your operations without scaling your team.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="mt-12 flex flex-wrap items-center gap-4"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <Link href="/register">
              <Button size="xl" className="group">
                Get started free
                <Icon name="arrow-right" size={18} className="transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
            <Link href="#technology">
              <Button size="xl" variant="outline">
                Explore the platform
              </Button>
            </Link>
          </motion.div>

          {/* Trust Indicator */}
          <motion.div
            className="mt-12 flex items-center gap-6 text-sm text-text-tertiary"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
          >
            <span className="flex items-center gap-2">
              <Icon name="check" size={16} className="text-mistral-orange" />
              No credit card required
            </span>
            <span className="flex items-center gap-2">
              <Icon name="check" size={16} className="text-mistral-orange" />
              Free tier available
            </span>
            <span className="flex items-center gap-2">
              <Icon name="check" size={16} className="text-mistral-orange" />
              Deploy in minutes
            </span>
          </motion.div>
        </div>
      </div>

      {/* Background Gradient Orbs */}
      <div className="absolute top-20 right-0 -z-10 w-[600px] h-[600px] opacity-20 blur-3xl bg-gradient-radial from-mistral-orange via-mistral-yellow/50 to-transparent" />
      <div className="absolute bottom-0 left-1/4 -z-10 w-[400px] h-[400px] opacity-10 blur-3xl bg-gradient-radial from-mistral-red to-transparent" />
    </section>
  );
}

// =============================================================================
// Features Section - Clean Grid with Pixel Icons
// =============================================================================

const features = [
  {
    icon: 'zap',
    title: 'Instant responses',
    description: 'AI agents respond in milliseconds, not minutes. Handle thousands of concurrent conversations.',
  },
  {
    icon: 'chat',
    title: 'Multi-channel support',
    description: 'Deploy across chat, email, SMS, and web. Meet customers wherever they are.',
  },
  {
    icon: 'agent-router',
    title: 'Smart routing',
    description: 'Automatically route conversations to the right agent or escalate to humans when needed.',
  },
  {
    icon: 'settings',
    title: 'Enterprise security',
    description: 'SOC 2 compliant with end-to-end encryption, SSO, and role-based access control.',
  },
];

function FeaturesSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section id="technology" className="py-24 lg:py-32 bg-surface" ref={ref}>
      <div className="container">
        <div className="grid lg:grid-cols-2 gap-16 items-start">
          {/* Left - Text */}
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            animate={isInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.7 }}
          >
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text-primary tracking-tight">
              Built for
              <br />
              <span className="text-mistral-orange">enterprise scale</span>
            </h2>
            <p className="mt-6 text-lg text-text-secondary max-w-md leading-relaxed">
              Our platform handles millions of conversations daily with enterprise-grade reliability,
              security, and performance.
            </p>
            <Link href="/register" className="inline-block mt-8">
              <Button size="lg" className="group">
                Start building
                <Icon name="arrow-right" size={16} className="transition-transform group-hover:translate-x-1" />
              </Button>
            </Link>
          </motion.div>

          {/* Right - Features Grid */}
          <div className="grid sm:grid-cols-2 gap-6">
            {features.map((feature, index) => (
              <motion.div
                key={feature.title}
                className="group p-6 rounded-2xl bg-background border border-border hover:border-mistral-orange/50 transition-all duration-300"
                initial={{ opacity: 0, y: 40 }}
                animate={isInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.5, delay: 0.1 + index * 0.1 }}
                whileHover={{ y: -4 }}
              >
                <div className="w-12 h-12 rounded-xl bg-surface flex items-center justify-center mb-4 group-hover:bg-mistral-orange/10 transition-colors">
                  <Icon name={feature.icon} size={24} className="text-mistral-orange" />
                </div>
                <h3 className="text-lg font-semibold text-text-primary mb-2 group-hover:text-mistral-orange transition-colors">
                  {feature.title}
                </h3>
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
// Agents Section - Showcase 243+ Agents
// =============================================================================

const agentTiers = [
  {
    tier: 'Essential',
    icon: 'tier-essential',
    count: 45,
    agents: ['Support Agent', 'FAQ Bot', 'Ticket Triage'],
    color: 'mistral-orange',
  },
  {
    tier: 'Professional',
    icon: 'tier-professional',
    count: 78,
    agents: ['Sales Qualifier', 'Demo Scheduler', 'Lead Scorer'],
    color: 'mistral-orange-light',
  },
  {
    tier: 'Enterprise',
    icon: 'tier-enterprise',
    count: 120,
    agents: ['Custom Workflows', 'API Integration', 'Analytics'],
    color: 'mistral-yellow',
  },
];

function AgentsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section id="agents" className="py-24 lg:py-32" ref={ref}>
      <div className="container">
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
        >
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text-primary tracking-tight">
            243+ specialized agents
          </h2>
          <p className="mt-6 text-lg text-text-secondary max-w-2xl mx-auto">
            Purpose-built AI agents for every customer interaction, organized into tiers for your needs.
          </p>
        </motion.div>

        {/* Agent Tier Cards */}
        <div className="grid md:grid-cols-3 gap-6 lg:gap-8">
          {agentTiers.map((tier, index) => (
            <motion.div
              key={tier.tier}
              className="group relative p-8 rounded-2xl bg-surface border border-border hover:border-mistral-orange transition-all duration-300"
              initial={{ opacity: 0, y: 40 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: index * 0.15 }}
              whileHover={{ y: -6 }}
            >
              {/* Tier Icon */}
              <div className={`w-16 h-16 rounded-2xl bg-${tier.color}/10 flex items-center justify-center mb-6`}>
                <Icon name={tier.icon} size={32} className={`text-${tier.color}`} />
              </div>

              {/* Tier Info */}
              <h3 className="text-2xl font-bold text-text-primary mb-2">{tier.tier}</h3>
              <p className="text-4xl font-black text-mistral-orange mb-4">{tier.count}+</p>
              <p className="text-sm text-text-tertiary mb-6">specialized agents</p>

              {/* Sample Agents */}
              <ul className="space-y-2">
                {tier.agents.map((agent) => (
                  <li key={agent} className="flex items-center gap-2 text-sm text-text-secondary">
                    <Icon name="check" size={14} className="text-mistral-orange" />
                    {agent}
                  </li>
                ))}
              </ul>

              {/* Hover Glow */}
              <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none bg-gradient-to-br from-mistral-orange/5 to-transparent" />
            </motion.div>
          ))}
        </div>

        {/* View All CTA */}
        <motion.div
          className="text-center mt-12"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.5, delay: 0.6 }}
        >
          <Link href="/docs">
            <Button variant="outline" size="lg" className="group">
              View all agents
              <Icon name="arrow-right" size={16} className="transition-transform group-hover:translate-x-1" />
            </Button>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

// =============================================================================
// Stats Section - Bold Numbers on Dark
// =============================================================================

const stats = [
  { value: '99.9%', label: 'Uptime SLA', icon: 'check' },
  { value: '<100ms', label: 'Response time', icon: 'zap' },
  { value: '85%', label: 'Auto-resolution', icon: 'agent-router' },
  { value: '24/7', label: 'Availability', icon: 'clock' },
];

function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section className="py-20 lg:py-24 bg-white" ref={ref}>
      <div className="container">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 lg:gap-12">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              className="text-center"
              initial={{ opacity: 0, y: 30 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-black/5 mb-4">
                <Icon name={stat.icon} size={24} className="text-mistral-orange" />
              </div>
              <div className="text-4xl md:text-5xl lg:text-6xl font-black text-black tracking-tight">
                {stat.value}
              </div>
              <div className="mt-2 text-sm font-medium text-black/60">{stat.label}</div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// How It Works Section - Numbered Steps
// =============================================================================

const steps = [
  {
    number: '1',
    title: 'Connect',
    description: 'Integrate with your existing tools - Zendesk, Intercom, Salesforce, and more. Takes minutes, not days.',
    icon: 'connect',
  },
  {
    number: '2',
    title: 'Train',
    description: 'Upload your knowledge base, FAQs, and product docs. AI learns your brand voice and policies.',
    icon: 'book',
  },
  {
    number: '3',
    title: 'Deploy',
    description: 'Go live instantly. Watch AI agents handle customer inquiries while you focus on growth.',
    icon: 'send',
  },
];

function HowItWorksSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="py-24 lg:py-32 bg-surface" ref={ref}>
      <div className="container">
        <motion.div
          className="mb-16"
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
        >
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text-primary tracking-tight">
            Up and running
            <br />
            <span className="text-mistral-orange">in minutes</span>
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-3 gap-8 lg:gap-12">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              className="relative"
              initial={{ opacity: 0, y: 40 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.5, delay: index * 0.2 }}
            >
              {/* Large Number */}
              <motion.div
                className="text-[120px] lg:text-[160px] font-black text-mistral-orange/20 leading-none select-none"
                animate={isInView ? {
                  color: ['rgba(249, 115, 22, 0.1)', 'rgba(249, 115, 22, 0.3)', 'rgba(249, 115, 22, 0.1)']
                } : {}}
                transition={{ duration: 2, delay: index * 0.3, repeat: Infinity, repeatDelay: 3 }}
              >
                {step.number}
              </motion.div>

              {/* Content */}
              <div className="-mt-16 lg:-mt-20 relative z-10">
                <div className="w-12 h-12 rounded-xl bg-mistral-orange/10 flex items-center justify-center mb-4">
                  <Icon name={step.icon} size={24} className="text-mistral-orange" />
                </div>
                <h3 className="text-2xl lg:text-3xl font-bold text-text-primary mb-3">{step.title}</h3>
                <p className="text-text-secondary leading-relaxed">{step.description}</p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// CTA Section - Final Push
// =============================================================================

function CTASection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="py-24 lg:py-32" ref={ref}>
      <div className="container">
        <motion.div
          className="relative max-w-4xl mx-auto text-center p-12 lg:p-16 rounded-3xl bg-surface border border-border overflow-hidden"
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7 }}
        >
          {/* Background Gradient */}
          <div className="absolute inset-0 bg-gradient-to-br from-mistral-orange/5 via-transparent to-mistral-yellow/5 pointer-events-none" />

          <div className="relative z-10">
            <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold text-text-primary tracking-tight">
              Ready to scale
              <br />
              <span className="text-mistral-orange">your support?</span>
            </h2>
            <p className="mt-6 text-lg text-text-secondary max-w-xl mx-auto">
              Join hundreds of companies using AI-powered support to deliver exceptional customer experiences.
            </p>

            <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
              <Link href="/register">
                <Button size="xl" className="group">
                  Get started free
                  <Icon name="arrow-right" size={18} className="transition-transform group-hover:translate-x-1" />
                </Button>
              </Link>
              <Link href="/login">
                <Button size="xl" variant="outline">
                  Sign in
                </Button>
              </Link>
            </div>

            {/* Trust Badges */}
            <div className="mt-10 flex items-center justify-center gap-8 text-sm text-text-tertiary">
              <span className="flex items-center gap-2">
                <Icon name="settings" size={16} />
                SOC 2 Compliant
              </span>
              <span className="flex items-center gap-2">
                <Icon name="check" size={16} />
                GDPR Ready
              </span>
              <span className="flex items-center gap-2">
                <Icon name="lock" size={16} />
                Enterprise SSO
              </span>
            </div>
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
