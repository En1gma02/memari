# Frontend Documentation

## Overview
The frontend is a **Next.js 16.1.1** application with **React 19.2.3**, styled using **shadcn/ui** components and **Tailwind CSS v4**. It uses **Bun** as the package manager and runtime.

## Initial Setup Command
The project was initialized using the following shadcn preset:
```bash
bunx --bun shadcn@latest create --preset "https://ui.shadcn.com/init?base=base&style=nova&baseColor=neutral&theme=emerald&iconLibrary=lucide&font=figtree&menuAccent=subtle&menuColor=default&radius=small&template=next" --template next
```

### Preset Configuration Breakdown:
- **Base**: `base` - Base UI framework
- **Style**: `nova` - Modern, polished design system variant
- **Base Color**: `neutral` - Neutral color palette
- **Theme**: `emerald` - Emerald green as the primary theme color
- **Icon Library**: `lucide` - Using Lucide icons
- **Font**: `figtree` - Figtree as the primary font family
- **Menu Accent**: `subtle` - Subtle menu accent style
- **Menu Color**: `default` - Default menu color scheme
- **Radius**: `small` - Small border radius (0.45rem)
- **Template**: `next` - Next.js project template

---

## Project Structure

```
frontend/
├── app/                          # Next.js 16 App Router
│   ├── favicon.ico              # App favicon
│   ├── globals.css              # Global styles and Tailwind configuration
│   ├── layout.tsx               # Root layout component
│   └── page.tsx                 # Home page (renders ComponentExample)
├── components/                   # React components
│   ├── ui/                      # shadcn/ui components
│   │   ├── alert-dialog.tsx
│   │   ├── badge.tsx
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── combobox.tsx
│   │   ├── dropdown-menu.tsx
│   │   ├── field.tsx
│   │   ├── input-group.tsx
│   │   ├── input.tsx
│   │   ├── label.tsx
│   │   ├── select.tsx
│   │   ├── separator.tsx
│   │   └── textarea.tsx
│   ├── component-example.tsx    # Example component showcasing UI elements
│   └── example.tsx              # Additional example component
├── lib/                         # Utility functions
│   └── utils.ts                 # Contains cn() utility for className merging
├── public/                      # Static assets
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── .gitignore                   # Git ignore rules
├── .next/                       # Next.js build output (generated)
├── bun.lock                     # Bun lockfile
├── components.json              # shadcn/ui configuration
├── eslint.config.mjs            # ESLint configuration
├── next.config.ts               # Next.js configuration
├── next-env.d.ts                # Next.js TypeScript declarations
├── node_modules/                # Dependencies
├── package.json                 # Project dependencies and scripts
├── postcss.config.mjs           # PostCSS configuration for Tailwind
├── README.md                    # Frontend-specific readme
└── tsconfig.json                # TypeScript configuration
```

---

## Key Configuration Files

### `package.json`
```json
{
  "name": "memari",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "eslint"
  },
  "dependencies": {
    "@base-ui/react": "^1.0.0",           // Base UI primitives
    "class-variance-authority": "^0.7.1", // CVA for variant management
    "clsx": "^2.1.1",                     // Conditional className utility
    "lucide-react": "^0.562.0",           // Lucide icon library
    "next": "16.1.1",                     // Next.js framework
    "react": "19.2.3",                    // React library
    "react-dom": "19.2.3",                // React DOM
    "shadcn": "^3.6.2",                   // shadcn/ui CLI and components
    "tailwind-merge": "^3.4.0",           // Tailwind class merging
    "tw-animate-css": "^1.4.0"            // CSS animations for Tailwind
  },
  "devDependencies": {
    "@tailwindcss/postcss": "^4",         // Tailwind CSS v4 PostCSS plugin
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "16.1.1",
    "tailwindcss": "^4",                  // Tailwind CSS v4
    "typescript": "^5"
  }
}
```

**Note**: Uses Bun-specific fields `ignoreScripts` and `trustedDependencies` for `sharp` and `unrs-resolver`.

### `components.json` (shadcn/ui config)
```json
{
  "$schema": "https://ui.shadcn.com/schema.json",
  "style": "base-nova",              // Nova style variant
  "rsc": true,                       // React Server Components enabled
  "tsx": true,                       // TypeScript + JSX
  "tailwind": {
    "config": "",                    // Using inline Tailwind config in globals.css
    "css": "app/globals.css",
    "baseColor": "neutral",
    "cssVariables": true,            // Using CSS variables for theming
    "prefix": ""                     // No class prefix
  },
  "iconLibrary": "lucide",
  "aliases": {
    "components": "@/components",
    "utils": "@/lib/utils",
    "ui": "@/components/ui",
    "lib": "@/lib",
    "hooks": "@/hooks"
  },
  "menuColor": "default",
  "menuAccent": "subtle"
}
```

