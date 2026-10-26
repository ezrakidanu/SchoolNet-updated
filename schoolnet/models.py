"""Database models for accounts, staff profiles, community posts and events."""
from __future__ import annotations

from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, ForeignKeyConstraint, UniqueConstraint
from sqlalchemy.orm import validates
from werkzeug.security import check_password_hash, generate_password_hash
from . import db


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(254), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    role = db.Column(db.String(80), nullable=False, default="Community member")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    profile = db.relationship("Profile", back_populates="user", uselist=False,
                               cascade="all, delete-orphan")
    posts = db.relationship("Post", back_populates="user", foreign_keys="Post.user_id",
                            cascade="all, delete-orphan")
    comments = db.relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    likes = db.relationship("Like", back_populates="user", cascade="all, delete-orphan")

    @validates("email")
    def normalize_email(self, _key, value: str) -> str:
        return value.strip().casefold()

    @property
    def name(self) -> str:
        return self.display_name

    @property
    def initials(self) -> str:
        return "".join(part[0] for part in self.name.split()[:2]).upper() or "U"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), unique=True, nullable=True)
    name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(120), nullable=False)
    bio = db.Column(db.Text, nullable=False)
    initials = db.Column(db.String(8), nullable=False)
    color = db.Column(db.String(24), nullable=False)
    department = db.Column(db.String(120), nullable=False)
    user = db.relationship("User", back_populates="profile", foreign_keys=[user_id])
    posts = db.relationship("Post", back_populates="profile", foreign_keys="Post.profile_id")
    __table_args__ = (UniqueConstraint("user_id", "id", name="uq_profile_owner_id"),)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True, index=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("profile.id", ondelete="RESTRICT"), nullable=False, index=True)
    seed_key = db.Column(db.String(80), unique=True, nullable=True)
    category = db.Column(db.String(24), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, index=True)
    pinned = db.Column(db.Boolean, nullable=False, default=False)
    image = db.Column(db.String(255), nullable=True)
    user = db.relationship("User", back_populates="posts", foreign_keys=[user_id])
    profile = db.relationship("Profile", back_populates="posts", foreign_keys=[profile_id])
    comments = db.relationship("Comment", back_populates="post", cascade="all, delete-orphan", order_by="Comment.created_at")
    likes = db.relationship("Like", back_populates="post", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("category IN ('Academics', 'Clubs', 'Sports', 'General')", name="ck_post_category"),
        ForeignKeyConstraint(["user_id", "profile_id"], ["profile.user_id", "profile.id"],
                             name="fk_post_owner_profile"),
    )

    @property
    def author_name(self) -> str:
        return self.user.name if self.user is not None else self.profile.name

    @property
    def author_role(self) -> str:
        return self.user.role if self.user is not None else self.profile.role

    @property
    def author_initials(self) -> str:
        return self.user.initials if self.user is not None else self.profile.initials

    @property
    def image_path(self) -> str | None:
        return self.image.removeprefix("/static/") if self.image else None

    @property
    def like_count(self) -> int:
        return len(self.likes)

    @property
    def comment_count(self) -> int:
        return len(self.comments)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    post = db.relationship("Post", back_populates="comments")
    user = db.relationship("User", back_populates="comments")


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    post = db.relationship("Post", back_populates="likes")
    user = db.relationship("User", back_populates="likes")
    __table_args__ = (UniqueConstraint("post_id", "user_id", name="uq_like_post_user"),)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    category = db.Column(db.String(40), nullable=False)
    starts_at = db.Column(db.DateTime(timezone=True), nullable=False, index=True)
    location = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)

    @property
    def time(self) -> str:
        hour = self.starts_at.strftime("%I").lstrip("0") or "0"
        return f"{hour}:{self.starts_at:%M %p}"
