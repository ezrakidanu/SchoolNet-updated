"""SchoolNet Flask application factory and extension wiring. Sole creator, developer, and author: Ezra Kidanu."""
from __future__ import annotations

import os
import secrets
from datetime import timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from flask import Flask, render_template, request
from flask_login import LoginManager, current_user
from sqlalchemy import event
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect


db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def normalize_database_url(url: str) -> str:
    """Use psycopg 3 explicitly for PostgreSQL URLs from common providers."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _is_production(config: dict[str, Any]) -> bool:
    return str(config.get("APP_ENV") or "").strip().lower() == "production"


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    load_dotenv()
    default_env = "testing" if test_config and test_config.get("TESTING") else "production"
    app_env = os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or default_env
    project_root = Path(__file__).resolve().parent.parent
    app = Flask(__name__, instance_relative_config=True,
                template_folder=str(project_root / "templates"),
                static_folder=str(project_root / "public" / "static"), static_url_path="/static")
    instance_path = Path(app.instance_path)
    database_url = os.environ.get("DATABASE_URL")
    on_vercel = bool(os.environ.get("VERCEL") or os.environ.get("VERCEL_ENV"))
    if on_vercel and not database_url:
        raise RuntimeError("DATABASE_URL must be configured on Vercel; use a persistent PostgreSQL database, not function-local SQLite.")
    if not on_vercel:
        instance_path.mkdir(parents=True, exist_ok=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=normalize_database_url(database_url or f"sqlite:///{instance_path / 'schoolnet_standalone.db'}"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="None",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="None",
        REMEMBER_COOKIE_DURATION=timedelta(days=30),
        WTF_CSRF_TIME_LIMIT=3600,
        APP_ENV=app_env,
    )
    if test_config:
        app.config.update(test_config)

    secure_cookie = (test_config.get("SESSION_COOKIE_SECURE") if test_config and "SESSION_COOKIE_SECURE" in test_config
                     else os.environ.get("SESSION_COOKIE_SECURE"))
    if test_config and "APP_ENV" in test_config and "SESSION_COOKIE_SECURE" not in test_config:
        secure_cookie = None
    # HTTPS Preview and production require Secure; local HTTP opts out explicitly in .env.
    app.config["SESSION_COOKIE_SECURE"] = _as_bool(secure_cookie, True)
    app.config["REMEMBER_COOKIE_SECURE"] = app.config["SESSION_COOKIE_SECURE"]
    cookie_samesite = "None" if app.config["SESSION_COOKIE_SECURE"] else "Lax"
    app.config["SESSION_COOKIE_SAMESITE"] = cookie_samesite
    app.config["REMEMBER_COOKIE_SAMESITE"] = cookie_samesite

    if _is_production(app.config):
        if not app.config.get("SECRET_KEY"):
            raise RuntimeError("SECRET_KEY must be set in production.")
    elif not app.config.get("SECRET_KEY"):
        # Development only: convenient for `python app.py`; sessions reset on restart.
        app.config["SECRET_KEY"] = secrets.token_urlsafe(32)

    app.config["SQLALCHEMY_DATABASE_URI"] = normalize_database_url(app.config["SQLALCHEMY_DATABASE_URI"])
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
        sqlite_path = app.config["SQLALCHEMY_DATABASE_URI"].removeprefix("sqlite:///")
        if sqlite_path and sqlite_path != ":memory:":
            Path(sqlite_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to continue."
    csrf.init_app(app)

    from . import models  # noqa: F401 - register model metadata before create_all
    from .auth import auth_bp
    from .routes import CATEGORIES, main_bp
    from .seed import seed_demo_data

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    @login_manager.user_loader
    def load_user(user_id: str):
        try:
            return db.session.get(models.User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.context_processor
    def template_contract():
        from .forms import CommentForm, LogoutForm, PostForm
        return {"post_form": PostForm(), "comment_form": CommentForm(), "logout_form": LogoutForm(),
                "categories": CATEGORIES,
                "current_user": current_user if current_user.is_authenticated else None}

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        if request.path.startswith("/auth/") or request.method != "GET":
            response.headers["Cache-Control"] = "no-store"
        elif request.endpoint and request.endpoint.startswith("main.") and request.endpoint not in {"main.health", "main.manifest", "main.service_worker"}:
            response.headers["Cache-Control"] = "private, no-store"
        return response

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("error.html"), 500

    with app.app_context():
        if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite:"):
            @event.listens_for(db.engine, "connect")
            def _enable_sqlite_foreign_keys(connection, _record):
                cursor = connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        db.create_all()
        seed_demo_data()
    return app
