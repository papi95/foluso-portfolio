# Architecture and pilot boundaries

## Current system

- `index.html`, `styles.css`, and `script.js` are the fast marketing/discovery page. Its profile, gig-preview, gear, and community cards are explicitly illustrative examples.
- `pilot.html`, `pilot.css`, and `pilot.js` are the working gig-board application.
- `server.py` is a FastAPI JSON API and serves only explicit HTML/CSS/JS files plus an allowlist of planning/policy documents. It does not mount or expose the repository directory.
- SQLite stores users, sessions, gigs, applications, and reports. Set `CREWS_GIGS_DB` to the persistent data volume in deployment.
- `rust-core/` contains Rust domain types as a reusable future core; it is not called by the Python API or browser yet.

## Live pilot workflow

Account registration/login → post a gig → filter/search open gigs → submit an application → poster-only applicant list → close a gig. Signed-in users may report a gig; configured moderators can review/dismiss reports or close the reported gig. Moderator access is based on the server-side `MODERATOR_EMAILS` allowlist, never a client-submitted role. A `PILOT_INVITE_CODE` can gate registration.

Password hashes use PBKDF2-HMAC-SHA256 with per-user salt. Session IDs are random bearer tokens stored only as hashes and sent in HttpOnly, SameSite=Strict cookies. State-changing API requests require a per-session CSRF header. API responses are no-store. User content is rendered with `textContent`/DOM construction rather than HTML string injection. The app sets CSP and other browser security headers and restricts static file serving.

## Not yet production-complete

The pilot has no email verification, account recovery, direct messaging, gear listings/transactions, payments, automated report emails, profile verification, or automated dispute handling. Reports are stored for review but need an active moderator account and a monitored real-world support contact. Login/rate-limit state is in process memory; production needs a trusted edge/persistent rate limiter. Before broad launch, add database backups/restore drills, monitoring, dependency patching, account export/deletion, and security/privacy review. Use managed PostgreSQL rather than SQLite if multiple app instances are needed.

The policy and terms docs in this repo are drafts, not legal advice or final notices. The founder still needs to conduct user interviews and name/domain/trademark checks.

## Performance and accessibility

No UI framework, external fonts, image downloads, or analytics are loaded. Listing art is CSS-generated. Native HTML controls, labels, skip links, status announcements, keyboard-operable dialogs, responsive layouts, and reduced-motion handling are used. Keep new features keyboard accessible; optimize real images before adding them.

## Visual palette

Slate `#0F172A` / `#1E293B` foundations; amber `#F59E0B` / `#D97706` primary actions and gig signals; pale `#F8FAFC` / `#E2E8F0` typography and cards; signal cyan for gear; muted slate-blue for community; and crimson `#EF4444` for urgent/live states.
