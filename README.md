# Crews & Gigs — media-production pilot

A lightweight full-stack pilot for media professionals. The initial usable workflow is intentionally focused: create an account, post a gig, find and apply to gigs, review applications, close a post, and report a concerning listing. The landing page still includes illustrative people and gear cards; only gigs created in the pilot API are live records.

## Run the pilot locally

Requires Python 3.11 or newer.

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn server:app --host 0.0.0.0 --port 8000
```

Open <http://localhost:8000> for the marketing page or <http://localhost:8000/app> for the working gig-board pilot. The SQLite database is created at `instance/crews-gigs.sqlite3`; it is ignored by Git. Set `CREWS_GIGS_DB` to use a different path.

Run the API tests:

```sh
python -m unittest discover -s tests -v
```

Run the Rust domain-core tests separately with `cd rust-core && cargo test`.

## MVP scope

**Included:** password-hashed member accounts, HttpOnly SameSite session cookies, CSRF checks on state-changing API routes, validated gig posts, location/discipline/keyword filters, applications, poster-only applicant review (applicant email sharing is optional and off by default), closing gigs, and reports.

**Not included:** email verification/recovery, identity or credential verification, messaging/chat, gear transactions, payments/escrow, ratings, or automated moderation. The MVP does not claim that talent is verified or that a gig booking/payment is guaranteed. The signup should remain an invite-only/controlled pilot until a monitored safety contact, backups, privacy review, and production hosting are ready.

## Pilot and launch preparation

- Proposed first market, not yet confirmed: Lagos, with remote gigs allowed. See [pilot product plan](docs/PRODUCT-PLAN.md).
- Use the interview questions and usability tasks in [pilot research](docs/PILOT-RESEARCH.md); recruit and interview real professionals before expanding.
- Complete the name/domain/social-handle and trademark checks in the plan with the founder and a qualified professional. This project does not establish legal clearance or availability.
- Review [community guidelines](docs/COMMUNITY-GUIDELINES.md), [privacy draft](docs/PRIVACY.md), and [terms draft](docs/TERMS.md) with qualified local counsel. They are planning drafts, not publication-ready legal notices.
- The [launch announcement](docs/LAUNCH-ANNOUNCEMENT.md) is a template; only claim functionality that is live.

## Fly.io deployment setup

`fly.toml` is configured to run the existing FastAPI app and Docker image in Johannesburg (`jnb`), enforce HTTPS, check `/health`, and mount a persistent SQLite volume at `/data`. Change `app` in `fly.toml` if that Fly app name is already taken. From an installed and authenticated `flyctl` CLI:

```sh
fly launch --no-deploy
fly volumes create crews_gigs_data --region jnb --size 1
fly secrets set PILOT_INVITE_CODE='choose-a-long-random-code' MODERATOR_EMAILS='moderator@example.com'
fly deploy
```

Create the moderator account using the invite code, then verify `https://<your-fly-app>.fly.dev/health` and `/app`. Keep a single machine while using SQLite; maintain and test volume backups. The current GitHub Pages project site is static and cannot run the API. After the Fly deployment is live, point the marketing-site join, login, and gig-board links to the Fly app URL so signup and API requests use the same HTTPS origin. The current `/app` link on GitHub Pages cannot work until that destination is updated.

## Production deployment requirements

GitHub Pages can host only the static marketing page; it cannot run the API. Deploy this FastAPI application on an HTTPS-capable app host with a persistent volume for SQLite (or move to managed PostgreSQL), set `CREWS_GIGS_DB` to that volume, and set `COOKIE_SECURE=1`. Use a trusted reverse proxy, external/persistent rate limiting, monitored backups and restore tests, a support inbox, and dependency updates. Do not expose the repository or database through static file serving. Do not use the local SQLite configuration as a multi-instance production database.

The server deliberately serves only allow-listed static files and public policy/plan documents. It returns security headers, stores only a PBKDF2 password hash, stores hashed session tokens, and never returns member email addresses in public gig responses. Configure `PILOT_INVITE_CODE` to gate registration and `MODERATOR_EMAILS` to grant the report-review tab to already-registered moderator accounts. See `.env.example`; set these values in the host's environment/secret manager, not in Git.

The in-memory login limiter is a basic single-process pilot safeguard, not a substitute for a persistent edge rate limiter in production. Email verification/password recovery and automated email alerts are not built; use a tightly controlled invite pilot until those are added. Reports are stored in the database but are not automatically emailed to moderators. Configure an actual moderator account and support channel and check the review queue routinely.

### Container quick start

```sh
docker build -t crews-gigs .
docker run --rm -p 8000:8000 \\
  -v crews-gigs-data:/data \\
  -e PILOT_INVITE_CODE='replace-with-a-long-random-code' \\
  -e MODERATOR_EMAILS='moderator@example.com' \\
  crews-gigs
```

The container sets `COOKIE_SECURE=1`, so run it behind HTTPS. Register the moderator account using the invite code, then sign in to review reports. For a short local HTTP-only check, run Uvicorn directly (the default cookie setting is non-Secure for localhost only).

## Repository map

```text
.
├── index.html / styles.css / script.js  # Marketing landing page and demo discovery
├── pilot.html / pilot.css / pilot.js    # Working pilot interface
├── server.py                            # FastAPI + SQLite API and allow-listed assets
├── requirements.txt                     # Runtime dependencies
├── tests/test_api.py                    # Auth, posting, application, permission, and safety tests
├── rust-core/                           # Rust media-listing domain types
└── docs/                                 # Pilot plan, research kit, policies, launch copy
```
