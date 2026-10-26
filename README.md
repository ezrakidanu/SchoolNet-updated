# SchoolNet · Dessie Special Boarding School (YWMDSBS Dessie)

**Sole creator, developer & author: Ezra Kidanu**

SchoolNet is the official responsive school-community space for **Dessie Special Boarding School (YWMDSBS Dessie)**, for announcements, staff updates, member conversations, and school events. It uses server-rendered Flask/Jinja pages, local CSS and images, and small progressive-enhancement scripts. The interface uses a sage-and-mint editorial-social design, with desktop rail navigation and a compact mobile bar.

Seeded staff profiles and sample announcements/events are illustrative. Do not use this application for sensitive student information without a separate security, privacy, and operational review.

## Local setup

Use Python **3.12 or newer**. From the project directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Copy the safe environment example and generate a private application secret if you want local sessions to survive a server restart:

```bash
cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Paste the generated value into `SECRET_KEY` in `.env`, and do not commit that file. The app loads `.env` locally, defaults to `APP_ENV=development`, and generates a temporary secret if `SECRET_KEY` is blank. For local HTTP only, keep `SESSION_COOKIE_SECURE=false`; public HTTPS uses Secure, HttpOnly cookies with `SameSite=None` for embedded Preview compatibility. Leave `DATABASE_URL` blank to use `instance/schoolnet_standalone.db`, or set `DATABASE_URL=sqlite:///schoolnet_standalone.db` (SQLite URLs are relative to Flask's `instance/` directory). The legacy `instance/schoolnet.db` is deliberately not the default and remains untouched.

Start the local app with:

```bash
python run.py
```

Then open `http://127.0.0.1:5000`. For a public deployment, use HTTPS and set `SESSION_COOKIE_SECURE=true`.

## Member flows and security

Visitors can browse the Dessie Special Boarding School community feed, people directory, profiles, and calendar without JavaScript. Signup and sign-in use the `/auth/signup` and `/auth/login` pages; sign-out submits a CSRF-protected POST to `/auth/logout`. Signed-in members publish with their own registered name, react to updates, and comment. Publishing does not offer a staff-identity selector. Existing seeded staff announcements should continue to display their staff authors, including Mr. Abebe (Physics Teacher), Ms. Sara (Science Club Coordinator), and Coach Dan (Sports Director).

Every state-changing form includes a server-validated CSRF token. Passwords must be stored using a suitable one-way password-hashing method; never display or log plaintext passwords. Email addresses and passwords are account credentials and must not be included in public profiles, posts, comments, or application logs. Escape user-supplied text when rendering HTML and validate all submitted values on the server.

Successful sign-ins can persist for 30 days with Flask-Login's signed, HttpOnly remember cookie; the sign-in page includes a checked “Remember me on this device” control. The browser may remember the email address only in local storage to refill the form. Passwords are never stored in local storage, cookies, or JavaScript. Logout clears the remembered session. A stable production `SECRET_KEY` and durable user database are required for sessions to survive server deployments.
New accounts require a password at least 12 characters long; change password rules deliberately and review all existing accounts if they are ever altered.

Category filtering, search, and sorting use ordinary GET requests so the feed remains useful without client-side scripting. The local JavaScript is limited to install-prompt handling, service-worker registration, and decorative icon semantics; it does not provide authentication or publishing APIs.

## Deployment on Render

Create a Python web service from the GitHub repository. Use:

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4`
- **Health-check path:** `/health`

Set a fresh high-entropy `SECRET_KEY`, `APP_ENV=production`, and `SESSION_COOKIE_SECURE=true` in the Render service's environment. Do not put credentials in source control, build arguments, frontend code, or logs.

Use a managed PostgreSQL database for durable live data and provide its connection URL as `DATABASE_URL`. SQLite is appropriate for local development and small, single-instance experiments only. SQLite files on Render's ordinary ephemeral filesystem can be lost when an instance is replaced or redeployed; do not treat that filesystem as durable storage. If intentionally using a persistent disk, plan backups and restore procedures and confirm the deployment's storage and scaling behavior.

The application exposes `/health` for a lightweight health check. Verify signup, login, logout, CSRF-protected publishing, reactions, comments, and durable writes in the deployed environment before inviting members.

## Routes and project layout

The page interface is organized around these endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/` | Community feed with GET category, search, and sort controls |
| POST | `/posts` | Publish an update as the signed-in member |
| GET | `/posts/<post_id>` | View an announcement and its conversation |
| POST | `/posts/<post_id>/comments` | Add a member comment |
| POST | `/posts/<post_id>/like` | Toggle a member reaction |
| GET | `/people` | Browse and search school profiles |
| GET | `/people/<profile_id>` | View a profile and related updates |
| GET | `/calendar` | Browse school events |
| GET/POST | `/auth/signup` | Create an account |
| GET/POST | `/auth/login` | Sign in |
| POST | `/auth/logout` | Sign out |
| GET | `/health` | Deployment health check |

