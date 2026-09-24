from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import settings
from app.db_url import resolve_database_url_from_environ
from app.database import Base
from app import models  # noqa: F401
from app import knowledge_models  # noqa: F401
from app import orchestration_models  # noqa: F401
from app import finops_models  # noqa: F401
from app import experience_models  # noqa: F401
from app import opportunity_models  # noqa: F401

config = context.config
db_url = resolve_database_url_from_environ() or settings.database_url
if not db_url or db_url.startswith("driver://"):
    db_url = settings.database_url

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(db_url, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
