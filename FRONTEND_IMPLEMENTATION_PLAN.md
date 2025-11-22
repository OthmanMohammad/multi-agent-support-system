# Frontend Implementation: Production-Grade Multi-Agent Support System UI

## 📋 Issue Overview

**Objective:** Build a production-grade, enterprise-quality frontend application for the Multi-Agent Support System that rivals ChatGPT, Claude, and Gemini in terms of user experience, code quality, and performance.

**Status:** Ready for Implementation
**Priority:** High
**Complexity:** High
**Estimated Timeline:** 5-6 focused development sessions

---

## 🎯 Executive Summary

This issue documents the complete implementation plan for a world-class frontend application that will serve as the user interface for our sophisticated multi-agent AI customer support platform. The frontend will be built using the latest web technologies with zero compromises on quality, following industry best practices and enterprise-grade patterns.

### Key Goals

1. **Zero Cost Infrastructure** - Deploy on Oracle Cloud Always Free instance alongside backend
2. **Enterprise-Grade Quality** - Code quality and architecture that matches Fortune 500 standards
3. **Modern User Experience** - ChatGPT/Claude-quality interface with real-time streaming
4. **Type Safety** - End-to-end type safety from FastAPI backend to React frontend
5. **Performance** - Lighthouse score of 100 across all categories
6. **Accessibility** - WCAG 2.1 Level AA compliance minimum
7. **Production Ready** - Comprehensive testing, monitoring, and deployment automation

---

## 🏗️ Architecture Overview

### Repository Structure

We will adopt a **monorepo structure** keeping the existing backend as-is and adding a new `frontend/` directory:

```
multi-agent-support-system/
├── src/                           # ✅ Existing backend (no changes)
├── deployment/                    # ✅ Existing (will extend for frontend)
├── docs/                          # ✅ Existing (will add frontend docs)
├── migrations/                    # ✅ Existing
├── tests/                         # ✅ Existing
├── requirements.txt               # ✅ Existing
├── docker-compose.yml             # 🔄 Extend with frontend service
├── Dockerfile                     # ✅ Existing (backend)
│
├── frontend/                      # 🆕 NEW - Next.js Application
│   ├── app/                       # Next.js 15 App Router
│   ├── components/                # React components
│   ├── lib/                       # Core libraries & utilities
│   ├── hooks/                     # Custom React hooks
│   ├── stores/                    # State management (Zustand)
│   ├── types/                     # TypeScript type definitions
│   ├── config/                    # Configuration files
│   ├── public/                    # Static assets
│   ├── __tests__/                 # Test files
│   ├── Dockerfile                 # Frontend production image
│   ├── package.json               # Frontend dependencies
│   ├── tsconfig.json              # TypeScript configuration
│   ├── next.config.mjs            # Next.js configuration
│   ├── tailwind.config.ts         # Tailwind CSS configuration
│   ├── .eslintrc.json             # ESLint rules
│   ├── .prettierrc                # Prettier configuration
│   └── README.md                  # Frontend documentation
│
└── README.md                      # 🔄 Update with frontend info
```

**Rationale for Monorepo:**
- ✅ Single source of truth for API contracts
- ✅ Atomic commits spanning frontend + backend changes
- ✅ Simplified type sharing via OpenAPI spec generation
- ✅ Unified CI/CD pipeline
- ✅ Reduced operational overhead
- ✅ Industry standard (used by Google, Microsoft, Meta, Vercel)

---

## 🛠️ Technology Stack

### Core Framework & Runtime

| Technology | Version | Justification |
|------------|---------|---------------|
| **Next.js** | 15.x (App Router) | Industry-leading React framework with RSC, streaming SSR, automatic code splitting, and built-in optimizations. Used by OpenAI, TikTok, Netflix. |
| **React** | 19 RC | Latest stable release with improved concurrent rendering and automatic batching |
| **TypeScript** | 5.7+ | Type safety, better DX, catches 15% of bugs at compile time (Microsoft research) |
| **Node.js** | 22 LTS | Latest long-term support release with improved performance |
| **pnpm** | 9.x | 3x faster than npm, efficient disk space usage, strict dependency resolution |

### Styling & UI Components

| Technology | Version | Justification |
|------------|---------|---------------|
| **Tailwind CSS** | 4.x | Utility-first CSS framework, zero runtime cost, excellent DX, used by 80% of new projects |
| **shadcn/ui** | Latest | Copy-paste component system built on Radix UI, full customization, WCAG 2.1 compliant, 78k+ GitHub stars |
| **Radix UI** | Latest | Headless accessible UI primitives, powers shadcn/ui |
| **Lucide React** | Latest | 24k+ high-quality icons, tree-shakeable, modern design |
| **Framer Motion** | 11.x | Production-grade animation library, used by Apple, Amazon, Google |
| **Geist Font** | Latest | Vercel's professional typeface, optimized for readability |

### State Management

| Technology | Version | Justification |
|------------|---------|---------------|
| **TanStack Query** | 5.x | Gold standard for server state management, automatic caching/refetching/optimistic updates |
| **Zustand** | 4.x | Lightweight client state (2KB), simple API, no boilerplate, better DX than Redux |
| **React Hook Form** | 7.x | Best-in-class form library, minimal re-renders, built-in validation |
| **Zod** | 3.x | Runtime type validation, integrates with React Hook Form and TypeScript |

### API Integration & Data Fetching

| Technology | Version | Justification |
|------------|---------|---------------|
| **openapi-typescript** | Latest | Auto-generate TypeScript types from FastAPI OpenAPI spec, end-to-end type safety |
| **Native Fetch API** | - | Modern standard, works with TanStack Query, no axios bloat |
| **EventSource API** | - | Native SSE support for real-time streaming responses |

### UI/UX Enhancement

| Technology | Version | Justification |
|------------|---------|---------------|
| **react-markdown** | Latest | Markdown rendering for chat messages |
| **remark / rehype** | Latest | Markdown processing plugins (GFM, code blocks, tables) |
| **shiki** | Latest | Syntax highlighting using VS Code's highlighter, supports 100+ languages |
| **date-fns** | 3.x | Lightweight date library (vs bloated moment.js), tree-shakeable |
| **sonner** | Latest | Beautiful toast notifications, created by shadcn/ui author |

### Developer Experience

| Technology | Version | Justification |
|------------|---------|---------------|
| **ESLint** | 9.x | Industry-standard linting, catch bugs before runtime |
| **Prettier** | 3.x | Opinionated code formatting, eliminates style debates |
| **TypeScript ESLint** | Latest | TypeScript-specific linting rules |
| **Husky** | Latest | Git hooks for quality gates |
| **lint-staged** | Latest | Run linters only on staged files (fast) |
| **Commitizen** | Latest | Standardized commit messages |
| **Commitlint** | Latest | Enforce conventional commits |

### Testing Stack

| Technology | Version | Justification |
|------------|---------|---------------|
| **Vitest** | 2.x | 10x faster than Jest, Vite-powered, ESM-native |
| **React Testing Library** | Latest | Industry standard for component testing, encourages accessibility |
| **Playwright** | 1.44+ | Best E2E framework, beats Cypress in speed and reliability |
| **MSW** | 2.x | Mock Service Worker for realistic API mocking |
| **@axe-core/react** | Latest | Automated accessibility testing |

### Build & Optimization

| Technology | Version | Justification |
|------------|---------|---------------|
| **Turbopack** | Next.js 15 default | 700x faster than Webpack (Vercel benchmarks) |
| **SWC** | Built into Next.js | Rust-based compiler, 20x faster than Babel |
| **Next.js Image** | Built-in | Automatic image optimization (WebP/AVIF), lazy loading |
| **Bundle Analyzer** | Latest | Visualize bundle size, identify optimization opportunities |

### Security

| Technology | Version | Justification |
|------------|---------|---------------|
| **NextAuth.js** | 5.x (Auth.js) | Industry standard auth library, supports OAuth + credentials |
| **jose** | Latest | JWT operations (secure, well-maintained) |
| **@upstash/ratelimit** | Latest | Redis-backed rate limiting, distributed-safe |

