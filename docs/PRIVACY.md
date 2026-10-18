# Privacy notice — implementation draft

**Not a final legal notice.** This draft must be reviewed and completed by the service owner and a qualified privacy professional before public signup. Add the controller's full legal identity, contact details, hosting location, retention period, processors, and applicable Nigeria/international privacy requirements.

## Current pilot data

When a member registers, the pilot stores email, display name, media discipline, city, a salted PBKDF2 password hash, and account creation time. It stores gig posts, applications and their messages, and reports. Raw passwords are not stored. Session identifiers are stored as hashes; the browser receives an HttpOnly, SameSite=Strict cookie. CSRF tokens are stored with sessions. Search filters are used to query gig listings and are not intentionally persisted.

Do not post phone numbers, home addresses, identity documents, payment information, or other sensitive personal details in gig descriptions or applications. Public gig responses reveal the poster's display name and professional fields, not email. Applicants' name, discipline, city, and application message are visible to the gig poster. An applicant's email is shared only if they explicitly tick the opt-in on the application form; it is off by default.

## Purpose and sharing

Data is used to operate accounts, display gigs, route applications to posters, prevent abuse, and respond to reports. The current pilot has no analytics, advertising, payment provider, email delivery, or third-party messaging integration. Hosting providers and operational backups may process/store data; disclose the actual providers before launch.

## Retention and rights

The pilot has not yet automated account export/deletion or established a final retention schedule. Before public launch, publish a support contact and implement access/correction/deletion requests, account closure, backup deletion windows, and retention rules for safety reports and legal obligations. Users can contact **[insert monitored privacy email]** for requests.

## Security

Use HTTPS, restrict database file permissions, encrypt and back up production storage, rotate secrets, patch dependencies, limit moderator access, and never expose the SQLite database or secrets from static routes. Notify affected people and regulators as required if a breach occurs.
