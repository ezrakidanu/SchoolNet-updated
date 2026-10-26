"""Public browsing and authenticated community actions."""
from __future__ import annotations

from pathlib import Path
from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from sqlalchemy import or_
from . import db
from .forms import CommentForm, PostForm
from .models import Comment, Event, Like, Post, Profile, User


main_bp = Blueprint("main", __name__)
CATEGORIES = ("Academics", "Clubs", "Sports", "General")


def _feed_query():
    query = Post.query
    category = request.args.get("category", "All").strip()
    search = request.args.get("q", "").strip()
    order = request.args.get("sort", request.args.get("order", "latest"))
    if category in CATEGORIES:
        query = query.filter(Post.category == category)
    else:
        category = "All"
    if search:
        escaped = search.replace("%", "\\%").replace("_", "\\_")
        pattern = f"%{escaped}%"
        query = query.outerjoin(Profile, Post.profile_id == Profile.id).outerjoin(
            Post.user
        ).filter(or_(Post.title.ilike(pattern), Post.content.ilike(pattern),
                     Profile.name.ilike(pattern), Post.user.has(User.display_name.ilike(pattern))))
    if order == "oldest":
        query = query.order_by(Post.created_at.asc(), Post.id.asc())
    else:
        order = "latest"
        query = query.order_by(Post.pinned.desc(), Post.created_at.desc(), Post.id.desc())
    return query, category, search, order


@main_bp.get("/")
def index():
    query, category, search, order = _feed_query()
    return render_template("index.html", posts=query.all(), profiles=Profile.query.filter_by(user_id=None).order_by(Profile.id).all(),
                           events=Event.query.order_by(Event.starts_at).all(), category=category,
                           search=search, order=order, categories=CATEGORIES)


@main_bp.post("/posts")
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(user=current_user, profile=current_user.profile, category=form.category.data, title=form.title.data.strip(),
                    content=form.content.data.strip())
        db.session.add(post)
        db.session.commit()
        flash("Your announcement has been published.", "success")
    else:
        flash("Please check the post details and try again.", "error")
    return redirect(url_for("main.index"))


@main_bp.get("/posts/<int:post_id>")
def post_detail(post_id: int):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    return render_template("post_detail.html", post=post, posts=[post], comment_form=CommentForm(),
                           profiles=Profile.query.filter_by(user_id=None).order_by(Profile.id).all(),
                           events=Event.query.order_by(Event.starts_at).all(), categories=CATEGORIES)


@main_bp.post("/posts/<int:post_id>/comments")
@login_required
def add_comment(post_id: int):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    form = CommentForm()
    if form.validate_on_submit():
        db.session.add(Comment(post=post, user=current_user, content=form.content.data.strip()))
        db.session.commit()
        flash("Your comment has been added.", "success")
    else:
        flash("Please enter a comment of up to 500 characters.", "error")
    return redirect(url_for("main.post_detail", post_id=post_id))


@main_bp.post("/posts/<int:post_id>/like")
@login_required
def toggle_like(post_id: int):
    post = db.session.get(Post, post_id)
    if post is None:
        abort(404)
    like = Like.query.filter_by(post_id=post_id, user_id=current_user.id).first()
    if like:
        db.session.delete(like)
        flash("Reaction removed.", "success")
    else:
        db.session.add(Like(post=post, user=current_user))
        flash("You liked this post.", "success")
    db.session.commit()
    return redirect(url_for("main.post_detail", post_id=post_id))


@main_bp.get("/people")
def people():
    query = Profile.query
    term = request.args.get("q", "").strip()
    if term:
        pattern = f"%{term}%"
        query = query.filter(or_(Profile.name.ilike(pattern), Profile.role.ilike(pattern), Profile.department.ilike(pattern)))
    return render_template("people.html", profiles=query.order_by(Profile.name).all(),
                           posts=[], events=Event.query.order_by(Event.starts_at).all(), categories=CATEGORIES)


@main_bp.get("/people/<int:profile_id>")
def profile(profile_id: int):
    person = db.session.get(Profile, profile_id)
    if person is None:
        abort(404)
    return render_template("profile.html", profile=person,
                           posts=Post.query.filter_by(profile_id=person.id).order_by(Post.created_at.desc()).all(),
                           profiles=Profile.query.order_by(Profile.id).all(),
                           events=Event.query.order_by(Event.starts_at).all())


@main_bp.get("/calendar")
def calendar():
    events = Event.query.order_by(Event.starts_at).all()
    term = request.args.get("q", "").strip()
    if term:
        pattern = f"%{term}%"
        events = Event.query.filter(or_(Event.title.ilike(pattern), Event.location.ilike(pattern), Event.description.ilike(pattern))).order_by(Event.starts_at).all()
    return render_template("calendar.html", events=events, posts=[],
                           profiles=Profile.query.filter_by(user_id=None).order_by(Profile.id).all(), categories=CATEGORIES)


@main_bp.get("/health")
def health():
    db.session.execute(db.text("SELECT 1"))
    return {"status": "ok"}


@main_bp.get("/manifest.webmanifest")
def manifest():
    manifest_path = Path(current_app.static_folder) / "manifest.webmanifest"
    response = current_app.response_class(manifest_path.read_bytes(), mimetype="application/manifest+json")
    response.headers["Cache-Control"] = "no-cache"
    return response


@main_bp.get("/service-worker.js")
def service_worker():
    # The checked-in worker is the app-owned source. Strip navigation caching so
    # account/data pages can never be persisted as a shared offline response.
    worker_path = Path(current_app.static_folder) / "service-worker.js"
    source = worker_path.read_text(encoding="utf-8")
    response = current_app.response_class(source, mimetype="application/javascript")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["Service-Worker-Allowed"] = "/"
    return response