### Analytics & Monitoring

| Technology | Version | Justification |
|------------|---------|---------------|
| **Umami** | Latest | Self-hosted privacy-focused analytics, GDPR compliant, <2KB script |
| **Sentry** | Latest | Best-in-class error tracking, free tier: 5k errors/month |
| **Pino** | Latest | Fastest structured logging library for Node.js |
| **Next.js Speed Insights** | Open-source | Performance monitoring (Core Web Vitals) |

### Deployment

| Technology | Version | Justification |
|------------|---------|---------------|
| **Oracle Cloud** | Always Free | 4 vCPU, 24GB RAM, 200GB storage, 10TB bandwidth - all FREE forever |
| **Docker** | Latest | Containerization for consistent environments |
| **Docker Compose** | 3.8 | Multi-container orchestration |
| **Nginx** | 1.25+ | Reverse proxy, static file serving, rate limiting |
| **GitHub Actions** | - | CI/CD automation (free for public repos) |

---

## 📐 Design Philosophy & Principles

### 1. User Experience (UX)

**Inspiration:** ChatGPT, Claude, and Gemini chat interfaces

**Core Principles:**
- ✅ **Minimalist Design** - Clean, distraction-free interface
- ✅ **Real-time Responsiveness** - Instant feedback, streaming responses
- ✅ **Keyboard-First** - Power users can navigate entirely via keyboard
- ✅ **Progressive Enhancement** - Works without JavaScript (where possible)
- ✅ **Mobile-First Responsive** - Perfect experience on all devices
- ✅ **Dark/Light Mode** - System preference detection + manual toggle
- ✅ **Accessibility First** - WCAG 2.1 Level AA minimum

**UI Components Inspired by ChatGPT/Claude:**
```
Layout:
├── Collapsible sidebar (conversation history)
├── Main chat area (80% viewport)
├── Message bubbles (alternating user/assistant)
├── Floating input box (bottom, sticky)
├── Header with user profile + settings
└── Command palette (⌘K for quick actions)

Chat Features:
├── Streaming text animation (typewriter effect)
├── "Thinking..." indicator with animated dots
├── Agent indicator badge (shows which AI agent is responding)
├── Code syntax highlighting with copy button
├── Markdown rendering (bold, italic, lists, tables, links)
├── Message timestamp (shown on hover)
├── Regenerate response button
├── Edit previous message
├── Stop generation button (during streaming)
└── Export conversation (PDF, Markdown, JSON)
```

**Color Palette (Professional, ChatGPT-Inspired):**
```typescript
// Light Mode
background:       '#FFFFFF'  // Pure white
surface:          '#F7F7F8'  // Subtle gray for cards
surfaceHover:     '#ECECEC'  // Hover state
border:           '#E5E5E5'  // Borders
text:             '#1F1F1F'  // Near-black for readability
textSecondary:    '#6B6B6B'  // Secondary text
accent:           '#10A37F'  // ChatGPT green (primary actions)
accentHover:      '#0D8A6A'  // Darker on hover
error:            '#EF4444'  // Red for errors
warning:          '#F59E0B'  // Amber for warnings
success:          '#10B981'  // Green for success

// Dark Mode
backgroundDark:   '#212121'  // Soft black (not pure #000)
surfaceDark:      '#2A2A2A'  // Elevated surfaces
surfaceHoverDark: '#3F3F3F'  // Hover state
borderDark:       '#404040'  // Subtle borders
textDark:         '#ECECEC'  // Off-white for readability
textSecondaryDark:'#B4B4B4'  // Secondary text
accentDark:       '#19C37D'  // Brighter green for dark mode
```

### 2. Code Quality Standards

**Zero Tolerance for:**
- ❌ `any` types in TypeScript
- ❌ Console.log statements in production
- ❌ Unused imports or variables
- ❌ Magic numbers (use named constants)
- ❌ Deeply nested conditionals (max 3 levels)
- ❌ Functions longer than 50 lines
- ❌ Files longer than 300 lines
- ❌ Prop drilling (use composition or state management)

**Enforced via Tooling:**
```json
// tsconfig.json (strict mode)
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "strictFunctionTypes": true,
    "strictBindCallApply": true,
    "strictPropertyInitialization": true,
    "noImplicitThis": true,
    "alwaysStrict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

**ESLint Rules (200+ rules enforced):**
```json
{
  "extends": [
    "next/core-web-vitals",
    "plugin:@typescript-eslint/recommended-type-checked",
    "plugin:@typescript-eslint/stylistic-type-checked",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:jsx-a11y/recommended"
  ],
  "rules": {
    "no-console": "error",
    "@typescript-eslint/no-unused-vars": "error",
    "@typescript-eslint/no-explicit-any": "error",
    "@typescript-eslint/explicit-function-return-type": "warn",
    "react/prop-types": "off",
    "react/react-in-jsx-scope": "off",
    "complexity": ["error", 10],
    "max-lines": ["error", 300],
    "max-depth": ["error", 3]
  }
}
```

### 3. Architecture Patterns

**Feature-Based Organization (NOT type-based):**

❌ **BAD (Type-based):**
```
src/
├── components/  # All components mixed together
├── hooks/       # All hooks mixed together
├── utils/       # All utilities mixed together
└── types/       # All types mixed together
```

✅ **GOOD (Feature-based):**
```
src/
├── features/
│   ├── auth/
│   │   ├── components/    # LoginForm, RegisterForm
│   │   ├── hooks/         # useAuth, useSession
│   │   ├── api/           # login(), register(), logout()
│   │   ├── types/         # AuthUser, LoginRequest
│   │   ├── utils/         # validatePassword(), etc.
│   │   └── __tests__/     # Feature-specific tests
│   ├── chat/
│   │   ├── components/    # MessageBubble, ChatInput
│   │   ├── hooks/         # useChat, useStreamingMessage
│   │   ├── api/           # sendMessage(), streamResponse()
│   │   ├── types/         # Message, Conversation
│   │   └── __tests__/
│   └── analytics/
│       └── ...
└── shared/               # Truly shared code only
    ├── components/       # Button, Input (from shadcn/ui)
    ├── hooks/            # useMediaQuery, useDebounce
    └── utils/            # cn(), formatDate()
```

**Benefits:**
- ✅ Easy to locate code (everything for a feature in one place)
- ✅ Easy to delete features (just delete the folder)
- ✅ Prevents circular dependencies
- ✅ Scales to large teams
- ✅ Aligns with business domains

**Design Patterns (SOLID Principles):**

1. **Single Responsibility** - Each component/function does ONE thing
2. **Open/Closed** - Open for extension, closed for modification
3. **Liskov Substitution** - Subtypes must be substitutable
4. **Interface Segregation** - Many specific interfaces > one general
5. **Dependency Inversion** - Depend on abstractions, not concretions

**React Patterns:**
- ✅ **Composition over Inheritance** - Use composition for reusability
- ✅ **Container/Presenter** - Separate logic from presentation
- ✅ **Compound Components** - Related components work together
- ✅ **Render Props / Custom Hooks** - Share stateful logic
- ✅ **Error Boundaries** - Graceful error handling
- ✅ **Suspense Boundaries** - Progressive loading

### 4. Performance Standards

**Lighthouse Scores (Minimum Acceptable):**
```
Performance:        100 / 100
Accessibility:      100 / 100
Best Practices:     100 / 100
SEO:                100 / 100
PWA:                 90 / 100 (optional)
```

**Core Web Vitals (Google Standards):**
```
First Contentful Paint (FCP):    < 1.0s   (Good: < 1.8s)
Largest Contentful Paint (LCP):  < 2.0s   (Good: < 2.5s)
Time to Interactive (TTI):       < 3.0s   (Good: < 3.8s)
Cumulative Layout Shift (CLS):   < 0.1    (Good: < 0.1)
First Input Delay (FID):         < 100ms  (Good: < 100ms)
Interaction to Next Paint (INP): < 200ms  (Good: < 200ms)
```

**Bundle Size Targets:**
```
Initial JavaScript:    < 150 KB (gzipped)
Total JavaScript:      < 400 KB (gzipped)
CSS:                   < 50 KB (gzipped)
Fonts:                 < 100 KB (WOFF2)
Images:                Lazy-loaded, WebP/AVIF, responsive
```

**Optimization Techniques:**
```typescript
// 1. React Server Components (default in App Router)
export default async function Page() {
  const data = await fetchData(); // Runs on server
  return <ClientComponent data={data} />; // Minimal JS to client
}

