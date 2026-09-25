---
name: ui-design
description: Use when building or restyling UI (pages, components, themes, landing pages) in any framework — applies the project's design system first, otherwise bundled contrast-checked light/dark palettes, type and spacing scales, interaction states, dark mode without flash, Core Web Vitals and SEO basics. Not for reviewing or auditing existing UI (use code-review), or profiling slow pages (use performance-review).
---

# UI Design

Apply these rules while writing UI code. Don't announce or print a checklist; the result should just be better UI. Adapt to the stack in use (React, Vue, Svelte, plain HTML/CSS, SwiftUI, Flutter…).

## Rule 1 — Use the project's design system before anything in this file

Before choosing a color, size, or component, look for what the project already has:

- Token sources: CSS custom properties in global stylesheets, `tailwind.config.*` / `@theme` blocks, SCSS variables, `theme.ts` / `tokens.json`, Style Dictionary output, native asset catalogs.
- Component libraries: shadcn/ui, MUI, Chakra, Radix, Vuetify, Angular Material, an internal `components/ui` folder, and so on.
- Existing dark-mode mechanism (`.dark` class, `data-theme`, a theme provider, `next-themes`).

If any exist, use them: reuse the components, reference the tokens by name, follow the existing dark-mode mechanism, and don't add parallel values. If you need a value the system lacks, add it to the system's source file in its naming style instead of hard-coding it in a component. If the project's own colors fail contrast, still use them but say which pair fails and how much it fails by. Don't silently swap in the palettes below.

Only when the project has no design system should you use the bundled tokens below. Pick one palette per project and use only its values.

Match the depth to the task. A prototype needs one palette and the basic semantic structure. A public production page needs the full token set, complete SEO metadata and the Core Web Vitals rules. For a component library, all styling comes from tokens and every variant and state is documented.

## Contrast — compute it, don't guess

WCAG 2.x AA: **4.5:1** for text; **3:1** for large text (≥ 24px, or ≥ 18.66px bold) and for UI component boundaries, focus indicators and meaningful icons. Disabled controls and purely decorative elements are exempt. Check every foreground/background pair you introduce, in both themes, including hover states.

```js
const lum = hex => { const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255)
  .map(c => c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4); return 0.2126 * r + 0.7152 * g + 0.0722 * b }
const contrast = (a, b) => { const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x); return (hi + 0.05) / (lo + 0.05) }
// contrast('#52525b', '#e4e4e7') → 6.09
```

## Fallback palettes

Every token has a light value and a dark value. What each token may be used for:

- **Surfaces**: `bg` (page), `bg-subtle` (cards, sidebars), `bg-muted` (hover rows, chips, code blocks).
- **Text on any surface** (≥ 4.5:1 on all three): `fg`, `fg-muted` (secondary text, placeholders), `accent`.
- **Control boundary** (≥ 3:1 on `bg` and `bg-subtle`): `border-strong`, for input, checkbox and toggle outlines.
- **Decorative only** (contrast not required, never use for text or as the only boundary of a control): `border` (dividers, card edges).
- **Filled buttons** (≥ 4.5:1): `primary-fg` on `primary` and on `primary-hover`; `accent-fg` on `accent` and on `accent-hover`.

| Token | Zinc light | Zinc dark | Slate light | Slate dark | Stone light | Stone dark |
|---|---|---|---|---|---|---|
| `--color-bg` | `#ffffff` | `#09090b` | `#ffffff` | `#0f172a` | `#ffffff` | `#1c1917` |
| `--color-bg-subtle` | `#f4f4f5` | `#18181b` | `#f8fafc` | `#1e293b` | `#f5f5f4` | `#292524` |
| `--color-bg-muted` | `#e4e4e7` | `#27272a` | `#f1f5f9` | `#334155` | `#e7e5e4` | `#44403c` |
| `--color-fg` | `#09090b` | `#fafafa` | `#0f172a` | `#f8fafc` | `#1c1917` | `#fafaf9` |
| `--color-fg-muted` | `#52525b` | `#a1a1aa` | `#475569` | `#cbd5e1` | `#57534e` | `#d6d3d1` |
| `--color-border` | `#e4e4e7` | `#27272a` | `#e2e8f0` | `#334155` | `#e7e5e4` | `#44403c` |
| `--color-border-strong` | `#71717a` | `#71717a` | `#64748b` | `#64748b` | `#78716c` | `#78716c` |
| `--color-primary` | `#18181b` | `#fafafa` | `#0f172a` | `#f8fafc` | `#1c1917` | `#fafaf9` |
| `--color-primary-fg` | `#fafafa` | `#09090b` | `#f8fafc` | `#0f172a` | `#fafaf9` | `#1c1917` |
| `--color-primary-hover` | `#27272a` | `#e4e4e7` | `#1e293b` | `#e2e8f0` | `#292524` | `#e7e5e4` |
| `--color-accent` | `#1d4ed8` | `#60a5fa` | `#4f46e5` | `#a5b4fc` | `#b43c0b` | `#fb923c` |
| `--color-accent-fg` | `#ffffff` | `#09090b` | `#ffffff` | `#0f172a` | `#ffffff` | `#1c1917` |
| `--color-accent-hover` | `#1e40af` | `#93c5fd` | `#4338ca` | `#c7d2fe` | `#9a3412` | `#fdba74` |

