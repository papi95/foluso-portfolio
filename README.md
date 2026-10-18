# Foluso — Creative Developer Portfolio

A responsive, interactive portfolio for a multidisciplinary full-stack developer, AI builder, motion designer, and visual designer. Built as a fast static site with vanilla HTML, CSS, and JavaScript, plus a dependency-free Rust domain core.

## Preview locally

No build step is required. From the repository root, serve the files over HTTP:

```sh
python3 -m http.server 8000
```

Open <http://localhost:8000>. Alternatively, use any static file server or open `index.html` directly (a local server is recommended).

## Features

- Responsive layout with mobile navigation and reduced-motion support
- Interactive project discipline filters
- Animated motion/visual treatments and progressive section reveals
- Accessible labels, semantic landmarks, descriptive metadata, and mailto contact
- Rust core with project data, discipline filtering, and email validation helpers

## Repository map

```text
.
├── index.html             # Portfolio page and content
├── styles.css             # Responsive visual system and project art
├── script.js              # Filtering, navigation, and reveal interactions
├── rust-core/             # Dependency-free Rust library and unit tests
├── docs/
│   ├── ARCHITECTURE.md    # Structure and implementation notes
│   └── CONTENT.md         # Updating portfolio content
├── CONTRIBUTING.md
├── LICENSE
└── README.md
```

## Rust core

The Rust crate is a reusable domain layer for a future API, static-site generator, or WebAssembly integration. It currently defines the portfolio project model, curated dataset, discipline filtering, and basic email validation.

```sh
cd rust-core
cargo test
```

The current browser experience is static and does not require or invoke the Rust crate at runtime. Keep the Rust helpers and browser behavior aligned if contact handling or projects move to a backend.

## Customize

- Edit project cards, biography, services, and contact details in `index.html`.
- Update colors, typography, layouts, and abstract CSS artwork in `styles.css`.
- Update filter interactions and navigation behavior in `script.js`.
- See [docs/CONTENT.md](docs/CONTENT.md) for content maintenance notes.

## Deployment

Deploy the repository root to any static hosting provider (GitHub Pages, Netlify, Cloudflare Pages, etc.). No environment variables or build command are required. For production, replace the sample social URLs and `hello@foluso.dev` with verified contact destinations and add real project case-study URLs.

## License

MIT — see [LICENSE](LICENSE).