// 2. Dynamic imports for code splitting
const HeavyComponent = dynamic(() => import('./Heavy'), {
  loading: () => <Skeleton />,
  ssr: false
});

// 3. Memoization for expensive computations
const expensiveValue = useMemo(() => {
  return computeExpensiveValue(a, b);
}, [a, b]);

// 4. Image optimization
import Image from 'next/image';
<Image
  src="/hero.jpg"
  width={1200}
  height={600}
  alt="Hero"
  priority  // LCP image
  placeholder="blur"
/>

// 5. Font optimization
import { Inter } from 'next/font/google';
const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-inter'
});
```

### 5. Accessibility Standards

**WCAG 2.1 Level AA Compliance (Minimum):**

| Guideline | Requirement | Implementation |
|-----------|-------------|----------------|
| **Perceivable** | Content must be presentable to users in ways they can perceive | - Alt text for all images<br>- Captions for videos<br>- Color contrast 4.5:1 minimum |
| **Operable** | UI components must be operable | - Full keyboard navigation<br>- No keyboard traps<br>- Skip to main content link<br>- Focus indicators visible |
| **Understandable** | Information and operation must be understandable | - Clear labels<br>- Error messages helpful<br>- Consistent navigation |
| **Robust** | Content must be robust enough for assistive technologies | - Valid HTML<br>- ARIA labels<br>- Semantic markup |

**Testing:**
```bash
# Automated accessibility testing
pnpm test:a11y  # Runs axe-core checks

# Manual testing checklist
- [ ] Keyboard navigation works (Tab, Shift+Tab, Enter, Esc)
- [ ] Screen reader announces all interactive elements
- [ ] Focus indicators visible on all interactive elements
- [ ] No content appears only on hover (must work on focus too)
- [ ] Form errors clearly associated with inputs
- [ ] Headings follow logical hierarchy (h1 -> h2 -> h3)
- [ ] Color is not the only means of conveying information
```

**Implementation Examples:**
```typescript
// ✅ Good: Accessible button
<button
  type="button"
  aria-label="Send message"
  onClick={handleSend}
  disabled={isLoading}
  className="focus:ring-2 focus:ring-offset-2"
>
  <SendIcon aria-hidden="true" />
  <span className="sr-only">Send message</span>
</button>

// ✅ Good: Accessible form
<form onSubmit={handleSubmit}>
  <label htmlFor="email">
    Email address
    <span className="text-red-500" aria-label="required">*</span>
  </label>
  <input
    id="email"
    type="email"
    aria-required="true"
    aria-invalid={!!errors.email}
    aria-describedby={errors.email ? "email-error" : undefined}
  />
  {errors.email && (
    <p id="email-error" role="alert" className="text-red-500">
      {errors.email.message}
    </p>
  )}
</form>

// ✅ Good: Accessible modal
<Dialog
  open={isOpen}
  onClose={handleClose}
  aria-labelledby="dialog-title"
  aria-describedby="dialog-description"
>
  <DialogTitle id="dialog-title">Confirm action</DialogTitle>
  <DialogDescription id="dialog-description">
    Are you sure you want to delete this conversation?
  </DialogDescription>
  <button onClick={handleClose}>Cancel</button>
  <button onClick={handleConfirm}>Delete</button>
