# Library Directory

Core utilities and shared logic used across the application.

## Structure

```
lib/
├── api/          # API client and data fetching utilities
├── validation/   # Zod schemas and validation functions
├── utils/        # General utility functions
└── utils.ts      # Main utility functions (cn, debounce, etc.)
```

## Key Files

- **utils.ts** - Common utility functions
  - `cn()` - Tailwind class merging
  - `formatRelativeTime()` - Date formatting
  - `debounce()` - Function debouncing
  - `truncate()` - String truncation

## Usage

```typescript
import { cn } from "@/lib/utils";

// Merge Tailwind classes
const className = cn("px-4 py-2", isActive && "bg-blue-500");
```
