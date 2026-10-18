# Architecture

## Overview

The site is a static, progressively enhanced portfolio. `index.html` owns semantic structure and visible copy, `styles.css` provides the responsive design system and CSS-based artwork, and `script.js` adds small client-side interactions. There are no runtime JavaScript dependencies, build tools, network APIs, or user data collection.

The `rust-core` crate captures reusable domain concepts (portfolio projects, disciplines, and basic email validation). It is deliberately not coupled to the page: the static site works without Rust installed. A future Rust API or WebAssembly module could consume the same project/domain model.

## Browser behavior

- Category buttons filter cards by their `data-category` value.
- The mobile menu updates `aria-expanded` and closes after navigation.
- Intersection Observer reveals selected content when it enters the viewport. Content stays visible when the API is unavailable or reduced motion is requested.
- The year in the footer is derived from the browser clock.

## Accessibility and performance

Use semantic headings and landmarks, meaningful link labels, keyboard-operable native buttons, visible text contrast, and a reduced-motion override. Keep decorative artwork in CSS or mark it as decorative. Avoid introducing large dependencies for simple interactions.

## Security and privacy

There is no backend, analytics, cookie storage, or form submission. The contact CTA opens the visitor's email client. External profile links use `rel="noreferrer"`. If a form or backend is added, validate inputs server-side, document data retention, and protect secrets outside the static repository.
