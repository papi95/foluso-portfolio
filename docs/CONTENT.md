# Product and demo content notes

All names, profiles, listings, prices, locations, gigs, and community activity currently shown in `script.js` are illustrative sample data. They are not verified members or active offers. Keep this clear in any public preview and replace demo content only with consented, accurate listings.

Each sample listing has a `type` (`people`, `gigs`, `gear`, `help`) for category filtering, a `searchable` text field used by local keyword search, a location, tags, and CSS artwork class. Update all those values together when adding or changing a sample listing. Never use unsanitized user-submitted data in `innerHTML` in a production application; render user content with safe DOM APIs or a framework's escaping and validate on the server.

The signup dialog is a front-end demonstration only. It neither stores nor transmits data. Do not collect actual member information until the backend, security, privacy policy, retention rules, and consent flows are ready. The login screen is also a placeholder.
