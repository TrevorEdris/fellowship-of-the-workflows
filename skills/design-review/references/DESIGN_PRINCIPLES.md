# S-Tier SaaS Dashboard Design Checklist

Inspired by Stripe, Airbnb, Linear.

## I. Core Design Philosophy & Strategy

- [ ] **Users First:** Prioritize user needs, workflows, and ease of use in every design decision
- [ ] **Meticulous Craft:** Aim for precision, polish, and high quality in every UI element and interaction
- [ ] **Speed & Performance:** Design for fast load times and snappy, responsive interactions
- [ ] **Simplicity & Clarity:** Strive for a clean, uncluttered interface. Ensure labels, instructions, and information are unambiguous
- [ ] **Focus & Efficiency:** Help users achieve their goals quickly and with minimal friction
- [ ] **Consistency:** Maintain a uniform design language (colors, typography, components, patterns) across the entire dashboard
- [ ] **Accessibility (WCAG AA+):** Design for inclusivity. Ensure sufficient color contrast, keyboard navigability, and screen reader compatibility
- [ ] **Opinionated Design:** Establish clear, efficient default workflows and settings, reducing decision fatigue

## II. Design System Foundation

### Color Palette
- [ ] **Primary Brand Color:** Used strategically
- [ ] **Neutrals:** Scale of grays (5-7 steps) for text, backgrounds, borders
- [ ] **Semantic Colors:** Success (green), Error (red), Warning (amber), Informational (blue)
- [ ] **Dark Mode Palette:** Corresponding accessible dark mode
- [ ] **Accessibility Check:** All combinations meet WCAG AA contrast ratios

### Typography
- [ ] **Primary Font:** Clean, legible sans-serif (Inter, Manrope, system-ui)
- [ ] **Modular Scale:** H1, H2, H3, H4, Body Large, Body Medium, Body Small
- [ ] **Font Weights:** Limited set (Regular, Medium, SemiBold, Bold)
- [ ] **Line Height:** Generous for readability (1.5-1.7 for body)

### Spacing
- [ ] **Base Unit:** 8px
- [ ] **Spacing Scale:** 4px, 8px, 12px, 16px, 24px, 32px, 48px

### Border Radii
- [ ] **Small:** 4-6px (inputs, buttons)
- [ ] **Medium:** 8-12px (cards, modals)

### Core Components (with states: default, hover, active, focus, disabled)
- [ ] Buttons (primary, secondary, tertiary, destructive, link)
- [ ] Input Fields (text, textarea, select, date picker)
- [ ] Checkboxes & Radio Buttons
- [ ] Toggles/Switches
- [ ] Cards
- [ ] Tables (with sorting, filtering)
- [ ] Modals/Dialogs
- [ ] Navigation (Sidebar, Tabs)
- [ ] Badges/Tags
- [ ] Tooltips
- [ ] Progress Indicators
- [ ] Icons (single, modern icon set; SVG)
- [ ] Avatars

## III. Layout & Visual Hierarchy

- [ ] **Responsive Grid:** 12-column system
- [ ] **Strategic White Space:** Ample negative space for clarity
- [ ] **Clear Visual Hierarchy:** Typography, spacing, positioning guide the eye
- [ ] **Consistent Alignment:** Elements aligned consistently
- [ ] **Dashboard Layout:** Persistent left sidebar, content area, optional top bar
- [ ] **Mobile-First:** Graceful adaptation to smaller screens

## IV. Interaction Design

- [ ] **Purposeful Micro-interactions:** Subtle feedback for actions
- [ ] **Animation Timing:** 150-300ms with appropriate easing
- [ ] **Loading States:** Skeleton screens, spinners
- [ ] **Smooth Transitions:** State changes, modal appearances
- [ ] **Keyboard Navigation:** Full accessibility with clear focus states

## V. Accessibility Checklist (WCAG 2.1 AA)

- [ ] Color contrast ratio ≥ 4.5:1 for text
- [ ] All interactive elements keyboard accessible
- [ ] Visible focus indicators
- [ ] Semantic HTML structure
- [ ] Form labels properly associated
- [ ] Images have alt text
- [ ] No reliance on color alone for information
- [ ] Touch targets ≥ 44x44px on mobile

## VI. Performance Considerations

- [ ] Optimized images and assets
- [ ] Lazy loading for below-fold content
- [ ] Minimal bundle size impact
- [ ] Core Web Vitals targets met
