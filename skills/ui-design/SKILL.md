---
name: ui-design
description: Use when building UI — applies design tokens, color palettes (light/dark), typography, spacing, UX principles, and SEO best practices automatically regardless of framework.
---

# UI Design Skill

You internalize these principles and apply them silently when building UI. Do not announce or checklist — just write better UI. Adapt to the framework and language in use (React, Vue, HTML/CSS, SwiftUI, etc.).

## Context Awareness

- **Prototype / MVP** — use one palette, minimal token set, skip advanced SEO
- **Production / public-facing** — full token system, semantic HTML, complete SEO meta, accessible markup
- **Design system / component library** — enforce tokens strictly, document variants, expose theme contracts

## Color Palettes

Use CSS custom properties (or equivalent: SCSS variables, design tokens, theme objects). Always define both light and dark variants.

### Palette A — Zinc (neutral, modern, SaaS)

```css
:root {
  /* Surfaces */
  --color-bg:          #ffffff;
  --color-bg-subtle:   #f4f4f5;
  --color-bg-muted:    #e4e4e7;

  /* Content */
  --color-fg:          #09090b;
  --color-fg-muted:    #71717a;
  --color-fg-subtle:   #a1a1aa;

  /* Border */
  --color-border:      #e4e4e7;
  --color-border-strong: #d4d4d8;

  /* Primary action */
  --color-primary:     #18181b;
  --color-primary-fg:  #fafafa;
  --color-primary-hover: #27272a;

  /* Accent */
  --color-accent:      #3b82f6;
  --color-accent-fg:   #ffffff;
  --color-accent-hover: #2563eb;
}

[data-theme="dark"] {
  --color-bg:          #09090b;
  --color-bg-subtle:   #18181b;
  --color-bg-muted:    #27272a;

  --color-fg:          #fafafa;
  --color-fg-muted:    #a1a1aa;
  --color-fg-subtle:   #71717a;

  --color-border:      #27272a;
  --color-border-strong: #3f3f46;

  --color-primary:     #fafafa;
  --color-primary-fg:  #09090b;
  --color-primary-hover: #e4e4e7;

  --color-accent:      #60a5fa;
  --color-accent-fg:   #0f172a;
  --color-accent-hover: #93c5fd;
}
```

### Palette B — Slate (cool-toned, professional, dashboard)

```css
:root {
  --color-bg:          #ffffff;
  --color-bg-subtle:   #f8fafc;
  --color-bg-muted:    #f1f5f9;

  --color-fg:          #0f172a;
  --color-fg-muted:    #64748b;
  --color-fg-subtle:   #94a3b8;

  --color-border:      #e2e8f0;
  --color-border-strong: #cbd5e1;

  --color-primary:     #0f172a;
  --color-primary-fg:  #f8fafc;
  --color-primary-hover: #1e293b;

  --color-accent:      #6366f1;
  --color-accent-fg:   #ffffff;
  --color-accent-hover: #4f46e5;
}

[data-theme="dark"] {
  --color-bg:          #0f172a;
  --color-bg-subtle:   #1e293b;
  --color-bg-muted:    #334155;

  --color-fg:          #f8fafc;
  --color-fg-muted:    #94a3b8;
  --color-fg-subtle:   #64748b;

  --color-border:      #334155;
  --color-border-strong: #475569;

  --color-primary:     #f8fafc;
  --color-primary-fg:  #0f172a;
  --color-primary-hover: #e2e8f0;

  --color-accent:      #818cf8;
  --color-accent-fg:   #0f172a;
  --color-accent-hover: #a5b4fc;
}
```

### Palette C — Stone (warm, editorial, content-first)