Zinc is neutral (SaaS), Slate is cool (dashboards), and Stone is warm (editorial).

State colors work with any palette. `--color-<state>` is for text and icons and is checked at 4.5:1 on its own `-bg` and on every palette's `bg` and `bg-subtle`. `-bg` also holds each palette's `fg` at 4.5:1 or more. `-border` is decorative. A filled state button (for example, white text on a danger background) is a new pair, so compute its contrast.

| Token | Light | Dark |
|---|---|---|
| `--color-success` | `#15803d` | `#4ade80` |
| `--color-success-bg` | `#f0fdf4` | `#052e16` |
| `--color-success-border` | `#bbf7d0` | `#166534` |
| `--color-warning` | `#b45309` | `#fbbf24` |
| `--color-warning-bg` | `#fffbeb` | `#451a03` |
| `--color-warning-border` | `#fde68a` | `#854d0e` |
| `--color-danger` | `#b91c1c` | `#f87171` |
| `--color-danger-bg` | `#fef2f2` | `#450a0a` |
| `--color-danger-border` | `#fecaca` | `#991b1b` |
| `--color-info` | `#1d4ed8` | `#60a5fa` |
| `--color-info-bg` | `#eff6ff` | `#172554` |
| `--color-info-border` | `#bfdbfe` | `#1e40af` |

Don't use color as the only signal. Pair state colors with an icon or text such as "Error: …".

## Dark mode — follow the OS by default, allow an optional override, avoid a flash

Light values go in `:root`. Dark values are applied when the OS prefers dark and the user hasn't forced light, or when the user has forced dark:

```css
:root { color-scheme: light dark; /* light tokens */ }
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* dark tokens */ }
}
:root[data-theme="dark"] { /* same dark tokens */ }
:root[data-theme="light"] { color-scheme: light; }
:root[data-theme="dark"]  { color-scheme: dark; }
```

This needs no JavaScript and can't flash. The dark block appears twice. If the project has a CSS build step, generate both copies from one source. If you only support browsers from 2024 onward, you can use `light-dark()` instead. `color-scheme` makes native form controls and scrollbars match the theme.

JavaScript is only needed when there's a manual toggle. Restore the saved choice with a small inline, synchronous script in `<head>`. Don't use `defer`, `async` or a module script, because it must run before the first paint:

```html
<script>
  try { const t = localStorage.getItem('theme'); if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t } catch {}
</script>
```

```js
function setTheme(t) { // 'light' | 'dark' | 'system'
  const root = document.documentElement
  if (t === 'system') { delete root.dataset.theme; localStorage.removeItem('theme') }
  else { root.dataset.theme = t; localStorage.setItem('theme', t) }
}
```

In SSR frameworks, use the project's existing theme provider if it has one.

## Type, spacing, radius

```css
:root {
  --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --font-mono: ui-monospace, "Cascadia Code", "Fira Code", monospace;
  --text-xs: .75rem; --text-sm: .875rem; --text-base: 1rem; --text-lg: 1.125rem;
  --text-xl: 1.25rem; --text-2xl: 1.5rem; --text-3xl: 1.875rem; --text-4xl: 2.25rem;
  --leading-tight: 1.25; --leading-normal: 1.5;             /* headings / body */
  --space-1: .25rem; --space-2: .5rem; --space-3: .75rem; --space-4: 1rem;
  --space-6: 1.5rem; --space-8: 2rem; --space-12: 3rem; --space-16: 4rem;
  --radius-sm: .25rem; --radius: .5rem; --radius-lg: .75rem; --radius-full: 9999px;
}
```

