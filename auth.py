"""Email/password account registration and session management. Sole creator, developer, and author: Ezra Kidanu."""
from __future__ import annotations

from urllib.parse import urljoin, urlsplit
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError
from . import db
from .forms import LoginForm, SignupForm
from .models import Profile as UserProfile, User


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def _safe_next_url(target: str | None) -> bool:
    if not target:
        return False
    ref = urlsplit(request.host_url)
    test = urlsplit(urljoin(request.host_url, target))
    return test.scheme in {"http", "https"} and ref.netloc == test.netloc


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = SignupForm()
    if request.method == "POST" and form.email.data:
        form.email.data = form.email.data.strip()
    if form.validate_on_submit():
        user = User(email=form.email.data, display_name=form.name.data.strip(), role="Community member")
        user.set_password(form.password.data)
        user.profile = UserProfile(name=user.name, role=user.role,
            bio="A SchoolNet community member.", initials=user.initials,
            color="#6F927D", department="Community")
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            form.email.errors.append("An account with this email already exists.")
        else:
            login_user(user, remember=True)
            flash("Your account is ready. Welcome to Dessie Special Boarding School!", "success")
            return redirect(url_for("main.index"))
    return render_template("auth/signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = LoginForm()
    if request.method == "POST" and form.email.data:
        form.email.data = form.email.data.strip()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().casefold()).first()
        if user is None or not user.check_password(form.password.data):
            flash("Check your email and password, then try again.", "error")
        else:
            # Remembered sessions are signed, HTTP-only cookies; passwords are never persisted.
            login_user(user, remember=form.remember_me.data)
            flash("You are now logged in.", "success")
            target = request.args.get("next")
            return redirect(target if _safe_next_url(target) else url_for("main.index"))
    return render_template("auth/login.html", form=form)


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "success")
    return redirect(url_for("main.index"))