### `tsconfig.json`
- **Target**: ES2017
- **Module**: ESNext with bundler resolution
- **Strict mode**: Enabled
- **Path alias**: `@/*` maps to project root
- **JSX**: `react-jsx` (automatic runtime)

### `next.config.ts`
Basic Next.js configuration with no custom options currently enabled.

### `eslint.config.mjs`
Uses Next.js recommended ESLint configs:
- `eslint-config-next/core-web-vitals`
- `eslint-config-next/typescript`
- Ignores: `.next/`, `out/`, `build/`, `next-env.d.ts`

### `postcss.config.mjs`
Uses `@tailwindcss/postcss` plugin for Tailwind CSS v4 processing.

---

## Design System & Styling

### Tailwind CSS v4
The project uses **Tailwind CSS v4** with the new PostCSS plugin architecture (`@tailwindcss/postcss`).

### CSS Architecture (`app/globals.css`)

#### Imports:
```css
@import "tailwindcss";
@import "tw-animate-css";
@import "shadcn/tailwind.css";
```

#### Color Scheme
Uses **OKLCH color space** for consistent and perceptually uniform colors:

**Light Mode**:
- Background: `oklch(1 0 0)` (pure white)
- Foreground: `oklch(0.145 0 0)` (near black)
- Primary: `oklch(0.60 0.13 163)` (emerald theme)
- Primary Foreground: `oklch(0.98 0.02 166)` (light emerald)

**Dark Mode** (`.dark` class):
- Background: `oklch(0.145 0 0)` (near black)
- Foreground: `oklch(0.985 0 0)` (near white)
- Primary: `oklch(0.70 0.15 162)` (brighter emerald)
- Borders use `oklch(1 0 0 / 10%)` (white with 10% opacity)

#### Border Radius System
```css
--radius: 0.45rem;              /* Base radius (small) */
--radius-sm: calc(--radius - 4px);
--radius-md: calc(--radius - 2px);
--radius-lg: var(--radius);
--radius-xl: calc(--radius + 4px);
--radius-2xl: calc(--radius + 8px);
--radius-3xl: calc(--radius + 12px);
--radius-4xl: calc(--radius + 16px);
```

#### Theme Variables
All colors, spacing, and design tokens are defined as CSS custom properties and aliased in the `@theme inline` block for Tailwind to consume.

### Typography
**Fonts configured** (loaded via Next.js `next/font/google`):
1. **Figtree**: Primary sans-serif font (`--font-sans`)
2. **Geist**: Alternative sans font (`--font-geist-sans`)
3. **Geist Mono**: Monospace font (`--font-geist-mono`)

Applied in `app/layout.tsx`:
```tsx
const figtree = Figtree({subsets:['latin'], variable:'--font-sans'});
// HTML element gets figtree.variable
// Body gets geistSans and geistMono variables
```

### Dark Mode
Dark mode is implemented via the `.dark` class on the `<html>` element. Custom variant defined:
```css
@custom-variant dark (&:is(.dark *));
```

---

## Components

### shadcn/ui Components Installed
The following UI components are available in `components/ui/`:

1. **alert-dialog.tsx** - Modal dialog for alerts and confirmations
2. **badge.tsx** - Badge/pill component with variants
3. **button.tsx** - Button component with multiple variants (default, destructive, outline, ghost, link, etc.)
4. **card.tsx** - Card container with header, content, and footer sections
5. **combobox.tsx** - Searchable select dropdown
6. **dropdown-menu.tsx** - Dropdown menu with items, separators, and sub-menus
7. **field.tsx** - Form field wrapper with label, description, and error message
8. **input-group.tsx** - Input with prefix/suffix addons
9. **input.tsx** - Basic text input
10. **label.tsx** - Form label
11. **select.tsx** - Select dropdown
12. **separator.tsx** - Horizontal/vertical divider
13. **textarea.tsx** - Multi-line text input

All components use `class-variance-authority` (CVA) for variant management and the `cn()` utility for className merging.

### Example Components
- **`component-example.tsx`**: Comprehensive showcase demonstrating all installed UI components
- **`example.tsx`**: Additional example component

### Adding New Components
Use the shadcn CLI to add more components:
```bash
bunx shadcn@latest add <component-name>
```

Example:
```bash
bunx shadcn@latest add dialog
bunx shadcn@latest add toast
```

---

## Utility Functions

### `lib/utils.ts`
```typescript
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
```

**Purpose**: Merges Tailwind CSS classes intelligently, handling conflicts (e.g., `px-4 px-2` → `px-2`). Used extensively in all UI components.

---

## Development Workflow

### Installation
```bash
# Install dependencies
bun install
```

### Running Dev Server
```bash
# Start development server (default: http://localhost:3000)
bun run dev
```

### Building for Production
```bash
# Build optimized production bundle
bun run build

# Start production server
bun run start
```

### Linting
```bash
# Run ESLint
bun run lint
```

---

## App Router Structure

