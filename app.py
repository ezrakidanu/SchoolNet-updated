"""SchoolNet WSGI entry point. Developer and author: Ezra Kidanu."""
from __future__ import annotations

import os

from schoolnet import create_app


if __name__ == "__main__":
    os.environ.setdefault("APP_ENV", "development")

app = create_app()


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "5000")),
        debug=app.config["APP_ENV"] == "development",
    )
