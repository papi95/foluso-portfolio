# Architecture and product boundaries

## Current prototype

The product is currently a static, progressively enhanced site. `index.html` owns semantic structure, `styles.css` contains responsive presentation and CSS-generated listing artwork, and `script.js` renders local sample listings and adds filtering, keyword/location search, navigation, and the invite dialog. There are no runtime dependencies, third-party scripts, APIs, accounts, database, or persistent user data.

Searches filter only the small hard-coded demo dataset in the visitor's browser. Submitting the invite form displays an in-page prototype confirmation and sends nothing to a server. Sign-in is a visual placeholder, not authentication. Equipment and gig cards are examples, not live offers.

The Rust crate defines future domain types for media listings, disciplines, and lightweight email syntax validation. It is not currently connected to the front end or compiled to WebAssembly.

## Product areas represented

- People and professional profiles
- Paid and freelance opportunities
- Equipment for sale or rent
- Community questions and peer advice
- Global location-aware discovery

## Production services still needed

A production platform requires a secure backend and database, identity and profile management, search/indexing, direct messaging, gig applications and hiring workflows, listing moderation, equipment availability and condition management, payment processing, dispute resolution, and abuse reporting. User-generated content must be escaped and validated server-side. Protect private contact information and provide clear privacy controls, safety guidance, community standards, terms, and support channels.

## Performance and accessibility

The static prototype has no build step, external font requests, or large image assets. Controls use native HTML elements; the page includes a skip link, labels, responsive navigation, and reduced-motion rules. Keep new interactions keyboard-operable and provide useful empty/error states.

## Visual palette

The UI uses slate `#0F172A` / `#1E293B` foundations, amber `#F59E0B` / `#D97706` primary actions, pale `#F8FAFC` / `#E2E8F0` text and card surfaces, and red `#EF4444` for status/focus alerts.
