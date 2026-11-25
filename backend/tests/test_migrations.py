from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text

from app import models  # noqa: F401
from app.core.config import settings
from app.db import Base
from app.models_slack import SlackConnection  # noqa: F401


@pytest.mark.parametrize("existing_schema", [False, True])
def test_upgrade_builds_or_adopts_database(tmp_path, monkeypatch, existing_schema):
    database_path = tmp_path / "migration-test.db"
    database_url = f"sqlite:///{database_path.as_posix()}"
    if existing_schema:
        legacy_engine = create_engine(database_url)
        Base.metadata.create_all(bind=legacy_engine)
        with legacy_engine.begin() as connection:
            connection.execute(text("ALTER TABLE action_items DROP COLUMN source_line"))
        legacy_engine.dispose()

    monkeypatch.setattr(settings, "database_url", database_url)
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    command.upgrade(config, "head")
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    inspector = inspect(engine)
    assert {"users", "meetings", "action_items", "slack_connections"} <= set(
        inspector.get_table_names()
    )
    assert "source_line" in {
        column["name"] for column in inspector.get_columns("action_items")
    }
    transcript = next(column for column in inspector.get_columns("meetings") if column["name"] == "transcript")
    assert transcript["nullable"] is True
    engine.dispose()
