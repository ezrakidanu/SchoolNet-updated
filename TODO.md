# Standalone SchoolNet rebuild outcomes

- [x] **Project structure and independence.** Organize SchoolNet as a flat or standard clean Flask package with a clear `app.py` (or `run.py`) entry point at the root level, plus `templates/` for HTML pages, `static/` for CSS/JS/images, and clearly defined routes. Remove Manus-specific dependencies, internal account logins, restricted hooks, and platform-only runtime assumptions so it runs entirely independently.
- [x] **Email/password accounts and persistence.** Implement standard Sign Up / Login / Logout using Flask-Login and SQLAlchemy (with SQLite or PostgreSQL compatibility). Users can register independently without third-party or platform-locked authentication. Store password hashes, protect browser forms against CSRF, and publish/comment under the signed-in account rather than permitting impersonation of a staff profile.
- [x] **SchoolNet community functionality.** Preserve the existing responsive announcement feed and dedicated profiles for Mr. Abebe (Physics Teacher), Ms. Sara (Science Club Coordinator), and Coach Dan (Sports Director), seeded school posts and events, and the installable PWA. Account-created posts identify their registered author; existing fictional staff seed posts retain staff attribution.
- [x] **Ezra Kidanu authorship.** Clearly establish Ezra Kidanu as the sole creator, developer, and author across the README, code comments, footer credits, and project documentation.
- [x] **Deployment dependencies and Render start command.** Include a clean `requirements.txt` containing only necessary dependencies (Flask, Flask-SQLAlchemy, Flask-Login, Gunicorn, and required form/driver packages). Provide a working `Procfile` or exact Gunicorn command (`gunicorn app:app`) optimized for Render, use Render's `PORT`, and include valid environment/setup instructions for a production secret and PostgreSQL.
- [x] **Exportable standalone source.** Ensure the complete source tree contains no missing imports or broken package references and builds/runs with the documented commands. Provide a clean ZIP ready to export to GitHub, excluding secrets, databases, virtual environments, and platform-only metadata. Do not connect or push to an unprovided user-owned GitHub repository.
- [x] **Dessie Special Boarding School branding.** Hardcode the correct school name—“Dessie Special Boarding School” (YWMDSBS Dessie)—across all UI headers, welcome screens, login banners, and README files. Remove references to placeholder names such as “Greenwood”; retain SchoolNet as the app name.
- [x] **Persistent login without password exposure.** Fix the state bug where entered email and login inputs are forgotten. Retain the email locally for convenience and retain authenticated login sessions with a secure persistent session mechanism; do not store or persist a plaintext password.

## Verification evidence

- `python3 -m unittest discover -s tests -v`: all 15 tests passed, including remembered-login restoration after deleting the short-lived session cookie, logout revocation, email-only local autofill, exact Dessie identity, and default-on remember control.
- `python3 -m compileall -q app.py run.py schoolnet tests`, JavaScript syntax checks, and `git diff --check` passed.
- Preview `/`, `/auth/login`, `/auth/signup`, `/health`, `/manus-routes.json`, `/manifest.webmanifest`, and `/service-worker.js` returned HTTP 200; HTTPS-preview session-cookie flags were verified as `Secure`, `HttpOnly`, and `SameSite=None`. Mobile screenshots showed the school identity and login controls fit the 390px layout.
- A production-mode Gunicorn WSGI smoke test returned HTTP 200 for `/health` and the CSRF-enabled `/auth/signup` page with the documented environment settings.
- PostgreSQL URL normalization is covered; no live PostgreSQL service was available for connection testing. The legacy `instance/schoolnet.db` is not used as the ORM default and is documented as unmigrated.
- The GitHub-ready source bundle was integrity-checked and excludes secret files, database files, bytecode, and platform-only project metadata.

## Implementation notes

Keep the existing visual design, logo, staff content, and PWA while replacing the old token/OAuth flow and raw SQLite persistence with conventional Flask components. Leave the legacy `instance/schoolnet.db` untouched and use a separate ORM database path; do not silently claim that old runtime records have been migrated. SQLite is convenient for local use; PostgreSQL via `DATABASE_URL` is the durable deployment option.
