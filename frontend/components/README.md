# Components

Production-ready React components for the Multi-Agent Support System.

## Structure

```
components/
├── ui/                    # Base UI components (shadcn/ui style)
│   ├── button.tsx        # Button with variants
│   ├── input.tsx         # Text input
│   ├── label.tsx         # Form label
│   ├── textarea.tsx      # Multi-line text input
│   ├── card.tsx          # Card container
│   ├── badge.tsx         # Badge/tag component
│   ├── avatar.tsx        # User avatar
│   └── separator.tsx     # Visual separator
│
├── layout/                # Layout components
│   └── header.tsx        # Application header
│
├── theme-provider.tsx    # Dark/light mode provider
└── theme-toggle.tsx      # Theme switcher button
```

## UI Components

### Button
```tsx
import { Button } from "@/components/ui/button";

<Button variant="default">Click me</Button>
<Button variant="destructive">Delete</Button>
<Button variant="outline">Cancel</Button>
<Button variant="ghost">Ghost</Button>
<Button size="sm">Small</Button>
<Button size="lg">Large</Button>
```

### Input
```tsx
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

<Label htmlFor="email">Email</Label>
<Input id="email" type="email" placeholder="Enter your email" />
```

### Card
```tsx
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";

<Card>
  <CardHeader>
    <CardTitle>Card Title</CardTitle>
    <CardDescription>Card description</CardDescription>
  </CardHeader>
  <CardContent>
    Card content goes here
  </CardContent>
</Card>
```

## Theme System

### Theme Provider
Wrap your app with `ThemeProvider` (already done in `app/layout.tsx`):

```tsx
import { ThemeProvider } from "@/components/theme-provider";

<ThemeProvider>{children}</ThemeProvider>
```

### Theme Toggle
```tsx
import { ThemeToggle } from "@/components/theme-toggle";

<ThemeToggle />
```

## Layout Components

### Header
```tsx
import { Header } from "@/components/layout/header";

<Header />
```

## Best Practices

1. **Use Composition** - Build complex components from simple ones
2. **Follow Accessibility** - All components have ARIA labels and keyboard navigation
3. **Type Safety** - All components are fully typed with TypeScript
4. **Consistent Styling** - Use Tailwind classes and our design tokens
5. **Performance** - Components use React.forwardRef for better performance

## Adding New Components

1. Create component file in appropriate directory
2. Use `cn()` utility for class merging
3. Export component with TypeScript types
4. Add documentation in this README
5. Write tests for the component

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Radix UI Primitives](https://www.radix-ui.com/primitives)
- [Lucide Icons](https://lucide.dev)
- [Framer Motion](https://www.framer.com/motion/)