```css
:root {
  --color-bg:          #ffffff;
  --color-bg-subtle:   #f5f5f4;
  --color-bg-muted:    #e7e5e4;

  --color-fg:          #1c1917;
  --color-fg-muted:    #78716c;
  --color-fg-subtle:   #a8a29e;

  --color-border:      #e7e5e4;
  --color-border-strong: #d6d3d1;

  --color-primary:     #1c1917;
  --color-primary-fg:  #fafaf9;
  --color-primary-hover: #292524;

  --color-accent:      #f97316;
  --color-accent-fg:   #ffffff;
  --color-accent-hover: #ea580c;
}

[data-theme="dark"] {
  --color-bg:          #1c1917;
  --color-bg-subtle:   #292524;
  --color-bg-muted:    #44403c;

  --color-fg:          #fafaf9;
  --color-fg-muted:    #a8a29e;
  --color-fg-subtle:   #78716c;

  --color-border:      #44403c;
  --color-border-strong: #57534e;

  --color-primary:     #fafaf9;
  --color-primary-fg:  #1c1917;
  --color-primary-hover: #e7e5e4;

  --color-accent:      #fb923c;
  --color-accent-fg:   #1c1917;
  --color-accent-hover: #fdba74;
}
```

### Semantic State Colors (universal, pair with any palette)

```css
:root {
  /* Success */
  --color-success:     #22c55e;
  --color-success-bg:  #f0fdf4;
  --color-success-border: #bbf7d0;

  /* Warning */
  --color-warning:     #f59e0b;
  --color-warning-bg:  #fffbeb;
  --color-warning-border: #fde68a;

  /* Danger */
  --color-danger:      #ef4444;
  --color-danger-bg:   #fef2f2;
  --color-danger-border: #fecaca;

  /* Info */
  --color-info:        #3b82f6;
  --color-info-bg:     #eff6ff;
  --color-info-border: #bfdbfe;
}

[data-theme="dark"] {
  --color-success-bg:  #052e16;
  --color-success-border: #166534;

  --color-warning-bg:  #1c1400;
  --color-warning-border: #854d0e;

  --color-danger-bg:   #1f0a0a;
  --color-danger-border: #991b1b;

  --color-info-bg:     #0c1a2e;
  --color-info-border: #1e40af;
}
```

## Typography

```css
:root {
  /* Scale */
  --text-xs:   0.75rem;   /* 12px */
  --text-sm:   0.875rem;  /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg:   1.125rem;  /* 18px */
  --text-xl:   1.25rem;   /* 20px */
  --text-2xl:  1.5rem;    /* 24px */
  --text-3xl:  1.875rem;  /* 30px */
  --text-4xl:  2.25rem;   /* 36px */

  /* Weight */
  --font-normal:   400;
  --font-medium:   500;
  --font-semibold: 600;
  --font-bold:     700;

  /* Line height */
  --leading-tight:  1.25;
  --leading-snug:   1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;

  /* Font stack */
  --font-sans: ui-sans-serif, system-ui, -apple-system, sans-serif;
  --font-mono: ui-monospace, 'Cascadia Code', 'Fira Code', monospace;
}
```

Heading hierarchy — always maintain H1 → H2 → H3 order. Never skip levels. One H1 per page.

## Spacing & Layout

```css
:root {
  --space-1:  0.25rem;  /* 4px */
  --space-2:  0.5rem;   /* 8px */
  --space-3:  0.75rem;  /* 12px */
  --space-4:  1rem;     /* 16px */
  --space-6:  1.5rem;   /* 24px */
  --space-8:  2rem;     /* 32px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */

  /* Border radius */
  --radius-sm: 0.25rem;
  --radius:    0.5rem;
  --radius-lg: 0.75rem;
  --radius-xl: 1rem;
  --radius-full: 9999px;

  /* Shadow */
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow:    0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}
```

## Dark Mode Implementation

### CSS (recommended — zero JS flash)

```css
@media (prefers-color-scheme: dark) {
  :root { /* dark token overrides */ }
}

/* User override via data attribute */
[data-theme="light"] { /* force light */ }
[data-theme="dark"]  { /* force dark */ }
```

### JavaScript persistence

