# SchoolNet Standalone Flask Rebuild Plan

## Product and implementation approach

Rebuild SchoolNet as a conventional, self-contained Flask application that can run with `python app.py` locally and with `gunicorn app:app` on Render. The backend uses an application factory, Flask-Login browser sessions, Flask-WTF CSRF protection, Flask-SQLAlchemy models, and a configurable SQLAlchemy URL. SQLite is the local default; PostgreSQL is selected with `DATABASE_URL` and the bundled psycopg driver. Registration stores normalized unique email addresses and Werkzeug password hashes—never plaintext passwords. No third-party identity provider, Manus session, publisher key, JWT exchange, external API, or platform-only account code remains in the standalone export.

Keep the SchoolNet community feed, the three seeded staff profiles, demo announcements/events, comments, reactions, post search/category filtering, and the installable PWA. Anonymous visitors can browse; each signed-in user can publish as their own registered account, react, and comment. Demo announcements remain authored by their seeded staff profiles, while users cannot select/impersonate those profiles. Cookie-authenticated writes are ordinary same-origin POST forms with CSRF tokens. Account email addresses and password data never appear in feed templates.

The application owns its manifest and root-scoped service worker. Only the app shell and local static resources may be cached; account, feed, comment, reaction, and auth endpoints remain network-only. The development database uses a fresh standalone filename so an existing legacy SQLite file is not overwritten or interpreted as the new ORM schema. Existing legacy content is not implicitly migrated; document this clearly and retain the old file untouched.

## Dessie school identity and persistent sign-in update

Present the correct institution as **Dessie Special Boarding School (YWMDSBS Dessie)** across the shared desktop/mobile headers, feed welcome, signup/login identity banners, browser/PWA metadata, README, and project documentation. Remove every placeholder-school-name reference while retaining SchoolNet as the product name and Ezra Kidanu as the sole creator, developer, and author.

Keep the login email convenience value only in browser local storage; never persist the password in local storage, cookies, or application state beyond the submitted request. Add an explicit, default-checked “Remember me on this device” option backed by Flask-Login's signed, HTTP-only, secure-on-HTTPS remember cookie, with a documented 30-day lifetime. Logout clears the remembered session. Keep secure cookie settings compatible with HTTPS Preview, and explicitly document the local HTTP override.

## Project structure

```text
app.py                         # Root WSGI target: app = create_app()
  run.py                         # Optional local development runner
schoolnet/
  __init__.py                  # Factory, production config, startup seeding, headers
  models.py                    # User, Profile, Post, Comment, Like, Event ORM models
  forms.py                     # CSRF-protected signup/login/post/comment/logout forms
  auth.py                      # Independent signup/login/logout routes
  routes.py                    # Feed, post, staff, calendar, health, and PWA routes
  seed.py                      # Idempotent fictional staff/content seed data
templates/
  base.html                    # Shared navigation, account actions, flash messages, Ezra credit
  index.html                   # Searchable/filterable social feed and signed-in composer
  post_detail.html             # Announcement, comments, reactions
  people.html                  # Staff directory
  profile.html                 # Dedicated staff profile
  calendar.html                # Upcoming school events
  auth/login.html              # Email/password login
  auth/signup.html             # Independent account registration
  404.html                     # Branded not-found page
  error.html                   # Branded server-error page
static/
  css/styles.css               # Responsive sage-green social app styles
  js/app.js                    # Install prompt and service-worker registration
  js/icons.js                  # Inline local SVG icon helper
  images/                      # Existing logo, science photo, and PWA icons
  manifest.webmanifest         # Application-owned PWA metadata
  service-worker.js            # Root-scope static-shell cache only
tests/test_app.py              # Isolated temporary-database auth/feed/PWA regressions
requirements.txt               # Runtime packages only
Procfile                        # Render/Gunicorn command
Dockerfile                      # Optional standalone container
.env.example                    # Safe environment-variable names/examples
.python-version                 # Python runtime declaration
README.md                       # Ezra-attributed setup, security, Render, and GitHub handoff
ASSETS.md                       # Asset and attribution notes
TODO.md                         # Explicit requirement outcomes
```

Delete or replace the existing Manus-specific token/OAuth/auth implementation, bespoke SQLite layer, frontend bearer-token API client, obsolete JS-rendered view modules, and legacy tests. Preserve the existing visual identity and app icon assets. Keep project-host metadata separate from application runtime; the standalone export omits platform-only metadata and route declarations.

## Design

- **Design Movement:** Retain the existing friendly editorial social-feed direction, with the quiet clarity of a school newsletter and card-based community interactions.
- **Core Principles:** Make browsing immediate; tie every new post to a real app account; keep school information legible and calm; keep account controls and privacy boundaries explicit.
- **Color Philosophy:** Preserve sage green and pale mint as cues for belonging and steady growth, balanced by warm white surfaces and dark readable text.
- **Layout Paradigm:** Keep the compact navigation rail, wide central announcement stream, and narrow community/events rail on desktop; collapse to a focused single-column feed and bottom navigation on phones.
- **Signature Elements:** Preserve the original open-book logo; use color-coded category pills and staff monogram avatars; retain a restrained pinned-announcement band and compact event-date blocks.
- **Interaction Philosophy:** Prefer accessible server-rendered forms and visible success/error feedback. Authentication and publishing happen through protected forms; small enhancements never become required for core workflows.
- **Animation:** Keep existing entry transitions subtle, avoid motion that blocks reading, and honor `prefers-reduced-motion`.
- **Typography System:** Use local system-ui sans-serif stacks for headings and body copy, preserving the current compact editorial hierarchy without a remote font dependency.
- **Brand Essence:** “The calm, trustworthy home for a school's everyday announcements and people.” Personality: welcoming, clear, dependable.
- **Brand Voice:** Headlines are warm and specific; buttons say exactly what they do. Examples: “A good day to stay connected.” and “Share an update with your school.”
- **Wordmark & Logo:** Keep the existing custom open-book SchoolNet SVG and its companion name lockup rather than replacing it with a generic icon font.
- **Signature Brand Color:** SchoolNet sage `#39735b`, supported by light mint `#eaf3ed`.

## Deployment and operating constraints

`requirements.txt` contains only the runtime framework, ORM, session/CSRF/email-validation support, PostgreSQL driver, and Gunicorn. `Procfile` uses a Gunicorn WSGI command on `app:app`; Render's `PORT` is honored by the container and local server. Production must provide a stable high-entropy `SECRET_KEY`; local development may generate an ephemeral one. Secure session cookies default on in production and off only for local HTTP. Use PostgreSQL through `DATABASE_URL` for durable deployed data; Render's SQLite quick-start default is a smoke-test convenience and its filesystem may be ephemeral.

The export is a standalone source tree suitable for a normal GitHub repository. Exclude `.env`, virtual environments, database files, Manus project metadata, and any secret. Do not connect or push to a user-owned GitHub repository without an explicit repository/connection request. Save the completed project checkpoint in the existing project as required by its environment, then provide a clean source ZIP for direct user export.
