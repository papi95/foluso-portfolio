# Contributing

Thanks for helping improve Crews & Gigs.

## Workflow

1. Keep the phase-one scope focused on gig discovery and applications; document later-phase ideas rather than presenting them as live.
2. Use semantic HTML and native controls. Verify keyboard behavior and mobile layout.
3. Respect `prefers-reduced-motion`; make validation and error states understandable without color alone.
4. Install development dependencies with `pip install -r requirements-dev.txt` and run `python -m unittest discover -s tests -v` after API changes.
5. Run `node --check script.js && node --check pilot.js` after JavaScript changes.
6. Run `cd rust-core && cargo test` after Rust changes when Cargo is available.
7. Review the site at desktop and mobile widths. Never commit `.env`, SQLite data, passwords, invite codes, or member data.

## Security and content

Render member-generated content with text-safe DOM APIs, validate on the server, and keep static file serving allow-listed. Do not add claims that identities or gigs are verified unless a real process exists. Use only authorized images, fonts, and copy. Update product/security docs when behavior changes.
