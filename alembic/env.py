import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.database.database import Base
from app.models.user import User  # noqa: F401
from app.models.email_verification import EmailVerification  # noqa: F401
from app.models.social_link import SocialLink  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.password_reset import PasswordReset  # noqa: F401
from app.models.track import Track  # noqa: F401
from app.models.playlist import Playlist  # noqa: F401
from app.models.playlist_track import PlaylistTrack  # noqa: F401
from app.models.follow import Follow  # noqa: F401
from app.models.block import Block  # noqa: F401
from app.models.conversation import Conversation  # noqa: F401
from app.models.message import Message  # noqa: F401
from app.models.listening_history import ListeningHistory  # noqa: F401
from app.models.comment import Comment  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.playlist_like import PlaylistLike  # noqa: F401
from app.models.like import Like  # noqa: F401
from app.models.repost import Repost  # noqa: F401
from app.models.report import Report  # noqa: F401

config = context.config

# ✅ Override alembic.ini URL with environment variable
database_url = os.environ.get("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
