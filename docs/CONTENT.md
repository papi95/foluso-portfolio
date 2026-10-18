# Product and demo content notes

The marketing page's profile cards, gig preview rows, gear examples, member names, and community tip are illustrative. They are not verified members or live listings. The live opportunity board is at `/app` and shows only gigs posted through the pilot API. Keep this distinction clear in every public preview.

`script.js` contains static marketing examples for discovery filters. `pilot.js` receives real gig/profile metadata from `server.py` and builds UI using safe DOM APIs and `textContent`. Never interpolate user-provided content into HTML strings. Validate all incoming content server-side even when the browser also validates it.

The account form on `/app` creates a real pilot account in SQLite. Passwords are not stored in plaintext, but email verification, recovery, export, and deletion are not implemented. Do not collect real members broadly until those controls and the privacy notice are ready. The registration gate can be configured with `PILOT_INVITE_CODE`; moderators are configured with `MODERATOR_EMAILS`.

The gear and community sections describe later product phases. Do not change their “coming next” labels or claim functionality until those features are built, tested, moderated, and available to members.
