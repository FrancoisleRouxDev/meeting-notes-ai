import os
import tempfile

# Point the app at a throwaway database before the app is imported.
_test_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(_test_dir, "test.db").replace("\\", "/")
os.environ["SESSION_COOKIE_SECURE"] = "false"

import pytest  # noqa: E402

from app.db import Base, engine  # noqa: E402
from helpers import make_client  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def alice():
    return make_client("alice@example.com")


@pytest.fixture
def bob():
    return make_client("bob@example.com")
