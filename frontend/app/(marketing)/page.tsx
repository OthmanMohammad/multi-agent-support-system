'use client';

import { motion, useInView } from 'framer-motion';
import { ArrowRight } from 'lucide-react';
import Link from 'next/link';
import { useRef } from 'react';

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
// Animation Variants
// =============================================================================

const fadeInUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0 },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const scaleIn = {
  hidden: { opacity: 0, scale: 0.8 },
  visible: { opacity: 1, scale: 1 },
};

// =============================================================================
// Rainbow Gradient Bar
// =============================================================================

function RainbowBar() {
  return (
    <div className="flex h-1 w-full overflow-hidden">
      <motion.div
        className="flex-1 bg-brand-red"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.5, delay: 0 }}
        style={{ originX: 0 }}
      />
      <motion.div
        className="flex-1 bg-brand-orange-dark"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        style={{ originX: 0 }}
      />
      <motion.div
        className="flex-1 bg-brand-orange"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        style={{ originX: 0 }}
      />
      <motion.div
        className="flex-1 bg-brand-orange-light"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        style={{ originX: 0 }}
      />
      <motion.div
        className="flex-1 bg-brand-yellow"
        initial={{ scaleX: 0 }}
        animate={{ scaleX: 1 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        style={{ originX: 0 }}
      />
    </div>
  );
}

// =============================================================================
// Hero Section with Animations
// =============================================================================

function HeroSection() {
  return (
    <section className="relative py-24 md:py-32 lg:py-40">
      <div className="container">
        <div className="mx-auto max-w-4xl">
          {/* Headline with stagger animation */}
          <motion.h1
            className="text-5xl md:text-7xl lg:text-8xl font-bold text-text-primary tracking-tight leading-[0.95]"
            initial="hidden"
            animate="visible"
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: { staggerChildren: 0.08 },
              },
            }}
          >
            {'AI agents for'.split('').map((char, i) => (
              <motion.span
                key={i}
                variants={{
                  hidden: { opacity: 0, y: 20 },
                  visible: { opacity: 1, y: 0 },
                }}
              >
                {char}
              </motion.span>
            ))}
            <br />
            <span className="text-brand-orange">
              {'customer support'.split('').map((char, i) => (
                <motion.span
                  key={i}
                  variants={{
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0 },
                  }}
                >
                  {char}
                </motion.span>
              ))}
            </span>
          </motion.h1>

          {/* Subheadline */}
          <motion.p
            className="mt-8 text-xl md:text-2xl text-text-secondary max-w-2xl leading-relaxed"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1, duration: 0.6 }}
          >
            Deploy 243+ specialized AI agents to handle support, sales, and success. Scale without
            limits.
          </motion.p>

          {/* CTA Buttons */}
          <motion.div
            className="mt-12 flex flex-wrap items-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2, duration: 0.6 }}
          >
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
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Agents Section with Scroll Animation
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
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="py-24 bg-surface" ref={ref}>
      <div className="container">
        {/* Section Header */}
        <motion.div
          className="mb-16"
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={fadeInUp}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Specialized agents
          </h2>
          <p className="mt-4 text-xl text-text-secondary">
            Purpose-built for every customer interaction
          </p>
        </motion.div>

        {/* Agents Grid with stagger */}
        <motion.div
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={staggerContainer}
        >
          {agents.map((agent) => (
            <motion.div
              key={agent.name}
              className="group p-6 rounded-xl border border-border bg-background hover:border-brand-orange transition-all duration-300 cursor-pointer hover:shadow-lg"
              variants={scaleIn}
              transition={{ duration: 0.4 }}
              whileHover={{ y: -4 }}
            >
              <agent.icon size={48} className={`${agent.color} mb-4`} />
              <h3 className="text-lg font-semibold text-text-primary mb-1">{agent.name}</h3>
              <p className="text-text-secondary">{agent.description}</p>
            </motion.div>
          ))}
        </motion.div>

        {/* View all link */}
        <motion.div
          className="mt-12"
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : { opacity: 0 }}
          transition={{ delay: 0.8 }}
        >
          <Link
            href="#features"
            className="inline-flex items-center gap-2 text-text-primary font-medium hover:text-brand-orange transition-colors"
          >
            View all 243 agents
            <ArrowRight className="h-4 w-4" />
          </Link>
        </motion.div>
      </div>
    </section>
  );
}

