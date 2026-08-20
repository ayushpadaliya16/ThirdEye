---
name: Aether Spectralis
colors:
  surface: '#13121b'
  surface-dim: '#13121b'
  surface-bright: '#393842'
  surface-container-lowest: '#0e0d16'
  surface-container-low: '#1b1b24'
  surface-container: '#1f1f28'
  surface-container-high: '#2a2933'
  surface-container-highest: '#35343e'
  on-surface: '#e4e1ee'
  on-surface-variant: '#c7c4d8'
  inverse-surface: '#e4e1ee'
  inverse-on-surface: '#302f39'
  outline: '#918fa1'
  outline-variant: '#464555'
  surface-tint: '#c3c0ff'
  primary: '#c3c0ff'
  on-primary: '#1d00a5'
  primary-container: '#4f46e5'
  on-primary-container: '#dad7ff'
  inverse-primary: '#4d44e3'
  secondary: '#4cd7f6'
  on-secondary: '#003640'
  secondary-container: '#03b5d3'
  on-secondary-container: '#00424e'
  tertiary: '#89ceff'
  on-tertiary: '#00344d'
  tertiary-container: '#006693'
  on-tertiary-container: '#b8e0ff'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#e2dfff'
  primary-fixed-dim: '#c3c0ff'
  on-primary-fixed: '#0f0069'
  on-primary-fixed-variant: '#3323cc'
  secondary-fixed: '#acedff'
  secondary-fixed-dim: '#4cd7f6'
  on-secondary-fixed: '#001f26'
  on-secondary-fixed-variant: '#004e5c'
  tertiary-fixed: '#c9e6ff'
  tertiary-fixed-dim: '#89ceff'
  on-tertiary-fixed: '#001e2f'
  on-tertiary-fixed-variant: '#004c6e'
  background: '#13121b'
  on-background: '#e4e1ee'
  surface-variant: '#35343e'
typography:
  display-lg:
    fontFamily: Hanken Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Hanken Grotesk
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Hanken Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-mono:
    fontFamily: Geist
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.05em
  data-display:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  unit: 4px
  container-padding: 24px
  gutter: 16px
  glass-padding: 20px
  stack-gap: 12px
---

## Brand & Style

The design system is engineered for high-stakes digital investigation and cyber forensics. This version shifts from a clinical light environment to a **Deep-Space Forensic Vault**. It evokes a sense of "liquid glass" floating within a dark, pressurized chamber, prioritizing the visibility of glowing data against an infinite void through luminous accents and hyper-realistic transparency.

The aesthetic merges **Glassmorphism** with **Dark Minimalism**. It relies on high-index backdrop blurs and subtle specular highlights to create a multi-layered interface that feels both futuristic and surgical. The emotional response is one of deep immersion, intense focus, and technical authority, suitable for analysts navigating complex data landscapes in low-light operations centers.

## Colors

The palette is anchored in an **Obsidian and Deep Slate** base, providing a high-contrast foundation for luminous forensic data layers.

- **Primary Indigo (#4F46E5):** Used for primary actions, structural highlights, and critical focal points that "pierce" the dark background.
- **Luminous Cyan (#06B6D4):** The "specular" color, used for active states, interactive borders, and accent glows that simulate neon-lit instrumentation.
- **Ice Blue (#0EA5E9):** Dedicated to neutral data visualization and secondary telemetry.
- **Error Red (#BA1A1A):** High-risk alerts and catastrophic failure indicators.
- **Warning Amber:** Suspicious activity and warnings.
- **Success Emerald:** Verified safe states and successful bypasses.

Surface colors are achieved through ultra-low opacity primary tints or deep greys combined with heavy backdrop saturation to maintain the "glass" effect in a dark mode context.

## Typography

This design system utilizes a trio of sans-serif typefaces to balance legibility with a technical aesthetic.

- **Hanken Grotesk** is used for headlines to provide a sharp, contemporary edge.
- **Inter** serves as the workhorse for body text, ensuring readability in dense forensic reports.
- **Geist** (Monospaced/Technical) is reserved for data labels, timestamps, and hex code strings, reinforcing the developer-centric nature of the product.

All typography should be rendered with `antialiased` smoothing. In this dark mode variation, text colors primarily use high-contrast neutrals (like `on-surface: #E4E1EE`) to ensure maximum legibility against dark, translucent backgrounds.

## Layout & Spacing

The layout philosophy follows a **Fluid Grid** model with a heavy emphasis on "Safe Zones"—areas of high-density data surrounded by significant negative space to reduce cognitive load.

- **Desktop:** 12-column grid, 24px margins, 16px gutters.
- **Tablet:** 8-column grid, 16px margins, 12px gutters.
- **Mobile:** 4-column grid, 12px margins, 8px gutters.

The spacing rhythm is strictly based on a 4px scale. "Liquid Glass" panels should utilize consistent internal padding of 20px to maintain the illusion of depth and internal volume.

## Elevation & Depth

In Dark Mode, depth is achieved through layering light and transparency rather than shadows:

1.  **Backdrop Blurs:** Every surface must have a `backdrop-blur` of at least 40px (3xl) to differentiate layers from the deep background.
2.  **Tonal Stacking:** Higher elevation levels use slightly brighter surface opacities (e.g., `surface-container-high`) to simulate light catching the glass.
3.  **Specular Borders:** Use 1px top-and-left borders with 20% opacity Cyan (#06B6D4) or Indigo (#4F46E5) to create a "sheen" effect.
4.  **Glows:** Instead of traditional shadows, use ultra-soft outer glows (5-10% opacity of the primary color) for active or elevated elements to suggest they are self-illuminated.

## Shapes

The shape language is sophisticated and "Soft-Tech." The `Rounded` setting (0.5rem base) prevents the interface from feeling too industrial or sharp, while the `rounded-xl` (1.5rem) used for primary glass cards creates the "Liquid" feel.

- **Buttons/Inputs:** 8px (0.5rem).
- **Glass Panels:** 24px (1.5rem).
- **Chips/Pills:** Fully rounded (pill).

## Components

### Glass Cards
The foundation of the UI. Must feature `bg-slate-900/60`, `backdrop-blur-3xl`, and a `1px border-white/10`. On hover, the border opacity should increase to 25% or adopt the primary color.

### Glowing Status Pills
Small, high-contrast badges used for system health. 
- **Safe:** Emerald-400 text, emerald-500/10 background, 1px emerald-500/30 border.
- **Critical:** Crimson-400 text, crimson-500/10 background, with a pulsing inner-glow.

### Luminous Data Counters
Large numerical displays using **Geist**. Use the Luminous Cyan or Primary Indigo for the text color with a subtle `text-shadow` to simulate a HUD display.

### Input Fields
Deep, semi-transparent backgrounds (`bg-black/40`), with a Cyan bottom-border that glows when focused. Use Geist for the input text.

### Action Buttons
Primary buttons use a linear gradient from `Indigo-600` to `Indigo-700`. They should feature a "glass sheen" overlay—a diagonal white gradient at 10% opacity that shifts on hover to maintain the tactile glass feel.