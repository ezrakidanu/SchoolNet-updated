"""Idempotent fictional staff, announcement, and event seed data."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from . import db
from .models import Event, Post, Profile


def seed_demo_data() -> None:
    profiles = [
        (1, "Mr. Abebe", "Physics Teacher", "Helping students turn careful practice into confident progress.", "MA", "#7B9175", "Science Department"),
        (2, "Ms. Sara", "Science Club Coordinator", "Making space for questions, experiments, and imaginative thinking.", "MS", "#8B769A", "Student Life"),
        (3, "Coach Dan", "Sports Director", "Building teamwork, courage, and joy beyond the classroom.", "CD", "#C98458", "Athletics"),
    ]
    profile_objects = {}
    for ident, name, role, bio, initials, color, department in profiles:
        profile = db.session.get(Profile, ident)
        if profile is None:
            profile = Profile(id=ident, name=name, role=role, bio=bio, initials=initials, color=color, department=department)
            db.session.add(profile)
        profile_objects[ident] = profile

    now = datetime.now(timezone.utc).replace(microsecond=0)
    post_data = [
        ("seed-physics", 1, "Academics", "A little preparation. A lot of possibility.", "Our next physics revision session is coming up. Bring your questions, your formula sheet, and a friend as we prepare together for the upcoming exam.\n\nA little practice today can make a big difference tomorrow. Check the school calendar for the details.", now, True, None),
        ("seed-science-club", 2, "Clubs", "Big ideas start with a little curiosity.", "Science Club registration is now open. Join us for practical investigations, thoughtful conversation, and a welcoming first meetup this week.", now - timedelta(hours=3), False, "/static/images/science-lab.jpg"),
        ("seed-sports", 3, "Sports", "Your next chapter starts on the field.", "Football trials are approaching. All experience levels are welcome—come ready to move, learn, and support your teammates.", now - timedelta(hours=7), False, None),
        ("seed-library", 1, "General", "A quiet place to focus is waiting for you.", "The library study area will stay open after lessons this week for anyone looking for a calm space to read, revise, or work with classmates.", now - timedelta(days=1), False, None),
    ]
    for key, profile_id, category, title, content, created_at, pinned, image in post_data:
        if Post.query.filter_by(seed_key=key).first() is None:
            db.session.add(Post(seed_key=key, profile=profile_objects[profile_id], category=category,
                                title=title, content=content, created_at=created_at, pinned=pinned, image=image))

    event_data = [
        (1, "Physics revision session", "Academics", 2, 15, 30, "Physics Lab", "A friendly revision session focused on key exam topics and student questions."),
        (2, "Science Club meetup", "Clubs", 4, 16, 0, "Innovation Room", "Meet fellow curious minds, plan experiments, and register for the term ahead."),
        (3, "Inter-house sports day", "Sports", 7, 9, 0, "Main Field", "A day of spirited, inclusive competition for every house and every supporter."),
    ]
    for ident, title, category, days, hour, minute, location, description in event_data:
        if db.session.get(Event, ident) is None:
            starts_at = (now + timedelta(days=days)).replace(hour=hour, minute=minute, second=0)
            db.session.add(Event(id=ident, title=title, category=category, starts_at=starts_at,
                                 location=location, description=description))
    db.session.commit()