### `app/layout.tsx`
- **Root layout** for the entire application
- Loads fonts (Figtree, Geist, Geist Mono)
- Applies global className utilities
- Metadata configuration (title, description)
- Dark mode class can be toggled on `<html>` element

### `app/page.tsx`
- **Home page** (route: `/`)
- Currently renders `<ComponentExample />` as a demonstration

### Adding New Pages
Create new files/folders in `app/`:
```
app/
├── page.tsx           → /
├── about/
│   └── page.tsx       → /about
└── dashboard/
    ├── page.tsx       → /dashboard
    └── settings/
        └── page.tsx   → /dashboard/settings
```

---

## Path Aliases

Configured in `tsconfig.json` and `components.json`:
```typescript
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { MyComponent } from "@/components/my-component"
```

- `@/*` → Project root

---

## Static Assets

Place public assets in `public/`:
```tsx
<Image src="/logo.png" alt="Logo" width={100} height={100} />
```

Default SVG assets:
- `file.svg`, `globe.svg`, `next.svg`, `vercel.svg`, `window.svg`

---

## Styling Best Practices

### Using Components
```tsx
import { Button } from "@/components/ui/button"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"

export default function MyPage() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Welcome</CardTitle>
      </CardHeader>
      <CardContent>
        <Button variant="default">Click me</Button>
      </CardContent>
    </Card>
  )
}
```

### Custom Styling
Mix Tailwind utilities with shadcn components:
```tsx
<Button className="mt-4 bg-emerald-600 hover:bg-emerald-700">
  Custom Styled Button
</Button>
```

### Theming
Modify CSS variables in `app/globals.css` to customize the theme:
```css
:root {
  --primary: oklch(0.60 0.13 163);  /* Change primary color */
  --radius: 0.75rem;                 /* Increase border radius */
}
```

---

## TypeScript

### Type Safety
All components are fully typed with TypeScript.

### Component Props Example
```tsx
interface MyComponentProps {
  title: string;
  variant?: "default" | "outline";
  onClick?: () => void;
}

export function MyComponent({ title, variant = "default", onClick }: MyComponentProps) {
  return <Button variant={variant} onClick={onClick}>{title}</Button>
}
```

---

## Adding Dependencies

Using Bun:
```bash
bun add <package-name>
bun add -d <dev-package-name>
```

Example:
```bash
bun add axios zustand
bun add -d @types/node
```

---

## Environment Variables

Create `.env.local` for local environment variables:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_FEATURE_FLAG=true
```

Access in code:
```typescript
const apiUrl = process.env.NEXT_PUBLIC_API_URL;
```

**Note**: Only variables prefixed with `NEXT_PUBLIC_` are exposed to the browser.

---

## Future Development Considerations

### For Developers:
1. **Component Organization**: Keep related components grouped in folders
2. **State Management**: Consider adding Zustand, Jotai, or React Context for global state
3. **API Layer**: Create a dedicated `services/` or `api/` directory for API calls
4. **Form Handling**: Add `react-hook-form` + `zod` for form validation
5. **Routing**: Leverage Next.js App Router features (loading.tsx, error.tsx, etc.)

### For Coding Agents:
1. **File Structure**: Always place components in `components/`, utilities in `lib/`
2. **Imports**: Use `@/` path aliases for cleaner imports
3. **Styling**: Prefer Tailwind utilities over custom CSS when possible
4. **Component Addition**: Use `bunx shadcn@latest add <component>` for new UI components
5. **Type Safety**: Always define TypeScript interfaces for component props
6. **Naming Conventions**:
   - Components: PascalCase (`MyComponent.tsx`)
   - Utilities: camelCase (`utils.ts`)
   - Pages: lowercase (`page.tsx`, `layout.tsx`)

---

## Common Commands Reference

```bash
# Development
bun run dev              # Start dev server
bun run build            # Build for production
bun run start            # Start production server
bun run lint             # Run ESLint

# shadcn/ui
bunx shadcn@latest add <component>     # Add a component
bunx shadcn@latest add --all           # Add all components
bunx shadcn@latest diff                # Check for updates

# Dependencies
bun add <package>        # Add dependency
bun remove <package>     # Remove dependency
bun install              # Install all dependencies
```

---

## Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [shadcn/ui Documentation](https://ui.shadcn.com)
- [Tailwind CSS v4 Documentation](https://tailwindcss.com/docs)
- [Lucide Icons](https://lucide.dev)
- [Bun Documentation](https://bun.sh/docs)
- [React 19 Documentation](https://react.dev)

---

## Notes

- **Bun Runtime**: This project uses Bun for faster installation and runtime performance
- **React 19**: Latest React features including improved hooks and server components
- **Tailwind v4**: Uses the new PostCSS architecture (no `tailwind.config.js` file needed)
- **OKLCH Colors**: Provides better perceptual uniformity and wider color gamut support
- **App Router**: Uses Next.js 16's App Router (not Pages Router)
- **Server Components**: RSC (React Server Components) enabled by default