// =============================================================================
// Features Section
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
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section id="features" className="py-24" ref={ref}>
      <div className="container">
        <div className="grid gap-8 lg:grid-cols-2">
          {/* Left column - Header */}
          <motion.div
            initial="hidden"
            animate={isInView ? 'visible' : 'hidden'}
            variants={fadeInUp}
            transition={{ duration: 0.6 }}
          >
            <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
              Built for scale
            </h2>
            <p className="mt-4 text-xl text-text-secondary max-w-md">
              Everything you need to transform customer support
            </p>

            <motion.div
              className="mt-8"
              initial={{ opacity: 0 }}
              animate={isInView ? { opacity: 1 } : { opacity: 0 }}
              transition={{ delay: 0.4 }}
            >
              <Link href="/register">
                <Button>
                  Start building
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </motion.div>
          </motion.div>

          {/* Right column - Features */}
          <motion.div
            className="grid gap-6 sm:grid-cols-2"
            initial="hidden"
            animate={isInView ? 'visible' : 'hidden'}
            variants={staggerContainer}
          >
            {features.map((feature) => (
              <motion.div key={feature.title} className="p-6" variants={fadeInUp}>
                <feature.icon size={32} className="text-brand-orange mb-4" />
                <h3 className="text-lg font-semibold text-text-primary mb-2">{feature.title}</h3>
                <p className="text-text-secondary text-sm">{feature.description}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </div>
    </section>
  );
}

// =============================================================================
// Stats Section with Counter Animation
// =============================================================================

const stats = [
  { value: '243', suffix: '+', label: 'Specialized agents' },
  { value: '99.9', suffix: '%', label: 'Uptime SLA' },
  { value: '<2', suffix: 's', label: 'Response time' },
  { value: '85', suffix: '%', label: 'Auto-resolution' },
];

function AnimatedCounter({
  value,
  suffix,
  isInView,
}: {
  value: string;
  suffix: string;
  isInView: boolean;
}) {
  return (
    <motion.span
      initial={{ opacity: 0 }}
      animate={isInView ? { opacity: 1 } : { opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      {value}
      {suffix}
    </motion.span>
  );
}

function StatsSection() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-50px' });

  return (
    <section className="py-24 bg-text-primary" ref={ref}>
      <div className="container">
        <motion.div
          className="grid grid-cols-2 gap-8 md:grid-cols-4"
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={staggerContainer}
        >
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              className="text-center"
              variants={scaleIn}
              transition={{ duration: 0.5, delay: index * 0.1 }}
            >
              <div className="text-5xl md:text-6xl font-bold text-white tracking-tight">
                <AnimatedCounter value={stat.value} suffix={stat.suffix} isInView={isInView} />
              </div>
              <div className="mt-2 text-white/60 text-sm">{stat.label}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}

// =============================================================================
// How it Works Section with Sequential Animation
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
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section className="py-24" ref={ref}>
      <div className="container">
        <motion.div
          className="mb-16"
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={fadeInUp}
        >
          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Up and running in minutes
          </h2>
        </motion.div>

        <div className="grid gap-8 md:grid-cols-3">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              className="relative"
              initial={{ opacity: 0, x: -30 }}
              animate={isInView ? { opacity: 1, x: 0 } : { opacity: 0, x: -30 }}
              transition={{ duration: 0.6, delay: index * 0.3 }}
            >
              <motion.div
                className="text-8xl font-bold leading-none"
                initial={{ color: '#E9E2CB' }}
                animate={isInView ? { color: '#FF8205' } : { color: '#E9E2CB' }}
                transition={{ duration: 0.8, delay: index * 0.3 + 0.3 }}
              >
                {step.number}
              </motion.div>
              <div className="mt-4">
                <h3 className="text-2xl font-semibold text-text-primary">{step.title}</h3>
                <p className="mt-2 text-text-secondary">{step.description}</p>
              </div>
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
    <section className="py-24 bg-background-secondary" ref={ref}>
      <div className="container">
        <motion.div
          className="mx-auto max-w-3xl text-center"
          initial="hidden"
          animate={isInView ? 'visible' : 'hidden'}
          variants={fadeInUp}
          transition={{ duration: 0.6 }}
        >
          <motion.div
            initial={{ scale: 0, rotate: -180 }}
            animate={isInView ? { scale: 1, rotate: 0 } : { scale: 0, rotate: -180 }}
            transition={{ duration: 0.8, type: 'spring' }}
          >
            <PixelMLogoIcon size={64} className="mx-auto mb-8" />
          </motion.div>

          <h2 className="text-4xl md:text-5xl font-bold text-text-primary tracking-tight">
            Ready to scale?
          </h2>
          <p className="mt-4 text-xl text-text-secondary">
            Join hundreds of companies using AI-powered support
          </p>

          <motion.div
            className="mt-10 flex flex-wrap items-center justify-center gap-4"
            initial={{ opacity: 0, y: 20 }}
            animate={isInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
            transition={{ delay: 0.3 }}
          >
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
          </motion.div>

          <motion.p
            className="mt-6 text-sm text-text-tertiary"
            initial={{ opacity: 0 }}
            animate={isInView ? { opacity: 1 } : { opacity: 0 }}
            transition={{ delay: 0.5 }}
          >
            No credit card required · 14-day free trial · Cancel anytime
          </motion.p>
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
      <AgentsSection />
      <FeaturesSection />
      <StatsSection />
      <HowItWorksSection />
      <CTASection />
      <RainbowBar />
    </>
  );
}
