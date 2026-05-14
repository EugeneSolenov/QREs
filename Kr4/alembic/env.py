import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import models  # noqa: F401,E402
from app.database import Base, DATABASE_URL  # noqa: E402

cfg = context.config

if cfg.config_file_name is not None:
    fileConfig(cfg.config_file_name)

cfg.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", DATABASE_URL))
target_metadata = Base.metadata


def f1():
    url = cfg.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def f2():
    con = engine_from_config(
        cfg.get_section(cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with con.connect() as c:
        context.configure(connection=c, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    f1()
else:
    f2()
