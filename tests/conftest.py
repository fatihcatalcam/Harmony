from pathlib import Path
import sys

import pytest
import werkzeug
try:
    werkzeug.__version__
except AttributeError:
    werkzeug.__version__ = "3.0.0"


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Harmony import create_app
from Harmony.extensions import csrf, db, talisman


@pytest.fixture(scope="session")
def app(tmp_path_factory):
    test_db_path = tmp_path_factory.mktemp("data") / "test.db"
    app = create_app()
    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{test_db_path}",
        WTF_CSRF_ENABLED=False,
        SERVER_NAME="localhost",
        SESSION_COOKIE_SECURE=False,
        TALISMAN_FORCE_HTTPS=False,
    )

    csrf.exempt(app.view_functions["main.send_message"])
    talisman.force_https = False
    talisman.force_https_permanent = False

    with app.app_context():
        db.session.remove()
        db.engine.dispose()
        db.drop_all()
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    test_client = app.test_client()
    test_client.environ_base["wsgi.url_scheme"] = "https"
    return test_client


