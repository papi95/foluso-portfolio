# Folu Network — Media Community Prototype

A fast, responsive front-end prototype for a global media community: musicians, live and AV crews, photographers, videographers, designers, editors, producers, and the people who support them. The concept brings collaborators, paid gigs, equipment sales and rentals, and peer help into one network.

The current build is a static prototype with local sample listings. Search, category filtering, responsive navigation, and the invite dialog work in-browser. Accounts, messaging, payments, verified listings, and real submissions require a backend and are not yet connected. The signup modal clearly identifies itself as a prototype and does not send or store the submitted details.

## Run locally

No install or build step is required:

```sh
python3 -m http.server 8000
```

Visit <http://localhost:8000>.

## Prototype features

- Search sample profiles, gigs, equipment, and community discussions by keyword and location
- Filter by people, gigs, gear, and help
- Responsive menu and browser-native invite dialog
- Accessible focus skip link, labels, keyboard-operable controls, and reduced-motion support
- CSS-generated illustration and listing artwork; no large images, JS frameworks, or font downloads
- Rust domain model in `rust-core/` as a foundation for a future backend

## Files

```text
.
├── index.html             # Product landing/discovery experience
├── styles.css             # Responsive visual system and CSS artwork
├── script.js              # Local sample data, filters, search, and invite prototype
├── rust-core/             # Dependency-free Rust media-network domain model
├── docs/                  # Product and technical notes
├── CONTRIBUTING.md
└── LICENSE
```

## Rust domain core

The small, dependency-free Rust crate models media listings and listing categories. It is not currently compiled to WebAssembly or connected to the static page. Run its unit tests with:

```sh
cd rust-core
cargo test
```

## Production roadmap

Before launching a real network, add a secure API and persistent database; member accounts and profiles; direct messaging; gig applications; moderation and report flows; verified equipment condition/availability; safe payments or escrow; privacy and terms documentation; and operational support. Validate identity, payment, and listing data server-side. Clearly define location privacy, dispute handling, prohibited listings, and platform fees.

## Deployment

Deploy the repository root to any static host. No build command is needed for the prototype. A static host will only publish the demo; it cannot provide the marketplace, accounts, or messaging backend described in the roadmap.

## License

MIT — see [LICENSE](LICENSE).
