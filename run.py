"""Optional local runner; production WSGI imports app:app from app.py."""
from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "development")

from app import app  # noqa: E402


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=app.config["APP_ENV"] == "development",
    )