```text
schoolnet/
├── README.md                      # Setup, security, and deployment guide
├── app.py                         # Root WSGI entry point: app:app
├── run.py                         # Optional development runner
├── schoolnet/
│   ├── __init__.py                # App factory, config, CSRF and extensions
│   ├── models.py                  # Users, profiles, posts, comments, likes, events
│   ├── forms.py                   # Validated CSRF-protected forms
│   ├── auth.py                    # Signup, login, logout
│   ├── routes.py                  # Feed, people, events, and health routes
│   └── seed.py                    # Fictional demo profiles, posts, and events
├── templates/
│   ├── base.html                 # Shared navigation, shell, PWA entry, author footer
│   ├── index.html                # Server-rendered community feed and publish form
│   ├── auth/                     # Signup and sign-in pages
│   ├── post_detail.html          # Announcement and comments
│   ├── people.html               # Directory
│   ├── profile.html              # Profile detail
│   ├── calendar.html             # Event list
│   ├── 404.html, error.html      # Branded error pages
│   └── _macros.html              # Inline SVG and avatar macros
├── static/
│   ├── css/styles.css            # Standalone responsive sage/mint styling
│   ├── js/app.js                 # PWA install prompt and service-worker setup
│   ├── js/icons.js               # Decorative inline-icon semantics
│   ├── images/                   # Local logo, PWA icons, and Science Club photo
│   ├── manifest.webmanifest     # Installable app identity
│   └── service-worker.js         # Static app-shell asset cache only
├── tests/                        # Automated regression tests
├── requirements.txt              # Python dependencies
├── Procfile                       # Render/Gunicorn command using $PORT
├── .env.example                   # Safe configuration template
├── .python-version                # Python runtime version
├── .gitignore                     # Secrets, runtime data, and caches
└── ASSETS.md                     # Visual asset and source notes
```

## Database and existing local data

`DATABASE_URL` should point to SQLite for local work or PostgreSQL for durable hosted data. Configure automated database backups for live deployments and test a restore before depending on the service.
For a new database the application creates its tables on startup. No schema migration framework is bundled; use an explicit migration plan/tool before changing model schemas on a deployed database.

The legacy custom `instance/schoolnet.db` remains untouched. No old-data auto-migration is performed; keep a separate backup and plan an intentional migration if existing records need to be carried forward.

## Progressive Web App and offline limits

SchoolNet links `/manifest.webmanifest` and registers `/service-worker.js` at the site root. The worker caches only the public static shell assets that exist in `static/` and the manifest. It never stores rendered feed pages, account pages, authentication, comments, reactions, or other data responses. The PWA install banner uses Android Chrome's `beforeinstallprompt` when available; otherwise it shows the browser-menu install steps.

Offline availability is intentionally limited to cached styles, scripts, logo, and image assets. Fresh pages and all account or community data still require an internet connection; the app does not present stale feed content as current while offline. Public PWA installation requires HTTPS (except on localhost).

## Tests

Run the repository's test suite with:

```bash
python -m unittest discover -s tests -v
```

All 15 repository regression tests pass in the build environment. They cover signup/login/logout, password hashing and normalization, 30-day remembered sessions and logout clearing, email-only browser autofill, Dessie branding, CSRF enforcement, account-bound publishing/comments/reactions, profile/feed rendering, SQLite persistence, production secret checks, PostgreSQL URL normalization, health, and private-data cache exclusions. PostgreSQL URL normalization is tested, but a live PostgreSQL service was not available for integration testing.

## Exporting to GitHub

Commit the source, local static assets, templates, and documentation. Keep `.env`, generated secrets, database files, user data, backups, and deployment credentials out of Git. Review the repository's ignore rules before staging files, and use Render environment settings or a managed secret store for production configuration.
