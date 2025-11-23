# Multi-Agent Support System - Frontend

built with Next.js 16, React 19, TypeScript, and Tailwind CSS 4.

## 🚀 Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16.0.3 | React framework with App Router, RSC, Turbopack |
| **React** | 19.2.0 | UI library with improved concurrent rendering |
| **TypeScript** | 5.9.3 | Type-safe JavaScript with strict mode |
| **Tailwind CSS** | 4.1.17 | Utility-first CSS framework |
| **pnpm** | 10.23.0 | Fast, efficient package manager |

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── (auth)/            # Authentication routes (login, register)
│   ├── (dashboard)/       # Protected dashboard routes
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Landing page
│   └── globals.css        # Global styles + design system
│
├── components/            # React components
│   ├── ui/               # shadcn/ui components (buttons, inputs, etc.)
│   ├── layout/           # Header, Sidebar, Footer
│   ├── chat/             # Chat-specific components
│   └── shared/           # Shared components
│
├── lib/                   # Core utilities
│   ├── api/              # API client & hooks
│   ├── validation/       # Zod schemas
│   ├── utils/            # Helper functions
│   └── utils.ts          # Main utilities (cn, debounce, etc.)
│
├── hooks/                 # Custom React hooks
├── stores/                # Zustand state management
│   ├── authStore.ts      # Authentication state
│   ├── chatStore.ts      # Chat state
│   └── uiStore.ts        # UI state (theme, sidebar, etc.)
│
├── types/                 # TypeScript type definitions
│   └── global.d.ts       # Global type declarations
│
├── config/                # Configuration
│   └── site.ts           # Site metadata & navigation
│
├── __tests__/            # Test files
│
├── public/               # Static assets
│
├── .env.example          # Environment variables template
├── tsconfig.json         # TypeScript configuration
├── tailwind.config.ts    # Tailwind CSS configuration
├── eslint.config.mjs     # ESLint rules
├── .prettierrc           # Prettier configuration
└── package.json          # Dependencies & scripts
```

## 🛠️ Getting Started

### Prerequisites

- **Node.js** 22+ LTS
- **pnpm** 10+ (or npm 10+)
- Backend API running at `http://localhost:8000`

### Installation

```bash
# Install dependencies
pnpm install

# Copy environment variables
cp .env.example .env.local

# Edit .env.local with your values
```

### Development

```bash
# Start development server
pnpm dev

# Open http://localhost:3000 in your browser
```

### Available Scripts

```bash
pnpm dev          # Start development server (with Turbopack)
pnpm build        # Build for production
pnpm start        # Start production server
pnpm lint         # Run ESLint
pnpm lint:fix     # Fix ESLint errors automatically
pnpm format       # Format code with Prettier
pnpm format:check # Check code formatting
pnpm type-check   # Run TypeScript type checking
pnpm validate     # Run all checks (type-check + lint + format)
```

## 🎨 Design System

### Colors (ChatGPT/Claude-Inspired)

**Light Mode:**
- Background: `#ffffff`
- Surface: `#f7f7f8`
- Text: `#1f1f1f`
- Accent: `#10a37f` (ChatGPT green)

**Dark Mode:**
- Background: `#212121`
- Surface: `#2a2a2a`
- Text: `#ececec`
- Accent: `#19c37d`

### Typography

- **Font:** Geist Sans & Geist Mono (Vercel's fonts)
- **Scale:** 8px base (0.5rem, 1rem, 1.5rem, 2rem, etc.)

### Components

All UI components use:
- **Tailwind CSS** for styling
- **Radix UI** for accessible primitives (via shadcn/ui)
- **Framer Motion** for animations

## 🔧 Configuration

### TypeScript (Ultra-Strict Mode)

17+ strict compiler options enabled:
- `noUncheckedIndexedAccess`
- `noImplicitAny`
- `strictNullChecks`
- `noUnusedLocals`
- And more...

### ESLint (Enterprise Rules)

- TypeScript strict rules
- React best practices
- Accessibility (WCAG 2.1 AA)
- Import organization
- Code quality standards

### Prettier (Consistent Formatting)

- 2 spaces indentation
- Double quotes
- Semicolons
- 80 character line width

## 🌍 Environment Variables

Required variables (see `.env.example`):

```bash
# Application URLs
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000

# Authentication
NEXTAUTH_SECRET=<generate-with-openssl-rand>
NEXTAUTH_URL=http://localhost:3000
```

Optional variables:
- Google/GitHub OAuth credentials
- Analytics (Umami)
- Error tracking (Sentry)

## 🧪 Testing

```bash
# Run unit tests
pnpm test

# Run tests with coverage
pnpm test:coverage

# Run E2E tests
pnpm test:e2e
```

## 📦 Building for Production

```bash
# Create optimized production build
pnpm build

# Preview production build locally
pnpm start

# Check for errors
pnpm lint && pnpm type-check
```

### Code Organization

- ✅ **Feature-based structure** (not type-based)
- ✅ **Colocate related files** (components, hooks, types together)
- ✅ **Use path aliases** (`@/components`, `@/lib`, etc.)

### Component Patterns

- ✅ **Server Components by default** (use `'use client'` only when needed)
- ✅ **Composition over props drilling** (use context/stores)
- ✅ **Extract reusable logic** into custom hooks

### Performance

- ✅ **Code splitting** via dynamic imports
- ✅ **Image optimization** with `next/image`
- ✅ **Font optimization** with `next/font`
- ✅ **Bundle analysis** with `@next/bundle-analyzer`

### Accessibility

- ✅ **Semantic HTML** (proper heading hierarchy)
- ✅ **Keyboard navigation** (focus management)
- ✅ **ARIA labels** (for screen readers)
- ✅ **Color contrast** (4.5:1 minimum)

## 📚 Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [shadcn/ui](https://ui.shadcn.com)

## 🐛 Troubleshooting

### Port already in use

```bash
# Use different port
pnpm dev -p 3001
```

### Module not found

```bash
# Clear cache and reinstall
rm -rf node_modules .next
pnpm install
```

### Type errors

```bash
# Regenerate types
pnpm type-check
```

## 📝 License

Same as parent project (see root LICENSE file).
