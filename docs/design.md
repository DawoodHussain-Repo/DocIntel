# DocIntel Design System

Documentation for the visual design language powering the DocIntel frontend.

---

## Design Philosophy

DocIntel uses a **dark glassmorphism** aesthetic — layered translucent surfaces over a deep blue-black canvas with teal accent lighting. The design communicates enterprise-grade sophistication and legal industry seriousness while remaining approachable through subtle animations and generous spacing.

---

## Color Palette

### Core Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--bg-0` | `#06131f` | Deepest background |
| `--bg-1` | `#0e1f31` | Secondary background |
| `--surface-0` | `rgba(11, 32, 50, 0.8)` | Glass panel background (top) |
| `--surface-1` | `rgba(8, 24, 39, 0.88)` | Glass panel background (bottom) |
| `--surface-border` | `rgba(98, 149, 186, 0.3)` | Panel border |

### Text Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--text-primary` | `#e5eff8` | Body text, headings |
| `--text-secondary` | `#9eb7cb` | Subtitles, metadata, labels |

### Accent Colors

| Token | Value | Usage |
|-------|-------|-------|
| `--accent` | `#0ea5a6` | Teal accent (base) |
| `--accent-strong` | `#1bc4c8` | Teal accent (bright, focus rings, highlights) |
| `--warning` | `#f59e0b` | Amber — tool call badges |
| `--danger` | `#ef4444` | Red — errors, destructive actions |

---

## Typography

### Font Stack

| Role | Font Family | Source |
|------|------------|--------|
| Body | IBM Plex Sans | Google Fonts |
| Headings | Space Grotesk | Google Fonts |

### Font Weights

| Weight | Usage |
|--------|-------|
| 400 | Body text |
| 500 | Subtle emphasis |
| 600 | Labels, buttons, section headers |
| 700 | Page titles (headings only) |

### Type Scale

| Class | Size | Font | Usage |
|-------|------|------|-------|
| `.brand-title` | 1.45rem | Heading | Sidebar title |
| `.chat-title` | 1.35rem | Heading | Chat panel title |
| `.dropzone-title` | 0.95rem | Body | Upload zone label |
| `.document-name` | 0.82rem | Body | File names |
| `.eyebrow` | 0.72rem | Body | Uppercase category labels |
| `.section-count` | 0.74rem | Body | Badge counters |

---

## Layout System

### App Shell

The root layout uses CSS Grid:

```css
.app-shell {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 1rem;
  height: 100vh;
  padding: 1rem;
}
```

### Responsive Breakpoints

| Breakpoint | Behavior |
|-----------|----------|
| `> 1024px` | Side-by-side panels (320px sidebar + fluid chat) |
| `≤ 1024px` | Stacked layout, sidebar limited to 42vh |
| `≤ 640px` | Reduced padding, full-width messages |

---

## Component Catalog

### Glass Panel

Base container for all major sections. Uses gradient background + `backdrop-filter: blur(12px)` for frosted glass effect.

```css
.glass-panel {
  border: 1px solid var(--surface-border);
  border-radius: 20px;
  background: linear-gradient(180deg, var(--surface-0), var(--surface-1));
  backdrop-filter: blur(12px);
  box-shadow: 0 14px 32px rgba(2, 10, 18, 0.38);
}
```

### Buttons

Three tiers of visual hierarchy:

| Class | Appearance | Usage |
|-------|-----------|-------|
| `.button-primary` | Teal gradient, dark text | Primary actions (Send) |
| `.button-secondary` | Transparent dark, light text | Secondary actions (Browse, Clear) |
| `.button-tertiary` | Red-tinted dark | Destructive actions (Remove) |

All buttons share:
- `border-radius: 12px`
- `font-family: var(--font-heading)`
- Hover: `translateY(-1px) + brightness(1.03)`
- Focus: `2px solid var(--accent-strong)` outline
- Disabled: `opacity: 0.5, cursor: not-allowed`

### Dropzone

Upload target area with dashed border that activates on drag:

- Default: dashed border at 55% opacity
- Active (`.dropzone-active`): teal border + slight lift (`translateY(-1px)`)

### Message Card

Chat message bubble with role-based styling:

| Variant | Background |
|---------|-----------|
| Assistant | Solid dark (`rgba(9, 28, 45, 0.92)`) |
| User | Teal gradient overlay |

### Citation Pill

Inline badge for `[Page X]` references:

```css
.citation-pill {
  border-radius: 999px;
  background: linear-gradient(145deg, #8de4e8, #4fc0cb);
  color: #032b30;
  font-size: 0.72rem;
}
```

### Tool Call Badge

Amber-tinted badge shown during agent tool invocation:

```css
.tool-call-badge {
  border: 1px solid rgba(245, 158, 11, 0.5);
  background: rgba(113, 63, 18, 0.42);
  color: #fde68a;
  font-family: var(--font-heading);
}
```

---

## Animation System

### Entry Animation

All panels use `animate-enter-up` on mount:

```css
@keyframes enter-up {
  from { opacity: 0; transform: translateY(14px); }
  to   { opacity: 1; transform: translateY(0); }
}
```

- Duration: 480ms
- Easing: `cubic-bezier(0.16, 1, 0.3, 1)` (smooth overshoot)

### Hover Micro-Interactions

Buttons and interactive elements lift on hover:

```css
transform: translateY(-1px);
filter: brightness(1.03);
```

- Duration: 180ms
- Easing: `ease`

---

## Ambient Effects

### Background Gradient

Two `radial-gradient` layers create depth:
1. Primary: `#113456` at top-left (15%, 10%)
2. Secondary: linear gradient of `--bg-1` to `--bg-0`

### Ambient Glow

Decorative radial gradients (`pointer-events: none`) create teal and blue glows:
- Top-right: Teal glow (15% opacity)
- Bottom-left: Blue glow (16% opacity)

### Grid Overlay

Subtle grid pattern masked with a gradient:

```css
.ambient-grid {
  background-image:
    linear-gradient(rgba(124, 176, 214, 0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(124, 176, 214, 0.07) 1px, transparent 1px);
  background-size: 38px 38px;
  mask-image: linear-gradient(to bottom, rgba(0, 0, 0, 0.35), transparent 95%);
}
```

---

## Accessibility

| Feature | Implementation |
|---------|---------------|
| Screen reader labels | `.sr-only` class for visually hidden labels |
| Focus indicators | `2px solid var(--accent-strong)` on all interactive elements |
| Semantic HTML | `<header>`, `<main>`, `<footer>`, `<article>`, `<aside>` |
| Live region | `aria-live="polite"` on message scroll area |
| Keyboard navigation | Enter to send, Shift+Enter for newline |
| Color contrast | Light text on dark backgrounds (WCAG AA compliant) |