```js
// On page load — BEFORE render to avoid flash
const theme = localStorage.getItem('theme')
  ?? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
document.documentElement.dataset.theme = theme

// Toggle
function toggleTheme() {
  const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark'
  document.documentElement.dataset.theme = next
  localStorage.setItem('theme', next)
}
```

Place the detection script as the first `<script>` in `<head>` — before any CSS loads — to prevent flash of wrong theme.

## UX Principles

**Visual hierarchy** — size, weight, and color guide the eye. Primary action is always the most visually prominent element on screen.

**States** — every interactive element needs: default, hover, focus, active, disabled. Every data-fetching component needs: loading, empty, error, success states. Never leave state gaps.

**Feedback** — every user action needs acknowledgment within 100ms. If an operation takes >1s, show a loader. If >10s, show progress.

**Spacing** — use the spacing scale consistently. Related elements have less space between them than unrelated ones (proximity principle).

**Focus ring** — never remove `:focus-visible` outline. Style it to match the palette instead.

```css
:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
```

**Touch targets** — minimum 44×44px for interactive elements on mobile.

**Motion** — respect `prefers-reduced-motion`. Wrap animations:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## SEO Fundamentals

### Meta tags (every page)

```html
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />

  <title>Page Title – Site Name</title>  <!-- 50–60 chars -->
  <meta name="description" content="..." />  <!-- 120–155 chars -->
  <link rel="canonical" href="https://example.com/page" />

  <!-- Open Graph -->
  <meta property="og:type"        content="website" />
  <meta property="og:title"       content="Page Title" />
  <meta property="og:description" content="..." />
  <meta property="og:image"       content="https://example.com/og.png" />
  <meta property="og:url"         content="https://example.com/page" />

  <!-- Twitter -->
  <meta name="twitter:card"        content="summary_large_image" />
  <meta name="twitter:title"       content="Page Title" />
  <meta name="twitter:description" content="..." />
  <meta name="twitter:image"       content="https://example.com/og.png" />
</head>
```

### Semantic HTML

```html
<!-- ✅ Correct landmark structure -->
<header>
  <nav aria-label="Main navigation">...</nav>
</header>
<main>
  <article>
    <h1>Page Title</h1>  <!-- One H1 per page -->
    <section>
      <h2>Section</h2>
      <h3>Subsection</h3>
    </section>
  </article>
</main>
<footer>...</footer>

<!-- ✅ Images always have alt -->
<img src="..." alt="Descriptive text" />
<img src="decorative.png" alt="" role="presentation" />

<!-- ✅ Links have meaningful text -->
<!-- ❌ <a href="/blog">Click here</a> -->
<!-- ✅ --> <a href="/blog">Read our blog</a>
```

### Performance (Core Web Vitals)

- **LCP** (Largest Contentful Paint < 2.5s) — preload hero image, avoid render-blocking resources
- **CLS** (Cumulative Layout Shift < 0.1) — always set `width`/`height` on images and embeds
- **INP** (Interaction to Next Paint < 200ms) — avoid long tasks on main thread, defer non-critical JS

```html
<!-- Preload critical image -->
<link rel="preload" as="image" href="/hero.webp" />

<!-- Image with explicit dimensions to prevent CLS -->
<img src="/hero.webp" alt="..." width="1200" height="630" loading="lazy" />

<!-- Defer non-critical scripts -->
<script src="analytics.js" defer></script>
```

### Structured Data

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Page Title",
  "description": "Page description",
  "url": "https://example.com/page"
}
</script>
```

Use `Article` for blog posts, `Product` for e-commerce, `FAQPage` for FAQ, `BreadcrumbList` for navigation.

### URL & Navigation

- URLs: lowercase, hyphens (not underscores), no trailing slashes inconsistently
- Breadcrumbs on content-heavy sites
- `rel="noopener noreferrer"` on external links
- `robots.txt` and `sitemap.xml` for production sites
