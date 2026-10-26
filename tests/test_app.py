from __future__ import annotations

import ast
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from schoolnet import create_app, normalize_database_url
from schoolnet.models import Comment, Event, Like, Post, Profile, User


class SchoolNetTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = Path(tempfile.mkdtemp(prefix="schoolnet-test-"))
        self.database = self.tempdir / "schoolnet.db"
        self.config = {
            "TESTING": True,
            "SECRET_KEY": "unit-test-secret-key-with-sufficient-entropy",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{self.database}",
            "WTF_CSRF_ENABLED": False,
            "SESSION_COOKIE_SECURE": True,
            "SESSION_COOKIE_HTTPONLY": True,
            "SESSION_COOKIE_SAMESITE": "Lax",
        }
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def signup(self, client=None, email="person@example.com", password="correct horse battery", name="Avery Student"):
        client = client or self.client
        return client.post("/auth/signup", data={
            "name": name, "email": email, "password": password,
            "confirm_password": password,
        }, follow_redirects=False)

    def login(self, client=None, email="person@example.com", password="correct horse battery"):
        client = client or self.client
        return client.post("/auth/login", data={"email": email, "password": password, "remember_me": "y"})

    def post_data(self, **extra):
        return {"category": "Academics", "title": "An account-authored update",
                "content": "This announcement is authored by the account that is signed in.", **extra}

    def test_demo_seed_is_complete_and_idempotent(self):
        with self.app.app_context():
            self.assertEqual([(p.name, p.role) for p in Profile.query.order_by(Profile.id)], [
                ("Mr. Abebe", "Physics Teacher"),
                ("Ms. Sara", "Science Club Coordinator"),
                ("Coach Dan", "Sports Director"),
            ])
            self.assertEqual(Post.query.count(), 4)
            self.assertEqual(Event.query.count(), 3)
            self.assertEqual(Post.query.first().author_name, "Mr. Abebe")
            self.assertEqual(Post.query.first().author_role, "Physics Teacher")
            self.assertEqual(Post.query.first().author_initials, "MA")
        again = create_app(self.config)
        with again.app_context():
            self.assertEqual(Post.query.count(), 4)
            self.assertEqual(Event.query.count(), 3)

    def test_signup_normalizes_unique_email_hashes_password_and_logs_in(self):
        response = self.signup(email="  Avery@Example.COM  ")
        self.assertEqual(response.status_code, 302)
        self.assertIn("remember_token=", response.headers.get("Set-Cookie", ""))
        with self.app.app_context():
            user = User.query.one()
            self.assertEqual(user.email, "avery@example.com")
            self.assertNotEqual(user.password_hash, "correct horse battery")
            self.assertTrue(user.password_hash.startswith("scrypt:"))
            self.assertTrue(user.check_password("correct horse battery"))
            self.assertFalse(user.check_password("wrong password"))
        duplicate = self.signup(self.app.test_client(), email="AVERY@example.com")
        self.assertEqual(duplicate.status_code, 200)
        with self.app.app_context():
            self.assertEqual(User.query.count(), 1)

    def test_login_logout_and_secure_session_defaults(self):
        self.signup()
        other = self.app.test_client()
        bad_client = self.app.test_client()
        bad = bad_client.post("/auth/login", data={"email": "person@example.com", "password": "bad"})
        self.assertEqual(bad.status_code, 200)
        self.assertIn(b'value="person@example.com"', bad.data)
        self.assertNotIn(b'value="bad"', bad.data)
        response = self.login(other)
        self.assertEqual(response.status_code, 302)
        self.assertIn("remember_token=", response.headers.get("Set-Cookie", ""))
        with other.session_transaction() as session:
            self.assertTrue(session)
        other.delete_cookie(self.app.config["SESSION_COOKIE_NAME"])
        restored = other.get("/", base_url="https://localhost")
        self.assertIn(b"Posting as Avery Student", restored.data)
        logout = other.post("/auth/logout")
        self.assertEqual(logout.status_code, 302)
        self.assertIn("remember_token=;", "\n".join(logout.headers.getlist("Set-Cookie")))
        cookie = self.app.config
        self.assertTrue(cookie["SESSION_COOKIE_SECURE"])
        self.assertTrue(cookie["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual(cookie["SESSION_COOKIE_SAMESITE"], "None")
        self.assertTrue(cookie["REMEMBER_COOKIE_SECURE"])
        self.assertTrue(cookie["REMEMBER_COOKIE_HTTPONLY"])
        self.assertEqual(cookie["REMEMBER_COOKIE_SAMESITE"], "None")
        self.assertEqual(cookie["REMEMBER_COOKIE_DURATION"].days, 30)

    def test_dessie_school_branding_and_email_only_browser_persistence(self):
        expected = b"Dessie Special Boarding School"
        for path in ["/", "/auth/login", "/auth/signup", "/people", "/calendar"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertIn(expected, response.data, path)
            self.assertIn(b"YWMDSBS Dessie", response.data, path)
            self.assertNotIn(b"Greenwood", response.data, path)
        login_page = self.client.get("/auth/login")
        self.assertIn(b'data-persist-email="true"', login_page.data)
        self.assertIn(b'name="remember_me"', login_page.data)
        self.assertIn(b'<input checked', login_page.data)
        app_script = Path("static/js/app.js").read_text(encoding="utf-8")
        self.assertIn("schoolnet-account-email", app_script)
        self.assertIn("window.localStorage.setItem(emailStorageKey, email)", app_script)
        self.assertIn("input.form?.addEventListener('submit', saveEmail)", app_script)
        self.assertNotRegex(app_script, r"localStorage\.(?:setItem|getItem)\([^)]*password")
        manifest = self.client.get("/manifest.webmanifest").get_json()
        self.assertIn("Dessie Special Boarding School", manifest["name"])
        self.assertIn("YWMDSBS Dessie", manifest["description"])
        self.assertNotIn("Greenwood", Path("README.md").read_text(encoding="utf-8"))
        self.assertIn("Sole creator, developer", Path("README.md").read_text(encoding="utf-8"))

    def test_posting_uses_actual_account_and_ignores_profile_spoof(self):
        self.signup()
        response = self.client.post("/posts", data=self.post_data(profile_id="1"), follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        with self.app.app_context():
            post = Post.query.filter_by(title="An account-authored update").one()
            self.assertEqual(post.author_name, "Avery Student")
            self.assertEqual(post.author_role, "Community member")
            self.assertEqual(post.profile.user_id, post.user.id)
            self.assertNotEqual(post.profile_id, 1)
            self.assertEqual(post.user.email, "person@example.com")

    def test_anonymous_writes_require_login(self):
        self.assertEqual(self.client.post("/posts", data=self.post_data()).status_code, 302)
        self.assertEqual(self.client.post("/posts/1/comments", data={"content": "A thoughtful response"}).status_code, 302)
        self.assertEqual(self.client.post("/posts/1/like").status_code, 302)

    def test_comments_and_likes_are_account_bound(self):
        self.signup()
        self.client.post("/posts", data=self.post_data())
        comment_response = self.client.post("/posts/1/comments", data={"content": "  Thanks for sharing this update.  "})
        self.assertEqual(comment_response.status_code, 302)
        with self.app.app_context():
            comment = Comment.query.one()
            self.assertEqual(comment.content, "Thanks for sharing this update.")
            self.assertEqual(comment.user.email, "person@example.com")
            self.assertEqual(comment.post.comment_count, 1)
        first = self.client.post("/posts/1/like")
        self.assertEqual(first.status_code, 302)
        with self.app.app_context():
            self.assertEqual(Like.query.count(), 1)
        self.client.post("/posts/1/like")
        with self.app.app_context():
            self.assertEqual(Like.query.count(), 0)

    def test_feed_search_categories_profiles_and_calendar(self):
        for path in ["/", "/?category=Academics", "/?q=physics", "/?order=oldest", "/people", "/people/1", "/calendar", "/posts/1"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
        with self.app.test_request_context("/?category=Sports&q=field&order=oldest"):
            from schoolnet.routes import _feed_query
            query, category, search, order = _feed_query()
            self.assertEqual(category, "Sports")
            self.assertEqual(search, "field")
            self.assertEqual(order, "oldest")
            self.assertEqual([p.title for p in query.all()], ["Your next chapter starts on the field."])

    def test_sqlite_database_persists_across_app_instances(self):
        self.signup()
        self.client.post("/posts", data=self.post_data())
        reopened = create_app(self.config)
        with reopened.app_context():
            self.assertEqual(Post.query.count(), 5)
            self.assertEqual(User.query.count(), 1)

    def test_csrf_protects_account_and_content_mutations(self):
        config = {**self.config, "WTF_CSRF_ENABLED": True}
        app = create_app(config)
        client = app.test_client()
        denied = client.post("/auth/signup", data={"name": "Test User", "email": "test@example.com",
                                                    "password": "long enough password", "confirm_password": "long enough password"})
        self.assertEqual(denied.status_code, 400)
        signup_page = client.get("/auth/signup")
        match = re.search(rb'name="csrf_token" type="hidden" value="([^"]+)"', signup_page.data)
        self.assertIsNotNone(match)
        token = match.group(1).decode()
        allowed = client.post("/auth/signup", data={"csrf_token": token, "name": "Test User",
            "email": "test@example.com", "password": "long enough password",
            "confirm_password": "long enough password"})
        self.assertEqual(allowed.status_code, 302)

    def test_manifest_worker_health_and_no_sensitive_route_cache(self):
        self.assertEqual(self.client.get("/health").get_json(), {"status": "ok"})
        manifest = self.client.get("/manifest.webmanifest")
        self.assertEqual(manifest.status_code, 200)
        self.assertEqual(manifest.mimetype, "application/manifest+json")
        self.assertEqual(manifest.get_json()["scope"], "/")
        worker = self.client.get("/service-worker.js")
        source = worker.get_data(as_text=True)
        self.assertEqual(worker.status_code, 200)
        self.assertIn("schoolnet-shell-v3", source)
        self.assertEqual(worker.headers["Service-Worker-Allowed"], "/")
        self.assertEqual(worker.headers["Cache-Control"], "no-cache")
        self.assertIn("url.pathname.startsWith('/auth/')", source)
        self.assertNotIn("cache.put('/', response.clone())", source)
        self.assertIn("request.mode === 'navigate'", source)
        self.assertIn("url.pathname.startsWith('/posts/')", source)
        self.assertNotIn("await cache.put('/'", source)

    def test_default_database_and_required_route_names(self):
        default_app = create_app({"TESTING": True, "SECRET_KEY": "default-path-test"})
        self.assertTrue(default_app.config["SQLALCHEMY_DATABASE_URI"].endswith("instance/schoolnet_standalone.db"))
        endpoints = {rule.endpoint: rule.rule for rule in self.app.url_map.iter_rules()}
        self.assertEqual(endpoints["auth.signup"], "/auth/signup")
        self.assertEqual(endpoints["auth.login"], "/auth/login")
        self.assertEqual(endpoints["auth.logout"], "/auth/logout")
        self.assertEqual(endpoints["main.create_post"], "/posts")
        self.assertEqual(endpoints["main.add_comment"], "/posts/<int:post_id>/comments")
        self.assertEqual(endpoints["main.toggle_like"], "/posts/<int:post_id>/like")

    def test_postgresql_url_normalization(self):
        self.assertEqual(normalize_database_url("postgres://u:p@db/school"), "postgresql+psycopg://u:p@db/school")
        self.assertEqual(normalize_database_url("postgresql://u:p@db/school"), "postgresql+psycopg://u:p@db/school")
        self.assertEqual(normalize_database_url("postgresql+psycopg://u:p@db/school"), "postgresql+psycopg://u:p@db/school")

    def test_production_requires_secret(self):
        with self.assertRaisesRegex(RuntimeError, "SECRET_KEY"):
            create_app({**self.config, "APP_ENV": "production", "SECRET_KEY": None})
        production = create_app({**self.config, "APP_ENV": "production", "SECRET_KEY": "stable-production-secret"})
        self.assertEqual(production.config["APP_ENV"], "production")

    def test_runtime_modules_have_no_external_token_auth_imports(self):
        runtime = [Path("app.py"), *Path("schoolnet").glob("*.py")]
        forbidden = {"jwt", "requests"}
        imported = set()
        for path in runtime:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.update(alias.name.split(".")[0] for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imported.add(node.module.split(".")[0])
        self.assertFalse(imported & forbidden, imported & forbidden)


if __name__ == "__main__":
    unittest.main(verbosity=2)