- Body text is at least 16px (`--text-base`), with lines of about 60–75 characters (`max-width: 65ch`). Use `rem` for type so it scales with the user's font size.
- Headings go in order (h1 → h2 → h3) without skipping levels, with one `h1` per page. Pick heading levels by document structure, not by size; set the size with CSS.
- Only use values from the spacing scale. Put related items closer together than unrelated ones.

## Interaction and states

- **Visual hierarchy**: each view has one primary action, and it's the most prominent element. Secondary actions use the outline or ghost style.
- **Interactive states**: every control has default, hover, `:focus-visible`, active and disabled states. Every data view has loading, empty, error and success states. Add the ones that are missing.
- **Focus**: never remove the focus outline without replacing it. `outline: 2px solid var(--color-accent); outline-offset: 2px;` gives at least 3:1 on every surface in the fallback palettes.
- **Feedback**: acknowledge each action within about 100ms. Show an indicator if an operation takes over 1s, and progress or a cancel option if it takes over 10s. Disable a submit button while its request is in flight.
- **Target size**: make targets at least 24×24 CSS px (WCAG 2.2 AA). Aim for 44×44 on touch devices.
- **Motion**: respect `prefers-reduced-motion` and remove non-essential animation:

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important;
    transition-duration: .01ms !important; scroll-behavior: auto !important; }
}
```

- **Semantics first**: use `<button>` for actions and `<a href>` for navigation. Every input has a `<label>`. Use landmarks: `header`, `nav` (with `aria-label` if there's more than one), `main`, `footer`. Use ARIA only when no native element fits.

## Core Web Vitals

The "good" thresholds, measured at the 75th percentile, are LCP ≤ 2.5s, INP ≤ 200ms and CLS ≤ 0.1.

```html
<!-- LCP / hero image: high priority, never lazy -->
<img src="/hero.webp" alt="Team reviewing a dashboard" width="1200" height="630" fetchpriority="high">

<!-- Below-the-fold images: lazy, dimensions set to prevent layout shift -->
<img src="/chart.webp" alt="Monthly signups, Jan–Jun" width="800" height="450" loading="lazy" decoding="async">

<!-- Preload only if the LCP image is found late (CSS background, JS-rendered) -->
<link rel="preload" as="image" href="/hero.webp" fetchpriority="high">

<script src="/analytics.js" defer></script>
```

- Set `width`/`height` (or `aspect-ratio`) on every image, video and embed. Reserve space for ads, banners and late-loading content.
- Keep the main thread free: split long tasks, and defer or lazy-load non-critical JS.
- Label any performance claim as an estimate unless you measured it.

## SEO basics (public pages)

```html
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Specific Page Title – Site Name</title>                <!-- ~60 chars, unique per page -->
  <meta name="description" content="What this page offers, in one sentence."> <!-- ~150 chars -->
  <link rel="canonical" href="https://example.com/page">
  <meta property="og:type" content="website">
  <meta property="og:title" content="Specific Page Title">
  <meta property="og:description" content="What this page offers, in one sentence.">
  <meta property="og:image" content="https://example.com/og.png">  <!-- 1200×630, absolute URL -->
  <meta property="og:url" content="https://example.com/page">
  <meta name="twitter:card" content="summary_large_image">          <!-- X falls back to og:* for title/description/image -->
</head>
```

- **Images**: give meaningful images an `alt` that describes their content or purpose. Decorative images get `alt=""`, which is enough on its own; `role="presentation"` isn't needed.
- **Link text**: say where the link goes ("Read the pricing guide", not "Click here").
- **Structured data**: add JSON-LD with the most specific type (`Article`, `Product`, `FAQPage`, `BreadcrumbList`). Only mark up content that's visible on the page.
- **URLs**: use lowercase with hyphens. Pick one trailing-slash policy and 301-redirect the other form.
- **Crawling**: production sites need `robots.txt` and `sitemap.xml`. Mark staging with `noindex`.
- **External links**: `target="_blank"` already implies `noopener` in current browsers. Add `rel="noreferrer"` only if you don't want to send the referrer.
