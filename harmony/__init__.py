import importlib
import importlib.util
import os
import warnings

from flask import Flask

if importlib.util.find_spec("dotenv") is not None:
    load_dotenv = importlib.import_module("dotenv").load_dotenv
else:  # pragma: no cover - optional dependency warning
    def load_dotenv(*args, **kwargs):
        warnings.warn(
            "python-dotenv is not installed; environment variables will not be auto-loaded.",
            RuntimeWarning,
            stacklevel=2,
        )
        return False

from .extensions import csrf, db, limiter, migrate, socketio, talisman
from .routes import register_routes


def _detect_async_mode():
    if importlib.util.find_spec("eventlet"):
        return "eventlet"
    return "threading"


def create_app():
    load_dotenv()

    app = Flask(__name__)

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_secret_key")
    app.config["SPOTIFY_CLIENT_ID"] = os.getenv("SPOTIFY_CLIENT_ID", "your_spotify_client_id")
    app.config["SPOTIFY_CLIENT_SECRET"] = os.getenv("SPOTIFY_CLIENT_SECRET", "your_spotify_client_secret")
    app.config["SPOTIFY_REDIRECT_URI"] = os.getenv(
        "SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5000/callback"
    )

    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    instance_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "instance"))
    os.makedirs(instance_path, exist_ok=True)
    app.instance_path = instance_path

    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(instance_path, 'app.db')}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    csrf.init_app(app)

    csp = {
        "default-src": ["'self'", "*"],
        "style-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.tailwindcss.com",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net",
            "https://fonts.googleapis.com",
        ],
        "script-src": [
            "'self'",
            "'unsafe-inline'",
            "https://cdn.tailwindcss.com",
            "https://cdnjs.cloudflare.com",
            "https://cdn.jsdelivr.net",
            "https://unpkg.com",
            "https://cdn.socket.io",
        ],
    }
    talisman.init_app(app, content_security_policy=csp)

    socketio.init_app(app, async_mode=_detect_async_mode())

    register_routes(app)

    from . import sockets  # noqa: F401

    with app.app_context():
        db.create_all()

    return app


__all__ = ["create_app", "db", "migrate", "socketio"]