</Dialog>
```

---

## 📦 Implementation Phases

### **Phase 1: Foundation & Setup** (Est. 30-45 min)

**Objective:** Establish rock-solid foundation with proper tooling and configuration

#### Tasks:

- [ ] **1.1** Initialize Next.js 15 project with TypeScript
  ```bash
  cd multi-agent-support-system
  pnpm create next-app@latest frontend \
    --typescript \
    --tailwind \
    --app \
    --src-dir=false \
    --import-alias="@/*" \
    --use-pnpm
  ```

- [ ] **1.2** Configure TypeScript in strict mode
  - Set all strict compiler options
  - Enable path aliases (`@/components`, `@/lib`, etc.)
  - Configure for Next.js App Router
  - Add type definitions for environment variables

- [ ] **1.3** Setup Tailwind CSS 4 with custom configuration
  - Install Tailwind CSS 4 (latest)
  - Configure theme (colors, fonts, spacing)
  - Add custom utilities
  - Setup dark mode (class-based strategy)

- [ ] **1.4** Install and configure ESLint (strict rules)
  - Extend recommended configs
  - Add TypeScript ESLint rules
  - Add React/JSX rules
  - Add accessibility rules (jsx-a11y)
  - Add import sorting rules

- [ ] **1.5** Setup Prettier for code formatting
  - Install Prettier
  - Configure `.prettierrc` (2 spaces, single quotes, etc.)
  - Add Prettier ESLint plugin (prevent conflicts)
  - Create `.prettierignore`

- [ ] **1.6** Configure Git hooks with Husky
  - Install Husky + lint-staged
  - Pre-commit hook: Run ESLint + Prettier on staged files
  - Pre-commit hook: Run TypeScript type checking
  - Commit-msg hook: Validate conventional commits

- [ ] **1.7** Setup commit conventions
  - Install Commitizen + Commitlint
  - Configure conventional commits
  - Add commit types (feat, fix, docs, style, refactor, test, chore)

- [ ] **1.8** Create base folder structure
  ```
  frontend/
  ├── app/
  │   ├── (auth)/
  │   ├── (dashboard)/
  │   ├── api/
  │   ├── layout.tsx
  │   └── page.tsx
  ├── components/
  │   ├── ui/          # shadcn/ui components
  │   ├── layout/      # Header, Sidebar, Footer
  │   ├── chat/        # Chat-specific components
  │   └── shared/      # Shared components
  ├── lib/
  │   ├── api/         # API client
  │   ├── auth/        # Auth utilities
  │   ├── validation/  # Zod schemas
  │   └── utils.ts     # Utility functions
  ├── hooks/           # Custom React hooks
  ├── stores/          # Zustand stores
  ├── types/           # TypeScript types
  ├── config/          # Configuration
  └── __tests__/       # Tests
  ```

- [ ] **1.9** Configure environment variables
  - Create `.env.local.example`
  - Add `NEXT_PUBLIC_API_URL` (FastAPI backend URL)
  - Add `NEXTAUTH_SECRET`, `NEXTAUTH_URL`
  - Add OAuth credentials (Google, GitHub)
  - Document all required env vars

- [ ] **1.10** Create comprehensive README.md
  - Project overview
  - Prerequisites
  - Installation instructions
  - Development workflow
  - Available scripts
  - Project structure
  - Contributing guidelines

#### Acceptance Criteria:
- ✅ Next.js 15 app runs without errors (`pnpm dev`)
- ✅ TypeScript strict mode enabled, no compilation errors
- ✅ ESLint passes with zero warnings
- ✅ Prettier formats all files consistently
- ✅ Git hooks prevent commits with lint/type errors
- ✅ All environment variables documented

#### Deliverables:
- Fully configured Next.js 15 project
- Complete tooling setup (ESLint, Prettier, Husky)
- Base folder structure
- Documentation (README.md)

---

### **Phase 2: Design System & UI Foundation** (Est. 45-60 min)

**Objective:** Build beautiful, accessible UI component library

#### Tasks:

- [ ] **2.1** Install shadcn/ui CLI and initialize
  ```bash
  pnpm dlx shadcn-ui@latest init
  ```
  - Configure with Tailwind CSS
  - Set base color (Slate)
  - Set CSS variables for theming

- [ ] **2.2** Install essential shadcn/ui components
  ```bash
  # Core components
  pnpm dlx shadcn-ui@latest add button input label textarea select

  # Layout components
  pnpm dlx shadcn-ui@latest add separator card tabs sheet dialog

  # Form components
  pnpm dlx shadcn-ui@latest add form checkbox radio-group switch

  # Feedback components
  pnpm dlx shadcn-ui@latest add toast alert progress skeleton

  # Navigation components
  pnpm dlx shadcn-ui@latest add dropdown-menu command navigation-menu

  # Data display components
  pnpm dlx shadcn-ui@latest add table badge avatar scroll-area
  ```

- [ ] **2.3** Create custom theme (ChatGPT/Claude-inspired)
  - Define color palette in `tailwind.config.ts`
  - Add custom colors (light/dark mode)
  - Configure typography (Geist font)
  - Add custom spacing/sizing values
  - Define border radius values
  - Add custom shadows

- [ ] **2.4** Setup dark/light mode theming
  - Install `next-themes`
  - Create ThemeProvider component
  - Implement theme toggle component
  - Detect system preference
  - Persist user preference (localStorage)
  - Add smooth transitions between themes

- [ ] **2.5** Install icon library (Lucide React)
  ```bash
  pnpm add lucide-react
  ```
  - Create icon wrapper component (for consistent sizing)
  - Document commonly used icons

- [ ] **2.6** Setup font optimization
  - Install Geist font (Vercel's font)
  - Configure in `app/layout.tsx`
  - Setup font variables
  - Optimize font loading (preload, display: swap)

- [ ] **2.7** Create layout components
  - **Header** component
    - Logo
    - Navigation menu
    - User profile dropdown
    - Theme toggle
    - Mobile responsive (hamburger menu)

  - **Sidebar** component
    - Conversation history
    - New conversation button
    - Filter/search conversations
    - Collapsible (desktop)
    - Slide-over (mobile)

  - **Footer** component (optional)
    - Links (Privacy, Terms, Docs)
    - Version info
    - Status indicator

- [ ] **2.8** Create shared utility components
  - **LoadingSpinner** - Consistent loading states
  - **ErrorMessage** - User-friendly error display
  - **EmptyState** - Placeholder for empty data
  - **ConfirmDialog** - Reusable confirmation modal
  - **SearchBar** - Reusable search input with debounce

- [ ] **2.9** Implement responsive design utilities
  - Mobile breakpoints (sm: 640px, md: 768px, lg: 1024px, xl: 1280px)
  - Custom hooks: `useMediaQuery`, `useBreakpoint`
  - Responsive container component
  - Mobile-first approach

- [ ] **2.10** Create Storybook for component documentation (optional but recommended)
  ```bash
  pnpm dlx storybook@latest init
  ```
  - Document all UI components
  - Add component variants
  - Add usage examples
  - Add accessibility notes

#### Acceptance Criteria:
- ✅ 20+ shadcn/ui components installed and working
- ✅ Dark/light mode toggles smoothly with persistence
- ✅ All components are responsive (mobile, tablet, desktop)
- ✅ Typography scales properly across devices
- ✅ Geist font loads optimally (no FOUT/FOIT)
- ✅ All interactive components have focus indicators
- ✅ Color contrast meets WCAG AA standards (4.5:1)

#### Deliverables:
- Complete design system
- Reusable UI components
- Layout components (Header, Sidebar, Footer)
- Theme system (dark/light mode)
- Responsive utilities

---

### **Phase 3: Authentication & Authorization** (Est. 45-60 min)

**Objective:** Implement secure, user-friendly authentication system

#### Tasks:

- [ ] **3.1** Install NextAuth.js (Auth.js v5)
  ```bash
  pnpm add next-auth@beta
  pnpm add @auth/core
  ```

- [ ] **3.2** Configure NextAuth.js
  - Create `app/api/auth/[...nextauth]/route.ts`
  - Setup JWT strategy
  - Configure session handling
  - Add CSRF protection
  - Setup secure cookies (httpOnly, secure, sameSite)

- [ ] **3.3** Implement Credentials Provider (Email/Password)
  - Create login API integration with FastAPI
  - Implement password validation
  - Add error handling (invalid credentials, network errors)
  - Implement rate limiting (prevent brute force)

- [ ] **3.4** Implement OAuth Providers
  - **Google OAuth**
    - Create Google OAuth app in Google Cloud Console
    - Configure redirect URIs
    - Add scopes (email, profile)
    - Implement provider in NextAuth

  - **GitHub OAuth**
    - Create GitHub OAuth app in GitHub Settings
    - Configure authorization callback URL
    - Add scopes (user:email)
    - Implement provider in NextAuth

- [ ] **3.5** Create authentication UI components
  - **LoginForm** component
    - Email input (with validation)
    - Password input (show/hide toggle)
    - Remember me checkbox
    - Form validation (Zod schema)
    - Loading states
    - Error messages
    - OAuth buttons (Google, GitHub)

  - **RegisterForm** component
    - Email input
    - Password input (strength indicator)
    - Confirm password input
    - Terms of service checkbox
    - Form validation
    - Loading states
    - Error messages

  - **ForgotPasswordForm** component (optional for v1)
  - **ResetPasswordForm** component (optional for v1)

- [ ] **3.6** Create authentication pages
  - `app/(auth)/login/page.tsx` - Login page
  - `app/(auth)/register/page.tsx` - Register page
  - `app/(auth)/layout.tsx` - Auth layout (centered card)
  - Redirect authenticated users to dashboard
  - Add "Sign in with Google/GitHub" buttons

- [ ] **3.7** Implement protected route middleware
  - Create `middleware.ts` in root
  - Check authentication status
  - Redirect unauthenticated users to login
  - Allow public routes (login, register, landing)
  - Add role-based access control (RBAC)

- [ ] **3.8** Create auth utilities and hooks
  - `useSession()` - Get current user session
  - `useAuth()` - Auth methods (login, logout, register)
  - `useUser()` - Get current user data
  - `usePermissions()` - Check user permissions
  - `requireAuth()` - HOC for protected components

- [ ] **3.9** Implement session management
  - Auto-refresh tokens before expiry
  - Handle token expiration gracefully
  - Logout on 401/403 errors
  - Clear local state on logout
  - Implement "Remember me" (longer session)

- [ ] **3.10** Create user profile/settings page
  - `app/(dashboard)/settings/page.tsx`
  - Display user info (email, name, avatar)
  - Update profile form
  - Change password form
  - Connected accounts (OAuth)
  - Delete account (with confirmation)

- [ ] **3.11** Implement authorization (RBAC)
  - Define user roles (admin, user)
  - Define permissions (read, write, delete)
  - Implement permission checks
  - Create permission guards
  - Add role-based UI (show/hide elements)

#### Acceptance Criteria:
- ✅ Users can register with email/password
- ✅ Users can login with email/password
- ✅ Users can login with Google OAuth
- ✅ Users can login with GitHub OAuth
- ✅ Protected routes redirect to login if unauthenticated
- ✅ Sessions persist across page refreshes
- ✅ Tokens auto-refresh before expiry
- ✅ Logout clears all session data
- ✅ Form validation provides helpful error messages
- ✅ Loading states shown during auth operations
- ✅ RBAC prevents unauthorized access

#### Deliverables:
- NextAuth.js configuration
- Login/Register pages
- OAuth integration (Google, GitHub)
- Protected route middleware
- User profile page
- Auth utilities and hooks

---

### **Phase 4: API Integration & Type Safety** (Est. 30-45 min)

**Objective:** Create type-safe API client with end-to-end type safety

#### Tasks:

- [ ] **4.1** Generate TypeScript types from FastAPI OpenAPI spec
  ```bash
  pnpm add -D openapi-typescript

  # Generate types (add to package.json scripts)
  pnpm openapi-typescript http://localhost:8000/openapi.json -o types/api.ts
  ```
  - Add npm script: `"generate:types": "openapi-typescript ..."`
  - Document in README
  - Run in CI/CD to detect schema drift

- [ ] **4.2** Setup TanStack Query (React Query)
  ```bash
  pnpm add @tanstack/react-query @tanstack/react-query-devtools
  ```
  - Create QueryClient with optimized defaults
  - Setup QueryClientProvider in root layout
  - Configure stale time, cache time, retry logic
  - Add devtools (development only)

- [ ] **4.3** Create type-safe API client
  - `lib/api/client.ts` - Base fetch wrapper
  - Add request/response interceptors
  - Add authentication (inject JWT token)
  - Add error handling (network, 4xx, 5xx)
  - Add request/response logging (development)
  - Add timeout handling
  - Type all endpoints using OpenAPI types

- [ ] **4.4** Implement API hooks for all endpoints

  **Conversation endpoints:**
  - `useConversations()` - List conversations (with pagination)
  - `useConversation(id)` - Get single conversation
  - `useCreateConversation()` - Create new conversation
  - `useDeleteConversation()` - Delete conversation
  - `useMessages(conversationId)` - Get messages
  - `useSendMessage()` - Send message (non-streaming)

  **Customer endpoints:**
  - `useCustomer(id)` - Get customer profile
  - `useUpdateCustomer()` - Update customer
  - `useCustomerInteractions(id)` - Get customer interactions

  **Analytics endpoints:**
  - `useAnalyticsOverview()` - System overview metrics
  - `useAgentPerformance()` - Agent metrics
  - `useConversationMetrics()` - Conversation analytics

  **Admin endpoints:**
  - `useBackendHealth()` - Check LLM backend health
  - `useSwitchBackend()` - Switch LLM backend
  - `useCostTracking()` - Get cost data

- [ ] **4.5** Implement optimistic updates
  - Optimistic message sending (instant UI update)
  - Rollback on error
  - Toast notification on success/failure

- [ ] **4.6** Setup API error handling
  - Create custom error classes
  - Map HTTP status codes to user-friendly messages
  - Handle network errors (offline, timeout)
  - Display error toasts
  - Log errors to Sentry

- [ ] **4.7** Implement request/response caching strategy
  - Cache conversations (5 min stale time)
  - Cache customer data (10 min stale time)
  - Cache analytics (30 sec stale time - more dynamic)
  - Infinite query for conversation list (pagination)
  - Manual invalidation on mutations

- [ ] **4.8** Create API mocks for development/testing
  - Install MSW (Mock Service Worker)
  - Create mock handlers for all endpoints
  - Setup MSW in development mode
  - Use mocks in tests
  - Document mock data structure

- [ ] **4.9** Setup API monitoring
  - Track API request duration
  - Track API error rates
  - Send metrics to analytics
  - Alert on high error rates

#### Acceptance Criteria:
- ✅ All API endpoints have corresponding hooks
- ✅ TypeScript autocomplete works for all API calls
- ✅ Invalid API calls caught at compile time
- ✅ API errors display user-friendly messages
- ✅ Optimistic updates work for message sending
- ✅ Cache strategy reduces unnecessary requests
- ✅ MSW mocks work in development
- ✅ TanStack Query devtools show cache state

#### Deliverables:
- Type-safe API client
- React Query hooks for all endpoints
- OpenAPI type generation script
- MSW mocks for development
- Error handling utilities

---

### **Phase 5: Chat Interface (Core Feature)** (Est. 60-90 min)

**Objective:** Build production-quality chat interface with real-time streaming

#### Tasks:

- [ ] **5.1** Create chat state management (Zustand)
  ```typescript
  // stores/chatStore.ts
  interface ChatStore {
    conversations: Conversation[];
    activeConversationId: string | null;
    messages: Message[];
    isStreaming: boolean;
    setActiveConversation: (id: string) => void;
    addMessage: (message: Message) => void;
    updateStreamingMessage: (chunk: string) => void;
  }
  ```

- [ ] **5.2** Implement SSE (Server-Sent Events) streaming
  - Create `useStreamingChat()` hook
  - Handle EventSource connection
  - Parse SSE events (conversation_id, thinking, intent, message, done)
  - Update UI in real-time as chunks arrive
  - Handle connection errors and reconnection
  - Implement abort mechanism (stop generation)

- [ ] **5.3** Create core chat components

  **MessageBubble component:**
  - User vs Assistant styling (different colors/alignment)
  - Avatar (user photo or agent icon)
  - Message content (markdown rendering)
  - Timestamp (shown on hover)
  - Actions: Copy, Edit, Regenerate, Delete
  - Loading state (skeleton)
  - Error state (retry button)

  **ChatInput component:**
  - Textarea with auto-resize (max 5 lines)
  - Send button (disabled when empty or streaming)
  - Stop button (visible during streaming)
  - Keyboard shortcuts (⌘+Enter to send, Esc to clear)
  - Character counter (optional)
  - File attachment (future feature)
  - Voice input (future feature)

  **StreamingMessage component:**
  - Typewriter animation effect
  - Cursor blink animation
  - Smooth text rendering

  **ThinkingIndicator component:**
  - Animated dots (...)
  - Agent name display
  - Subtle pulsing animation

  **AgentBadge component:**
  - Agent name with icon
  - Color-coded by tier
  - Tooltip with agent description

- [ ] **5.4** Implement markdown rendering
  ```bash
  pnpm add react-markdown remark-gfm remark-math rehype-katex
  ```
  - Support GitHub Flavored Markdown (GFM)
  - Support tables, task lists, strikethrough
  - Support math equations (KaTeX)
  - Sanitize HTML (prevent XSS)
  - Custom renderers for links (open in new tab)

- [ ] **5.5** Implement code syntax highlighting
  ```bash
  pnpm add shiki
  ```
  - Auto-detect language
  - Support 100+ languages
  - Use VS Code themes
  - Add copy button to code blocks
  - Show language label
  - Line numbers (optional)

- [ ] **5.6** Create conversation sidebar
  - **ConversationList component:**
    - List recent conversations (infinite scroll)
    - Show preview (first message)
    - Show timestamp (relative: "2 hours ago")
    - Highlight active conversation
    - Delete conversation (swipe action on mobile)
    - Search conversations
    - Filter by date, agent, status

  - **NewConversationButton component:**
    - Prominent button at top
    - Keyboard shortcut (⌘+N)
    - Create new conversation and navigate

- [ ] **5.7** Build main chat page
  - `app/(dashboard)/chat/page.tsx` - Default (new conversation)
  - `app/(dashboard)/chat/[id]/page.tsx` - Existing conversation
  - Three-column layout (mobile: collapsible)
    - Left: Conversation sidebar (collapsible)
    - Center: Chat messages
    - Right: Context panel (optional - customer info, KB articles)
  - Auto-scroll to bottom on new message
  - "Scroll to bottom" button when not at bottom
  - Loading states (skeleton)

- [ ] **5.8** Implement message actions
  - **Copy message** - Copy to clipboard with toast
  - **Edit message** - Edit user message and re-send
  - **Regenerate response** - Regenerate assistant message
  - **Delete message** - Remove message (with confirmation)
  - **Share conversation** - Generate shareable link (future)

- [ ] **5.9** Add keyboard shortcuts
  - `⌘+N` - New conversation
  - `⌘+K` - Command palette (search conversations/agents)
  - `⌘+Enter` - Send message
  - `Esc` - Clear input / Close modals
  - `↑` - Edit last message
  - `/` - Focus search

- [ ] **5.10** Implement conversation export
  - Export as Markdown
  - Export as JSON
  - Export as PDF (optional)
  - Download or copy to clipboard

- [ ] **5.11** Add empty states
  - New user: Welcome message, example prompts
  - No conversations: "Start your first conversation"
  - No messages: Placeholder with suggestions

- [ ] **5.12** Implement error handling
  - Network error: "Connection lost" with retry
  - API error: User-friendly message with support link
  - Streaming error: Graceful fallback to non-streaming
  - Rate limit error: "Too many requests, try again in X seconds"

#### Acceptance Criteria:
- ✅ Chat interface resembles ChatGPT/Claude quality
- ✅ Messages stream in real-time (<100ms latency)
- ✅ Markdown renders correctly (bold, lists, links, tables)
- ✅ Code blocks have syntax highlighting + copy button
- ✅ Users can create/delete conversations
- ✅ Keyboard shortcuts work
- ✅ Responsive on mobile (sidebar collapses)
- ✅ Empty states guide new users
- ✅ Error states allow recovery (retry)
- ✅ Accessibility: keyboard navigation, screen reader support

#### Deliverables:
- Complete chat interface
- SSE streaming implementation
- Markdown + code highlighting
- Conversation management
- Keyboard shortcuts
- Export functionality

---

### **Phase 6: Dashboard & Analytics** (Est. 45-60 min)

**Objective:** Create comprehensive dashboard with data visualization

#### Tasks:

- [ ] **6.1** Install charting library
  ```bash
  pnpm add recharts
  ```
  - Lightweight, React-native charts
  - Responsive by default
  - Accessible (SVG-based)

- [ ] **6.2** Create dashboard layout
  - `app/(dashboard)/page.tsx` - Dashboard home
  - Grid layout (responsive: 1 col mobile, 2-3 cols desktop)
  - Card-based sections

- [ ] **6.3** Implement key metrics cards
  - **Total Conversations** - Count with % change
  - **Active Users** - Current active users
  - **Avg Response Time** - Agent response time
  - **Resolution Rate** - % of resolved conversations
  - **Cost Today** - LLM costs (current day)
  - **Agent Usage** - Most used agents

- [ ] **6.4** Create analytics charts

  **Conversations Over Time:**
  - Line chart (last 7/30 days)
  - Trend indicator (up/down)

  **Intent Distribution:**
  - Pie chart or bar chart
  - Show top 5 intents (billing, technical, etc.)

  **Agent Performance:**
  - Table or bar chart
  - Metrics: resolution rate, avg time, interactions
  - Sort by performance

  **Customer Satisfaction:**
  - Line chart over time
  - Average rating (if feedback implemented)

  **LLM Cost Breakdown:**
  - Stacked bar chart (by backend: Claude, vLLM)
  - Daily/weekly/monthly views

- [ ] **6.5** Build analytics page
  - `app/(dashboard)/analytics/page.tsx`
  - More detailed charts than dashboard
  - Date range picker (last 7/30/90 days, custom)
  - Export data (CSV, JSON)
  - Filters (agent, intent, customer)

- [ ] **6.6** Create conversation history page
  - `app/(dashboard)/conversations/page.tsx`
  - Data table with all conversations
  - Columns: Customer, Intent, Agent, Status, Time, Actions
  - Search (by customer, message content)
  - Filter (by status, date, agent)
  - Pagination or infinite scroll
  - Bulk actions (delete, export)

- [ ] **6.7** Implement customer management page
  - `app/(dashboard)/customers/page.tsx`
  - List all customers (table)
  - Columns: Name, Email, Subscription, LTV, Last Active
  - Click to view customer details
  - Search and filter

  - `app/(dashboard)/customers/[id]/page.tsx`
  - Customer profile
  - Conversation history
  - Subscription details
  - Support tickets/interactions
  - Analytics (usage over time)

- [ ] **6.8** Build admin panel
  - `app/(dashboard)/admin/page.tsx` (admin role only)
  - **LLM Backend Management:**
    - Current backend status (Anthropic, vLLM)
    - Health check status
    - Switch backend button
    - Backend configuration

  - **Cost Tracking:**
    - Daily/weekly/monthly spend
    - Budget alerts
    - Cost per conversation
    - Token usage stats

  - **System Health:**
    - API uptime
    - Database health
    - Redis health
    - Error rates

- [ ] **6.9** Implement real-time updates
  - Use TanStack Query refetchInterval
  - WebSocket for real-time metrics (future)
  - Live conversation counter
  - Live cost tracker

- [ ] **6.10** Add data export functionality
  - Export conversations (CSV, JSON)
  - Export analytics (CSV, PDF)
  - Export customer list (CSV)
  - Scheduled reports (future)

#### Acceptance Criteria:
- ✅ Dashboard loads in <2 seconds
- ✅ Charts are responsive and accessible
- ✅ Data table supports search, filter, sort, pagination
- ✅ Admin panel restricted to admin users only
- ✅ Real-time metrics update automatically
- ✅ Export functionality works for all data types
- ✅ Mobile-friendly responsive design

#### Deliverables:
- Dashboard page with key metrics
- Analytics page with detailed charts
- Conversation history page
- Customer management pages
- Admin panel

---

### **Phase 7: Testing & Quality Assurance** (Est. 45-60 min)

**Objective:** Ensure code quality, reliability, and maintainability

#### Tasks:

- [ ] **7.1** Setup Vitest
  ```bash
  pnpm add -D vitest @vitejs/plugin-react jsdom
  pnpm add -D @testing-library/react @testing-library/jest-dom
  pnpm add -D @testing-library/user-event
  ```
  - Configure `vitest.config.ts`
  - Setup test utilities
  - Add coverage reporter

- [ ] **7.2** Write unit tests (Vitest)

  **Utility functions:**
  - `lib/utils.ts` - Test all utility functions
  - `lib/validation.ts` - Test Zod schemas
  - `lib/api/client.ts` - Test API client logic

  **Custom hooks:**
  - `useDebounce()` - Test debouncing logic
  - `useMediaQuery()` - Test breakpoint detection
  - `useLocalStorage()` - Test storage operations

- [ ] **7.3** Write component tests (React Testing Library)

  **UI Components:**
  - `Button` - Test variants, disabled state, onClick
  - `Input` - Test validation, error states
  - `Form` - Test submission, validation errors

  **Feature Components:**
  - `LoginForm` - Test validation, submission, error handling
  - `MessageBubble` - Test rendering user/assistant messages
  - `ChatInput` - Test message sending, keyboard shortcuts
  - `ConversationList` - Test filtering, selection

  **Testing principles:**
  - Test user behavior, not implementation
  - Use `screen.getByRole()` for accessibility
  - Test loading/error states
  - Mock API calls with MSW

- [ ] **7.4** Setup Mock Service Worker (MSW)
  ```bash
  pnpm add -D msw
  ```
  - Create mock handlers for all API endpoints
  - Mock successful responses
  - Mock error responses (4xx, 5xx)
  - Setup in tests and Storybook

- [ ] **7.5** Setup Playwright for E2E testing
  ```bash
  pnpm create playwright
  ```
  - Configure Playwright
  - Setup test browsers (Chromium, Firefox, WebKit)
  - Add screenshots/videos on failure

- [ ] **7.6** Write E2E tests (Playwright)

  **Critical user flows:**
  - **Authentication flow:**
    - User can register
    - User can login
    - User can logout
    - Protected routes redirect to login

  - **Chat flow:**
    - User can create new conversation
    - User can send message
    - User receives streaming response
    - User can view conversation history
    - User can delete conversation

  - **Analytics flow:**
    - User can view dashboard
    - Charts load correctly
    - Data exports work

- [ ] **7.7** Implement accessibility testing
  ```bash
  pnpm add -D @axe-core/playwright
  ```
  - Run axe-core in Playwright tests
  - Test keyboard navigation
  - Test screen reader announcements
  - Test color contrast
  - Test focus management

- [ ] **7.8** Setup test coverage reporting
  - Configure Vitest coverage (v8)
  - Set coverage thresholds:
    - Statements: 80%
    - Branches: 75%
    - Functions: 80%
    - Lines: 80%
  - Generate coverage reports (HTML, JSON)
  - Upload to Codecov (optional)

- [ ] **7.9** Add Visual Regression Testing (optional)
  ```bash
  pnpm add -D @playwright/test
  ```
  - Capture screenshots of key pages
  - Compare with baselines
  - Detect unintended UI changes

- [ ] **7.10** Create test documentation
  - Document testing strategy
  - Provide examples for each test type
  - Explain how to run tests
  - Explain how to update snapshots

#### Acceptance Criteria:
- ✅ Unit test coverage >80% for critical code
- ✅ Component tests cover all user interactions
- ✅ E2E tests pass for critical flows
- ✅ Accessibility tests pass (zero violations)
- ✅ All tests run in CI/CD
- ✅ Tests are fast (<30 seconds for unit, <5 min for E2E)

#### Deliverables:
- Comprehensive test suite (unit, component, E2E)
- MSW mocks for all endpoints
- Accessibility tests
- Test coverage reports
- Test documentation

---

### **Phase 8: Deployment & DevOps** (Est. 30-45 min)

**Objective:** Deploy to Oracle Cloud with production-grade infrastructure

#### Tasks:

- [ ] **8.1** Create optimized production Dockerfile
  ```dockerfile
  # Multi-stage build for minimal image size
  FROM node:22-alpine AS builder
  WORKDIR /app

  # Install dependencies
  COPY package.json pnpm-lock.yaml ./
  RUN corepack enable pnpm && pnpm install --frozen-lockfile

  # Build app
  COPY . .
  RUN pnpm build

  # Production image
  FROM node:22-alpine AS runner
  WORKDIR /app
  ENV NODE_ENV production

  # Copy built app
  COPY --from=builder /app/public ./public
  COPY --from=builder /app/.next/standalone ./
  COPY --from=builder /app/.next/static ./.next/static

  EXPOSE 3000
  CMD ["node", "server.js"]
  ```

- [ ] **8.2** Optimize Next.js for production
  - Enable standalone output (reduces image size)
  - Configure image optimization
  - Enable SWC minification
  - Configure caching headers
  - Add security headers
  - Enable compression (Brotli/Gzip)

- [ ] **8.3** Update docker-compose.yml
  - Add frontend service
  - Configure environment variables
  - Setup networking (app-network)
  - Add health checks
  - Configure resource limits (memory, CPU)
  - Add restart policy

- [ ] **8.4** Configure Nginx reverse proxy
  - Route `yourdomain.com` → Frontend (port 3000)
  - Route `api.yourdomain.com` → Backend (port 8000)
  - Add SSL/TLS termination
  - Configure caching (static assets)
  - Add rate limiting (10 req/sec)
  - Add security headers (HSTS, CSP, X-Frame-Options)
  - Enable Brotli/Gzip compression

- [ ] **8.5** Setup SSL certificates (Let's Encrypt)
  - Update certbot configuration
  - Generate certificates for frontend domain
  - Auto-renewal configuration
  - Redirect HTTP → HTTPS

- [ ] **8.6** Add frontend monitoring to Prometheus
  - Expose Next.js metrics endpoint
  - Add Prometheus scrape config
  - Track key metrics:
    - Request rate
    - Response time
    - Error rate
    - Active connections

- [ ] **8.7** Create Grafana dashboard for frontend
  - Frontend performance metrics
  - API response times
  - Error rates
  - User analytics (from Umami)
  - Combined backend + frontend dashboard

- [ ] **8.8** Setup Umami analytics
  - Add Umami service to docker-compose
  - Configure database (PostgreSQL)
  - Add tracking script to app
  - Create dashboards

- [ ] **8.9** Configure Sentry error tracking
  ```bash
  pnpm add @sentry/nextjs
  ```
  - Initialize Sentry SDK
  - Configure error reporting
  - Add source maps upload
  - Setup performance monitoring
  - Configure release tracking

- [ ] **8.10** Setup CI/CD pipeline (GitHub Actions)

  **`.github/workflows/frontend-ci.yml`:**
  ```yaml
  name: Frontend CI

  on:
    push:
      branches: [main, develop]
      paths: ['frontend/**']
    pull_request:
      paths: ['frontend/**']

  jobs:
    test:
      runs-on: ubuntu-latest
      steps:
        - Checkout code
        - Setup Node.js 22
        - Install pnpm
        - Install dependencies
        - Run TypeScript check
        - Run ESLint
        - Run Prettier check
        - Run unit tests with coverage
        - Run E2E tests
        - Upload coverage to Codecov

    build:
      runs-on: ubuntu-latest
      needs: test
      steps:
        - Checkout code
        - Setup Docker Buildx
        - Build Docker image
        - Push to GitHub Container Registry

    deploy:
      runs-on: ubuntu-latest
      needs: build
      if: github.ref == 'refs/heads/main'
      steps:
        - SSH to Oracle Cloud instance
        - Pull latest image
        - Run database migrations (if any)
        - Restart containers
        - Run health checks
        - Notify (Slack, Discord, etc.)
  ```

- [ ] **8.11** Create deployment scripts
  - `scripts/deploy-frontend.sh` - Deploy frontend only
  - `scripts/build-frontend.sh` - Build production image
  - `scripts/health-check-frontend.sh` - Verify deployment
  - Update existing `deploy.sh` to include frontend

- [ ] **8.12** Setup environment variable management
  - Use Doppler (or similar) for secrets
  - Document all required env vars
  - Add validation for missing vars
  - Separate dev/staging/prod configs

- [ ] **8.13** Configure CDN (optional - Cloudflare)
  - Setup Cloudflare DNS
  - Enable CDN caching for static assets
  - Configure cache rules
  - Enable minification
  - Setup Web Application Firewall (WAF)

- [ ] **8.14** Create deployment documentation
  - Prerequisites (Oracle Cloud account, DNS setup)
  - Step-by-step deployment guide
  - Environment variable reference
  - Troubleshooting common issues
  - Rollback procedure
  - Monitoring and alerting setup

#### Acceptance Criteria:
- ✅ Docker image builds successfully (<500MB)
- ✅ Frontend accessible via HTTPS (SSL A+ rating)
- ✅ CI/CD pipeline passes all checks
- ✅ Deployments are automated (push to main → deploy)
- ✅ Monitoring dashboards show frontend metrics
- ✅ Error tracking captures frontend errors
- ✅ Analytics tracks user behavior
- ✅ Health checks verify deployment success
- ✅ Rollback procedure documented and tested

#### Deliverables:
- Production Dockerfile
- Updated docker-compose.yml
- Nginx configuration
- CI/CD pipeline (GitHub Actions)
- Deployment scripts
- Monitoring dashboards (Grafana)
- Deployment documentation

---

### **Phase 9: Documentation & Polish** (Est. 20-30 min)

**Objective:** Create comprehensive documentation and final polish

#### Tasks:

- [ ] **9.1** Write comprehensive README.md
  - Project overview
  - Features list
  - Screenshots/GIFs
  - Tech stack
  - Prerequisites
  - Installation guide (local development)
  - Environment variables
  - Available scripts
  - Project structure
  - Development workflow
  - Testing guide
  - Deployment guide
  - Contributing guidelines
  - License
  - Credits

- [ ] **9.2** Create frontend architecture documentation
  - `docs/frontend/ARCHITECTURE.md`
  - High-level overview
  - Folder structure explanation
  - Data flow diagrams
  - State management strategy
  - API integration approach
  - Component hierarchy
  - Design system documentation

- [ ] **9.3** Document component library
  - Create Storybook (if not done in Phase 2)
  - Document all reusable components
  - Provide usage examples
  - Document props and variants
  - Add accessibility notes
  - Add best practices

- [ ] **9.4** Create API integration guide
  - `docs/frontend/API_INTEGRATION.md`
  - How to add new endpoints
  - How to regenerate types
  - Caching strategy
  - Error handling patterns
  - Example API hook implementations

- [ ] **9.5** Write testing documentation
  - `docs/frontend/TESTING.md`
  - Testing philosophy
  - How to write unit tests
  - How to write component tests
  - How to write E2E tests
  - How to run tests
  - How to update snapshots
  - Coverage requirements

- [ ] **9.6** Create deployment runbook
  - `docs/frontend/DEPLOYMENT.md`
  - Pre-deployment checklist
  - Deployment steps
  - Post-deployment verification
  - Monitoring and alerts
  - Rollback procedure
  - Common issues and solutions

- [ ] **9.7** Document environment variables
  - Create `.env.example` with all variables
  - Add inline comments explaining each variable
  - Document required vs optional
  - Document default values
  - Security considerations

- [ ] **9.8** Create troubleshooting guide
  - `docs/frontend/TROUBLESHOOTING.md`
  - Common errors and solutions
  - Build errors
  - Runtime errors
  - Deployment errors
  - Performance issues
  - Browser compatibility issues

- [ ] **9.9** Add inline code documentation
  - JSDoc comments for complex functions
  - Document non-obvious code
  - Add TODO/FIXME comments for tech debt
  - Document design decisions (ADRs - Architecture Decision Records)

- [ ] **9.10** Create changelog
  - `CHANGELOG.md`
  - Document all changes by version
  - Follow Keep a Changelog format
  - Link to issues/PRs

- [ ] **9.11** Final polish
  - Remove console.logs
  - Remove unused code/imports
  - Fix all ESLint warnings
  - Optimize bundle size (analyze with Bundle Analyzer)
  - Run Lighthouse audit (aim for 100 scores)
  - Test on multiple browsers (Chrome, Firefox, Safari, Edge)
  - Test on multiple devices (mobile, tablet, desktop)
  - Fix any remaining a11y issues

- [ ] **9.12** Create demo video/screenshots
  - Record demo video (2-3 minutes)
  - Take high-quality screenshots
  - Add to README.md
  - Upload to YouTube (if public repo)

#### Acceptance Criteria:
- ✅ README is comprehensive and easy to follow
- ✅ All major features documented
- ✅ Code is well-commented
- ✅ No console errors or warnings
- ✅ Lighthouse score 100 (or >95 minimum)
- ✅ Works on all major browsers
- ✅ Works on mobile, tablet, desktop
- ✅ Zero accessibility violations

#### Deliverables:
- Comprehensive documentation
- Storybook (component library)
- Demo video + screenshots
- Polished, production-ready code

---

## 📊 Success Metrics

### Performance Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Lighthouse Performance** | 100 | Chrome DevTools |
| **First Contentful Paint (FCP)** | <1.0s | Lighthouse |
| **Largest Contentful Paint (LCP)** | <2.0s | Lighthouse |
| **Time to Interactive (TTI)** | <3.0s | Lighthouse |
| **Cumulative Layout Shift (CLS)** | <0.1 | Lighthouse |
| **Total Blocking Time (TBT)** | <200ms | Lighthouse |
| **Bundle Size (gzipped)** | <200KB | Next.js build output |
| **Time to First Byte (TTFB)** | <600ms | WebPageTest |

### Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **TypeScript Strict Mode** | 100% | tsconfig.json |
| **ESLint Errors** | 0 | ESLint report |
| **ESLint Warnings** | 0 | ESLint report |
| **Test Coverage (Statements)** | >80% | Vitest coverage |
| **Test Coverage (Branches)** | >75% | Vitest coverage |
| **Accessibility Score** | 100 | Lighthouse |
| **axe-core Violations** | 0 | Playwright + axe |
| **Console Errors (Production)** | 0 | Manual check |

### User Experience Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Mobile Responsive** | 100% | Manual testing |
| **Browser Compatibility** | Chrome, Firefox, Safari, Edge (latest 2 versions) | BrowserStack |
| **WCAG Compliance** | Level AA | Manual + automated testing |
| **Keyboard Navigation** | 100% functional | Manual testing |
| **Screen Reader Support** | Full support | Manual testing (NVDA, VoiceOver) |

### Deployment Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Build Time** | <5 minutes | CI/CD logs |
| **Docker Image Size** | <500MB | Docker images |
| **Deployment Time** | <10 minutes | CI/CD logs |
| **Uptime** | >99.9% | Prometheus/Grafana |
| **Error Rate** | <0.1% | Sentry |

---

## 🔗 Dependencies & Prerequisites

### Development Environment

- **Node.js** 22 LTS (required)
- **pnpm** 9.x (recommended) or npm 10.x
- **Git** 2.x
- **VS Code** (recommended) with extensions:
  - ESLint
  - Prettier
  - TypeScript and JavaScript Language Features
  - Tailwind CSS IntelliSense
  - GitLens

### Backend Requirements

- FastAPI backend running on `localhost:8000` (or configured URL)
- OpenAPI spec available at `/openapi.json`
- Authentication endpoints (`/api/auth/*`)
- Chat endpoints (`/api/chat/*`, `/api/conversations/*`)
- Analytics endpoints (`/api/analytics/*`)
- Admin endpoints (`/api/admin/*`)

### External Services

- **OAuth Providers:**
  - Google OAuth 2.0 (Client ID + Secret)
  - GitHub OAuth (Client ID + Secret)

- **Analytics (optional but recommended):**
  - Umami instance (self-hosted)
  - Sentry account (free tier)

### Infrastructure

- **Oracle Cloud Always Free instance:**
  - 4 vCPUs (ARM64)
  - 24GB RAM
  - 200GB storage
  - 10TB bandwidth/month

- **Domain name** (for production)
- **SSL certificate** (Let's Encrypt - free)

---

## 🚨 Risk Assessment & Mitigation

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **API schema changes break frontend** | Medium | High | - Auto-generate types from OpenAPI<br>- Run type generation in CI<br>- Version API |
| **Bundle size grows too large** | Medium | Medium | - Monitor with Bundle Analyzer<br>- Code splitting<br>- Tree shaking<br>- Dynamic imports |
| **Performance degradation** | Low | High | - Regular Lighthouse audits<br>- Performance budgets in CI<br>- Monitoring (Sentry) |
| **Security vulnerabilities** | Low | High | - Dependency scanning (Snyk, Dependabot)<br>- Regular updates<br>- Security headers<br>- Input validation |
| **Browser compatibility issues** | Low | Medium | - Test on BrowserStack<br>- Use PostCSS/Autoprefixer<br>- Progressive enhancement |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Oracle Cloud outage** | Low | High | - Monitor uptime (UptimeRobot)<br>- Document recovery procedure<br>- Consider backup hosting |
| **SSL certificate expiration** | Low | Medium | - Auto-renewal via Certbot<br>- Monitoring alerts<br>- Manual backup process |
| **Deployment failures** | Medium | Medium | - Automated rollback<br>- Canary deployments<br>- Health checks<br>- Blue-green deployment |
| **Data loss** | Low | High | - Regular backups (daily)<br>- Test restore procedure<br>- Replicate critical data |

---

## 📚 References & Resources

### Official Documentation

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [TanStack Query Documentation](https://tanstack.com/query/latest)
- [Vitest Documentation](https://vitest.dev)
- [Playwright Documentation](https://playwright.dev)

### Learning Resources

- [Next.js Learn](https://nextjs.org/learn) - Official Next.js tutorial
- [React Testing Library Guide](https://testing-library.com/docs/react-testing-library/intro/)
- [Web.dev](https://web.dev) - Web best practices (Google)
- [MDN Web Docs](https://developer.mozilla.org) - Web standards

### Tools & Services

- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Performance auditing
- [WebPageTest](https://www.webpagetest.org) - Performance testing
- [BrowserStack](https://www.browserstack.com) - Cross-browser testing
- [Sentry](https://sentry.io) - Error tracking
- [Umami](https://umami.is) - Analytics

---

## 🎯 Definition of Done

A phase is considered complete when:

- ✅ All tasks in the phase are completed
- ✅ All acceptance criteria are met
- ✅ Code passes all quality checks (TypeScript, ESLint, Prettier)
- ✅ Tests are written and passing (unit, component, E2E as applicable)
- ✅ Code is reviewed (self-review minimum, peer review recommended)
- ✅ Documentation is updated
- ✅ Changes are committed with conventional commit messages
- ✅ Feature is tested in development environment
- ✅ No regressions introduced (existing features still work)

The entire project is considered complete when:

- ✅ All 9 phases are complete
- ✅ All success metrics are met
- ✅ Production deployment successful
- ✅ Monitoring and alerting configured
- ✅ Documentation comprehensive
- ✅ Demo video/screenshots created
- ✅ Project is production-ready

---

## 📞 Support & Communication

**Issue Tracker:** GitHub Issues (this repository)
**Documentation:** `/docs/frontend/`
**Questions:** GitHub Discussions or team chat

---

## 📝 Notes

- This implementation plan follows industry best practices and enterprise-grade standards
- All technology choices are battle-tested in production by leading companies
- Zero compromises on code quality, performance, or accessibility
- 100% free infrastructure (Oracle Cloud Always Free)
- Designed for long-term maintainability and scalability
- Built with the same standards as ChatGPT, Claude, and other top-tier applications

---

**Let's build something amazing! 🚀**
